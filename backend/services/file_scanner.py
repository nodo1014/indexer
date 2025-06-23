import os
import logging
from pathlib import Path
from typing import List, Dict, Set, Any, Tuple, Optional
import subprocess
from functools import lru_cache
import concurrent.futures
from tqdm import tqdm

logger = logging.getLogger(__name__)

# 지원하는 미디어 확장자 분류
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
# 지원하는 자막 파일 확장자
SUBTITLE_EXTENSIONS = {".srt", ".vtt", ".smi", ".ass"}

# 캐시 설정
CACHE_TTL = 300  # 캐시 유효 시간 (초)
MAX_CACHE_ITEMS = 100  # 최대 캐시 항목 수

# 자막 변환 및 저장 함수 추가
def convert_and_save_subtitle(input_path: str, output_path: str, target_format: str = 'srt') -> Dict[str, Any]:
    """
    자막 파일을 지정된 포맷으로 변환하여 저장합니다.
    ffmpeg를 사용하여 다양한 자막 포맷 간 변환을 지원합니다.
    
    Args:
        input_path (str): 변환할 자막 파일 경로
        output_path (str): 변환 결과를 저장할 경로
        target_format (str, optional): 변환 대상 포맷 (기본값: 'srt')
    
    Returns:
        Dict[str, Any]: 변환 결과 정보
    """
    logger.info(f"🔄 자막 변환 시작: {input_path} -> {output_path} (포맷: {target_format})")
    
    try:
        # 입력 파일 확인
        if not os.path.exists(input_path):
            return {"success": False, "error": f"입력 파일이 존재하지 않습니다: {input_path}"}
        
        # 출력 포맷 검증
        if target_format not in ['srt', 'vtt', 'ass']:
            return {"success": False, "error": f"지원하지 않는 자막 포맷입니다: {target_format}"}
        
        # ffmpeg 명령어 구성
        cmd = [
            'ffmpeg', '-y', '-i', input_path, 
            '-c:s', target_format,  # 자막 코덱 지정
            output_path
        ]
        
        logger.debug(f"🔧 ffmpeg 명령 실행: {' '.join(cmd)}")
        
        # ffmpeg 실행
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        # 실행 결과 확인
        if proc.returncode == 0 and os.path.exists(output_path):
            logger.info(f"✅ 자막 변환 성공: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "format": target_format
            }
        else:
            logger.error(f"❌ 자막 변환 실패: {proc.stderr}")
            return {
                "success": False,
                "error": proc.stderr or "알 수 없는 변환 오류"
            }
            
    except Exception as e:
        logger.error(f"❌ 자막 변환 중 예외 발생: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

# LRU 캐시 데코레이터로 디렉토리 스캔 결과 캐싱
@lru_cache(maxsize=MAX_CACHE_ITEMS)
def scan_directory_cached(directory: str, cache_key: str) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """디렉토리 스캔 결과를 캐싱하는 함수 (위에 cache_key는 filter_video, filter_audio 상태를 포함한 키)"""
    # 실제 디렉토리 스캔은 이 함수 내에서 구현하지 않고, 
    # scan_media_files 함수에서 캐시 키 생성 후 이 함수를 호출하는 방식으로 사용
    return [], {"total_files": 0, "video_count": 0, "audio_count": 0, "with_subtitle_count": 0, "without_subtitle_count": 0}

def scan_media_files(directory: str, filter_video: bool = True, filter_audio: bool = True) -> List[Dict[str, str]]:
    """지정된 디렉토리와 하위 디렉토리를 스캔하여 미디어 파일(자막 유무 포함) 전체를 반환합니다 (타입 필터링 적용)."""
    start_time = os.times()
    logger.info(f"📁 미디어 스캔 시작: '{directory}' (Video: {filter_video}, Audio: {filter_audio})")
    
    # 캐시 키 생성 (디렉토리 경로 + 필터 상태)
    cache_key = f"{directory}:{filter_video}:{filter_audio}"
    
    # 캐시된 결과가 있는지 확인
    try:
        # 캐시 유효성 확인 (디렉토리 수정 시간 기준)
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"⚠️ 지정된 경로가 존재하지 않거나 디렉토리가 아닙니다: {directory}")
            return []
            
        # 캐시된 결과 사용
        if cache_key in scan_directory_cached.cache_info().currsize:
            logger.info(f"🔄 캐시된 스캔 결과 사용: {directory}")
            cached_result, summary = scan_directory_cached(directory, cache_key)
            logger.info(f"✅ 미디어 스캔 완료 (캐시): {len(cached_result)}개 파일 발견")
            return cached_result
    except Exception as e:
        logger.warning(f"⚠️ 캐시 확인 중 오류 발생: {e}")
        # 캐시 오류 시 무시하고 계속 진행
        pass
    
    media_files: List[Dict[str, str]] = []
    processed_basenames: Set[str] = set()
    allowed_extensions: Set[str] = set()
    summary = {
        "total_files": 0,
        "video_count": 0,
        "audio_count": 0,
        "with_subtitle_count": 0,
        "without_subtitle_count": 0
    }
    
    if filter_video:
        allowed_extensions.update(VIDEO_EXTENSIONS)
    if filter_audio:
        allowed_extensions.update(AUDIO_EXTENSIONS)

    if not allowed_extensions:
        logger.warning("⚠️ 스캔할 미디어 타입이 선택되지 않았습니다 (영상/오디오 모두 해제됨). 빈 목록을 반환합니다.")
        return []

    try:
        target_path = Path(directory)
        if not target_path.is_dir():
            logger.error(f"⚠️ 지정된 경로가 디렉토리가 아닙니다: {directory}")
            return []

        # 병렬 처리를 위한 함수
        def process_file(item: Path) -> Optional[Dict[str, str]]:
            if not item.is_file():
                return None
                
            file_ext = item.suffix.lower()
            base_name = item.stem
            full_path_str = str(item.resolve())

            if base_name in processed_basenames:
                return None

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
                file_type = "video" if file_ext in VIDEO_EXTENSIONS else "audio"
                
                # 요약 정보 업데이트
                nonlocal summary
                summary["total_files"] += 1
                if file_type == "video":
                    summary["video_count"] += 1
                else:
                    summary["audio_count"] += 1
                    
                if has_subtitle:
                    summary["with_subtitle_count"] += 1
                else:
                    summary["without_subtitle_count"] += 1
                
                processed_basenames.add(base_name)
                return {
                    "name": item.name,
                    "path": full_path_str,
                    "type": file_type,
                    "has_subtitle": has_subtitle,
                    "subtitle_files": subtitle_files
                }
            # 2. 자막 파일이면, 해당 파일명(언어코드 제외)을 처리된 것으로 간주
            elif file_ext in SUBTITLE_EXTENSIONS:
                processed_basenames.add(base_name)
                for lang_code in ['_en', '_ko', '_ja', '_zh']:
                    if base_name.endswith(lang_code):
                        original_base_name = base_name[:-len(lang_code)]
                        processed_basenames.add(original_base_name)
                        break
            return None

        # 모든 파일 목록 수집 (tqdm으로 진행률 표시)
        all_files = list(target_path.rglob('*'))
        logger.info(f"🔍 총 {len(all_files)}개 파일/디렉토리 발견. 미디어 파일 필터링 중...")
        
        # ThreadPoolExecutor를 사용한 병렬 처리 (tqdm으로 진행률 표시)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            with tqdm(total=len(all_files), desc="미디어 파일 스캔", unit="files") as pbar:
                futures = []
                for item in all_files:
                    future = executor.submit(process_file, item)
                    futures.append(future)
                
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        media_files.append(result)
                    pbar.update(1)

        # 결과 정렬 (경로 기준)
        media_files.sort(key=lambda x: x['path'])
        
        end_time = os.times()
        elapsed = end_time.user - start_time.user + end_time.system - start_time.system
        logger.info(f"✅ 미디어 스캔 완료: {len(media_files)}개의 미디어 파일 찾음 (소요 시간: {elapsed:.2f}초)")
        logger.info(f"📊 스캔 요약: 총 {summary['total_files']}개 (비디오: {summary['video_count']}, 오디오: {summary['audio_count']}, "
                   f"자막 있음: {summary['with_subtitle_count']}, 자막 없음: {summary['without_subtitle_count']})")

        # 캐시에 결과 저장
        scan_directory_cached.cache_clear()  # 기존 캐시 지우기
        scan_directory_cached(directory, cache_key)  # 새 결과 저장

    except Exception as e:
        logger.error(f"❌ 디렉토리 스캔 중 오류 발생: {e}", exc_info=True)

    return media_files

