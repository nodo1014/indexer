# NAS 미디어 자막 자동화 서버 (FastAPI + Whisper)

## 개요
- NAS 미디어 파일을 위한 웹 기반 자막 생성/관리 자동화 도구
- FastAPI(Python) 백엔드 + HTML/JS 프론트엔드
- 디렉토리 브라우징, 실시간 진행률, Whisper 기반 자막 생성, 외부 자막 다운로드, 싱크/품질 체크, 자막 미리보기/수정/삭제 등 지원

## 주요 기능
- 폴더/파일 탐색 및 필터링, 실시간 작업 현황
- AI 자막 다운로드(외부/Whisper), 음성으로 자막 생성(Whisper)
- 자막 싱크/품질 체크, 자동 보정, 자막 미리보기/수정/삭제
- 내장 자막 추출/변환, 외부 자막 다운로드(OpenSubtitles)
- **탭 UI**: "AI 자막 다운로드"/"음성으로 자막 생성" 탭, 디자인/높이/정렬 완전 통일, 고정 높이 적용
- **JS 3분할 구조**: main.js(컨트롤러), websocket.js(실시간), render.js(화면 출력)

## 설치 및 실행
1. **Python 3.9+ 및 가상환경 권장**
2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
3. FastAPI 서버 실행
   ```bash
   uvicorn backend.main:app --reload
   ```
4. 웹브라우저에서 접속: [http://localhost:8000](http://localhost:8000)

## 디렉토리 구조
```
backend/
  main.py           # FastAPI 엔트리포인트
  ...
  static/
    main.js         # JS 컨트롤러
    websocket.js    # 실시간 통신
    render.js       # 화면 렌더링
    style.css       # 스타일 (탭 UI 포함)
  templates/
    index.html      # 메인 템플릿 (JS 분리)
README.md
PROGRESS.md
```

## 참고
- Whisper, ffmpeg, pysrt 등 필요 패키지 별도 설치 필요
- 상세 워크플로우/진행상황: PROGRESS.md 참고