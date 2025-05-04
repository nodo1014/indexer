import os
import logging
from pathlib import Path
from typing import List, Dict, Set, Any
import subprocess

logger = logging.getLogger(__name__)

# 지원하는 미디어 확장자 분류
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
# 지원하는 자막 파일 확장자
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".smi", ".ass"}

def scan_media_files(directory: str, filter_video: bool = True, filter_audio: bool = True) -> List[Dict[str, str]]:
    """지정된 디렉토리와 하위 디렉토리를 스캔하여 미디어 파일(자막 유무 포함) 전체를 반환합니다 (타입 필터링 적용)."""
    media_files: List[Dict[str, str]] = []
    processed_basenames: Set[str] = set()
    allowed_extensions: Set[str] = set()
    if filter_video:
        allowed_extensions.update(VIDEO_EXTENSIONS)
    if filter_audio:
        allowed_extensions.update(AUDIO_EXTENSIONS)

    if not allowed_extensions:
        logger.warning("스캔할 미디어 타입이 선택되지 않았습니다 (영상/오디오 모두 해제됨). 빈 목록을 반환합니다.")
        return []

    try:
        target_path = Path(directory)
        if not target_path.is_dir():
            logger.error(f"지정된 경로가 디렉토리가 아닙니다: {directory}")
            return []

        logger.info(f"디렉토리 스캔 시작: {directory} (Video: {filter_video}, Audio: {filter_audio})")
        for item in target_path.rglob('*'):
            if item.is_file():
                file_ext = item.suffix.lower()
                base_name = item.stem
                full_path_str = str(item.resolve())

                if base_name in processed_basenames:
                    continue

                # 1. 미디어 파일인지 확인 (선택된 필터 기준)
                if file_ext in allowed_extensions:
                    subtitle_files = []
                    for sub_ext in SUBTITLE_EXTENSIONS:
                        # 기본 자막 (movie.srt)
                        subtitle_path = item.with_suffix(sub_ext)
                        if subtitle_path.exists():
                            subtitle_files.append(subtitle_path.name)
                        # 언어 코드 포함 자막 (movie_en.srt)
                        parent_dir = item.parent
                        for lang_code in ['_en', '_ko', '_ja', '_zh']:
                            lang_sub_name = f"{base_name}{lang_code}{sub_ext}"
                            lang_sub_path = parent_dir / lang_sub_name
                            if lang_sub_path.exists():
                                subtitle_files.append(lang_sub_path.name)
                    has_subtitle = len(subtitle_files) > 0
                    media_files.append({
                        "name": item.name,
                        "path": full_path_str,
                        "type": "video" if file_ext in VIDEO_EXTENSIONS else "audio",
                        "has_subtitle": has_subtitle,
                        "subtitle_files": subtitle_files
                    })
                    processed_basenames.add(base_name)
                    logger.debug(f"미디어 파일: {item.name}, 자막: {subtitle_files if has_subtitle else '없음'}")

                # 2. 자막 파일이면, 해당 파일명(언어코드 제외)을 처리된 것으로 간주
                elif file_ext in SUBTITLE_EXTENSIONS:
                    processed_basenames.add(base_name)
                    for lang_code in ['_en', '_ko', '_ja', '_zh']:
                        if base_name.endswith(lang_code):
                            original_base_name = base_name[:-len(lang_code)]
                            processed_basenames.add(original_base_name)
                            break

        logger.info(f"디렉토리 스캔 완료: {len(media_files)}개의 미디어 파일 반환 (자막 유무 포함)")

    except Exception as e:
        logger.error(f"디렉토리 스캔 중 오류 발생: {e}", exc_info=True)

    return sorted(media_files, key=lambda x: x['path'])

def list_subdirectories(directory: str) -> List[str]:
    """지정된 디렉토리의 하위 디렉토리 목록(절대 경로)을 반환합니다."""
    subdirs = []
    logger.info(f"[list_subdirectories] 시작: '{directory}'") 
    
    try:
        base_path = Path(directory).resolve()  # 절대 경로로 변환
        
        if not base_path.exists():
            logger.error(f"[list_subdirectories] 경로가 존재하지 않음: '{directory}'")
            return subdirs
            
        if not base_path.is_dir():
            logger.warning(f"[list_subdirectories] '{directory}'는 디렉토리가 아님.")
            return subdirs
            
        logger.info(f"[list_subdirectories] '{base_path}'는 디렉토리임. 내용 확인 시작.")
        
        # 디렉토리 목록만 추출 (rglob 대신 iterdir 사용)
        for item in base_path.iterdir():
            if item.is_dir():
                subdirs.append(str(item.resolve()))  # 절대 경로로 추가
                logger.debug(f"[list_subdirectories] 하위 디렉토리 발견: {item}")
        
        # 이름 순으로 정렬
        subdirs.sort()
        logger.info(f"[list_subdirectories] 발견된 하위 디렉토리 ({len(subdirs)}개): {subdirs}") 
        
    except PermissionError as e:
        logger.error(f"하위 디렉토리 목록 조회 중 권한 오류: {directory} - {e}")
    except Exception as e:
        logger.error(f"하위 디렉토리 목록 조회 중 오류: {directory} - {e}", exc_info=True)
        
    return subdirs