def list_subdirectories(directory: str) -> List[str]:
    """지정된 디렉토리의 하위 디렉토리 목록(절대 경로)을 반환합니다."""
    subdirs = []
    logger.info(f"📁 디렉토리 목록 조회: '{directory}'") 
    
    try:
        base_path = Path(directory).resolve()  # 절대 경로로 변환
        
        if not base_path.exists():
            logger.error(f"⚠️ 경로가 존재하지 않음: '{directory}'")
            return subdirs
            
        if not base_path.is_dir():
            logger.warning(f"⚠️ '{directory}'는 디렉토리가 아님.")
            return subdirs
            
        logger.debug(f"📂 '{base_path}'는 디렉토리임. 내용 조회 중...")
        
        # 디렉토리 목록만 추출 (rglob 대신 iterdir 사용)
        for item in base_path.iterdir():
            if item.is_dir():
                subdirs.append(str(item.resolve()))  # 절대 경로로 추가
                logger.debug(f"- 하위 디렉토리: {item.name}")
        
        # 이름 순으로 정렬
        subdirs.sort()
        logger.info(f"✅ 하위 디렉토리 조회 완료: {len(subdirs)}개 발견") 
        
    except PermissionError as e:
        logger.error(f"❌ 하위 디렉토리 목록 조회 중 권한 오류: {directory} - {e}")
    except Exception as e:
        logger.error(f"❌ 하위 디렉토리 목록 조회 중 오류: {directory} - {e}", exc_info=True)
        
    return subdirs

