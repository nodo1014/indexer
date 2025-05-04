# backend/connection_manager.py
from typing import List, Dict, Tuple, Set
from fastapi import WebSocket, WebSocketDisconnect
import logging
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # 활성 연결 관리: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # 실행 중인 백그라운드 작업 관리: client_id -> asyncio.Task
        self.active_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        # 기존 연결이 있다면 끊고 새로 연결 (혹은 에러 처리)
        if client_id in self.active_connections:
             logger.warning(f"기존 WebSocket 연결 강제 종료: {client_id}")
             existing_ws = self.active_connections[client_id]
             try:
                 await existing_ws.close(code=1008) # Policy Violation or similar
             except Exception as e:
                 logger.warning(f"기존 WebSocket 종료 중 오류: {e}")
             # 작업도 취소할지 여부 결정 필요. 일단은 연결만 끊음.
             # await self.cancel_task(client_id)
        self.active_connections[client_id] = websocket
        logger.info(f"ConnectionManager: 클라이언트 연결됨 - {client_id}")

    async def disconnect(self, websocket: WebSocket, client_id: str):
        # 연결 목록에서 제거 (해당 client_id의 websocket이 맞는지 확인 후)
        if client_id in self.active_connections and self.active_connections[client_id] == websocket:
            del self.active_connections[client_id]
            logger.info(f"ConnectionManager: 클라이언트 연결 해제됨 - {client_id}")
            # 연결 해제 시 관련 작업 자동 취소 (선택 사항, 필요시 주석 해제)
            # await self.cancel_task(client_id)
        else:
             logger.warning(f"ConnectionManager: 알 수 없거나 오래된 웹소켓 연결 해제 시도 - {client_id}")

    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
                logger.debug(f"개인 메시지 전송 (Client: {client_id}): {message['type'] if 'type' in message else 'Unknown type'}")
            except Exception as e:
                logger.error(f"개인 메시지 전송 실패 (Client: {client_id}): {e}")
                # 메시지 전송 실패 시 연결 제거 또는 재시도 로직 추가 가능
                # await self.disconnect(websocket, client_id)

    async def broadcast(self, message: str):
        # 현재는 사용되지 않지만, 전체 브로드캐스트가 필요할 경우 구현
        pass

    # --- Task Management --- #

    def add_task(self, client_id: str, task: asyncio.Task):
        """백그라운드 작업을 등록합니다."""
        if client_id in self.active_tasks:
            logger.warning(f"이미 활성 작업이 있는 Client ID에 새 작업 추가 시도: {client_id}. 이전 작업 취소 후 등록합니다.")
            # 기존 작업 취소 시도
            old_task = self.active_tasks[client_id]
            if not old_task.done():
                old_task.cancel()
        self.active_tasks[client_id] = task
        logger.info(f"ConnectionManager: 작업 등록됨 - {client_id}")

    def is_task_active(self, client_id: str) -> bool:
        """해당 클라이언트 ID로 활성 작업이 있는지 확인합니다."""
        return client_id in self.active_tasks and not self.active_tasks[client_id].done()

    async def cancel_task(self, client_id: str):
        """지정된 클라이언트 ID의 백그라운드 작업을 취소합니다."""
        if client_id in self.active_tasks:
            task = self.active_tasks[client_id]
            if not task.done():
                logger.info(f"ConnectionManager: 작업 취소 요청 - {client_id}")
                task.cancel()
                try:
                    # 작업이 취소될 때까지 잠시 대기 (선택 사항, 너무 길면 응답 지연)
                    await asyncio.wait_for(task, timeout=1.0)
                except asyncio.CancelledError:
                    logger.info(f"ConnectionManager: 작업 정상 취소됨 - {client_id}")
                except asyncio.TimeoutError:
                    logger.warning(f"ConnectionManager: 작업 취소 확인 시간 초과 - {client_id}")
                except Exception as e:
                    logger.error(f"ConnectionManager: 작업 취소 확인 중 오류 - {client_id}: {e}")
            else:
                logger.info(f"ConnectionManager: 이미 완료된 작업 취소 시도 - {client_id}")
            # 작업 목록에서 제거는 작업 완료/취소 시 run_whisper_batch 에서 직접 하도록 함
            # del self.active_tasks[client_id]
        else:
            logger.warning(f"ConnectionManager: 취소할 작업 없음 - {client_id}")

    def remove_task(self, client_id: str):
        """완료되거나 취소된 작업을 목록에서 제거합니다."""
        if client_id in self.active_tasks:
             del self.active_tasks[client_id]
             logger.info(f"ConnectionManager: 작업 제거됨 (완료/취소) - {client_id}")

manager = ConnectionManager() 