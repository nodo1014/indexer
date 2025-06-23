import os
import sys
import uuid # client_id 생성을 위해 추가
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, Query, Body, APIRouter
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse # JSONResponse 추가
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware  # CORS 미들웨어 추가
import logging
from pathlib import Path # Path 객체 사용
import urllib.parse # URL 인코딩된 경로 디코딩
from typing import List, Optional, Dict, Any, Union # Optional 추가
import json
import asyncio # 추가
import time
import shutil
from backend.services.file_scanner import extract_embedded_subtitles, convert_and_save_subtitle
from backend.services.subtitle_downloader import download_subtitle_from_opensubtitles, download_and_save_subtitle, search_and_download_subtitle, load_download_stats, get_cache_key, check_subtitle_cache, MAX_DAILY_DOWNLOADS, OPENSUBTITLES_DEV_MODE, fallback_search_subtitle
from backend.services.sync_checker import check_subtitle_sync, advanced_sync_and_save
from fastapi import status
from backend.config import settings
from backend.connection_manager import ConnectionManager
from backend.job_manager import job_manager
from backend.services.file_scanner import scan_media_files, list_subdirectories, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, list_subdirectories_with_media_counts
from backend.services.whisper_runner import run_whisper_batch

# 현재 디렉토리를 가져와서 import 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# 실행 위치에 따른 경로 설정
is_running_from_root = os.path.basename(os.getcwd()) != 'backend'

# 향상된 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 콘솔 핸들러 추가 (컬러 로깅 지원)
try:
    import coloredlogs
    coloredlogs.install(
        level=logging.INFO,
        logger=logger,
        fmt='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info("컬러 로깅 활성화됨")
except ImportError:
    logger.info("coloredlogs 모듈이 설치되지 않아 기본 로그 형식을 사용합니다. 컬러 로깅을 위해: pip install coloredlogs")

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Whisper Subtitle Generator",
    description="자막 생성 및 관리를 위한 FastAPI 서버",
    version="1.0.0"
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용, 운영 환경에서는 변경 필요)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

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

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트 핸들러"""
    logger.info("✅ 애플리케이션이 시작되었습니다")
    logger.info(f"📂 NAS 미디어 경로: {NAS_BASE_PATH}")
    logger.info(f"🔧 Whisper 모델 로드 준비 완료")
    logger.info(f"🌐 API 서버 URL: http://localhost:8000")
    
    # OpenSubtitles API 키 확인
    if settings.opensubtitles_api_key:
        logger.info(f"🔑 OpenSubtitles API 키 설정됨")
    else:
        logger.warning(f"⚠️ OpenSubtitles API 키가 설정되지 않았습니다. 자막 다운로드 기능이 제한됩니다.")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트 핸들러"""
    logger.info("애플리케이션이 종료되었습니다")
    # 필요한 정리 작업 수행

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
        job_manager.add_job(filename, language, model_size, client_id=client_id, file_path=file_path)

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
    """
    WebSocket 연결 엔드포인트
    클라이언트와 양방향 통신을 위한 WebSocket 연결을 처리합니다.
    """
    await websocket.accept()
    logging.info(f"WebSocket 연결 수락 - 클라이언트 ID: {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logging.debug(f"WebSocket 메시지 수신: {data}")
            
            # 클라이언트 메시지 처리
            await websocket.send_json({
                "type": "ack",
                "message": "메시지가 처리되었습니다.",
                "client_id": client_id
            })
    except WebSocketDisconnect:
        logging.info(f"WebSocket 연결 종료 - 클라이언트 ID: {client_id}")
    except Exception as e:
        logging.exception(f"WebSocket 오류 - 클라이언트 ID: {client_id}")

@app.get("/api/jobs")
async def get_jobs():
    """
    전체 작업 목록 조회 API
    """
    try:
        # 임시로 빈 작업 목록 반환 (실제로는 작업 관리자에서 가져와야 함)
        return {"jobs": []}
    except Exception as e:
        logging.exception("작업 목록 조회 중 오류 발생")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/job/{job_id}/action")
def job_action(job_id: str, action: str = Body(..., embed=True)):
    """특정 작업에 대해 일시정지/중단/재개/삭제 명령을 처리합니다."""
    job = job_manager.get_job(job_id)
    if not job:
        return {"error": "Job not found"}
    client_id = job_manager.get_client_id(job_id)
    if action == "pause":
        job_manager.set_status(job_id, "일시정지")
    elif action == "stop":
        job_manager.set_status(job_id, "중단됨")
        job_manager.set_progress(job_id, 0)
        # 실제 실행 중인 작업도 중단
        if client_id:
            loop = asyncio.get_event_loop()
            loop.create_task(manager.cancel_task(client_id))
    elif action == "resume":
        job_manager.set_status(job_id, "진행중")
    elif action == "delete":
        job_manager.delete_job(job_id)
        # 실제 실행 중인 작업도 중단
        if client_id:
            loop = asyncio.get_event_loop()
            loop.create_task(manager.cancel_task(client_id))
        return {"result": "deleted"}
    else:
        return {"error": "Unknown action"}
    return {"result": "ok", "job": job_manager.get_job(job_id)}

@app.post("/api/extract_subtitles")
async def api_extract_subtitles(request: Request):
    data = await request.json()
    media_path = data.get("media_path")
    if not media_path:
        raise HTTPException(status_code=400, detail="media_path 파라미터가 필요합니다.")
    try:
        result = extract_embedded_subtitles(media_path)
        return JSONResponse(content={"tracks": result})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/convert_subtitle")
async def api_convert_subtitle(request: Request):
    data = await request.json()
    input_path = data.get("input_path")
    output_path = data.get("output_path")
    target_format = data.get("target_format", "srt")
    if not input_path or not output_path:
        raise HTTPException(status_code=400, detail="input_path, output_path 파라미터가 필요합니다.")
    try:
        result = convert_and_save_subtitle(input_path, output_path, target_format)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/download_subtitle")
async def api_download_subtitle(request: Request):
    data = await request.json()
    filename = data.get("filename")
    language = data.get("language", "ko")
    if not filename:
        raise HTTPException(status_code=400, detail="filename 파라미터가 필요합니다.")
    try:
        result = download_subtitle_from_opensubtitles(filename, language)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)

