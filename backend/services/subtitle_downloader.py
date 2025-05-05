import os
import requests
from typing import List, Dict
import re
from difflib import SequenceMatcher
from backend.config import settings
import logging
import json
import time
import hashlib
from pathlib import Path

# OpenSubtitles API 정보
OPENSUBTITLES_API_URL = 'https://api.opensubtitles.com/api/v1'
OPENSUBTITLES_API_KEY = settings.opensubtitles_api_key or os.getenv('OPENSUBTITLES_API_KEY', '')

# 개발 모드 설정 (API 일일 한도 100건)
OPENSUBTITLES_DEV_MODE = True

# 다운로드 제한 설정 (운영 환경에서는 일일 5건)
MAX_DAILY_DOWNLOADS = 100 if OPENSUBTITLES_DEV_MODE else 5

# 자막 캐시 디렉토리 설정
SUBTITLE_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'subtitle_cache')
os.makedirs(SUBTITLE_CACHE_DIR, exist_ok=True)

# 다운로드 통계 파일
DOWNLOAD_STATS_FILE = os.path.join(SUBTITLE_CACHE_DIR, 'download_stats.json')

# API 키가 없을 경우 경고 로그 출력
if not OPENSUBTITLES_API_KEY:
    logging.warning("OpenSubtitles API 키가 설정되지 않았습니다. .env 파일에 OPENSUBTITLES_API_KEY를 추가하세요.")

# 다운로드 통계 로드
def load_download_stats() -> Dict:
    """다운로드 통계 파일에서 일일 다운로드 횟수 정보를 로드합니다."""
    if os.path.exists(DOWNLOAD_STATS_FILE):
        try:
            with open(DOWNLOAD_STATS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"다운로드 통계 로드 중 오류 발생: {str(e)}")
    
    # 기본 통계 구조
    return {
        'today': time.strftime('%Y-%m-%d'),
        'daily_downloads': 0,
        'total_downloads': 0,
        'cached_subtitles': {}
    }

# 다운로드 통계 저장
def save_download_stats(stats: Dict) -> None:
    """다운로드 통계를 파일에 저장합니다."""
    try:
        # 오늘 날짜 확인 및 필요시 초기화
        today = time.strftime('%Y-%m-%d')
        if stats.get('today') != today:
            stats['today'] = today
            stats['daily_downloads'] = 0
        
        with open(DOWNLOAD_STATS_FILE, 'w') as f:
            json.dump(stats, f, indent=2)
    except Exception as e:
        logging.error(f"다운로드 통계 저장 중 오류 발생: {str(e)}")

# 다운로드 횟수 증가 및 체크
def check_download_limit() -> bool:
    """
    일일 다운로드 횟수를 확인하고 제한 내인지 확인합니다.
    제한 내이면 카운터를 증가시키고 True를 반환, 제한을 초과하면 False를 반환합니다.
    """
    stats = load_download_stats()
    
    # 오늘 날짜 확인
    today = time.strftime('%Y-%m-%d')
    if stats.get('today') != today:
        stats['today'] = today
        stats['daily_downloads'] = 0
    
    # 제한 확인
    if stats['daily_downloads'] >= MAX_DAILY_DOWNLOADS:
        logging.warning(f"일일 다운로드 제한 ({MAX_DAILY_DOWNLOADS}건) 초과")
        return False
    
    # 카운터 증가
    stats['daily_downloads'] += 1
    stats['total_downloads'] += 1
    save_download_stats(stats)
    
    return True

# 자막 캐시 키 생성
def get_cache_key(filename: str, language: str) -> str:
    """파일명과 언어를 기반으로 캐시 키를 생성합니다."""
    clean_fn = clean_title(filename)
    return hashlib.md5(f"{clean_fn}_{language}".encode()).hexdigest()

# 자막 캐시 확인
def check_subtitle_cache(filename: str, language: str) -> Dict:
    """
    자막 캐시를 확인하여, 캐싱된 자막이 있는지 확인합니다.
    캐시된 자막이 있으면 {'success': True, 'cache_path': 경로} 형태로 반환합니다.
    """
    stats = load_download_stats()
    cache_key = get_cache_key(filename, language)
    
    if cache_key in stats.get('cached_subtitles', {}):
        cache_info = stats['cached_subtitles'][cache_key]
        cache_path = cache_info.get('cache_path')
        
        if cache_path and os.path.exists(cache_path):
            return {
                'success': True, 
                'cache_path': cache_path, 
                'source': 'cache',
                'details': cache_info
            }
    
    return {'success': False}