def count_media_recursive(directory: Path) -> Tuple[int, int]:
    """디렉토리 내 모든 하위 폴더까지 영상/오디오 파일 개수를 재귀적으로 합산"""
    video_count = 0
    audio_count = 0
    try:
        # 디렉토리에 파일이 너무 많으면 처리에 시간이 오래 걸릴 수 있음
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
        logger.warning(f"⚠️ '{directory}' 내부 파일 개수 집계 중 오류: {e}")
    return video_count, audio_count

def list_subdirectories_with_media_counts(directory: str) -> list:
    """
    지정된 디렉토리의 하위 디렉토리 목록(절대 경로)과 각 디렉토리 내 영상/오디오 파일 개수를 (하위폴더까지 포함하여) 반환합니다.
    반환 예시: [{ 'name': 'Movies', 'path': '/mnt/qq/Movies', 'video_count': 3, 'audio_count': 1 }, ...]
    """
    subdirs_info = []
    logger.info(f"📁 디렉토리 목록 및 미디어 파일 개수 조회 시작: '{directory}'")
    try:
        base_path = Path(directory).resolve()
        if not base_path.exists() or not base_path.is_dir():
            logger.warning(f"⚠️ '{directory}'는 디렉토리가 아니거나 존재하지 않습니다.")
            return subdirs_info
            
        # 하위 디렉토리 목록 가져오기
        subdirs = []
        for item in base_path.iterdir():
            if item.is_dir():
                subdirs.append(item)
                
        # 병렬 처리를 위한 함수
        def process_directory(item: Path) -> Dict[str, Any]:
            video_count, audio_count = count_media_recursive(item)
            return {
                'name': item.name,
                'path': str(item.resolve()),
                'video_count': video_count,
                'audio_count': audio_count
            }
        
        # ThreadPoolExecutor를 사용한 병렬 처리 (tqdm으로 진행률 표시)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            with tqdm(total=len(subdirs), desc="디렉토리 미디어 파일 개수 집계", unit="dirs") as pbar:
                futures = {executor.submit(process_directory, item): item for item in subdirs}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    subdirs_info.append(result)
                    pbar.update(1)
                    logger.debug(f"- {result['name']}: 비디오 {result['video_count']}개, 오디오 {result['audio_count']}개")
        
        # 이름 순으로 정렬
        subdirs_info.sort(key=lambda x: x['name'])
        logger.info(f"✅ 디렉토리 목록 및 미디어 파일 개수 조회 완료: {len(subdirs_info)}개 디렉토리")
        
    except Exception as e:
        logger.error(f"❌ 디렉토리 미디어 파일 개수 조회 중 오류: {e}", exc_info=True)
    
    return subdirs_info