@app.post("/api/auto_download_and_sync_subtitle")
async def api_auto_download_and_sync_subtitle(request: Request):
    """
    외부 자막 후보 중 best_match를 자동 다운로드 → 싱크 대조/보정/저장까지 자동화
    """
    data = await request.json()
    media_path = data.get("media_path")
    language = data.get("language", "ko")
    
    if not media_path:
        raise HTTPException(status_code=400, detail="media_path 파라미터가 필요합니다.")
    
    try:
        # 파일 이름 추출
        filename = os.path.basename(media_path)
        logger.info(f"자동 자막 다운로드 및 동기화 요청: {filename}, 언어: {language}")
        
        # 1단계: 자막 다운로드
        download_result = download_subtitle_from_opensubtitles(filename, language)
        
        if not download_result.get("success") or not download_result.get("subtitle_path"):
            return JSONResponse(content={
                "success": False, 
                "error": "적합한 자막을 찾을 수 없습니다."
            })
        
        subtitle_path = download_result.get("subtitle_path")
        
        # 2단계: 자막 싱크 확인 및 조정
        sync_result = check_subtitle_sync(media_path, subtitle_path)
        
        # 싱크가 좋지 않은 경우 보정 시도
        if not sync_result.get("in_sync", False) and sync_result.get("score", 0) < 0.7:
            logger.info(f"자막 싱크가 좋지 않음 (점수: {sync_result.get('score')}), 보정 시도 중...")
            
            # 고급 싱크 조정 및 저장
            advanced_result = advanced_sync_and_save(
                media_path, 
                subtitle_path, 
                avg_offset=sync_result.get("avg_offset", 0)
            )
            
            final_subtitle_path = advanced_result.get("output_path", subtitle_path)
            sync_applied = True
        else:
            # 싱크가 좋은 경우 원본 사용
            final_subtitle_path = subtitle_path
            sync_applied = False
        
        # 결과 반환
        return JSONResponse(content={
            "success": True,
            "final_subtitle_path": final_subtitle_path,
            "sync": sync_result.get("in_sync", False) or sync_applied,
            "score": sync_result.get("score", 0),
            "avg_offset": sync_result.get("avg_offset", 0),
            "sync_result": sync_result
        })
        
    except Exception as e:
        logger.error(f"자동 자막 다운로드 및 동기화 중 오류: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False, 
            "error": f"자동 자막 처리 중 오류 발생: {str(e)}"
        }, status_code=500)

