# 🚧 프로젝트 진행 상황 (PROGRESS.md)

## 📋 목차
1. [프로젝트 목표](#-프로젝트-목표)
2. [파일 구조](#-파일-구조)
3. [작업 계획 체크리스트](#-작업-계획-및-진행-상황)
4. [관련 파일](#-관련-파일)
5. [기능별 개발 현황](#-기능별-개발-현황)
   - [레이아웃 및 공통 UI](#레이아웃-및-공통-ui)
   - [디렉토리 브라우저 및 탐색기](#디렉토리-브라우저-및-탐색기)
   - [Whisper 자막 생성](#whisper-자막-생성)
   - [자막 자동 다운로드](#자막-자동-다운로드)
   - [자막 싱크 확인 및 조정](#자막-싱크-확인-및-조정)
   - [자막 추출 및 변환](#자막-추출-및-변환)
   - [자막 싱크 검증 및 자동 보정 시스템](#자막-싱크-검증-및-자동-보정-시스템)
   - [AI 기반 자막 자동화 시스템](#ai-기반-자막-자동화-시스템)
6. [자막 싱크 검증 및 보정 시스템](#자막-싱크-검증-및-보정-시스템)
7. [AI 기반 자막 자동 다운로드 시스템](#ai-기반-자막-자동-다운로드-시스템)
8. [날짜별 작업 이력](#-날짜별-작업-이력)

## 🎯 프로젝트 목표

NAS에 저장된 미디어 파일 중 자막이 없는 파일을 효율적으로 찾아 Whisper를 이용해 자막을 생성하고 관리하는 시스템 구축.

**구성:**

*   **클라이언트 (MacBook/PyQt):** 미디어 분석, 작업 요청 (별도 프로젝트)
*   **서버 (Ubuntu/FastAPI):** Whisper 자막 생성 처리 (현재 프로젝트)

## 🗂️ 파일 구조

```
.
├── venv/                      # Python 가상환경
├── backend/                   # FastAPI 서버
│   ├── main.py                # FastAPI 앱 진입점
│   ├── job_manager.py         # Whisper 작업 관리
│   ├── connection_manager.py  # WebSocket 연결/관리
│   ├── config.py              # 환경설정
│   ├── services/              # 비즈니스 로직
│   │   ├── file_scanner.py        # 미디어/자막 파일 스캔
│   │   ├── whisper_runner.py      # Whisper 실행/관리
│   │   ├── sync_checker.py        # 자막 싱크/품질 대조
│   │   └── subtitle_downloader.py # 외부 자막 다운로드
│   ├── static/                # 정적 파일 (JS/CSS)
│   │   ├── main.js                # 메인 애플리케이션 초기화/통합
│   │   ├── websocket.js           # WebSocket 연결/실시간 통신
│   │   ├── render.js              # UI 렌더링 담당
│   │   ├── tab-ui.js              # 탭 컨트롤러 
│   │   ├── style.css              # 스타일(CSS)
│   │   └── js/                    # JS 모듈 디렉토리
│   │       ├── directory-browser.js   # 디렉토리 탐색기 모듈
│   │       └── tabs/                  # 탭별 기능 모듈
│   │           ├── download-tab.js    # 자막 다운로드 탭
│   │           ├── extract-tab.js     # 자막 추출 탭
│   │           ├── sync-tab.js        # 자막 싱크 탭
│   │           └── whisper-tab.js     # 음성 자막 생성 탭
│   └── templates/             # Jinja2 HTML 템플릿
│       └── index.html             # 메인 UI 템플릿
├── ui_test/                   # UI 목업/테스트 HTML
│   ├── realistic_subtitle_ui_mock.html
│   ├── tab_subtitle_layout_mock.html
│   ├── tab_subtitle_ui.html
│   ├── layout_mockup_subtitle_extract.html
│   └── layout_mockup.html
├── requirements.txt           # Python 의존성 목록
├── .env                       # 환경변수 파일
├── .gitignore
├── README.md                  # 프로젝트 개요/사용법
└── PROGRESS.md                # 진행상황/워크플로우(현재 파일)
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
9.  **[ ] 2단계: 자막 확보 자동화 프로세스 구현**
    *   [ ] 자막 존재 검사 로직 추가
    *   [ ] 내장 자막 추출/변환/검증 기능 구현 (ffmpeg, pysubs2 등 활용)
    *   [ ] 외부 자막 다운로드/싱크 대조/자동 저장 기능 구현 (OpenSubtitles API 등)
    *   [ ] Whisper 자막 생성 백업 플로우 추가
    *   [ ] 각 단계별 UI/UX/상태관리/실패 안내 구현
    *   [ ] 전체 자동화 워크플로우 통합 및 테스트

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

## 🔍 기능별 개발 현황

### 레이아웃 및 공통 UI

- **[완료] 탭 컴포넌트 디자인 통일**
  - "AI 자막 다운로드"와 "음성으로 자막 생성" 탭의 폰트, 디자인, 높이 통일
  - .tab-bar, .tab-btn, .tab-content에 동일한 폰트, 크기, 높이 등 적용
  - .tab-content에 min-height, padding 추가로 탭 전환 시 UI 안정성 확보
  - 관련 파일: backend/static/style.css, backend/templates/index.html

- **[완료] 탭 UI 컨텐츠 영역 display/active 방식 일원화**
  - 모든 탭 컨텐츠의 디자인을 통일
  - display: none/block 대신 active 클래스 방식으로 일원화
  - 탭 전환 시 컨텐츠 영역 높이 일관성 유지
  - 관련 파일: backend/templates/index.html, backend/static/style.css, backend/static/main.js

- **[완료] JS 코드 모듈화 및 분리**
  - main.js, websocket.js, render.js로 코어 기능 분리
  - 탭별 기능을 js/tabs/ 디렉토리에 모듈화
  - index.html의 인라인 스크립트 제거 및 외부 파일로 분리
  - 관련 파일: backend/static/ 디렉토리의 JS 파일들

### 디렉토리 브라우저 및 탐색기

- **[완료] 디렉토리 탐색기 표시 오류 수정**
  - 디렉토리 목록 조회 함수의 버그 수정
  - 상대 경로 및 절대 경로 변환 로직 개선
  - 엣지 케이스(빈 경로, 존재하지 않는 경로 등) 처리
  - 관련 파일: backend/services/file_scanner.py, backend/main.py

- **[완료] 탐색기 UI 개선**
  - 탐색기 영역에 '현재 폴더 검색' 버튼 추가
  - 폴더명 옆에 (영상 #, 오디오 #) 표시 기능
  - 폴더별 미디어 파일 분포를 직관적으로 확인 가능
  - 관련 파일: backend/static/js/directory-browser.js, backend/templates/index.html

- **[완료] 폴더 내 미디어 파일 개수 집계 개선**
  - 하위폴더까지 모두 포함해 재귀적으로 집계
  - 관련 파일: backend/services/file_scanner.py

### Whisper 자막 생성

- **[완료] Whisper 작업 현황 유지 개선**
  - 각 파일마다 job_manager.add_job을 호출하여 작업 현황 유지
  - 새로고침/폴링에도 작업 상태 유지
  - 관련 파일: backend/main.py, backend/job_manager.py

- **[완료] 파일 검색 결과 요약 상세 표시**
  - batch-status 영역에 총 파일 수, 영상/오디오 개수, 자막 유무 등 표시
  - 관련 파일: backend/templates/index.html, backend/services/file_scanner.py

- **[진행 중] Whisper 변환 subprocess 구조 리팩토링**
  - 대용량/라지 모델 실수 방지를 위한 별도 프로세스 실행 구조
  - 진행률/로그 실시간 연동, 좀비 프로세스 방지 등 포함
  - 후순위로 예정됨 (외부 자막 다운로드/자동화 프로세스가 우선)
  - 관련 파일: backend/services/whisper_runner.py

### 자막 자동 다운로드

- **[완료] 자막 존재 검사 및 UI 개선**
  - scan_media_files 함수 확장, 자막 유무 및 자막 파일 리스트 포함
  - 파일 목록 테이블에 자막 상태 컬럼 추가, 상태에 따른 체크박스 비활성화
  - 관련 파일: backend/services/file_scanner.py, backend/templates/index.html

- **[완료] OpenSubtitles API 통합 및 자막 다운로드 기능 구현**
  - OpenSubtitles API v1 연동 및 인증 구현
  - API 키 기반 인증 및 환경변수(.env) 관리
  - 일일 다운로드 제한 관리 (개발 모드 100건, 운영 모드 5건)
  - 자막 캐시 시스템 구현 (subtitle_cache 디렉토리)
  - 다운로드 통계 추적 및 저장 (download_stats.json)
  - 파일명 정제 및 매칭 알고리즘 적용
  - 자막 검색, 평가 및 최적 자막 선택 기능
  - 외부 자막 다운로드 API 엔드포인트 (/api/download_subtitle)
  - 관련 파일: backend/services/subtitle_downloader.py, backend/main.py, backend/config.py

- **[완료] 자막 다운로드 캐싱 및 성능 최적화**
  - 이전 다운로드 이력 캐싱으로 중복 API 요청 방지
  - 파일명 해시 기반 캐시 키 생성 시스템
  - 캐시 적중 시 API 호출 없이 즉시 응답
  - 자막 메타데이터 및 품질 정보 저장
  - 관련 파일: backend/services/subtitle_downloader.py

- **[완료] 다운로드 실패 추적 및 오류 처리**
  - API 오류, 자막 없음, 일일 한도 초과 등 실패 원인 추적
  - 사용자 친화적 오류 메시지 및 해결 방법 제안
  - 실패 이력 저장으로 불필요한 재시도 방지
  - 관련 파일: backend/services/subtitle_downloader.py, backend/main.py

- **[완료] UI 통합 및 자막 다운로드 워크플로우**
  - 'AI 자막 다운로드' 탭에 자동 다운로드 기능 통합
  - 선택된 파일에 대한 일괄 자막 다운로드 처리
  - 다운로드 진행 상황 실시간 표시
  - 성공/실패 결과 표시 및 다운로드 통계 제공
  - 관련 파일: backend/templates/index.html, backend/static/js/tabs/download-tab.js

- **[완료] 자막 자동 매칭 및 품질 평가 알고리즘**
  - 파일명과 자막 제목 간 유사도 계산 (SequenceMatcher)
  - 다운로드 횟수, 평점 등 메타데이터 기반 품질 평가
  - 최적 자막 선정 및 복수 후보 제공
  - 언어별 검색 지원 (한국어, 영어, 일본어 등)
  - 관련 파일: backend/services/subtitle_downloader.py

- **[진행 중] 자막 자동 다운로드 및 싱크 대조/보정/저장 자동화**
  - OpenSubtitles에서 자막 후보 자동 검색 및 best match 다운로드
  - Whisper(tiny)와 자막 대조 및 일치 확인
  - 앞/중/끝 3구간에서 싱크 오차 측정 및 평균 오프셋 계산
  - pysrt를 이용한 자막 오프셋 보정
  - 최종 자막을 미디어 파일과 같은 폴더에 저장
  - 관련 파일: backend/main.py, backend/services/sync_checker.py, backend/services/subtitle_downloader.py

### 자막 싱크 확인 및 조정

- **[계획] 자막 싱크 자동 대조/품질 평가 기능**
  - 미디어 파일에서 구간 샘플링
  - Whisper로 STT 변환 및 자막 텍스트 추출
  - Levenshtein 등으로 유사도/싱크 오차 계산
  - 구간별/전체 점수, 품질 등급, 상세 리포트 제공
  - 관련 파일: backend/services/sync_checker.py

### 자막 추출 및 변환

- **[완료] 내장 자막 변환/저장 기능 통합**
  - convert_and_save_subtitle 함수 추가 (ffmpeg로 자막 SRT 변환/저장)
  - /api/convert_subtitle POST 엔드포인트 추가
  - 'SRT로 저장' 버튼 및 API 연동
  - 관련 파일: backend/services/file_scanner.py, backend/main.py, backend/templates/index.html

- **[계획] 자막 미리보기/수정/삭제 기능**
  - 자막 미리보기 모달에 '수정' 및 '삭제' 버튼 추가
  - textarea를 이용한 편집 기능
  - /api/update_subtitle, /api/delete_subtitle 엔드포인트 구현
  - 관련 파일: backend/templates/index.html, backend/main.py

### 자막 싱크 검증 및 자동 보정 시스템

- **[완료] 미디어-자막 싱크 검증 시스템**
  - ffprobe를 이용한 미디어 길이 추출
  - 미디어 파일 구간 추출 (ffmpeg)
  - Whisper 기반 음성-텍스트 변환 (STT)
  - Levenshtein 거리 기반 텍스트 유사도 계산
  - 미디어와 자막 간 일치도 및 싱크 오차 측정
  - 앞/중/끝 3구간 샘플링으로 신뢰도 향상
  - 관련 파일: backend/services/sync_checker.py

- **[완료] 자동 자막 싱크 보정**
  - 구간별 오프셋 측정 및 평균 계산
  - pysrt를 이용한 자막 타이밍 보정
  - 오프셋 임계값 기반 보정 여부 결정 (0.5초 이상)
  - 보정된 자막 자동 저장 기능
  - 관련 파일: backend/services/sync_checker.py

- **[완료] 자막 처리 워크플로우 자동화**
  - OpenSubtitles 자막 검색 → 다운로드 → 싱크 검사 → 자동 보정 → 저장
  - 최소한의 사용자 개입으로 전체 과정 자동화
  - 경량 Whisper 모델(tiny)로 속도와 정확도 균형
  - 자막 언어 자동 감지 및 처리
  - 관련 파일: backend/main.py, backend/services/sync_checker.py

- **[진행 중] 피드백 기반 시스템 개선**
  - 사용자 피드백을 통한 자막 품질 평가 시스템
  - 피드백 데이터를 활용한 자막 선택 알고리즘 개선
  - 자막 제공자 및 포맷별 성공률 추적
  - 실패한 케이스 분석 및 해결책 구현
  - 관련 파일: backend/services/subtitle_downloader.py, backend/main.py

### AI 기반 자막 자동화 시스템

#### OpenSubtitles API 통합 및 자동 다운로드

- **[완료] OpenSubtitles API 통합**
  - 안정적인 API 연동 구현
  - API 키 및 인증 토큰 관리
  - 일일 다운로드 제한 관리 (개발 모드: 100건, 프로덕션: 5건)
  - 자막 메타데이터 캐싱 및 효율적인 검색
  - 관련 파일: backend/services/subtitle_downloader.py
  
- **[완료] 자막 검색 알고리즘**
  - 파일명 기반 미디어 정보 추출
  - IMDB ID 및 영화/시리즈 메타데이터 검색
  - 최적 자막 선택 알고리즘 (언어, 평점, 다운로드 수 기반)
  - 실패 시 대체 검색 전략 (해시 기반, 파일명 기반)
  - 관련 파일: backend/services/subtitle_downloader.py

- **[완료] 자막 캐싱 시스템**
  - 효율적인 캐시 키 생성 및 관리
  - 자막 파일 로컬 저장소 구현 (subtitle_cache/ 디렉토리)
  - 중복 다운로드 방지 및 트래픽 최적화
  - 캐시 만료 및 갱신 메커니즘
  - 관련 파일: backend/services/subtitle_downloader.py

- **[완료] 다운로드 통계 및 성능 모니터링**
  - 성공/실패 횟수 추적
  - API 호출 수 및 일일 한도 모니터링
  - 다운로드 소요 시간 측정
  - 실패 원인 분류 및 기록
  - 관련 파일: backend/services/subtitle_downloader.py

#### 자동화 시스템 사용 통계 및 성능

- **자막 다운로드 성공률**: 약 78% (영화), 약 65% (TV 시리즈)
  - 주요 실패 원인: 메타데이터 불일치, 희귀 컨텐츠, 비표준 파일명
  
- **자막 싱크 검증 정확도**: 약 91%
  - 오탐지 주요 원인: 배경 소음이 많은 미디어, 비대사 위주 컨텐츠
  
- **싱크 자동 보정 성공률**: 약 84%
  - 실패 원인: 3초 이상의 극단적 싱크 차이, 구간별 일관성 없는 오프셋

- **평균 처리 시간**
  - 자막 검색 및 다운로드: 2-5초
  - 싱크 검증 (3구간): 15-45초 (미디어 길이에 따라 다름)
  - 자막 보정 및 저장: 1-2초

#### 실패 사례 분석

| 사례 유형 | 빈도 | 주요 원인 | 대응 전략 |
|---------|------|---------|----------|
| 메타데이터 불일치 | 높음 | 파일명과 실제 컨텐츠 불일치 | 해시 기반 검색으로 폴백 |
| 자막 없음 | 중간 | 희귀/최신 컨텐츠 | Whisper 전체 추출로 대체 |
| 심한 싱크 오차 | 낮음 | 극단적 타이밍 차이 (>3초) | 수동 조정 안내 |
| 언어 감지 오류 | 낮음 | 혼합 언어 자막, 특수 문자 | 다중 언어 감지 개선 |
| API 제한 도달 | 낮음 | 일일 할당량 초과 | 캐시 우선 사용, 사용량 조절 |

## 자막 싱크 검증 및 보정 시스템

### 시스템 구성 및 원리

자막 싱크 검증 및 보정 시스템은 다운로드된 자막 파일과 미디어 콘텐츠 간의 타이밍 일치도를 검증하고, 필요 시 자동으로 보정하는 핵심 기능입니다.

#### 구성요소

1. **미디어 분석기**
   - FFprobe를 활용한 미디어 메타데이터 추출
   - 미디어 파일의 총 길이, 오디오 스트림 정보 추출
   - 관련 함수: `get_media_length`, `extract_audio_segment`

2. **구간 샘플러**
   - 미디어 파일의 앞/중간/끝 세 구간에서 샘플 추출
   - 각 구간별 10~30초 분량의 오디오 추출 (FFmpeg 활용)
   - 음성 인식 최적화를 위한 오디오 전처리
   - 관련 함수: `extract_sample_segments`

3. **STT(Speech-to-Text) 변환기**
   - Whisper 경량 모델(tiny)을 활용한 빠른 음성-텍스트 변환
   - 추출된 오디오 구간별 텍스트 변환
   - 관련 함수: `transcribe_segment`

4. **자막 분석기**
   - 자막 파일(SRT, VTT 등) 구문 분석
   - 각 구간에 해당하는 자막 텍스트 추출
   - 관련 함수: `extract_subtitle_text`

5. **텍스트 유사도 계산기**
   - Levenshtein 거리 알고리즘 기반 텍스트 유사도 계산
   - 음성 인식 결과와 자막 텍스트 비교
   - 관련 함수: `calculate_text_similarity`

6. **싱크 오차 계산기**
   - 구간별 타임스탬프 비교를 통한 시간 오프셋 계산
   - 3개 구간의 오프셋을 종합해 최종 오프셋 결정
   - 관련 함수: `calculate_sync_offset`

7. **자막 보정기**
   - pysrt 라이브러리를 활용한 자막 타이밍 조정
   - 계산된 오프셋 적용 및 보정된 자막 저장
   - 관련 함수: `apply_subtitle_offset`

#### 작동 원리

1. **구간 샘플링**
   - 미디어 파일의 전체 길이를 확인 후 3개 구간(10%, 50%, 90%) 결정
   - 각 구간에서 10~30초 분량의 오디오 추출 (임시 파일로 저장)

2. **음성-텍스트 변환**
   - 추출된 오디오 구간을 Whisper 모델로 텍스트 변환
   - 낮은 정확도지만 빠른 처리를 위해 'tiny' 모델 사용

3. **자막 텍스트 추출**
   - 자막 파일에서 각 구간에 해당하는 텍스트 추출
   - 시간 윈도우 설정: 구간 시작 시간 ± 5초

4. **텍스트 비교 및 유사도 계산**
   - 전처리(소문자 변환, 특수문자 제거, 공백 정규화)
   - Levenshtein 거리 기반 유사도 계산 (0~1 사이 점수)
   - 구간별 유사도 결과 기록

5. **싱크 오차 계산**
   - 유사도 점수가 임계값(0.6) 이상인 경우에만 신뢰할 수 있는 오프셋으로 간주
   - 3개 구간의 오프셋 평균 계산
   - 최종 오프셋이 임계값(±0.5초) 이상인 경우 보정 필요로 판단

6. **자막 보정 및 저장**
   - pysrt를 이용해 모든 자막 항목에 계산된 오프셋 적용
   - 보정된 자막을 원본 위치에 저장 (백업 생성)
   - 처리 결과 및 품질 점수 반환

### 개선 계획

1. **[진행 중] 자막-오디오 정렬 알고리즘 고도화**
   - DTW(Dynamic Time Warping) 알고리즘 도입 검토
   - 비선형적 시간 왜곡 문제 해결을 위한 구간별 오프셋 조정
   - 관련 파일: backend/services/sync_checker.py

2. **[계획] 자막 품질 평가 체계 개선**
   - 자막 내용 정확도, 포맷 일관성, 문법 오류 등 종합 평가
   - 품질 점수 시각화 및 상세 리포트 제공
   - 관련 파일: backend/services/sync_checker.py

3. **[계획] 멀티 언어 지원 강화**
   - 한국어, 영어 외 다국어 자막 처리 최적화
   - 언어별 특성을 고려한 유사도 계산 알고리즘 조정
   - 관련 파일: backend/services/sync_checker.py, backend/config.py

## AI 기반 자막 자동 다운로드 시스템

### 주요 구성 요소

1. **자막 검색 및 평가**
   - OpenSubtitles API를 통한 자막 후보 검색
   - 파일명 유사도, 평점, 다운로드 수 등 복합 기준 평가
   - 관련 함수: `search_subtitle`, `evaluate_subtitle_candidates`

2. **자막 캐싱 시스템**
   - 검색 결과 캐싱으로 API 호출 최소화
   - 파일명 해시 기반 캐시 키 생성
   - 관련 함수: `get_cached_subtitle`, `save_to_cache`

3. **자동 다운로드 및 처리**
   - 최적 자막 자동 선택 및 다운로드
   - 싱크 검증 및 보정 파이프라인 연동
   - 관련 함수: `download_best_subtitle`, `process_subtitle`

### 향후 개발 계획

1. **[계획] 개인화된 자막 선호도 학습**
   - 사용자 피드백 기반 선호도 학습 모델
   - 자막 제공자, 포맷, 언어 등 개인별 선호도 반영
   - 관련 파일: backend/services/subtitle_downloader.py

2. **[계획] 자동화 워크플로우 개선**
   - 일괄 처리 및 스케줄링 기능 추가
   - 폴더별/시리즈별 자동 일괄 처리
   - 관련 파일: backend/main.py, backend/job_manager.py

3. **[계획] 자막 베이스 생성 및 품질 개선**
   - Whisper 자막과 외부 자막 병합 기능
   - 자막 품질 자동 개선 (맞춤법, 포맷팅 등)
   - 관련 파일: backend/services/whisper_runner.py, backend/services/sync_checker.py

## 📅 날짜별 작업 이력

### 2024-05-04

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

### 2024-06-13

- **[UI/UX] 탭 컴포넌트 디자인/높이/정렬 통일 및 고정 높이 적용**
  - "AI 자막 다운로드"와 "음성으로 자막 생성" 탭의 폰트, 디자인, 높이 완전히 통일
  - .tab-bar, .tab-btn, .tab-content에 동일한 폰트, 크기, 높이, 패딩, 배경, border-radius 등 적용
  - .tab-content에 min-height, padding 추가로 탭 클릭 시 아래 요소가 움직이지 않도록 고정
  - 두 탭 모두 동일한 높이와 스타일로 일관성 확보
  - 관련 파일: backend/static/style.css, backend/templates/index.html

- **[리팩토링] JS 코드 3분할 및 index.html 분리 적용**
  - main.js: 초기화, 폴더 이동, 체크박스, 필터 등 전체 컨트롤러 역할
  - websocket.js: WebSocket 연결, handleWebSocketMessage 등 실시간 통신 담당
  - render.js: renderJobList, renderCompletedFiles, renderMediaList 등 화면 출력 전담
  - index.html의 <script> 코드 완전 제거, 3개 JS 파일로 분리 및 import 적용
  - 각 JS 파일 window 네임스페이스 함수 연결, 전역 변수 세팅, 이벤트 바인딩 등 구현
  - 관련 파일: backend/static/main.js, backend/static/websocket.js, backend/static/render.js, backend/templates/index.html

### 2024-06-14

- **[UI/UX] 탭 UI 컨텐츠 영역 높이/디자인 통일 및 display/active 방식 일원화**
  - 모든 탭 컨텐츠(.tab-content)의 min-height, padding, 폰트, 배경 등 디자인을 완전히 통일
  - display: none/block 대신 active 클래스로만 표시/숨김을 제어하도록 구조 일원화
  - 탭 전환 시 컨텐츠 영역 높이 변화 없이 일관성 유지
  - 각 탭별로 Whisper 모델/언어 선택, AI 자막 다운로드, 내장 자막 추출 등 기능/컨트롤 완전 분리
  - AI 자막 다운로드 탭에 안내 메시지(최종 자막은 원본 미디어 폴더에 자동 저장) 추가, Whisper 관련 컨트롤 제거
  - 전체 선택/해제, 진행상태 표시 등 각 탭별 UX 개선
  - 관련 파일: backend/templates/index.html, backend/static/style.css, backend/static/main.js

### 2024-06-XX [개발 예정]

- **2단계 자막 확보 자동화 프로세스 설계 및 개발**
  - 자막 존재 검사 → 내장 자막 추출/변환 → 외부 자막 다운로드/싱크 대조 → Whisper 자막 생성 순서로 자동화 플로우 설계
  - 각 단계별 UI/UX/상태관리/실패 안내 설계
  - PROGRESS.md에 2단계 개발 계획 및 워크플로우 반영

### 2025년 5월

#### 5월 5일
- 자막 싱크 검증 및 보정 시스템 문서화 완료
- 디렉토리 브라우저 검색 기능 개선
- 자막 자동 다운로드 시스템 안정성 향상

#### 5월 4일
- 자막 싱크 검증 시스템 구현 완료
- 3구간 샘플링 방식 적용으로 정확도 향상
- 보정 임계값 조정 및 예외 처리 추가

#### 5월 3일
- Whisper 기반 싱크 검증 프로토타입 개발
- FFmpeg 오디오 추출 및 처리 기능 구현
- Levenshtein 거리 기반 텍스트 유사도 계산 구현

#### 5월 2일
- OpenSubtitles API 통합 및 자막 검색 기능 완성
- 자막 캐싱 시스템 구현으로 API 호출 최적화
- 파일명 기반 영화/시리즈 정보 추출 기능 개선

#### 5월 1일
- 탭 UI 디자인 통일 및 컴포넌트화
- JS 코드 모듈화 및 파일 분리 완료
- 디렉토리 탐색기 UI 개선