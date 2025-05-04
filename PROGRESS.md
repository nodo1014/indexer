# 🚧 프로젝트 진행 상황 (PROGRESS.md)

## 🎯 프로젝트 목표

NAS에 저장된 미디어 파일 중 자막이 없는 파일을 효율적으로 찾아 Whisper를 이용해 자막을 생성하고 관리하는 시스템 구축.

**구성:**

*   **클라이언트 (MacBook/PyQt):** 미디어 분석, 작업 요청 (별도 프로젝트)
*   **서버 (Ubuntu/FastAPI):** Whisper 자막 생성 처리 (현재 프로젝트)

## 🗂️ 파일 구조 (예상)

```
.
├── venv/                   # 가상 환경
├── backend/                # FastAPI 서버 관련 코드
│   ├── main.py             # FastAPI 앱 진입점
│   ├── routers/            # API 라우터
│   │   └── whisper.py      # Whisper 관련 API
│   ├── services/           # 비즈니스 로직 (파일 스캔, Whisper 실행 등)
│   │   └── file_scanner.py
│   │   └── whisper_runner.py
│   ├── templates/          # Jinja2 HTML 템플릿
│   │   └── index.html
│   └── static/             # CSS, JS 등 정적 파일
│       └── style.css
├── requirements.txt        # Python 의존성 목록
├── README.md               # 프로젝트 개요 및 사용법
└── PROGRESS.md             # 작업 진행 상황 및 계획 (현재 파일)
```

## 📝 작업 계획 및 진행 상황

1.  **[X] 프로젝트 초기 설정:**
    *   [X] `README.md`, `PROGRESS.md` 생성 (backend/README.md, backend/PROGRESS.md)
    *   [X] Python 가상 환경 설정 (`venv`)
    *   [X] `requirements.txt` 파일 생성 및 기본 패키지 (FastAPI, Uvicorn, Jinja2) 추가
    *   [X] 기본 FastAPI 앱 구조 설정 (`backend/main.py`)
2.  **[X] NAS 스캔 기능 구현:**
    *   [X] 지정된 NAS 마운트 경로 탐색
    *   [X] 미디어 파일 (`.mp4`, `.mkv`, `.mp3`) 식별
    *   [X] 자막 파일 (`.srt`, `.vtt`, `.smi`) 존재 여부 확인
    *   [X] 자막 없는 파일 목록 생성 (`backend/services/file_scanner.py`)
3.  **[X] 웹 UI 구현 (Jinja2):**
    *   [X] 자막 없는 파일 목록 표시 (`backend/templates/index.html`)
    *   [X] 파일 선택용 체크박스 추가
    *   [X] Whisper 실행 버튼 추가
    *   [X] 결과 표시 영역 추가
4.  **[X] Whisper 연동 기능 구현:**
    *   [X] 선택된 파일 목록을 받아 Whisper 실행 (`backend/services/whisper_runner.py`)
    *   [X] Whisper 모델 선택 기능 (UI 및 백엔드 연동)
    *   [X] Whisper 실행 상태 피드백 (진행률 등)
    *   [X] 결과 파일 (`_lang.srt`) 저장
    *   [X] 동시 실행 제한 및 작업 큐 관리
5.  **[X] 결과 처리 및 다운로드:**
    *   [X] 생성된 자막 파일 목록 업데이트
    *   [X] 자막 미리보기 기능
    *   [X] 자막 파일 다운로드 링크 제공
6.  **[X] 로깅 및 오류 처리:**
    *   [X] 주요 작업 단계 로깅 추가
    *   [X] Whisper 실행 오류 처리
7.  **[X] 리팩토링 및 오류 수정:**
    *   [X] 디렉토리 탐색기 표시 오류 수정
       *   [X] `list_subdirectories` 함수 개선 (backend/services/file_scanner.py)
       *   [X] 브라우저 경로 관리 수정 (backend/main.py의 browse 엔드포인트)
       *   [X] 탐색기 UI 개선 (backend/templates/index.html의 JavaScript)
    *   [X] CSS 스타일 개선 및 UI 디자인 보완 (backend/static/style.css)
    *   [X] 오류 메시지 및 로깅 개선
    *   [X] WebSocket 연결 안정성 향상 (재연결 로직 추가)
    *   [X] 코드 구조 및 가독성 향상
