import logging
import time
from typing import List, Dict, Optional, Callable
from pathlib import Path
import whisper # openai-whisper 패키지
import asyncio # Semaphore 사용 위해 추가
import json # JSON 로딩 추가 (main.py에서 이동 가능하나 일단 여기둠)
import tqdm # 프로그레스바 지원

# Updated: 2025-05-04 (GitHub Copilot + Claude 3.7 지원)

# ConnectionManager 임포트 (타입 힌팅 및 실제 사용)
from backend.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

# 동시에 실행할 Whisper 작업 수 제한 (GPU 메모리 등에 따라 조절)
MAX_CONCURRENT_WHISPER_TASKS = 1
whisper_semaphore = asyncio.Semaphore(MAX_CONCURRENT_WHISPER_TASKS)
SRT_PREVIEW_LINES = 3 # 미리보기에 표시할 SRT 줄 수

def get_srt_preview(srt_path: Path) -> str:
    """Generate SRT preview string."""
    preview = []
    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            line_count = 0
            for line in f:
                 # 타임스탬프, 빈 줄, 숫자 라인 제외하고 텍스트만 추출 (간단하게)
                 if '-->' not in line and line.strip().isdigit():
                      continue
                 if line.strip():
                     preview.append(line.strip())
                     line_count += 1
                     if line_count >= SRT_PREVIEW_LINES:
                         break
        return "\n".join(preview)
    except Exception as e:
        logger.warning(f"SRT 미리보기 생성 실패 ({srt_path.name}): {e}")
        return "미리보기 생성 실패"