def extract_embedded_subtitles(media_path: str) -> List[Dict[str, Any]]:
    """
    mkv/mp4/avi 등 미디어 파일에서 내장(임베디드) 자막 트랙을 실제로 추출한다.
    ffprobe로 트랙 정보 추출 후, ffmpeg로 각 트랙을 .srt로 추출한다.
    """
    import json
    results = []
    logger.info(f"📼 미디어 파일에서 내장 자막 추출 시작: {Path(media_path).name}")
    
    try:
        # ffprobe로 자막 트랙 정보 추출
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 's',
            '-show_entries', 'stream=index:stream_tags=language',
            '-of', 'json', media_path
        ]
        logger.debug(f"🔍 ffprobe 명령 실행: {' '.join(cmd)}")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        if proc.returncode != 0:
            logger.error(f"❌ ffprobe 명령 실패: {proc.stderr}")
            return [{'track': None, 'language': None, 'format': None, 'output_path': None, 'status': 'error', 'error': proc.stderr}]
            
        info = json.loads(proc.stdout)
        streams = info.get('streams', [])
        
        if not streams:
            logger.info(f"ℹ️ 내장 자막 트랙이 없습니다: {Path(media_path).name}")
            return [{'track': None, 'language': None, 'format': None, 'output_path': None, 'status': 'no_subtitles', 'error': '내장 자막 트랙 없음'}]
            
        logger.info(f"📄 {len(streams)}개의 자막 트랙 발견. 추출 시작...")
        
        for stream in streams:
            track_idx = stream.get('index')
            lang = stream.get('tags', {}).get('language', 'und')
            # 임시 파일명: 원본명_track#.srt
            out_path = f"{media_path}_track{track_idx}.srt"
            
            # 실제 추출 명령: ffmpeg -y -i input -map 0:s:{track_idx} out_path
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', media_path, '-map', f'0:s:{track_idx}', out_path
            ]
            logger.debug(f"🔧 ffmpeg 명령 실행 (트랙 {track_idx}, 언어: {lang}): {' '.join(ffmpeg_cmd)}")
            
            ffmpeg_proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if ffmpeg_proc.returncode == 0 and os.path.exists(out_path):
                logger.info(f"✅ 자막 트랙 추출 성공 (트랙 {track_idx}, 언어: {lang}): {out_path}")
                results.append({
                    'track': track_idx,
                    'language': lang,
                    'format': 'srt',
                    'output_path': out_path,
                    'status': 'success'
                })
            else:
                logger.error(f"❌ 자막 트랙 추출 실패 (트랙 {track_idx}, 언어: {lang}): {ffmpeg_proc.stderr}")
                results.append({
                    'track': track_idx,
                    'language': lang,
                    'format': None,
                    'output_path': None,
                    'status': 'error',
                    'error': ffmpeg_proc.stderr
                })
    except Exception as e:
        logger.error(f"❌ 자막 추출 중 예외 발생: {e}", exc_info=True)
        results.append({
            'track': None,
            'language': None,
            'format': None,
            'output_path': None,
            'status': 'error',
            'error': str(e)
        })
    
    logger.info(f"📋 내장 자막 추출 완료: {len([r for r in results if r['status'] == 'success'])}개 성공, {len([r for r in results if r['status'] != 'success'])}개 실패")
    return results

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