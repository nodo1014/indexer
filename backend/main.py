import os
import sys
import uuid # client_id 생성을 위해 추가
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse # JSONResponse 추가
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from pathlib import Path # Path 객체 사용
import urllib.parse # URL 인코딩된 경로 디코딩
from typing import List, Optional, Dict # Optional 추가
import json
import asyncio # 추가

# 현재 디렉토리를 가져와서 import 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 실행 위치에 따른 경로 설정
is_running_from_root = os.path.basename(os.getcwd()) != 'backend'

# 설정, 서비스 및 연결 관리자 로드
try:
    # 백엔드 디렉토리에서 직접 실행할 경우
    from config import settings
    from services.file_scanner import scan_media_files, list_subdirectories, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, list_subdirectories_with_media_counts
    from services.whisper_runner import run_whisper_batch
    from connection_manager import ConnectionManager
    from job_manager import job_manager
except ModuleNotFoundError:
    # 프로젝트 루트에서 실행할 경우
    from backend.config import settings
    from backend.services.file_scanner import scan_media_files, list_subdirectories, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, list_subdirectories_with_media_counts
    from backend.services.whisper_runner import run_whisper_batch
    from backend.connection_manager import ConnectionManager
    from backend.job_manager import job_manager

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI 앱 인스턴스 생성
app = FastAPI()

# 정적 파일 마운트 (CSS, JS 등)
# 실행 위치에 따른 경로 설정
static_dir = "static" if not is_running_from_root else "backend/static"
templates_dir = "templates" if not is_running_from_root else "backend/templates"

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory=templates_dir)

# 애플리케이션 시작 시 NAS 기본 경로 설정 및 로깅
NAS_BASE_PATH = Path(settings.nas_media_path).resolve()
logger.info(f"설정된 NAS 기본 경로 (절대): {NAS_BASE_PATH}")
if not NAS_BASE_PATH.is_dir():
    logger.error(f"NAS 기본 경로({NAS_BASE_PATH})가 존재하지 않거나 디렉토리가 아닙니다. .env 또는 설정을 확인하세요.")
    # 애플리케이션 실행을 중단하거나 기본 경로를 안전한 값으로 설정할 수 있음
    # 예: NAS_BASE_PATH = Path(".") # 임시로 현재 디렉토리 사용

# WebSocket 연결 관리자
manager = ConnectionManager()

def is_safe_path(requested_path: Path) -> bool:
    """ 요청된 경로가 NAS_BASE_PATH 내에 있는지 확인 """
    try:
        # resolve()를 사용하여 심볼릭 링크 등을 처리하고 절대 경로 확인
        return requested_path.resolve().is_relative_to(NAS_BASE_PATH.resolve())
    except Exception as e:
        logger.warning(f"경로 유효성 검사 중 오류: {requested_path} - {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request,
                   scan_path: Optional[str] = Query(None), # 스캔할 특정 경로
                   filter_video: bool = Query(True),
                   filter_audio: bool = Query(True)):
    """메인 HTML 페이지를 렌더링합니다. 초기 파일 목록은 비동기적으로 로드됩니다."""
    client_id = request.cookies.get("client_id")
    if not client_id:
        client_id = str(uuid.uuid4())

    # scan_path 유효성 검사는 초기 경로 설정에만 사용
    initial_relative_path = ""
    if scan_path:
        temp_path = Path(scan_path)
        if not temp_path.is_absolute():
             resolved_path = (NAS_BASE_PATH / temp_path).resolve()
        else:
             resolved_path = temp_path.resolve()

        if is_safe_path(resolved_path):
            try:
                relative_path = str(resolved_path.relative_to(NAS_BASE_PATH))
                initial_relative_path = relative_path if relative_path != "." else ""
            except ValueError:
                 initial_relative_path = ""
        else:
            logger.warning(f"초기 로드 시 안전하지 않은 경로: {scan_path}, 기본 경로 사용")
            initial_relative_path = ""

    logger.info(f"메인 페이지 로드 요청: initial_path='{initial_relative_path}', client_id={client_id}")

    # 이제 파일 목록을 여기서 직접 로드하지 않음
    context = {
        "request": request,
        # "files": files_context, # 파일 목록 제거
        "client_id": client_id,
        "initial_path": initial_relative_path, # 초기 경로 전달 (JS에서 사용)
        "filter_video": filter_video, # 초기 필터 상태 전달
        "filter_audio": filter_audio
    }
    response = templates.TemplateResponse("index.html", context)
    response.set_cookie(key="client_id", value=client_id, httponly=True)
    return response