async def run_whisper_on_file(manager: ConnectionManager, client_id: str, file_path: str, model_size: str = "base", language: str = "auto") -> Dict:
    """단일 미디어 파일에 대해 Whisper를 실행 (언어 옵션 추가)하고 결과를 .srt 파일로 저장하며, WebSocket으로 상태를 알립니다. 취소 가능."""
    file_name = Path(file_path).name
    task = asyncio.current_task() # 현재 작업 가져오기
    result_data = {"status": "error", "message": "작업 시작 전 오류", "file_path": file_path}

    await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "waiting", "message": "대기 중...", "progress_percent": 0}, client_id)
    logger.info(f"🔄 [{file_name}] Whisper 작업이 대기열에 추가되었습니다. (모델: {model_size}, 언어: {language})")

    async with whisper_semaphore:
        if task.cancelled():
            logger.info(f"❌ [{file_name}] 작업 시작 전 취소됨 (Client: {client_id})")
            result_data = {"status": "cancelled", "message": "시작 전 취소됨", "file_path": file_path}
            await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "cancelled", "message": "취소됨", "progress_percent": 0}, client_id)
            return result_data

        logger.info(f"🚀 [{file_name}] Whisper 처리 시작 (모델: {model_size}, 언어: {language}) (Client: {client_id})")
        start_time = time.time()
        output_dir = Path(file_path).parent
        output_base = Path(file_path).stem
        result_data = {"status": "error", "message": "알 수 없는 처리 오류", "file_path": file_path}

        try:
            # 1. 모델 로드
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": f"Whisper 모델 로드 시작 ({model_size})", "progress_percent": 0}, client_id)
            await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "processing", "message": f"모델 로드 중 ({model_size})...", "progress_percent": 5}, client_id)
            if task.cancelled(): raise asyncio.CancelledError("모델 로드 중 취소됨")
            
            logger.info(f"📚 [{file_name}] Whisper 모델 '{model_size}' 로드 중...")
            model = whisper.load_model(model_size)
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": f"Whisper 모델 로드 완료 ({model_size})", "progress_percent": 5}, client_id)
            logger.info(f"✅ [{file_name}] Whisper 모델 '{model_size}' 로드 완료")

            # 2. 언어 감지 및 처리
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": "언어 감지 및 처리 시작", "progress_percent": 10}, client_id)
            await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "processing", "message": "처리 및 언어 감지 중...", "progress_percent": 10}, client_id)
            if task.cancelled(): raise asyncio.CancelledError("처리 시작 전 취소됨")

            # 진행률 추정용 콜백
            progress_percent = 10
            def progress_callback(current, total):
                percent = int(10 + 80 * (current / max(1, total)))
                nonlocal progress_percent
                progress_percent = percent
                # 실시간 진행률 전송
                asyncio.run_coroutine_threadsafe(
                    manager.send_personal_message({
                        "type": "status_update",
                        "file_path": file_path,
                        "status": "processing",
                        "message": f"진행 중... ({current}/{total})",
                        "progress_percent": percent
                    }, client_id),
                    asyncio.get_event_loop()
                )
                # 로그 메시지도 추가
                log_message = f"Segment {current}/{total} 처리 중"
                asyncio.run_coroutine_threadsafe(
                    manager.send_personal_message({
                        "type": "log",
                        "file_path": file_path,
                        "status": "info",
                        "message": log_message,
                        "progress_percent": percent
                    }, client_id),
                    asyncio.get_event_loop()
                )
                # 터미널에도 진행률 표시
                logger.info(f"⏳ [{file_name}] 진행률: {percent}% - {log_message}")

            # 터미널에 tqdm 프로그레스 표시를 위한 커스텀 콜백
            class WhisperProgressBar:
                def __init__(self, file_name: str):
                    self.file_name = file_name
                    self.pbar = None
                    self.total = 0
                    self.current = 0
                
                def __call__(self, current: int, total: int):
                    # progress_callback 호출하여 WebSocket 업데이트
                    progress_callback(current, total)
                    
                    # tqdm 프로그레스바 초기화 또는 업데이트
                    if self.pbar is None:
                        self.total = total
                        self.pbar = tqdm.tqdm(
                            total=total,
                            desc=f"[{self.file_name}] Whisper 변환",
                            unit="segment"
                        )
                    
                    # 진행 상태 업데이트
                    if current > self.current:
                        self.pbar.update(current - self.current)
                        self.current = current
                    
                    # 완료 시 닫기
                    if current >= total and self.pbar is not None:
                        self.pbar.close()
                        self.pbar = None

            # model.transcribe는 동기 함수이므로, 진행률 콜백을 segments 처리에 삽입
            async def patched_transcribe(*args, progress_bar: WhisperProgressBar, **kwargs):
                result = await asyncio.to_thread(lambda: model.transcribe(*args, **kwargs))
                segments = result.get('segments', [])
                total = len(segments)
                
                # segments가 이미 처리된 상태라서 수동으로 진행률 100%로 업데이트
                if progress_bar.pbar is not None:
                    progress_bar.pbar.n = total
                    progress_bar.pbar.refresh()
                    progress_bar.pbar.close()
                
                # WebSocket용 진행률도 100%로 업데이트
                progress_callback(total, total)
                return result

            # 언어 옵션 적용
            transcribe_kwargs = {}
            if language and language != "auto":
                transcribe_kwargs['language'] = language

            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": "Whisper 변환 시작", "progress_percent": progress_percent}, client_id)
            logger.info(f"🎧 [{file_name}] Whisper 변환 시작 중...")
            
            # 프로그레스바 객체 생성
            progress_bar = WhisperProgressBar(file_name)
            
            # 실제 변환 (스레드에서 실행)
            result = await patched_transcribe(file_path, verbose=False, progress_bar=progress_bar, **transcribe_kwargs)
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": "Whisper 변환 완료", "progress_percent": progress_percent}, client_id)

            logger.info(f"✅ [{file_name}] Whisper 변환 완료!")
            if task.cancelled(): raise asyncio.CancelledError("처리 완료 후 취소됨")

            detected_language = result.get("language", "unk")
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": f"감지된 언어: {detected_language}", "progress_percent": progress_percent}, client_id)
            logger.info(f"🔍 [{file_name}] 감지된 언어: {detected_language}")

            # 3. 영어 필터링
            if detected_language != 'en' and language in (None, '', 'auto', 'en'):
                message = f"건너뜀 (언어: {detected_language})"
                await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": message, "progress_percent": 100}, client_id)
                logger.info(f"⚠️ [{file_name}] Whisper 처리 건너뜀 (영어가 아님) - 언어: {detected_language}")
                result_data = {"status": "skipped", "message": message, "language": detected_language, "file_path": file_path}
                await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "skipped", "language": detected_language, "message": message, "progress_percent": 100}, client_id)
                return result_data

            # 4. SRT 파일 저장
            srt_filename = f"{output_base}_{detected_language}.srt"
            srt_path = output_dir / srt_filename
            await manager.send_personal_message({"type": "log", "file_path": file_path, "status": "info", "message": "SRT 파일 저장 시작", "progress_percent": 95}, client_id)
            await manager.send_personal_message({"type": "status_update", "file_path": file_path, "status": "processing", "message": "SRT 파일 저장 중...", "progress_percent": 95}, client_id)
            logger.info(f"💾 [{file_name}] SRT 파일 저장 중... ({srt_filename})")
            if task.cancelled(): raise asyncio.CancelledError("SRT 저장 전 취소됨")

            # 파일 저장은 상대적으로 빠르므로 스레드로 감쌀 필요는 없을 수 있음
            # 단, NAS 환경에서는 I/O가 느릴 수 있으므로 스레드 고려 가능
            try:
                # WriteSRT 인스턴스 생성 및 호출 (Whisper 유틸리티 사용)
                writer = whisper.utils.WriteSRT(str(output_dir)) # 경로를 문자열로 전달해야 할 수 있음
                writer(result, str(file_path)) # 파일 경로도 문자열로

                # Whisper <= 1.1.1 버전에서는 writer가 자동으로 filename.srt 를 생성할 수 있음
                # 생성된 파일 이름 확인 및 언어 코드 추가 (필요시)
                default_srt_path = output_dir / f"{output_base}.srt"

                if default_srt_path.exists() and default_srt_path != srt_path :
                    # whisper가 기본 이름으로 저장했고, 우리가 원하는 이름과 다르면 변경
                     default_srt_path.rename(srt_path)
                     logger.info(f"✅ [{file_name}] SRT 파일 저장 완료 (이름 변경됨): {srt_path}")
                elif srt_path.exists():
                    # 이미 원하는 이름으로 저장되었거나, writer가 언어 코드를 포함하여 생성
                     logger.info(f"✅ [{file_name}] SRT 파일 저장 완료: {srt_path}")
                else:
                     # WriteSRT가 작동하지 않았거나 경로 문제 발생 시 수동 생성 (기존 로직 유지)
                    logger.warning(f"⚠️ [{file_name}] WriteSRT 유틸리티로 SRT 생성이 안된 것 같습니다. 수동으로 생성합니다.")
                    with open(srt_path, "w", encoding="utf-8") as srt_file:
                        i = 1
                        for segment in result['segments']:
                            start = format_timestamp(segment['start'])
                            end = format_timestamp(segment['end'])
                            text = segment['text'].strip()
                            srt_file.write(f"{i}\n")
                            srt_file.write(f"{start} --> {end}\n")
                            srt_file.write(f"{text}\n\n")
                            i += 1
                    logger.info(f"✅ [{file_name}] SRT 파일 수동 저장 완료: {srt_path}")

            except Exception as write_err:
                 logger.error(f"❌ [{file_name}] SRT 파일 저장 중 오류 발생: {write_err}", exc_info=True)
                 # 오류 발생 시 작업 상태 업데이트
                 raise RuntimeError(f"SRT 저장 오류: {write_err}") from write_err # 에러 전파

            # 5. 완료 처리
            if task.cancelled(): raise asyncio.CancelledError("완료 처리 전 취소됨")

            end_time = time.time()
            processing_time = end_time - start_time
            srt_preview = get_srt_preview(srt_path) # 미리보기 생성
            logger.info(f"🎉 [{file_name}] Whisper 처리 완료! (소요 시간: {processing_time:.2f}초)")
            result_data = {
                "status": "completed",
                "output_path": str(srt_path),
                "language": detected_language,
                "processing_time": processing_time,
                "file_path": file_path,
                "subtitle_preview": srt_preview # 미리보기 추가
            }
            await manager.send_personal_message({
                "type": "status_update", 
                "file_path": file_path, 
                "status": "completed", 
                "language": detected_language,
                "message": f"완료! (소요 시간: {processing_time:.2f}초)",
                "progress_percent": 100,
                "result": result_data
            }, client_id)
            await manager.send_personal_message({
                "type": "log", 
                "file_path": file_path, 
                "status": "info", 
                "message": f"처리 완료 (소요 시간: {processing_time:.2f}초, 언어: {detected_language})",
                "progress_percent": 100
            }, client_id)

            return result_data

        except asyncio.CancelledError as cancel_err:
            cancelled_message = str(cancel_err) or "사용자에 의해 취소됨"
            logger.info(f"❌ [{file_name}] 작업 취소됨: {cancelled_message}")
            result_data = {"status": "cancelled", "message": cancelled_message, "file_path": file_path}
            await manager.send_personal_message({
                "type": "status_update", 
                "file_path": file_path, 
                "status": "cancelled", 
                "message": f"취소됨: {cancelled_message}", 
                "progress_percent": progress_percent
            }, client_id)
            await manager.send_personal_message({
                "type": "log", 
                "file_path": file_path, 
                "status": "warning", 
                "message": f"취소됨: {cancelled_message}", 
                "progress_percent": progress_percent
            }, client_id)
            return result_data
            
        except Exception as e:
            error_message = f"Whisper 처리 중 오류: {str(e)}"
            logger.error(f"❌ [{file_name}] {error_message}", exc_info=True)
            result_data = {"status": "error", "message": error_message, "file_path": file_path}
            await manager.send_personal_message({
                "type": "status_update", 
                "file_path": file_path, 
                "status": "error", 
                "message": error_message, 
                "progress_percent": progress_percent
            }, client_id)
            await manager.send_personal_message({
                "type": "log", 
                "file_path": file_path, 
                "status": "error", 
                "message": error_message, 
                "progress_percent": progress_percent
            }, client_id)
            return result_data

