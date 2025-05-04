import os
import requests
from typing import List, Dict
import re
from difflib import SequenceMatcher

# OpenSubtitles API 정보 (환경변수/설정에서 관리)
OPENSUBTITLES_API_URL = os.getenv('OPENSUBTITLES_API_URL', 'https://api.opensubtitles.com/api/v1')
OPENSUBTITLES_API_KEY = os.getenv('OPENSUBTITLES_API_KEY', '')

# 파일명 정제 함수 (확장자, 해상도, 코덱, 릴그룹 등 제거)
def clean_title(title: str) -> str:
    title = re.sub(r'\.(mp4|mkv|avi|srt|ass|vtt)$', '', title, flags=re.I)
    title = re.sub(r'\b(720p|1080p|2160p|4k|x264|h264|x265|hevc|bluray|web-dl|hdrip|dvdrip|aac|dts|hdtv|remux|yts|rarbg|ettv|evo|fgt|ntb|ctrlhd|lol|killers|dimension|publichd|ettv|yify|web|webrip|amzn|nf|ddp5?1|dd5?1|h\.?264|h\.?265|ac3|mp3|flac|subs?)\b', '', title, flags=re.I)
    title = re.sub(r'[^\w\s]', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    return title.strip().lower()

# 두 파일명(정제 후) 유사도(0~1) 반환
def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, clean_title(a), clean_title(b)).ratio()

# 실제 OpenSubtitles API 연동: 자막 후보 리스트 검색
def download_subtitle_from_opensubtitles(filename: str, language: str = 'ko') -> Dict:
    """
    파일명/언어로 OpenSubtitles에서 자막 후보 리스트를 검색하여 반환한다.
    각 후보별로 media_title과의 일치율(%)을 계산, best_match(최고 일치율 후보)도 함께 반환.
    실패 시 목업/샘플 데이터 반환.
    """
    headers = {
        'Api-Key': OPENSUBTITLES_API_KEY,
        'Content-Type': 'application/json',
    }
    params = {
        'query': filename,
        'languages': language,
        'order_by': 'downloads',
        'order_direction': 'desc',
        'limit': 10
    }
    try:
        resp = requests.get(f"{OPENSUBTITLES_API_URL}/subtitles", headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        candidates = []
        for item in data.get('data', []):
            sub_fn = item.get('attributes', {}).get('files', [{}])[0].get('file_name', '')
            sim = title_similarity(filename, sub_fn)
            candidates.append({
                'filename': sub_fn,
                'lang': item.get('attributes', {}).get('language', ''),
                'download_url': item.get('attributes', {}).get('url', ''),
                'release': item.get('attributes', {}).get('release', ''),
                'fps': item.get('attributes', {}).get('fps', ''),
                'votes': item.get('attributes', {}).get('votes', 0),
                'downloads': item.get('attributes', {}).get('downloads_count', 0),
                'similarity': round(sim * 100, 1)
            })
        # 최고 일치율 후보
        best_match = max(candidates, key=lambda c: c['similarity'], default=None)
        return {'success': True, 'candidates': candidates, 'best_match': best_match}
    except Exception as e:
        # 실패 시 목업 데이터 반환
        mock_candidates = [
            {'filename': f'{filename}.ko.srt', 'lang': 'ko', 'download_url': 'https://example.com/mock1.srt', 'release': 'WEB-DL', 'fps': 23.976, 'votes': 10, 'downloads': 1000},
            {'filename': f'{filename}.en.srt', 'lang': 'en', 'download_url': 'https://example.com/mock2.srt', 'release': 'BluRay', 'fps': 24.0, 'votes': 5, 'downloads': 500}
        ]
        for c in mock_candidates:
            c['similarity'] = round(title_similarity(filename, c['filename']) * 100, 1)
        best_match = max(mock_candidates, key=lambda c: c['similarity'], default=None)
        return {
            'success': False,
            'error': str(e),
            'candidates': mock_candidates,
            'best_match': best_match
        }

# 실제 자막 파일 다운로드 및 저장

def download_and_save_subtitle(download_url: str, save_path: str) -> Dict:
    """
    지정된 URL에서 자막 파일을 다운로드하여 save_path에 저장한다.
    """
    try:
        resp = requests.get(download_url, timeout=10)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        return {'success': True, 'save_path': save_path}
    except Exception as e:
        return {'success': False, 'error': str(e)} 