@app.get("/api/files", response_class=JSONResponse)
async def get_files_in_path(scan_path: Optional[str] = Query(""),
                             filter_video: bool = Query(True),
                             filter_audio: bool = Query(True)):
    """지정된 상대 경로의 자막 없는 미디어 파일 목록을 JSON으로 반환합니다."""
    current_scan_path = NAS_BASE_PATH
    if scan_path:
        resolved_path = (NAS_BASE_PATH / scan_path).resolve()
        if is_safe_path(resolved_path) and resolved_path.is_dir():
            current_scan_path = resolved_path
        else:
            logger.warning(f"파일 목록 요청: 안전하지 않거나 존재하지 않는 경로 - {scan_path}")
            # 안전하지 않거나 없는 경로면 빈 목록 반환 또는 오류
            return {"files": [], "error": "Invalid or unsafe path"}

    logger.info(f"API 파일 목록 요청: {current_scan_path} (Video: {filter_video}, Audio: {filter_audio})")
    try:
        media_files_data = scan_media_files(str(current_scan_path), filter_video, filter_audio)
        # scan_media_files가 이미 필요한 {'name': ..., 'path': ..., 'type': ...} 형식으로 반환한다고 가정
        return {"files": media_files_data}
    except Exception as e:
        logger.error(f"API 파일 목록 검색 중 오류 ({scan_path}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"파일 목록 검색 중 오류 발생: {e}")

@app.get("/browse")
async def browse_directories(request: Request, current_path: Optional[str] = Query("")):
    """지정된 경로의 하위 디렉토리 목록을 반환합니다."""
    base_lookup_path = NAS_BASE_PATH
    
    if current_path:
        temp_path = (NAS_BASE_PATH / current_path).resolve()
        # 보안 검사: 요청된 경로가 NAS_BASE_PATH 내에 있는지 확인
        if is_safe_path(temp_path):
            if not temp_path.exists():
                logger.warning(f"존재하지 않는 브라우징 경로 요청: {current_path}")
                return {"directories": [], "parent_path": "", "current_relative_path": current_path, "error": "Path not found"}
            if not temp_path.is_dir():
                logger.warning(f"디렉토리가 아닌 경로 브라우징 요청: {current_path}")
                return {"directories": [], "parent_path": "", "current_relative_path": current_path, "error": "Not a directory"}
                
            base_lookup_path = temp_path
        else:
            logger.warning(f"안전하지 않은 브라우징 경로: {current_path}")
            return {"directories": [], "parent_path": "", "current_relative_path": current_path, "error": "Forbidden path"}

    logger.info(f"[/browse] 실제 탐색 경로: {base_lookup_path}")

    # 디렉토리 목록 + 미디어 개수 가져오기
    subdirs_info = list_subdirectories_with_media_counts(str(base_lookup_path))
    logger.info(f"[/browse] list_subdirectories_with_media_counts 결과: {subdirs_info}")

    # 부모 경로 계산
    parent_path = ""
    if base_lookup_path != NAS_BASE_PATH:
        try:
            parent_rel_path = base_lookup_path.parent.relative_to(NAS_BASE_PATH)
            parent_path = str(parent_rel_path) if str(parent_rel_path) != "." else ""
        except ValueError:
            parent_path = ""  # NAS Base 직전 경로 등 에러 케이스
            logger.warning(f"부모 경로 계산 중 오류: {base_lookup_path.parent}는 NAS_BASE_PATH의 상위에 있습니다")

    # 현재 상대 경로 계산
    current_relative_path = ""
    try:
        current_relative_path = str(base_lookup_path.relative_to(NAS_BASE_PATH))
        if current_relative_path == ".":
            current_relative_path = ""
    except ValueError:
        current_relative_path = ""
        logger.warning(f"현재 상대 경로 계산 중 오류: {base_lookup_path}는 NAS_BASE_PATH와 관계가 없습니다")

    # 디렉토리 경로를 NAS_BASE_PATH 기준으로 상대 경로로 변환 + 미디어 개수 포함
    relative_subdirs = []
    for info in subdirs_info:
        dir_path = Path(info['path'])
        try:
            rel_path = str(dir_path.relative_to(NAS_BASE_PATH))
            relative_subdirs.append({
                "name": info['name'],
                "path": rel_path,
                "video_count": info['video_count'],
                "audio_count": info['audio_count']
            })
        except ValueError:
            logger.warning(f"상대 경로 계산 실패: {dir_path}는 NAS_BASE_PATH와 관계가 없습니다")

    logger.info(f"[/browse] 반환되는 디렉토리 수: {len(relative_subdirs)}, parent_path: '{parent_path}', current_path: '{current_relative_path}'")
            
    return {
        "directories": relative_subdirs,
        "parent_path": parent_path,
        "current_relative_path": current_relative_path
    }

@app.post("/run-whisper")
async def run_whisper_endpoint(request: Request, background_tasks: BackgroundTasks):
    """선택된 파일들에 대해 Whisper 작업을 백그라운드에서 실행합니다."""
    data = await request.json()
    files_to_process = data.get('files', [])
    client_id = data.get('client_id')
    model_size = data.get('model_size', 'base') # 모델 크기 받기 (기본값 'base')
    language = data.get('language', 'auto')

    if not files_to_process or not client_id:
        logger.warning(f"Whisper 실행 요청 오류: 파일 목록 또는 클라이언트 ID 누락 (Client: {client_id})")
        raise HTTPException(status_code=400, detail="파일 목록과 클라이언트 ID가 필요합니다.")

    # 이미 해당 클라이언트 ID로 실행 중인 작업이 있는지 확인
    if manager.is_task_active(client_id):
        logger.warning(f"이미 실행 중인 작업이 있습니다 (Client: {client_id})")
        raise HTTPException(status_code=409, detail="이미 처리 중인 작업이 있습니다. 이전 작업을 완료하거나 중지해주세요.")

    logger.info(f"Whisper 실행 요청 받음 (Client: {client_id}): {len(files_to_process)}개 파일, 모델: {model_size}, 언어: {language}")

    # Whisper 작업 등록 (job_manager)
    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        job_manager.add_job(filename, language, model_size)

    # 백그라운드 작업 정의
    async def batch_task():
        await run_whisper_batch(manager, client_id, files_to_process, model_size, language)
    task = asyncio.create_task(batch_task())
    manager.add_task(client_id, task)

    # 응답 즉시 반환
    return {"message": f"{len(files_to_process)}개 파일에 대한 처리 작업을 시작했습니다.", "client_id": client_id}

@app.get("/download")
async def download_file(file_path: str):
    """생성된 SRT 파일을 다운로드합니다."""
    # 보안: 요청된 file_path가 실제로 NAS_BASE_PATH 하위에 있는지, 그리고 .srt 파일인지 확인
    try:
        requested_path = Path(file_path).resolve()
        nas_resolved = NAS_BASE_PATH.resolve()

        # 경로 검증 및 .srt 확장자 확인
        if not requested_path.is_relative_to(nas_resolved):
            logger.warning(f"잘못된 다운로드 경로 요청 (경계 벗어남): {file_path}")
            raise HTTPException(status_code=403, detail="접근 권한이 없는 파일입니다.")

        if requested_path.suffix.lower() != '.srt':
             logger.warning(f"잘못된 다운로드 파일 형식 요청: {file_path}")
             raise HTTPException(status_code=400, detail="SRT 파일만 다운로드할 수 있습니다.")

        if not requested_path.is_file():
            logger.warning(f"다운로드할 파일 없음: {file_path}")
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

        logger.info(f"SRT 파일 다운로드 요청: {file_path}")
        # FileResponse는 자동으로 Content-Disposition 헤더를 설정하여 다운로드를 유도함
        return FileResponse(str(requested_path), media_type='text/plain', filename=requested_path.name)

    except HTTPException as http_exc:
        raise http_exc # HTTP 예외는 그대로 전달
    except Exception as e:
        logger.error(f"파일 다운로드 중 예외 발생 ({file_path}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="파일 다운로드 중 서버 오류가 발생했습니다.")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket 연결을 처리하고, 클라이언트로부터 메시지를 받습니다."""
    await manager.connect(websocket, client_id)
    logger.info(f"WebSocket 연결됨: {client_id}")
    try:
        while True:
            # 클라이언트로부터 메시지 수신 대기 (예: 'stop' 요청)
            data = await websocket.receive_text()
            logger.info(f"WebSocket 메시지 수신 (Client: {client_id}): {data}")
            # 메시지 파싱 (JSON 가정)
            try:
                message = json.loads(data)
                if message.get("type") == "stop_processing":
                    logger.info(f"Whisper 작업 중지 요청 수신 (Client: {client_id})")
                    await manager.cancel_task(client_id)
                    await websocket.send_text(json.dumps({"type": "stop_acknowledged"}))
                # 다른 메시지 유형 처리 (필요한 경우)
                # else:
                #     logger.warning(f"알 수 없는 WebSocket 메시지 유형 (Client: {client_id}): {message.get('type')}")
            except json.JSONDecodeError:
                 logger.warning(f"잘못된 JSON 형식의 WebSocket 메시지 수신 (Client: {client_id}): {data}")
            except Exception as e:
                 logger.error(f"WebSocket 메시지 처리 중 오류 (Client: {client_id}): {e}", exc_info=True)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 끊김: {client_id}")
        # 연결이 끊겼을 때 관련 작업 취소 시도 (선택 사항)
        # await manager.cancel_task(client_id)
    except Exception as e:
        logger.error(f"WebSocket 오류 발생 (Client: {client_id}): {e}", exc_info=True)
    finally:
        # 연결이 어떤 이유로든 종료되면 정리
        await manager.disconnect(websocket, client_id)
        logger.info(f"WebSocket 연결 및 리소스 정리 완료: {client_id}")

@app.get("/api/jobs")
def get_all_jobs():
    """현재 등록된 모든 Whisper 작업 목록을 반환합니다."""
    return {"jobs": job_manager.get_jobs()}

@app.post("/api/job/{job_id}/action")
def job_action(job_id: str, action: str = Body(..., embed=True)):
    """특정 작업에 대해 일시정지/중단/재개/삭제 명령을 처리합니다."""
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    if action == "pause":
        job_manager.set_status(job_id, "일시정지")
    elif action == "stop":
        job_manager.set_status(job_id, "중단됨")
        job_manager.set_progress(job_id, 0)
    elif action == "resume":
        job_manager.set_status(job_id, "진행중")
    elif action == "delete":
        job_manager.delete_job(job_id)
        return {"result": "deleted"}
    else:
        return {"error": "Unknown action"}
    return {"result": "ok", "job": job_manager.get_job(job_id)}

# TODO: 완료된 파일 목록 제공 및 다운로드 기능 구현

# 애플리케이션 실행 (개발용)
# 실제 실행은 터미널에서 'cd backend && uvicorn main:app --reload' 또는
# 프로젝트 루트에서 'uvicorn backend.main:app --reload' 명령 사용 권장
if __name__ == "__main__":
    # 이 부분은 직접 실행보다는 터미널 명령 사용을 권장
    logger.warning("main.py를 직접 실행하는 것보다 uvicorn 명령 사용을 권장합니다.")
    import uvicorn
    # config에서 로드 실패 시 기본 경로 유효성 검사 추가 필요
    if NAS_BASE_PATH.is_dir():
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        logger.critical(f"NAS 기본 경로 '{NAS_BASE_PATH}' 가 유효하지 않아 서버를 시작할 수 없습니다. .env 파일을 확인하세요.") 