@app.get("/api/preview_subtitle")
def preview_subtitle(file_path: str = Query(..., description="자막 파일 경로"), max_lines: int = 200):
    """SRT 등 자막 파일의 앞부분(max_lines)만 미리보기로 반환"""
    if not os.path.exists(file_path):
        return {"error": "파일이 존재하지 않습니다."}
    try:
        lines = []
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append("... (이하 생략)")
                    break
                lines.append(line.rstrip())
        return {"success": True, "lines": lines}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/update_subtitle")
async def update_subtitle(request: Request):
    data = await request.json()
    file_path = data.get("file_path")
    content = data.get("content")
    if not file_path or content is None:
        raise HTTPException(status_code=400, detail="file_path, content 파라미터가 필요합니다.")
    try:
        target_path = Path(file_path).resolve()
        if not target_path.is_file():
            return {"success": False, "error": "파일이 존재하지 않습니다."}
        if not target_path.suffix.lower() in ['.srt', '.vtt', '.smi', '.ass']:
            return {"success": False, "error": "지원하지 않는 자막 파일 형식입니다."}
        if not is_safe_path(target_path):
            return {"success": False, "error": "허용되지 않은 경로입니다."}
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "message": "자막 파일이 성공적으로 수정되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/delete_subtitle")
async def delete_subtitle(request: Request):
    data = await request.json()
    file_path = data.get("file_path")
    if not file_path:
        raise HTTPException(status_code=400, detail="file_path 파라미터가 필요합니다.")
    try:
        target_path = Path(file_path).resolve()
        if not target_path.is_file():
            return {"success": False, "error": "파일이 존재하지 않습니다."}
        if not target_path.suffix.lower() in ['.srt', '.vtt', '.smi', '.ass']:
            return {"success": False, "error": "지원하지 않는 자막 파일 형식입니다."}
        if not is_safe_path(target_path):
            return {"success": False, "error": "허용되지 않은 경로입니다."}
        target_path.unlink()
        return {"success": True, "message": "자막 파일이 성공적으로 삭제되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/download_and_save_subtitle")
async def api_download_and_save_subtitle(request: Request):
    data = await request.json()
    download_url = data.get("download_url")
    save_path = data.get("save_path")
    if not download_url or not save_path:
        raise HTTPException(status_code=400, detail="download_url, save_path 파라미터가 필요합니다.")
    try:
        target_path = Path(save_path).resolve()
        if not is_safe_path(target_path):
            return {"success": False, "error": "허용되지 않은 경로입니다."}
        result = download_and_save_subtitle(download_url, str(target_path))
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/list_directory")
async def list_directory(path: str = ""):
    """
    디렉토리 목록 조회 API
    """
    # 기존 browse_directories 함수와 같은 로직 구현
    try:
        # 실제 파일 시스템 경로 계산
        absolute_path = os.path.join(NAS_BASE_PATH, path.lstrip('/'))
        logging.info(f"[/api/list_directory] 실제 탐색 경로: {absolute_path}")
        
        # 하위 디렉토리 정보 수집
        from media_utils import list_subdirectories_with_media_counts
        directories = list_subdirectories_with_media_counts(absolute_path)
        
        # 상위 디렉토리 경로 계산
        parent_path = ""
        if path:
            parent_parts = path.rstrip('/').split('/')
            if len(parent_parts) > 1:
                parent_path = '/'.join(parent_parts[:-1])
        
        return {
            "directories": directories,
            "parent_path": parent_path,
            "current_path": path
        }
    except Exception as e:
        logging.exception("디렉토리 목록 조회 중 오류 발생")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scan_directory", response_class=JSONResponse)
async def scan_directory(path: Optional[str] = Query("")):
    """현재 디렉토리의 미디어 파일을 모두 스캔하여 반환합니다."""
    current_scan_path = NAS_BASE_PATH
    if path:
        resolved_path = (NAS_BASE_PATH / path).resolve()
        if is_safe_path(resolved_path) and resolved_path.is_dir():
            current_scan_path = resolved_path
        else:
            logger.warning(f"디렉토리 스캔 요청: 안전하지 않거나 존재하지 않는 경로 - {path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "유효하지 않은 경로입니다."}
            )
    
    logger.info(f"API 디렉토리 스캔 요청: {current_scan_path}")
    try:
        # 모든 미디어 파일 스캔 (비디오 + 오디오)
        files = scan_media_files(str(current_scan_path), True, True)
        
        return {
            "files": files,
            "current_path": str(current_scan_path.relative_to(NAS_BASE_PATH)) if current_scan_path != NAS_BASE_PATH else ""
        }
    except Exception as e:
        logger.error(f"API 디렉토리 스캔 중 오류 ({path}): {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"디렉토리 스캔에 실패했습니다: {str(e)}"}
        )

