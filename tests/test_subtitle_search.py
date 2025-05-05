import sys
import os
import json

# 상위 디렉토리의 모듈을 import 하기 위한 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.subtitle_downloader import (
    clean_title,
    title_similarity,
    download_subtitle_from_opensubtitles
)

def test_clean_title():
    """
    파일명 정제 기능 테스트
    """
    test_cases = [
        {"input": "The.Movie.2022.1080p.WEB-DL.AAC.H.264-GROUP.mp4", "expected": "the movie 2022"},
        {"input": "TV.Show.S01E05.720p.HEVC.x265-RARBG.mkv", "expected": "tv show s01e05"},
        {"input": "My.Documentary.2023.4K.HDR.AMZN.WEB-DL.DDP5.1.ATMOS.mkv", "expected": "my documentary 2023"}
    ]
    
    print("=== 파일명 정제 테스트 ===")
    for tc in test_cases:
        result = clean_title(tc["input"])
        print(f"입력: {tc['input']}")
        print(f"결과: '{result}'")
        print(f"예상: '{tc['expected']}'")
        print(f"성공: {result == tc['expected']}\n")

def test_title_similarity():
    """
    파일명 유사도 계산 테스트
    """
    test_cases = [
        {"a": "The.Movie.2022.1080p.mp4", "b": "The Movie 2022.srt", "expected_high": True},
        {"a": "Movie.2022.WebDL.mp4", "b": "Completely Different.srt", "expected_high": False},
        {"a": "TV.Show.S01E05.mkv", "b": "TV Show S01E05 1080p.srt", "expected_high": True}
    ]
    
    print("=== 파일명 유사도 테스트 ===")
    for tc in test_cases:
        similarity = title_similarity(tc["a"], tc["b"])
        print(f"파일명 A: {tc['a']}")
        print(f"파일명 B: {tc['b']}")
        print(f"유사도: {similarity:.2f} ({similarity * 100:.1f}%)")
        is_high = similarity > 0.6  # 60% 이상을 높은 유사도로 간주
        print(f"높은 유사도: {is_high} (예상: {tc['expected_high']})\n")

def test_subtitle_search():
    """
    자막 검색 기능 테스트
    """
    test_files = [
        "Interstellar.2014.1080p.BluRay.mp4",
        "The.Office.S05E13.720p.WEB-DL.mkv",
        "Parasite.2019.HDR.4K.mp4"
    ]
    
    print("=== 자막 검색 테스트 ===")
    for filename in test_files:
        print(f"\n파일명: {filename}")
        print("자막 검색 시도 중...")
        
        # 한국어 자막 검색
        result_ko = download_subtitle_from_opensubtitles(filename, "ko")
        print(f"검색 성공: {result_ko['success']}")
        
        if 'error' in result_ko:
            print(f"오류: {result_ko.get('error', '알 수 없는 오류')}")
        
        # 후보 수
        candidates = result_ko.get('candidates', [])
        best_match = result_ko.get('best_match')
        
        print(f"후보 수: {len(candidates)}")
        if best_match:
            print(f"최고 일치율 후보: {best_match['filename']} ({best_match['similarity']}%)")
            print(f"언어: {best_match['lang']}, 릴리스: {best_match['release']}")
        
        print("\n결과 샘플 (최대 3개):")
        for idx, candidate in enumerate(candidates[:3]):
            print(f"{idx+1}. {candidate['filename']} ({candidate['similarity']}%)")
            print(f"   언어: {candidate['lang']}, 다운로드 수: {candidate['downloads']}")
        
        print("-" * 50)

def test_download_and_save_subtitle(tmp_path, monkeypatch):
    """
    실제 파일 다운로드 및 저장 기능 테스트
    """
    from backend.services.subtitle_downloader import download_and_save_subtitle
    import requests

    # 더미 응답 객체 정의
    class DummyResponse:
        def __init__(self, content):
            self.content = content
        def raise_for_status(self):
            pass

    # requests.get을 더미 함수로 교체
    def dummy_get(url, timeout):
        return DummyResponse(b"dummy subtitle content")
    monkeypatch.setattr(requests, 'get', dummy_get)

    # 임시 경로에 파일 저장 테스트
    save_path = tmp_path / "test.srt"
    result = download_and_save_subtitle("http://example.com/sub.srt", str(save_path))
    assert result['success'] is True
    assert save_path.read_bytes() == b"dummy subtitle content"

