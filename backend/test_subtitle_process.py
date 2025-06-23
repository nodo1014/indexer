import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor

# 테스트 설정
BASE_URL = "http://localhost:8080"
MEDIA_PATH = "/mnt/qq/Movie"  # 테스트할 미디어 경로
TEST_FILE = "Anyone.But.You.2023.1080p.WEBRip.1400MB.DD5.1.x264-GalaxyRG.mkv"  # 테스트할 파일

def test_process():
    # 1. 디렉토리 탐색 테스트
    browse_resp = requests.get(f"{BASE_URL}/api/browse?current_path=Movie")
    if browse_resp.status_code != 200:
        print(f"❌ 디렉토리 탐색 실패: {browse_resp.status_code}")
        return False
    
    # 2. 파일 목록 가져오기
    files_resp = requests.get(f"{BASE_URL}/api/files?scan_path=Movie")
    if files_resp.status_code != 200:
        print(f"❌ 파일 목록 조회 실패: {files_resp.status_code}")
        return False
    
    files = files_resp.json()
    test_file_path = f"{MEDIA_PATH}/{TEST_FILE}"
    
    # 3. 자막 다운로드 테스트
    subtitle_data = {
        "media_path": test_file_path,
        "language": "ko",
        "use_multilingual": True,
        "languages": ["ko", "en"]
    }
    
    download_resp = requests.post(f"{BASE_URL}/api/auto_process_subtitle", json=subtitle_data)
    
    if download_resp.status_code != 200:
        print(f"❌ 자막 다운로드 실패: {download_resp.status_code}")
        print(f"에러 메시지: {download_resp.text}")
        print("백엔드 로그에서 'subtitle_downloader' 관련 오류 확인 필요")
        return False
    
    result = download_resp.json()
    print(f"✅ 자막 다운로드 결과: {result}")
    return True

def run_with_timeout(func, timeout=30):
    """지정된 시간 내에 함수를 실행합니다"""
    with ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            print(f"⚠️ 테스트가 {timeout}초 제한시간을 초과했습니다")
            return False

if __name__ == "__main__":
    print("=== 자막 다운로드 프로세스 테스트 시작 ===")
    
    # 백엔드 서버가 실행 중인지 확인
    try:
        health = requests.get(f"{BASE_URL}/api/health", timeout=2)
        print("✅ 백엔드 서버 연결 성공")
    except requests.exceptions.ConnectionError:
        print("❌ 백엔드 서버에 연결할 수 없습니다")
        print("백엔드 서버를 실행한 후 다시 시도하세요: cd backend && python -m uvicorn main:app --reload --port 8080")
        exit(1)
    
    # 자막 다운로드 프로세스 테스트 실행
    success = run_with_timeout(test_process)
    
    if success:
        print("✅ 모든 테스트가 성공적으로 완료되었습니다")
    else:
        print("❌ 테스트 중 오류가 발생했습니다")
    
    print("=== 테스트 종료 ===")