@app.get("/api/opensubtitles/status", response_class=JSONResponse)
async def api_opensubtitles_status():
    """
    OpenSubtitles API의 상태(일일 사용량 등)를 확인합니다.
    """
    download_stats = load_download_stats()
    
    # 오늘 날짜 확인
    today = time.strftime('%Y-%m-%d')
    if download_stats.get('today') != today:
        download_stats['today'] = today
        download_stats['daily_downloads'] = 0
    
    # 캐시된 자막 수 계산
    cached_subtitles_count = len(download_stats.get('cached_subtitles', {}))
    
    return {
        "success": True,
        "daily_downloads": download_stats.get('daily_downloads', 0),
        "daily_limit": MAX_DAILY_DOWNLOADS,
        "remaining": MAX_DAILY_DOWNLOADS - download_stats.get('daily_downloads', 0),
        "total_downloads": download_stats.get('total_downloads', 0),
        "cached_subtitles_count": cached_subtitles_count,
        "dev_mode": OPENSUBTITLES_DEV_MODE,
        "api_key_set": bool(settings.opensubtitles_api_key)
    }

@app.post("/api/multilingual_subtitle_search")
async def api_multilingual_subtitle_search(request: Request):
    """
    여러 언어로 자막을 순차적으로 검색하는 기능을 제공합니다.
    한국어 자막을 찾지 못할 경우 영어나 다른 언어로 시도합니다.
    """
    data = await request.json()
    media_path = data.get("media_path")
    languages = data.get("languages", ["ko", "en"])  # 기본값: 한국어, 영어 순서로 시도
    min_similarity = data.get("min_similarity", 50.0)  # 기본 최소 유사도를 50%로 낮춤
    
    if not media_path:
        raise HTTPException(status_code=400, detail="media_path 파라미터가 필요합니다.")
    
    try:
        # 파일 경로 유효성 검사
        target_path = Path(media_path).resolve()
        if not is_safe_path(target_path):
            return JSONResponse(content={"success": False, "error": "허용되지 않은 경로입니다."}, status_code=403)
        
        if not target_path.is_file():
            return JSONResponse(content={"success": False, "error": "파일이 존재하지 않습니다."}, status_code=404)
        
        # 파일 이름 추출
        filename = target_path.name
        logger.info(f"다국어 자막 검색 요청: {filename}, 언어 우선순위: {languages}")
        
        # 자막 파일 경로 생성 (원본 미디어와 같은 디렉토리에 동일한 이름.srt)
        save_path = str(target_path.with_suffix('.srt'))
        
        # 다국어 자막 검색 실행
        result = fallback_search_subtitle(filename, save_path, languages, min_similarity)
        
        if result.get('success'):
            logger.info(f"다국어 자막 검색 성공: {result.get('language', '알 수 없음')} 언어로 찾음")
            # 성공 정보에 필요한 추가 데이터 첨부
            result['media_path'] = str(media_path)
            result['subtitle_path'] = save_path
            
            # 자막 싱크 체크 시도
            try:
                sync_result = check_subtitle_sync(str(target_path), save_path)
                result['sync_info'] = sync_result
            except Exception as sync_err:
                logger.warning(f"자막 싱크 체크 실패: {str(sync_err)}")
                result['sync_info'] = {"error": str(sync_err)}
        else:
            logger.warning(f"다국어 자막 검색 실패: {result.get('error', '알 수 없는 오류')}")
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"다국어 자막 검색 중 오류: {e}", exc_info=True)
        return JSONResponse(content={
            "success": False, 
            "error": f"자막 검색 중 오류 발생: {str(e)}"
        }, status_code=500)

