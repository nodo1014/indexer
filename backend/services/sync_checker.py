import os
from typing import Dict, List
import numpy as np
import whisper
import pysrt
from Levenshtein import ratio as levenshtein_ratio
import random

# 미디어 길이 추출 (ffprobe)
def get_media_duration(media_path: str) -> float:
    import subprocess, json
    cmd = [
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'json', media_path
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe 오류: {proc.stderr}")
    info = json.loads(proc.stdout)
    return float(info['format']['duration'])

# SRT에서 구간 텍스트 추출
def extract_subtitle_text(subs: List, start: float, end: float) -> str:
    texts = []
    for sub in subs:
        sub_start = sub.start.ordinal / 1000.0
        sub_end = sub.end.ordinal / 1000.0
        if sub_end < start:
            continue
        if sub_start > end:
            break
        texts.append(sub.text.replace('\n', ' '))
    return ' '.join(texts)

def check_subtitle_sync(media_path: str, subtitle_path: str, sample_count: int = 3) -> Dict:
    """
    미디어 파일과 자막 파일의 싱크를 샘플 구간(앞/중/끝 등)에서 대조한다.
    Whisper로 구간 STT → 자막 구간 텍스트와 비교 → 유사도/오프셋 계산
    반환: {'success': bool, 'sync': bool, 'score': float, 'details': [...], 'error': str|None}
    """
    try:
        # 1. 미디어 길이 측정
        duration = get_media_duration(media_path)
        if duration < 30:
            return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': '미디어 길이가 너무 짧음'}
        # 2. 샘플 구간 선정 (앞/중/끝, 랜덤 오프셋)
        sample_len = min(10, duration // (sample_count+1))  # 각 샘플 구간 길이(초)
        positions = np.linspace(0, duration-sample_len, sample_count)
        positions = [max(0, float(p) + random.uniform(-2, 2)) for p in positions]
        # 3. 자막 파싱
        subs = pysrt.open(subtitle_path, encoding='utf-8')
        # 4. Whisper 모델 로드 (base)
        model = whisper.load_model('base')
        details = []
        scores = []
        for idx, start in enumerate(positions):
            end = min(start + sample_len, duration)
            # 5. ffmpeg로 구간 추출 (wav 임시파일)
            tmp_wav = f"/tmp/sync_sample_{os.getpid()}_{idx}.wav"
            cmd = [
                'ffmpeg', '-y', '-ss', str(start), '-to', str(end), '-i', media_path,
                '-ar', '16000', '-ac', '1', '-vn', '-loglevel', 'error', tmp_wav
            ]
            import subprocess
            proc = subprocess.run(cmd, capture_output=True)
            if proc.returncode != 0:
                return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': f'ffmpeg 오류: {proc.stderr.decode()}'}
            # 6. Whisper로 STT
            stt_result = model.transcribe(tmp_wav, language=None)
            stt_text = ' '.join([seg['text'].strip() for seg in stt_result.get('segments', [])])
            # 7. 자막 텍스트 추출
            subtitle_text = extract_subtitle_text(subs, start, end)
            # 8. 유사도/싱크 오차 계산
            similarity = levenshtein_ratio(stt_text, subtitle_text) if subtitle_text else 0.0
            scores.append(similarity)
            details.append({
                'sample_idx': idx+1,
                'start': round(start, 2),
                'end': round(end, 2),
                'stt_text': stt_text,
                'subtitle_text': subtitle_text,
                'similarity': round(similarity, 3)
            })
            os.remove(tmp_wav)
        avg_score = float(np.mean(scores)) if scores else 0.0
        sync = avg_score > 0.7  # 임계값(조정 가능)
        return {
            'success': True,
            'sync': sync,
            'score': round(avg_score, 3),
            'details': details,
            'error': None
        }
    except Exception as e:
        return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': str(e)}

def advanced_sync_and_save(media_path: str, subtitle_path: str, save_path: str = None, first_sec: int = 120, sample_count: int = 3, sync_threshold: float = 0.7, max_shift_sec: float = 3.0) -> Dict:
    """
    1. 자막의 첫 부분(0~first_sec)에서 Whisper(en) STT와 자막을 대조
    2. 일치하면 앞/중/끝 3구간에서 싱크 오차 측정
    3. 오차가 크면 pysrt로 자막을 shift 보정
    4. 미디어와 같은 폴더, 같은 이름(.srt)로 저장
    반환: {'success': bool, 'sync': bool, 'score': float, 'details': [...], 'error': str|None, 'save_path': str}
    """
    import shutil
    try:
        # 1. 미디어 길이 측정
        duration = get_media_duration(media_path)
        if duration < 30:
            return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': '미디어 길이가 너무 짧음', 'save_path': None}
        # 2. 자막 파싱
        subs = pysrt.open(subtitle_path, encoding='utf-8')
        # 3. Whisper 모델 로드 (en)
        model = whisper.load_model('tiny')
        # 4. 첫 부분(0~first_sec) 대조
        first_end = min(first_sec, duration)
        # ffmpeg로 첫 부분 추출
        tmp_wav = f"/tmp/sync_first_{os.getpid()}.wav"
        cmd = [
            'ffmpeg', '-y', '-ss', '0', '-to', str(first_end), '-i', media_path,
            '-ar', '16000', '-ac', '1', '-vn', '-loglevel', 'error', tmp_wav
        ]
        import subprocess
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': f'ffmpeg 오류: {proc.stderr.decode()}', 'save_path': None}
        stt_result = model.transcribe(tmp_wav, language="en")
        stt_text = ' '.join([seg['text'].strip() for seg in stt_result.get('segments', [])])
        subtitle_text = extract_subtitle_text(subs, 0, first_end)
        similarity = levenshtein_ratio(stt_text, subtitle_text) if subtitle_text else 0.0
        os.remove(tmp_wav)
        if similarity < sync_threshold:
            return {'success': False, 'sync': False, 'score': similarity, 'details': [{'section': 'first', 'similarity': similarity}], 'error': '자막과 미디어가 일치하지 않음', 'save_path': None}
        # 5. 앞/중/끝 3구간 싱크 대조
        sample_len = min(10, duration // (sample_count+1))  # 각 샘플 구간 길이(초)
        positions = np.linspace(0, duration-sample_len, sample_count)
        positions = [max(0, float(p)) for p in positions]
        details = []
        offsets = []
        scores = []
        for idx, start in enumerate(positions):
            end = min(start + sample_len, duration)
            tmp_wav = f"/tmp/sync_sample_{os.getpid()}_{idx}.wav"
            cmd = [
                'ffmpeg', '-y', '-ss', str(start), '-to', str(end), '-i', media_path,
                '-ar', '16000', '-ac', '1', '-vn', '-loglevel', 'error', tmp_wav
            ]
            proc = subprocess.run(cmd, capture_output=True)
            if proc.returncode != 0:
                return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': f'ffmpeg 오류: {proc.stderr.decode()}', 'save_path': None}
            stt_result = model.transcribe(tmp_wav, language="en")
            stt_text = ' '.join([seg['text'].strip() for seg in stt_result.get('segments', [])])
            subtitle_text = extract_subtitle_text(subs, start, end)
            similarity = levenshtein_ratio(stt_text, subtitle_text) if subtitle_text else 0.0
            # 싱크 오프셋(초) 추정: STT segment와 자막 segment의 시작 시간 차이 평균
            stt_starts = [seg['start'] for seg in stt_result.get('segments', [])]
            sub_starts = [sub.start.ordinal/1000.0 for sub in subs if sub.start.ordinal/1000.0 >= start and sub.start.ordinal/1000.0 < end]
            if stt_starts and sub_starts:
                offset = np.mean([s - t for s, t in zip(sub_starts, stt_starts[:len(sub_starts)])])
            else:
                offset = 0.0
            offsets.append(offset)
            scores.append(similarity)
            details.append({
                'sample_idx': idx+1,
                'start': round(start, 2),
                'end': round(end, 2),
                'stt_text': stt_text,
                'subtitle_text': subtitle_text,
                'similarity': round(similarity, 3),
                'offset': round(offset, 2)
            })
            os.remove(tmp_wav)
        avg_score = float(np.mean(scores)) if scores else 0.0
        avg_offset = float(np.mean(offsets)) if offsets else 0.0
        sync = avg_score > sync_threshold and abs(avg_offset) < max_shift_sec
        # 6. 오프셋이 크면 자막 shift 보정
        if abs(avg_offset) > 0.5:  # 0.5초 이상이면 보정
            for sub in subs:
                sub.start = sub.start + avg_offset
                sub.end = sub.end + avg_offset
        # 7. 저장 경로 결정
        if not save_path:
            base, _ = os.path.splitext(media_path)
            save_path = base + ".srt"
        subs.save(save_path, encoding='utf-8')
        return {
            'success': True,
            'sync': sync,
            'score': round(avg_score, 3),
            'avg_offset': round(avg_offset, 2),
            'details': details,
            'error': None,
            'save_path': save_path
        }
    except Exception as e:
        return {'success': False, 'sync': False, 'score': 0.0, 'details': [], 'error': str(e), 'save_path': None} 