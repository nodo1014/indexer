#!/usr/bin/env python3
"""
OpenSubtitles API의 통합 검색 및 다운로드 기능 테스트
"""
import os
import sys
import tempfile
import re
from dotenv import load_dotenv

# 상위 디렉토리를 파이썬 패스에 추가
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# .env 파일 로드
load_dotenv(os.path.join(parent_dir, '.env'))

# 테스트할 서비스 함수 임포트
from backend.services.subtitle_downloader import (
    clean_title,
    search_and_download_subtitle
)

def test_integrated_subtitle_service():
    """통합 자막 검색 및 다운로드 서비스 테스트"""
    
    print("===== 통합 자막 검색 및 다운로드 테스트 시작 =====\n")
    
    # 테스트 할 영화 목록 (인기 영화와 정확한 릴리스명 포함)
    test_files = [
        "Parasite.2019.1080p.BluRay.x264-YTS.LT.mp4",
        "Avengers.Endgame.2019.1080p.BluRay.H264.AAC-RARBG.mp4",
        "The.Matrix.1999.1080p.BrRip.x264.YIFY.mp4"
    ]
    
    # 임시 디렉토리 생성 (테스트 자막 저장용)
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"임시 디렉토리 생성됨: {temp_dir}\n")
        
        for filename in test_files:
            print(f"\n파일명: {filename}")
            clean_name = clean_title(filename)
            print(f"정제된 제목: {clean_name}")
            
            # 임시 자막 파일 경로 생성
            base_name = os.path.splitext(filename)[0]
            save_path = os.path.join(temp_dir, f"{base_name}.srt")
            
            # 자막 검색 및 다운로드 테스트
            print("자막 검색 및 다운로드 시도 중...")
            result = search_and_download_subtitle(
                filename=filename,
                save_path=save_path,
                language="ko",
                min_similarity=50.0  # 테스트를 위해 낮은 유사도 허용
            )
            
            # 결과 출력
            print(f"성공 여부: {result['success']}")
            
            if result['success']:
                print(f"자막 저장 경로: {result['save_path']}")
                print(f"최적 매치 정보: {result.get('best_match', {}).get('title', 'N/A')}")
                print(f"유사도: {result.get('similarity', 0)}%")
                print(f"남은 다운로드 수: {result.get('remaining_downloads', 'N/A')}")
                
                # 자막 내용 미리보기
                try:
                    with open(save_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read(500)  # 처음 500자
                        print(f"\n자막 내용 미리보기 (처음 100자):\n{content[:100]}...")
                        
                        # SRT 형식 확인 (시간 코드 패턴)
                        has_timecode = bool(re.search(r'\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d', content))
                        print(f"SRT 시간 코드 확인됨: {has_timecode}")
                except Exception as e:
                    print(f"자막 파일 읽기 실패: {e}")
            else:
                print(f"실패 단계: {result.get('stage', 'unknown')}")
                print(f"오류 메시지: {result.get('error', 'unknown error')}")
                if 'best_match' in result:
                    print(f"최적 매치 정보: {result['best_match']}")
            
            print("-" * 60)
    
    print("\n===== 테스트 완료 =====")

if __name__ == "__main__":
    test_integrated_subtitle_service()