# 자막 캐시에 저장
def save_to_subtitle_cache(filename: str, language: str, save_path: str, subtitle_info: Dict) -> None:
    """다운로드한 자막을 캐시에 저장합니다."""
    stats = load_download_stats()
    cache_key = get_cache_key(filename, language)
    
    if 'cached_subtitles' not in stats:
        stats['cached_subtitles'] = {}
    
    # 캐시 정보 저장
    stats['cached_subtitles'][cache_key] = {
        'original_filename': filename,
        'language': language,
        'cache_path': save_path,
        'date_added': time.strftime('%Y-%m-%d %H:%M:%S'),
        'details': {
            'title': subtitle_info.get('title', ''),
            'similarity': subtitle_info.get('similarity', 0),
            'downloads': subtitle_info.get('downloads', 0)
        }
    }
    
    save_download_stats(stats)

# 파일명 정제 함수 (확장자, 해상도, 코덱, 릴그룹 등 제거)
def clean_title(title: str) -> str:
    # 확장자 제거
    title = re.sub(r'\.(mp4|mkv|avi|srt|ass|vtt)$', '', title, flags=re.I)
    
    # 시작 부분의 특수문자나 불필요한 문자 제거
    title = re.sub(r'^[\[\(].*?[\]\)]', '', title)
    
    # 해상도, 코덱, 릴리스 그룹 등 제거
    title = re.sub(r'\b(720p|1080p|2160p|4k|x264|h264|x265|hevc|bluray|web-dl|hdrip|dvdrip|aac|dts|hdtv|remux|yts|rarbg|ettv|evo|fgt|ntb|ctrlhd|lol|killers|dimension|publichd|ettv|yify|web|webrip|amzn|nf|ac3|mp3|flac|subs?|hdr|atmos|group)\b', '', title, flags=re.I)
    
    # 숫자가 포함된 오디오 코덱 패턴 (DDP5.1, DD5.1 등) 처리
    title = re.sub(r'\b(ddp5\.?1|dd5\.?1|h\.?264|h\.?265)\b', '', title, flags=re.I) 
    
    # 마지막 -GROUP 패턴 제거
    title = re.sub(r'[-][\w]+$', '', title)
    
    # 연도 추출 및 보존
    year_match = re.search(r'(19|20)\d{2}', title)
    year = year_match.group(0) if year_match else ""
    
    # 특수문자를 공백으로 변환
    title = re.sub(r'[^\w\s]', ' ', title)
    
    # 연속된 공백 제거
    title = re.sub(r'\s+', ' ', title)
    
    # 정제된 제목
    cleaned = title.strip().lower()
    
    # 연도가 있으면 추가
    if year and year not in cleaned:
        cleaned = f"{cleaned} {year}"
    
    return cleaned

# 두 문자열의 유사도(0~1) 계산
def string_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# 파일 제목 유사도 계산 (정제된 상태)
def title_similarity(a: str, b: str) -> float:
    return string_similarity(clean_title(a), clean_title(b))