8.  **[ ] 배포 및 테스트:**
    *   [ ] Ubuntu 서버 환경 설정 (NAS 마운트 확인)
    *   [ ] 실제 미디어 파일 테스트

## 🔗 관련 파일

*   `README.md`
*   `PROGRESS.md`
*   `backend/main.py` - FastAPI 메인 애플리케이션
*   `backend/services/file_scanner.py` - 파일 스캔 및 디렉토리 탐색 기능
*   `backend/services/whisper_runner.py` - Whisper 실행 및 작업 관리
*   `backend/connection_manager.py` - WebSocket 연결 및 작업 관리
*   `backend/templates/index.html` - 웹 UI 템플릿
*   `backend/static/style.css` - UI 디자인 스타일
*   `backend/config.py` - 애플리케이션 설정 관리

## 🛠️ 최근 변경 사항 (2025-03-25)

1. **디렉토리 탐색기 표시 오류 수정**
   - 디렉토리 목록 조회 함수의 버그 수정
   - 상대 경로 및 절대 경로 변환 로직 개선
   - 엣지 케이스(빈 경로, 존재하지 않는 경로 등) 처리

2. **UI 및 UX 개선**
   - 디렉토리 탐색기 UI 개선 (색상, 여백, 테두리 등)
   - 반응형 디자인 추가로 모바일 환경 지원
   - 에러 메시지 및 사용자 피드백 개선
   - **탐색기 영역에 '현재 폴더 검색' 버튼 추가**
   - 폴더 진입 시 파일 목록을 자동으로 불러오지 않고, 안내 메시지와 함께 사용자가 직접 '현재 폴더 검색' 버튼을 눌러야 미디어 파일 목록이 표시되도록 UX 개선
   - **탐색기에서 각 폴더명 옆에 (영상 #, 오디오 #)가 표시되어, 폴더별 미디어 파일 분포를 직관적으로 확인 가능하도록 개선**

3. **코드 리팩토링**
   - JavaScript 코드 구조화 및 모듈화
   - WebSocket 연결 안정성 강화 (자동 재연결 기능)
   - 타입 및 오류 처리 개선

## 📋 다음 단계

1. Ubuntu 서버에 배포 및 실제 NAS 환경에서 테스트
2. 성능 최적화 (대용량 디렉토리 처리 개선)
3. 사용자 피드백 수집 및 추가 기능 개발 검토 

# 진행 상황 및 변경 이력 (최신순)

## 2024-05-04

- **Whisper 작업 현황 유지 개선**
  - /run-whisper에서 Whisper 작업 실행 시 각 파일마다 job_manager.add_job을 호출하여, 새로고침/폴링에도 작업 현황이 사라지지 않도록 개선 (main.py, job_manager.py)
- **탐색기 트리 미디어 개수 집계 개선**
  - 폴더별 영상/오디오 개수를 하위폴더까지 모두 포함해 재귀적으로 집계하도록 개선 (file_scanner.py)
- **파일 검색 결과 요약 상세 표시**
  - 검색 후 batch-status 영역에 총 파일 수, 영상/오디오 개수, 자막 없는/있는 파일 수 등 상세 요약 표시 (index.html, file_scanner.py)
  - scanCurrentDirectory에서 '파일 검색 완료' 메시지 제거로 상세 요약이 유지됨 (index.html)
- **탐색기(디렉토리 브라우저) 영역 리팩토링**
  - id/class 네이밍 일관성, 한글 주석, null 체크, 폴더명 옆 (영상 #, 오디오 #) 표시 안정화 (index.html)
- **표 간격 및 컬럼별 너비 조정**
  - 상태/언어 컬럼 최소 너비, 자막 미리보기 컬럼 넓게, CSS 인라인 적용 (index.html)
- **상태/자막 미리보기 클릭 시 모달창 표시**
  - 상태 클릭: 상세 작업 상황 모달, 자막 미리보기 클릭: 전체 자막 모달(스크롤 가능) (index.html)
- **백엔드 파일 목록 응답에 has_subtitle 필드 추가**
  - 프론트 통계 계산 정상화 (file_scanner.py)

--- 