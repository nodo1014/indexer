# Whisper 자막 생성기 프론트엔드

이 프로젝트는 FastAPI 백엔드와 통신하는 SvelteKit 기반 프론트엔드입니다.

## 주요 기능

- NAS 미디어 파일 탐색 및 자막 관리
- Whisper 자막 생성 작업 실행 및 모니터링
- 자막 다운로드 및 관리
- WebSocket을 통한 실시간 작업 상태 모니터링

## 개발 환경 설정

1. 의존성 설치
```bash
npm install
```

2. 개발 서버 실행
```bash
npm run dev
```

3. 빌드
```bash
npm run build
```

## 프로젝트 구조

- `src/lib/api/` - 백엔드 API 연동 모듈
- `src/lib/components/` - 재사용 가능한 UI 컴포넌트
- `src/lib/stores/` - Svelte 상태 관리 스토어
- `src/routes/` - 페이지 및 라우팅
- `static/` - 정적 리소스

## 구현된 컴포넌트

### DirectoryBrowser
- NAS 폴더 구조 탐색
- 폴더별 미디어 파일 개수 표시
- 계층적 이동 및 경로 네비게이션

### MediaFilesTable
- 미디어 파일 목록 표시
- 자막 유무에 따른 필터링
- 파일 선택 및 일괄 작업

### JobStatusPanel
- 진행 중인 Whisper 작업 모니터링
- 실시간 진행률 표시
- 작업 제어 (일시 정지, 재개, 취소)

## 백엔드 연동

백엔드 API 모듈은 다음 기능을 제공합니다:

- `getDirectories` - 디렉토리 목록 조회
- `searchMediaFiles` - 미디어 파일 검색
- `runWhisper` - Whisper 작업 실행
- `getJobs` - 작업 목록 조회
- `controlJob` - 작업 제어 (일시정지, 재개, 취소)

WebSocket 연결은 실시간 작업 상태 업데이트를 위해 사용됩니다.