# 실제 OpenSubtitles API 연동: 자막 후보 리스트 검색
def download_subtitle_from_opensubtitles(filename: str, language: str = 'ko') -> Dict:
    """
    파일명/언어로 OpenSubtitles에서 자막 후보 리스트를 검색하여 반환한다.
    각 후보별로 media_title과의 일치율(%)을 계산, best_match(최고 일치율 후보)도 함께 반환.
    """
    if not OPENSUBTITLES_API_KEY:
        return {
            'success': False,
            'error': 'OpenSubtitles API key is not configured',
            'candidates': [],
            'best_match': None
        }
    
    # 영화 제목만 추출하여 검색에 사용
    clean_name = clean_title(filename)
    
    # 기본 테스트 스크립트에서 성공한 헤더와 파라미터 구성 사용
    headers = {
        'Api-Key': OPENSUBTITLES_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Subtitle Indexer/1.0'  # User-Agent 추가
    }
    
    params = {
        'query': clean_name,
        'languages': language
    }
    
    logging.debug(f"OpenSubtitles 검색 요청: {params}")
    
    try:
        resp = requests.get(f"{OPENSUBTITLES_API_URL}/subtitles", headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        logging.debug(f"OpenSubtitles API 응답: 상태 코드 {resp.status_code}")
        
        candidates = []
        for item in data.get('data', []):
            attributes = item.get('attributes', {})
            
            # 파일명 정보 획득
            files = attributes.get('files', [])
            sub_filename = files[0].get('file_name', '') if files else ''
            
            # 영화/시리즈 정보 획득
            feature = attributes.get('feature_details', {})
            feature_title = feature.get('movie_name', '') or feature.get('title', '')
            
            # 파일명과 검색어 유사도 계산 (파일명 또는 타이틀 정보에서 높은 쪽 사용)
            filename_sim = title_similarity(filename, sub_filename) if sub_filename else 0
            title_sim = string_similarity(clean_name, feature_title.lower()) if feature_title else 0
            sim = max(filename_sim, title_sim)  # 둘 중 더 높은 유사도 사용
            
            # 다운로드 URL을 위한 파일 ID
            file_id = item.get('id') or attributes.get('files', [{}])[0].get('file_id', '')
            
            candidates.append({
                'file_id': file_id,  # 필수 정보: 파일 ID
                'subtitle_id': attributes.get('id', ''),  # 자막 ID
                'filename': sub_filename,  # 자막 파일명
                'title': feature_title,  # 영화/시리즈 제목
                'lang': attributes.get('language', ''),  # 언어
                'release': attributes.get('release', ''),  # 릴리스 정보
                'fps': attributes.get('fps', ''),  # FPS
                'votes': attributes.get('votes', 0),  # 투표수
                'downloads': attributes.get('download_count', 0),  # 다운로드 수
                'similarity': round(sim * 100, 1),  # 유사도 (%)
                'download_url': None  # 실제 다운로드 URL은 별도 API로 요청
            })
        
        if not candidates:
            logging.warning(f"[OpenSubtitles] 검색 결과 없음: 파일명={filename}, 언어={language}")
        
        # 유사도 점수가 가장 높은 자막 선택
        candidates.sort(key=lambda c: (-c['similarity'], -c['downloads']))  # 유사도 내림차순, 그다음 다운로드 수 내림차순
        best_match = candidates[0] if candidates else None
        
        return {'success': True, 'candidates': candidates, 'best_match': best_match}
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"OpenSubtitles API 요청 실패: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg, 'candidates': [], 'best_match': None}
    
    except Exception as e:
        error_msg = f"OpenSubtitles API 검색 중 예외 발생: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg, 'candidates': [], 'best_match': None}

# 다운로드 링크 획득
def get_download_link(file_id: str) -> Dict:
    """
    자막 파일 ID로 실제 다운로드 URL을 요청합니다.
    """
    if not OPENSUBTITLES_API_KEY:
        return {'success': False, 'error': 'OpenSubtitles API key is not configured'}
    
    # API 요청 헤더
    headers = {
        'Api-Key': OPENSUBTITLES_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'User-Agent': 'Subtitle Indexer/1.0'
    }
    
    # 다운로드 링크 요청 본문
    payload = {
        'file_id': file_id
    }
    
    try:
        # 다운로드 링크 요청
        logging.debug(f"OpenSubtitles 다운로드 URL 요청: file_id={file_id}")
        resp = requests.post(f"{OPENSUBTITLES_API_URL}/download", headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        # 응답 파싱
        download_url = data.get('link')
        if not download_url:
            return {'success': False, 'error': '다운로드 URL을 찾을 수 없습니다', 'response': data}
        
        logging.debug(f"다운로드 URL 획득 성공: {download_url[:30]}...")
        return {
            'success': True,
            'download_url': download_url,
            'remaining': data.get('remaining', 0),  # 남은 다운로드 횟수
            'requests': data.get('requests', 0),  # 시간당 요청 횟수
            'message': data.get('message', '')  # 서버 메시지
        }
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"다운로드 URL 요청 실패: {str(e)}"
        logging.error(error_msg)
        try:
            error_data = resp.json() if hasattr(resp, 'json') else {}
            return {'success': False, 'error': error_msg, 'details': error_data}
        except:
            return {'success': False, 'error': error_msg}
    
    except Exception as e:
        error_msg = f"다운로드 URL 요청 중 예외 발생: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg}

# 자막 다운로드 및 저장
def download_subtitle(file_id: str, save_path: str, use_cache: bool = True) -> Dict:
    """
    파일 ID로 자막을 다운로드하여 저장합니다.
    
    Args:
        file_id: 자막 파일 ID
        save_path: 자막을 저장할 경로
        use_cache: 다운로드 제한을 고려하여 캐시 사용 여부
        
    Returns:
        Dict: 다운로드 결과
    """
    # 일일 다운로드 제한 확인
    if not check_download_limit():
        return {
            'success': False, 
            'error': f'일일 다운로드 제한 ({MAX_DAILY_DOWNLOADS}건) 초과',
            'limit_reached': True
        }
    
    # 1. 다운로드 URL 획득
    link_result = get_download_link(file_id)
    if not link_result['success']:
        return link_result
    
    download_url = link_result['download_url']
    
    # 2. 실제 자막 파일 다운로드
    try:
        logging.debug(f"자막 다운로드 시작: {download_url[:30]}...")
        resp = requests.get(download_url, timeout=10)
        resp.raise_for_status()
        
        # 3. 파일 저장
        with open(save_path, 'wb') as f:
            f.write(resp.content)
            
        # 4. 캐시 파일 저장 (원본은 유지)
        if use_cache:
            # 캐시 디렉토리에 복사본 저장
            filename = os.path.basename(save_path)
            cache_path = os.path.join(SUBTITLE_CACHE_DIR, f"{Path(filename).stem}_{file_id}.srt")
            
            try:
                with open(cache_path, 'wb') as f:
                    f.write(resp.content)
                logging.info(f"자막 캐시 저장 완료: {cache_path}")
            except Exception as e:
                logging.error(f"자막 캐시 저장 실패: {str(e)}")
        
        logging.info(f"자막 파일 저장 완료: {save_path}")
        return {
            'success': True, 
            'save_path': save_path, 
            'remaining_downloads': link_result.get('remaining', 0)
        }
    
    except requests.exceptions.HTTPError as e:
        error_msg = f"자막 다운로드 실패: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg}
    
    except Exception as e:
        error_msg = f"자막 다운로드 중 예외 발생: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg}

# 실제 자막 파일 다운로드 및 저장 (직접 URL을 아는 경우)
def download_and_save_subtitle(download_url: str, save_path: str) -> Dict:
    """
    지정된 URL에서 자막 파일을 다운로드하여 save_path에 저장합니다.
    """
    try:
        resp = requests.get(download_url, timeout=10)
        resp.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        return {'success': True, 'save_path': save_path}
    except Exception as e:
        error_msg = f"자막 다운로드 및 저장 실패: {str(e)}"
        logging.error(error_msg)
        return {'success': False, 'error': error_msg}

# 통합 함수: 파일명으로 자막 검색+다운로드
def search_and_download_subtitle(filename: str, save_path: str, language: str = 'ko', min_similarity: float = 60.0, use_cache: bool = True) -> Dict:
    """
    파일명을 기준으로 자막을 검색하고, 일치율이 높은 자막을 자동으로 다운로드합니다.
    
    Args:
        filename: 미디어 파일명
        save_path: 자막 저장 경로
        language: 자막 언어 (기본: 'ko')
        min_similarity: 최소 일치율 (기본: 60.0%)
        use_cache: 캐시 사용 여부 (기본: True)
        
    Returns:
        Dict: {'success': bool, 'message': str, ...}
    """
    # 0. 자막 캐시 확인 (캐시 사용 설정시)
    if use_cache:
        cache_result = check_subtitle_cache(filename, language)
        if cache_result['success']:
            # 캐시된 자막 파일 복사
            try:
                import shutil
                shutil.copy2(cache_result['cache_path'], save_path)
                return {
                    'success': True,
                    'save_path': save_path,
                    'source': 'cache',
                    'cache_details': cache_result.get('details', {})
                }
            except Exception as e:
                logging.error(f"캐시 자막 복사 중 오류: {str(e)}")
                # 캐시 복사 실패시 정상 다운로드 진행
    
    # 1. 자막 검색
    search_result = download_subtitle_from_opensubtitles(filename, language)
    
    if not search_result['success']:
        return {
            'success': False, 
            'stage': 'search',
            'error': search_result.get('error', '자막 검색 실패')
        }
    
    # 2. 최적 자막 선택
    best_match = search_result.get('best_match')
    if not best_match:
        return {
            'success': False,
            'stage': 'match',
            'error': '일치하는 자막을 찾을 수 없습니다',
            'candidates_count': len(search_result.get('candidates', [])) 
        }
    
    # 최소 유사도 체크
    if best_match['similarity'] < min_similarity:
        return {
            'success': False,
            'stage': 'similarity',
            'error': f'최고 일치율({best_match["similarity"]}%)이 최소 기준({min_similarity}%)보다 낮습니다',
            'best_match': best_match
        }
    
    # 3. 자막 다운로드 - ID로 다운로드 URL을 요청
    download_result = download_subtitle(best_match['file_id'], save_path, use_cache)
    
    if not download_result['success']:
        # 일일 제한 도달 시 특수 처리
        if download_result.get('limit_reached'):
            return {
                'success': False,
                'stage': 'limit',
                'error': download_result.get('error', '일일 다운로드 제한 초과'),
                'limit_reached': True
            }
        
        return {
            'success': False,
            'stage': 'download',
            'error': download_result.get('error', '자막 다운로드 실패'),
            'best_match': best_match
        }
    
    # 4. 다운로드 성공 시 캐시 정보 저장
    if use_cache:
        save_to_subtitle_cache(filename, language, download_result['save_path'], best_match)
    
    # 5. 성공
    return {
        'success': True,
        'save_path': download_result['save_path'],
        'best_match': best_match,
        'similarity': best_match['similarity'],
        'remaining_downloads': download_result.get('remaining_downloads'),
        'source': 'api'
    }

# 다양한 언어로 순차 검색 시도
def fallback_search_subtitle(filename: str, save_path: str, languages: List[str] = None, min_similarity: float = 50.0, use_cache: bool = True) -> Dict:
    """
    여러 언어로 자막을 순차적으로 검색합니다.
    한국어 자막을 찾지 못할 경우 영어나 다른 언어로 시도합니다.
    
    Args:
        filename: 미디어 파일명
        save_path: 자막 저장 경로
        languages: 시도할 언어 코드 리스트 (기본값: ['ko', 'en'])
        min_similarity: 최소 유사도 (기본: 50.0%)
        use_cache: 캐시 사용 여부 (기본: True)
        
    Returns:
        Dict: 검색/다운로드 결과
    """
    # 기본 언어 설정
    if not languages:
        languages = ['ko', 'en']
    
    # 로그 출력
    logging.info(f"[다국어 자막 검색] 파일: {filename}, 시도할 언어: {languages}")
    
    last_result = None
    errors = []
    
    # 각 언어별로 순차 시도
    for lang in languages:
        logging.info(f"[다국어 자막 검색] '{lang}' 언어로 시도 중...")
        result = search_and_download_subtitle(filename, save_path, lang, min_similarity, use_cache)
        
        # 성공하면 바로 반환
        if result.get('success'):
            logging.info(f"[다국어 자막 검색] '{lang}' 언어로 자막을 찾았습니다.")
            result['language'] = lang
            return result
        
        # 실패 원인 수집
        errors.append(f"{lang}: {result.get('error', '알 수 없는 오류')}")
        last_result = result
    
    # 모든 언어 시도 실패
    if last_result:
        last_result['success'] = False
        last_result['error'] = f"모든 언어({', '.join(languages)})로 검색했으나 적합한 자막을 찾지 못했습니다."
        last_result['tried_languages'] = languages
        last_result['language_errors'] = errors
    else:
        last_result = {
            'success': False,
            'error': f"모든 언어({', '.join(languages)})로 검색했으나 적합한 자막을 찾지 못했습니다.",
            'tried_languages': languages,
            'language_errors': errors
        }
    
    return last_result