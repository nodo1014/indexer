# Whisper 자막 생성기 서버 (FastAPI)

## 주요 기능

- NAS 저장소의 미디어 파일(영상/오디오)에서 자막이 없는 항목을 자동 탐색
- Whisper로 자막 생성 및 관리 (언어/모델 선택 가능)
- **작업 현황 패널**: 자막 생성 작업의 상태(진행중/일시정지/중단/완료 등)와 진행률을 실시간으로 확인/제어
    - 새로고침/폴링에도 작업 현황이 사라지지 않음 (서버가 꺼지지 않는 한 유지)
- **탐색기 트리**: 각 폴더별 (영상 #, 오디오 #) 개수를 하위폴더까지 모두 포함해 집계하여 표시
- 자막 미리보기, 다운로드, 상세 진행 로그 모달 등 다양한 UI/UX 제공

## 실행 환경 (whisper ai 사용시 중요!)
- proxmox ubuntu22.04 server
- ryzen 5600g 16g 512nvme
- No graphic card ( pip install 시, pytorch no-cpu 반영)

## 실행/설치 주의사항
- **반드시 가상환경(venv) 활성화 후 pip install 진행**
- **requirements.txt는 pip freeze로 최신화됨**
- **그래픽카드가 없는 환경에서는 pytorch 설치 시 no-cuda 버전 사용 필수**
  - 예시: `pip install torch==<버전>+cpu -f https://download.pytorch.org/whl/torch_stable.html`
- FastAPI 실행 시 반드시 프로젝트 루트(즉, backend가 아닌 indexer 폴더)에서 아래 명령어로 실행
  ```bash
  uvicorn backend.main:app --reload
  ```
- **.env 파일에 NAS_MEDIA_PATH 등 환경변수 필수 설정**
- **OPENSUBTITLES_API_KEY**: OpenSubtitles API를 사용하려면 `.env` 파일에 유효한 API 키를 설정하세요. 설정되지 않으면 모의(mock) 데이터를 반환합니다.

## 실행 방법

1. Python 3.10+ 및 가상환경(venv) 준비
2. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
3. .env 파일에 NAS_MEDIA_PATH 등 환경변수 설정
4. FastAPI 서버 실행
   ```bash
   uvicorn backend.main:app --reload
   ```
5. 웹 브라우저에서 `http://localhost:8000` 접속

## 주요 화면/구성

- **탐색기(좌측)**: 폴더 트리, (영상 #, 오디오 #) 표시, 자막 필터, 폴더 검색 버튼
- **작업 현황(탐색기 아래)**: 현재/대기/완료된 자막 생성 작업, 상태/진행률/제어 버튼(일시정지/중단/재개/삭제)
- **파일 목록(우측)**: 자막 없는 미디어 파일 리스트, 언어/모델/진행률/자막 미리보기 등

## 변경 이력 (주요)

- Whisper 작업 현황이 새로고침/폴링에도 사라지지 않도록 개선 (2024-05-04)
- 탐색기 트리의 영상/오디오 개수가 하위폴더까지 포함해 집계되도록 개선 (2024-05-04)
- 그 외 상세 내역은 PROGRESS.md 참고