def test_live_subtitle_search_and_download(tmp_path):
    """
    실제 OpenSubtitles API를 사용한 자막 검색 및 다운로드 통합 테스트
    (API 키 필요, .env에 OPENSUBTITLES_API_KEY가 설정되어 있어야 함)
    """
    import os
    from backend.services.subtitle_downloader import (
        download_subtitle_from_opensubtitles,
        get_subtitle_download_url,
        download_and_save_subtitle,
        login_opensubtitles,
        OPENSUBTITLES_API_KEY
    )
    
    # API 키가 설정되어 있는지 확인
    if not OPENSUBTITLES_API_KEY:
        print("OPENSUBTITLES_API_KEY가 설정되어 있지 않아 실제 테스트를 건너뜁니다.")
        return
    
    print("\n=== 실제 OpenSubtitles API 통합 테스트 ===")
    
    # 1. 먼저 로그인 (익명 접근)
    login_result = login_opensubtitles()
    print(f"OpenSubtitles API 로그인 결과: {login_result['success']}")
    if not login_result['success']:
        print(f"로그인 실패: {login_result.get('error', '알 수 없는 오류')}")
        if 'details' in login_result:
            print(f"세부 정보: {login_result['details']}")
        return
    
    # 인기 있는 영화로 검색 테스트 (한국어 자막)
    test_movies = [
        "Parasite.2019.1080p.mp4",
        "Avengers.Endgame.2019.1080p.mp4",
        "Interstellar.2014.1080p.mp4"
    ]
    
    for movie in test_movies:
        print(f"\n영화 파일: {movie}")
        # 정제된 파일명 출력 (디버깅용)
        from backend.services.subtitle_downloader import clean_title
        clean_movie = clean_title(movie)
        print(f"정제된 파일명: '{clean_movie}'")
        
        # 2. 자막 검색
        search_result = download_subtitle_from_opensubtitles(movie, "ko")
        print(f"검색 성공: {search_result['success']}")
        
        if not search_result['success']:
            print(f"오류: {search_result.get('error', '알 수 없는 오류')}")
            if 'details' in search_result:
                print(f"세부 정보: {search_result['details']}")
            continue
            
        if not search_result['candidates']:
            print("검색된 자막이 없습니다.")
            continue
            
        # 최고 일치율 자막 정보 출력
        best_match = search_result['best_match']
        if not best_match:
            print("일치하는 자막이 없습니다.")
            continue
            
        print(f"최고 일치율 자막: {best_match['filename']} ({best_match['similarity']}%)")
        print(f"언어: {best_match['lang']}, 다운로드 수: {best_match['downloads']}")
        
        # 실제 다운로드 URL 획득 테스트
        if best_match['similarity'] > 60:  # 일치율 60% 이상만 진행
            print(f"\n자막 다운로드 URL 요청 중... (file_id: {best_match['file_id']})")
            url_result = get_subtitle_download_url(best_match['file_id'])
            
            if not url_result['success']:
                print(f"다운로드 URL 획득 실패: {url_result.get('error', '알 수 없는 오류')}")
                if 'details' in url_result:
                    print(f"세부 정보: {url_result['details']}")
                continue
            
            # 다운로드 URL 획득 성공
            download_url = url_result['download_url']
            remaining = url_result.get('remaining_downloads', '알 수 없음')
            print(f"다운로드 URL 획득 성공! 남은 다운로드 수: {remaining}")
            
            # 3. 실제 다운로드 테스트
            save_path = tmp_path / f"{os.path.splitext(movie)[0]}.srt"
            print(f"자막 다운로드 시도... URL: {download_url[:50]}...")
            download_result = download_and_save_subtitle(download_url, str(save_path))
            
            if download_result['success']:
                print(f"자막 저장 성공: {save_path}")
                # 파일 내용 일부 확인
                with open(save_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read(500)  # 처음 500자만 읽기
                    print(f"자막 내용 미리보기 (처음 100자):\n{content[:100]}...")
            else:
                print(f"자막 다운로드 실패: {download_result.get('error', '알 수 없는 오류')}")
        else:
            print("일치율이 낮아 다운로드를 건너뜁니다.")
        
        print("-" * 50)
    
def test_download_subtitle_from_opensubtitles_success(monkeypatch):
    """
    OpenSubtitles 자막 검색 기능(monkeypatch) 성공 케이스 테스트
    """
    from backend.services.subtitle_downloader import download_subtitle_from_opensubtitles, OPENSUBTITLES_API_KEY
    import requests

    # 더미 API 응답 데이터
    dummy_data = {
        'data': [
            {'attributes': {
                'files': [{'file_name': 'Test.Movie.srt'}],
                'language': 'ko',
                'url': 'http://example.com/sub1.srt',
                'release': 'Test Release',
                'fps': 23.976,
                'votes': 10,
                'downloads_count': 5
            }}
        ]
    }

    # Dummy 응답 객체
    class DummyResponse:
        def __init__(self, data): self._data = data
        def raise_for_status(self): pass
        def json(self): return self._data

    # API 키 설정 및 requests.get 모킹
    monkeypatch.setattr('backend.services.subtitle_downloader.OPENSUBTITLES_API_KEY', 'dummy-key')
    monkeypatch.setattr(requests, 'get', lambda *args, **kwargs: DummyResponse(dummy_data))

    result = download_subtitle_from_opensubtitles('Test.Movie.mp4', 'ko')
    assert result['success'] is True
    assert isinstance(result['candidates'], list)
    assert result['best_match']['filename'] == 'Test.Movie.srt'


def test_download_subtitle_from_opensubtitles_no_key(monkeypatch):
    """
    OpenSubtitles API 키 미설정 시 에러 반환 테스트
    """
    from backend.services.subtitle_downloader import download_subtitle_from_opensubtitles

    # API 키 빈 문자열로 설정
    monkeypatch.setattr('backend.services.subtitle_downloader.OPENSUBTITLES_API_KEY', '')

    result = download_subtitle_from_opensubtitles('Any.mp4', 'en')
    assert result['success'] is False
    assert 'error' in result and 'API key' in result['error']

if __name__ == "__main__":
    # 각 테스트 함수 호출
    test_clean_title()
    print("\n" + "=" * 50 + "\n")
    
    test_title_similarity()
    print("\n" + "=" * 50 + "\n")
    
    test_subtitle_search()