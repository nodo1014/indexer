#!/usr/bin/env python3
"""
OpenSubtitles API의 기본 엔드포인트를 테스트하는 간단한 스크립트
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# 상위 디렉토리의 .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# API 키 확보
API_KEY = os.getenv('OPENSUBTITLES_API_KEY')
if not API_KEY:
    print("오류: API 키가 설정되지 않았습니다. .env 파일에 OPENSUBTITLES_API_KEY를 추가하세요.")
    sys.exit(1)

print(f"API 키: {API_KEY[:5]}...{API_KEY[-4:]} (총 {len(API_KEY)}자)")

# OpenSubtitles API 기본 URL
API_URL = "https://api.opensubtitles.com/api/v1"

# 기본 헤더
headers = {
    'Api-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'Subtitle Indexer/1.0'  # User-Agent 추가
}

def pretty_print_json(data):
    """JSON 데이터를 예쁘게 출력"""
    print(json.dumps(data, indent=2, ensure_ascii=False))

def test_languages_endpoint():
    """언어 목록 API 엔드포인트 테스트"""
    print("\n=== 지원 언어 목록 테스트 ===")
    try:
        resp = requests.get(f"{API_URL}/infos/languages", headers=headers)
        print(f"상태 코드: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"데이터 개수: {len(data.get('data', []))}개 언어 지원")
            # 한국어 정보 찾기
            ko_lang = next((lang for lang in data.get('data', []) if lang.get('iso639', '') == 'ko'), None)
            if ko_lang:
                print(f"한국어 정보: {ko_lang}")
            else:
                print("한국어(ko) 지원 정보를 찾을 수 없습니다.")
        else:
            print(f"오류 응답: {resp.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

def test_user_info():
    """사용자 정보 API 엔드포인트 테스트"""
    print("\n=== 사용자 정보 테스트 ===")
    try:
        resp = requests.get(f"{API_URL}/user", headers=headers)
        print(f"상태 코드: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("사용자 정보:")
            pretty_print_json(data)
        else:
            print(f"오류 응답: {resp.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

def test_subtitle_search(query="parasite", language="ko"):
    """자막 검색 API 엔드포인트 테스트"""
    print(f"\n=== 자막 검색 테스트 ({query}, {language}) ===")
    params = {
        "query": query,
        "languages": language
    }
    try:
        resp = requests.get(f"{API_URL}/subtitles", headers=headers, params=params)
        print(f"상태 코드: {resp.status_code}")
        print(f"요청 URL: {resp.url}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"검색 결과: {len(data.get('data', []))}건")
            
            # 첫 3개 결과만 출력
            for idx, item in enumerate(data.get('data', [])[:3]):
                attributes = item.get('attributes', {})
                print(f"\n결과 {idx+1}:")
                print(f"  제목: {attributes.get('feature_details', {}).get('movie_name', 'N/A')}")
                print(f"  릴리스: {attributes.get('release', 'N/A')}")
                print(f"  언어: {attributes.get('language', 'N/A')}")
                print(f"  다운로드 수: {attributes.get('download_count', 0)}")
                files = attributes.get('files', [])
                if files:
                    print(f"  파일명: {files[0].get('file_name', 'N/A')}")
        else:
            print(f"오류 응답: {resp.text}")
    except Exception as e:
        print(f"예외 발생: {e}")

if __name__ == "__main__":
    print("OpenSubtitles API 기본 테스트 시작\n")
    
    # 1. 지원 언어 목록 테스트
    test_languages_endpoint()
    
    # 2. 사용자 정보 테스트
    test_user_info()
    
    # 3. 자막 검색 테스트
    test_subtitle_search("parasite", "ko")  # 기생충 한국어 자막
    test_subtitle_search("avengers endgame", "ko")  # 어벤져스 엔드게임 한국어 자막
    
    print("\n테스트 완료")