def count_media_recursive(directory: Path) -> (int, int):
    """디렉토리 내 모든 하위 폴더까지 영상/오디오 파일 개수를 재귀적으로 합산"""
    video_count = 0
    audio_count = 0
    try:
        for item in directory.iterdir():
            if item.is_file():
                ext = item.suffix.lower()
                if ext in VIDEO_EXTENSIONS:
                    video_count += 1
                elif ext in AUDIO_EXTENSIONS:
                    audio_count += 1
            elif item.is_dir():
                v, a = count_media_recursive(item)
                video_count += v
                audio_count += a
    except Exception as e:
        logger.warning(f"[count_media_recursive] '{directory}' 내부 파일 개수 집계 중 오류: {e}")
    return video_count, audio_count

def list_subdirectories_with_media_counts(directory: str) -> list:
    """
    지정된 디렉토리의 하위 디렉토리 목록(절대 경로)과 각 디렉토리 내 영상/오디오 파일 개수를 (하위폴더까지 포함하여) 반환합니다.
    반환 예시: [{ 'name': 'Movies', 'path': '/mnt/qq/Movies', 'video_count': 3, 'audio_count': 1 }, ...]
    """
    subdirs_info = []
    logger.info(f"[list_subdirectories_with_media_counts] 시작: '{directory}'")
    try:
        base_path = Path(directory).resolve()
        if not base_path.exists() or not base_path.is_dir():
            logger.warning(f"[list_subdirectories_with_media_counts] '{directory}'는 디렉토리가 아님.")
            return subdirs_info
        for item in base_path.iterdir():
            if item.is_dir():
                video_count, audio_count = count_media_recursive(item)
                subdirs_info.append({
                    'name': item.name,
                    'path': str(item.resolve()),
                    'video_count': video_count,
                    'audio_count': audio_count
                })
        subdirs_info.sort(key=lambda x: x['name'])
        logger.info(f"[list_subdirectories_with_media_counts] 결과: {subdirs_info}")
    except Exception as e:
        logger.error(f"[list_subdirectories_with_media_counts] 오류: {e}", exc_info=True)
    return subdirs_info

def extract_embedded_subtitles(media_path: str) -> List[Dict[str, Any]]:
    """
    mkv/mp4/avi 등 미디어 파일에서 내장(임베디드) 자막 트랙을 실제로 추출한다.
    ffprobe로 트랙 정보 추출 후, ffmpeg로 각 트랙을 .srt로 추출한다.
    """
    import json
    results = []
    try:
        # ffprobe로 자막 트랙 정보 추출
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 's',
            '-show_entries', 'stream=index:stream_tags=language',
            '-of', 'json', media_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return [{'track': None, 'language': None, 'format': None, 'output_path': None, 'status': 'error', 'error': proc.stderr}]
        info = json.loads(proc.stdout)
        streams = info.get('streams', [])
        for stream in streams:
            track_idx = stream.get('index')
            lang = stream.get('tags', {}).get('language', 'und')
            # 임시 파일명: 원본명_track#.srt
            out_path = f"{media_path}_track{track_idx}.srt"
            # 실제 추출 명령: ffmpeg -y -i input -map 0:s:{track_idx} out_path
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', media_path, '-map', f'0:s:{track_idx}', out_path
            ]
            ffmpeg_proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if ffmpeg_proc.returncode == 0 and os.path.exists(out_path):
                results.append({
                    'track': track_idx,
                    'language': lang,
                    'format': 'srt',
                    'output_path': out_path,
                    'status': 'extracted',
                    'error': None
                })
            else:
                results.append({
                    'track': track_idx,
                    'language': lang,
                    'format': 'srt',
                    'output_path': out_path,
                    'status': 'error',
                    'error': ffmpeg_proc.stderr
                })
    except Exception as e:
        results.append({'track': None, 'language': None, 'format': None, 'output_path': None, 'status': 'error', 'error': str(e)})
    return results

def convert_and_save_subtitle(input_path: str, output_path: str, target_format: str = 'srt') -> dict:
    """
    ffmpeg를 사용해 자막 파일을 SRT 등 표준 포맷으로 변환/저장한다.
    input_path: 원본 자막 파일 경로
    output_path: 저장할 파일 경로
    target_format: 변환할 포맷 (기본 srt)
    반환: {'success': bool, 'output_path': str, 'error': str|None}
    """
    try:
        cmd = [
            'ffmpeg', '-y', '-i', input_path, output_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return {'success': True, 'output_path': output_path, 'error': None}
        else:
            return {'success': False, 'output_path': output_path, 'error': proc.stderr}
    except Exception as e:
        return {'success': False, 'output_path': output_path, 'error': str(e)}

# 테스트용 코드 업데이트
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_directory = "/path/to/your/test/media/folder"
    if not os.path.exists(test_directory):
        print(f"테스트 디렉토리가 존재하지 않습니다: {test_directory}")
    else:
        print("\n--- 영상만 스캔 ---")
        files_video = scan_media_files(test_directory, filter_video=True, filter_audio=False)
        for file_info in files_video:
            print(f"  {file_info['name']}")
        print(f"총 {len(files_video)}개")

        print("\n--- 오디오만 스캔 ---")
        files_audio = scan_media_files(test_directory, filter_video=False, filter_audio=True)
        for file_info in files_audio:
            print(f"  {file_info['name']}")
        print(f"총 {len(files_audio)}개")

        print("\n--- 영상 + 오디오 스캔 ---")
        files_all = scan_media_files(test_directory, filter_video=True, filter_audio=True)
        for file_info in files_all:
            print(f"  {file_info['name']}")
        print(f"총 {len(files_all)}개") 