def format_timestamp(seconds: float) -> str:
    """Seconds to SRT timestamp format"""
    assert seconds >= 0, "non-negative timestamp required"
    milliseconds = round(seconds * 1000.0)
    hours = milliseconds // 3_600_000; milliseconds %= 3_600_000
    minutes = milliseconds // 60_000; milliseconds %= 60_000
    seconds = milliseconds // 1_000; milliseconds %= 1_000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

async def run_whisper_batch(manager: ConnectionManager, client_id: str, files: List[str], model_size: str, language: str = "auto"):
    """여러 파일에 대해 동시에(제한적으로) Whisper를 실행하고 취소를 처리합니다. 언어 옵션 추가."""
    logger.info(f"Whisper 배치 작업 시작 (Client: {client_id}): {len(files)}개 파일, 모델: {model_size}, 언어: {language}, 동시 실행 제한: {MAX_CONCURRENT_WHISPER_TASKS}")
    await manager.send_personal_message({"type": "batch_start", "total_files": len(files)}, client_id)

    tasks = []
    for file_path in files:
        # 각 파일별로 언어 옵션 전달
        task = asyncio.create_task(run_whisper_on_file(manager, client_id, file_path, model_size, language))
        tasks.append(task)

    results = []
    batch_cancelled = False
    try:
        # asyncio.gather는 모든 작업이 완료되거나 첫 예외 발생 시 반환
        # return_exceptions=True 로 설정하면 예외 발생 시에도 계속 진행하고 결과를 받음 (취소 포함)
        results = await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        logger.info(f"배치 작업 전체가 외부에서 취소됨 (Client: {client_id}). 개별 작업 상태 확인 필요.")
        batch_cancelled = True
        # gather가 취소되면 results는 부분적일 수 있음. 개별 task 상태 확인.
        results = []
        for task in tasks:
            if task.cancelled():
                # run_whisper_on_file 내부에서 취소 처리 및 메시지 전송했을 것임
                 results.append({"status": "cancelled", "message": "배치 취소됨", "file_path": "unknown"}) # 파일 경로 모를 수 있음
            elif task.done() and task.exception():
                 exc = task.exception()
                 logger.error(f"배치 내 작업 오류 (취소 중 발생 가능): {exc}")
                 results.append({"status": "error", "message": str(exc), "file_path": "unknown"})
            elif task.done():
                 results.append(task.result()) # 정상 완료된 결과
            else:
                 # 아직 완료되지 않은 작업 (이론상 gather 취소 시 없어야 함)
                 logger.warning("Gather 취소 후 미완료 작업 발견?")
                 results.append({"status": "unknown", "message": "알수없음(취소 중)", "file_path": "unknown"})

    # 결과 분석 (CancelledError 포함하여)
    completed_count = 0
    skipped_count = 0
    error_count = 0
    cancelled_count = 0

    for r in results:
        if isinstance(r, asyncio.CancelledError) or (isinstance(r, dict) and r.get('status') == 'cancelled'):
            cancelled_count += 1
        elif isinstance(r, Exception) or (isinstance(r, dict) and r.get('status') == 'error'):
            error_count += 1
        elif isinstance(r, dict) and r.get('status') == 'completed':
            completed_count += 1
        elif isinstance(r, dict) and r.get('status') == 'skipped':
            skipped_count += 1
        # else: # 알 수 없는 결과 형태 (예: Exception이 아닌 다른 타입?)
        #     error_count += 1

    total_processed = completed_count + skipped_count + error_count + cancelled_count
    logger.info(f"Whisper 배치 작업 결과 분석 (Client: {client_id}): 총 {len(files)}개 요청, {total_processed}개 처리 시도 => 완료: {completed_count}, 건너뜀: {skipped_count}, 오류: {error_count}, 취소: {cancelled_count}")

    final_message_type = "batch_complete" if not batch_cancelled else "batch_cancelled"

    await manager.send_personal_message({
        "type": final_message_type,
        "total_files": len(files),
        "completed_count": completed_count,
        "skipped_count": skipped_count,
        "error_count": error_count,
        "cancelled_count": cancelled_count # 취소된 파일 수 추가
    }, client_id)

    # 작업 완료/취소 후 관리자에서 작업 제거
    manager.remove_task(client_id)

    return results # 실제 결과 반환 (상태 포함)

# 테스트용 코드 제거 (직접 실행하지 않음)