/**
 * WebSocket 연결 관리 모듈
 * FastAPI 백엔드와의 WebSocket 통신을 관리합니다.
 */

import { writable } from 'svelte/store';
import type { WhisperJob } from './index';

// 상태 관리
export const isConnected = writable(false);
export const socketMessages = writable<any[]>([]);

// 설정
const WS_URL = 'ws://localhost:8000';
const CLIENT_ID = 'frontend-client'; // 고정 클라이언트 ID
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000; // 3초

// WebSocket 인스턴스
let ws: WebSocket | null = null;
let reconnectAttempts = 0;
let reconnectTimer: number | null = null;

/**
 * WebSocket 메시지 처리 함수
 */
function handleWebSocketMessage(event: MessageEvent) {
  try {
    const data = JSON.parse(event.data);
    console.log('WebSocket 메시지 수신:', data);
    
    // 메시지 종류에 따른 처리
    switch (data.type) {
      case 'progress_update':
        // 진행 상황 업데이트 처리
        socketMessages.update(messages => [...messages, data]);
        break;
        
      case 'job_complete':
        // 작업 완료 처리
        socketMessages.update(messages => [...messages, data]);
        break;
        
      case 'job_error':
        // 작업 오류 처리
        socketMessages.update(messages => [...messages, data]);
        console.error('작업 오류:', data.error);
        break;
        
      default:
        // 기타 메시지 처리
        socketMessages.update(messages => [...messages, data]);
    }
  } catch (error) {
    console.error('WebSocket 메시지 파싱 오류:', error);
  }
}

/**
 * WebSocket 연결 함수
 */
export function connectWebSocket() {
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    console.log('WebSocket이 이미 연결 중이거나 연결되어 있습니다.');
    return;
  }
  
  try {
    // WebSocket 연결 URL에 client_id 추가
    ws = new WebSocket(`${WS_URL}/ws/${CLIENT_ID}`);
    
    // 이벤트 핸들러 설정
    ws.onopen = () => {
      console.log('WebSocket 연결됨');
      isConnected.set(true);
      reconnectAttempts = 0; // 재연결 시도 횟수 초기화
    };
    
    ws.onmessage = handleWebSocketMessage;
    
    ws.onclose = () => {
      console.log('WebSocket 연결 종료됨');
      isConnected.set(false);
      ws = null;
      
      // 자동 재연결
      attemptReconnect();
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
    };
  } catch (error) {
    console.error('WebSocket 연결 오류:', error);
    isConnected.set(false);
  }
}

/**
 * WebSocket 연결 해제 함수
 */
export function disconnectWebSocket() {
  if (ws) {
    console.log('WebSocket 연결 종료 중...');
    ws.close();
    ws = null;
  }
  
  // 재연결 타이머 취소
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  
  isConnected.set(false);
}

/**
 * WebSocket 재연결 시도 함수
 */
function attemptReconnect() {
  // 최대 재연결 시도 횟수 확인
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('최대 재연결 시도 횟수 초과. 재연결 중단.');
    return;
  }
  
  // 이미 타이머가 설정되어 있는지 확인
  if (reconnectTimer !== null) return;
  
  reconnectAttempts++;
  console.log(`WebSocket 재연결 시도 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
  
  // 일정 시간 후 재연결 시도
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    connectWebSocket();
  }, RECONNECT_INTERVAL);
}

/**
 * 서버에 메시지 전송 함수
 */
export function sendMessage(message: any) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.error('WebSocket이 연결되어 있지 않습니다.');
    return false;
  }
  
  try {
    ws.send(JSON.stringify(message));
    return true;
  } catch (error) {
    console.error('WebSocket 메시지 전송 오류:', error);
    return false;
  }
}

/**
 * 작업 중지 요청 함수
 */
export function stopProcessing() {
  return sendMessage({ type: 'stop_processing' });
}

export default {
  connectWebSocket,
  disconnectWebSocket,
  isConnected,
  socketMessages
}; 