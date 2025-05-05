import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    nas_media_path: str = "/mnt/qq" # 기본 경로
    opensubtitles_api_key: str = ""  # OpenSubtitles API 키 추가

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()

print("-" * 40)
print(f"DEBUG: config.py - Loaded nas_media_path: {settings.nas_media_path}")
print(f"DEBUG: config.py - OpenSubtitles API Key set: {'Yes' if settings.opensubtitles_api_key else 'No'}")
print(f"DEBUG: config.py - .env file path used: {settings.Config.env_file}")
print("-" * 40)