@app.post("/api/auto_process_subtitle")
async def auto_process_subtitle(request: Request, background_tasks: BackgroundTasks):
    """
    자막 자동 다운로드, 싱크 검증, 조정 통합 API 엔드포인트
    단계:
    1. 자막 다운로드 (OpenSubtitles API 활용)
    2. 싱크 검증 (Whisper 기반)
    3. 필요시 자막 오프셋 조정
    """
    data = await request.json()
    media_path = data.get("media_path")
    language = data.get("language", "ko")
    use_multilingual = data.get("use_multilingual", False)
    languages = data.get("languages", ["ko", "en"])
    
    if not media_path:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "미디어 경로가 지정되지 않았습니다."}
        )
    
    # 1단계: 자막 다운로드
    try:
        logging.info(f"자막 다운로드 시작: {media_path}")
        
        # OpenSubtitles에서 자막 검색 및 다운로드
        # 다국어 사용 여부에 따라 검색 전략 변경
        if use_multilingual:
            # 여러 언어로 순차 시도
            subtitle_result = None
            for lang in languages:
                try:
                    subtitle_result = subtitle_downloader.search_and_download_subtitle(
                        filename=os.path.basename(media_path),
                        save_path=os.path.dirname(media_path),
                        language=lang,
                        min_similarity=50.0
                    )
                    if subtitle_result.get("success"):
                        logging.info(f"자막 다운로드 성공 (언어: {lang}): {subtitle_result.get('subtitle_path')}")
                        break
                except Exception as e:
                    logging.error(f"자막 다운로드 중 오류 (언어: {lang}): {str(e)}")
                    continue
            
            # 모든 언어로 시도했지만 실패한 경우
            if not subtitle_result or not subtitle_result.get("success"):
                # 최후의 방법: 영화 이름으로 검색 (파일명 정제)
                try:
                    logging.info("최종 시도: 파일명 정제 후 검색")
                    subtitle_result = subtitle_downloader.fallback_search_subtitle(
                        filename=os.path.basename(media_path),
                        save_path=os.path.dirname(media_path),
                        languages=languages,
                        min_similarity=40.0
                    )
                except Exception as e:
                    logging.error(f"자막 대체 검색 중 오류: {str(e)}")
                    return JSONResponse(
                        status_code=404,
                        content={"success": False, "error": f"자막을 찾을 수 없습니다: {str(e)}"}
                    )
        else:
            # 단일 언어로 검색
            try:
                subtitle_result = subtitle_downloader.search_and_download_subtitle(
                    filename=os.path.basename(media_path),
                    save_path=os.path.dirname(media_path),
                    language=language,
                    min_similarity=50.0
                )
            except Exception as e:
                logging.error(f"자막 다운로드 중 오류: {str(e)}")
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "error": f"자막을 찾을 수 없습니다: {str(e)}"}
                )
        
        # 자막 다운로드 실패 시
        if not subtitle_result or not subtitle_result.get("success"):
            error_msg = subtitle_result.get("error", "알 수 없는 오류로 자막을 찾을 수 없습니다.")
            logging.error(f"자막 다운로드 실패: {error_msg}")
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": error_msg}
            )
        
        subtitle_path = subtitle_result.get("subtitle_path")
        
        # 2단계: 싱크 검증
        try:
            logging.info(f"자막 싱크 검증 시작: {subtitle_path}")
            sync_result = sync_checker.check_subtitle_sync(
                media_path=media_path,
                subtitle_path=subtitle_path
            )
            
            # 3단계: 필요시 자막 조정
            adjusted = False
            if sync_result.get("sync_status") != "good" and abs(sync_result.get("offset", 0)) > 0.5:
                logging.info(f"자막 오프셋 조정 필요: {sync_result.get('offset')}초")
                try:
                    adjust_result = sync_checker.adjust_subtitle_offset(
                        subtitle_path=subtitle_path,
                        offset=sync_result.get("offset")
                    )
                    
                    if adjust_result.get("success"):
                        logging.info(f"자막 오프셋 조정 성공: {adjust_result.get('adjusted_subtitle_path')}")
                        subtitle_path = adjust_result.get("adjusted_subtitle_path")
                        adjusted = True
                    else:
                        logging.warning(f"자막 오프셋 조정 실패: {adjust_result.get('error')}")
                except Exception as e:
                    logging.error(f"자막 오프셋 조정 중 오류: {str(e)}")
            else:
                logging.info(f"자막 오프셋 조정 불필요 (상태: {sync_result.get('sync_status')}, 오프셋: {sync_result.get('offset')}초)")
            
            # 최종 결과 반환
            return {
                "success": True,
                "subtitle_path": subtitle_path,
                "media_path": media_path,
                "sync_status": sync_result.get("sync_status"),
                "offset": sync_result.get("offset", 0),
                "adjusted": adjusted,
                "confidence": sync_result.get("confidence_score", 0)
            }
            
        except Exception as e:
            logging.error(f"자막 싱크 검증/조정 중 오류: {str(e)}")
            # 싱크 검증에 실패했더라도 자막을 찾았으면 성공으로 처리
            return {
                "success": True,
                "subtitle_path": subtitle_path,
                "media_path": media_path,
                "sync_status": "unknown",
                "offset": 0,
                "adjusted": False,
                "error_detail": str(e)
            }
            
    except Exception as e:
        logging.error(f"자막 자동 처리 중 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"자막 처리 중 오류가 발생했습니다: {str(e)}"}
        )

