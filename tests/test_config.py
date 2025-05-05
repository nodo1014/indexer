import pytest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings

def test_opensubtitles_api_key_set():
    """.env 또는 환경변수에 OpenSubtitles API 키가 올바르게 설정되어 있는지 확인합니다."""
    api_key = settings.opensubtitles_api_key
    assert api_key, (
        "OPENSUBTITLES_API_KEY가 .env에 설정되어 있지 않습니다. .env 파일에 실제 API 키를 입력하세요."
    )