@app.get("/api/settings", response_class=JSONResponse)
async def get_settings():
    """현재 시스템 설정을 반환합니다."""
    try:
        return {
            "nas_media_path": settings.nas_media_path,
            "opensubtitles_api_key": settings.opensubtitles_api_key
        }
    except Exception as e:
        logger.error(f"설정 조회 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"설정 조회 중 오류 발생: {str(e)}")

@app.post("/api/settings", response_class=JSONResponse)
async def update_settings(request: Request):
    """시스템 설정을 업데이트합니다."""
    try:
        data = await request.json()
        
        # 요청 데이터 유효성 검사
        nas_media_path = data.get("nas_media_path")
        opensubtitles_api_key = data.get("opensubtitles_api_key")
        
        # NAS 경로 업데이트
        if nas_media_path is not None:
            # 디렉토리 존재 확인
            path = Path(nas_media_path)
            if not path.exists() or not path.is_dir():
                raise HTTPException(status_code=400, detail=f"유효하지 않은 디렉토리 경로: {nas_media_path}")
            
            # 환경 변수 업데이트
            os.environ["NAS_MEDIA_PATH"] = nas_media_path
            # settings 객체 업데이트
            settings.nas_media_path = nas_media_path
            # NAS_BASE_PATH 전역 변수 업데이트
            global NAS_BASE_PATH
            NAS_BASE_PATH = Path(settings.nas_media_path).resolve()
        
        # OpenSubtitles API 키 업데이트
        if opensubtitles_api_key is not None:
            # 환경 변수 업데이트
            os.environ["OPENSUBTITLES_API_KEY"] = opensubtitles_api_key
            # settings 객체 업데이트
            settings.opensubtitles_api_key = opensubtitles_api_key
        
        # .env 파일 업데이트
        update_env_file(nas_media_path, opensubtitles_api_key)
        
        logger.info(f"설정 업데이트 완료: NAS 경로={nas_media_path}, API 키={'설정됨' if opensubtitles_api_key else '없음'}")
        
        return {
            "success": True,
            "nas_media_path": settings.nas_media_path,
            "opensubtitles_api_key": settings.opensubtitles_api_key
        }
    except HTTPException as http_exc:
        raise http_exc  # HTTP 예외는 그대로 전달
    except Exception as e:
        logger.error(f"설정 업데이트 중 오류 발생: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"설정 업데이트 중 오류 발생: {str(e)}")

def update_env_file(nas_media_path=None, opensubtitles_api_key=None):
    """
    .env 파일에 설정을 저장합니다.
    """
    try:
        env_path = Path('.env')
        
        # 현재 .env 파일 내용 읽기
        current_env = {}
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        current_env[key.strip()] = value.strip()
        
        # 변경할 설정 적용
        if nas_media_path is not None:
            current_env['NAS_MEDIA_PATH'] = nas_media_path
        if opensubtitles_api_key is not None:
            current_env['OPENSUBTITLES_API_KEY'] = opensubtitles_api_key
        
        # .env 파일 업데이트
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in current_env.items():
                f.write(f"{key}={value}\n")
            
            # 주석 추가
            if 'OPENSUBTITLES_API_KEY' in current_env:
                f.write("\n# OpenSubtitles API key\n")
                f.write("# Get your API key from https://www.opensubtitles.com/en/users/sign_up\n")
        
        logger.info(f".env 파일 업데이트 완료: {env_path}")
        return True
    except Exception as e:
        logger.error(f".env 파일 업데이트 중 오류 발생: {e}", exc_info=True)
        return False

# /api/browse 엔드포인트 추가 (기존 /browse와 동일한 로직)
@app.get("/api/browse")
async def api_browse_directories(request: Request, current_path: Optional[str] = Query("")):
    """지정된 경로의 하위 디렉토리 목록을 반환합니다."""
    return await browse_directories(request, current_path)

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