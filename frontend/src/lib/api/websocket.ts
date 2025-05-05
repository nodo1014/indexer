/**
 * WebSocket 연결 관리 모듈
 * FastAPI 백엔드와의 WebSocket 통신을 관리합니다.
 */

import { writable, type Writable } from 'svelte/store';
import type { WhisperJob } from './index';

// WebSocket 기본 URL 설정
const WS_BASE_URL = 'ws://localhost:8000/ws';

// 타입 정의
export type WebSocketStatus = 'disconnected' | 'connecting' | 'connected' | 'error';
export type WebSocketMessage = JobUpdateMessage | JobProgressMessage;

interface JobUpdateMessage {
  type: 'job_update';
  data: WhisperJob;
}

interface JobProgressMessage {
  type: 'job_progress';
  data: {
    job_id: string;
    progress: number;
    status: string;
  };
}

// 스토어 정의
export const wsStatus: Writable<WebSocketStatus> = writable('disconnected');
export const wsReconnectAttempts: Writable<number> = writable(0);
export const jobUpdates: Writable<WhisperJob[]> = writable([]);

// WebSocket 인스턴스
let ws: WebSocket | null = null;
let reconnectTimer: number | null = null;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000; // 3초

/**
 * WebSocket 메시지 핸들러
 */
const handleMessage = (event: MessageEvent) => {
  try {
    const message = JSON.parse(event.data) as WebSocketMessage;
    
    switch (message.type) {
      case 'job_update':
        updateJob(message.data);
        break;
      case 'job_progress':
        updateJobProgress(message.data);
        break;
      default:
        console.warn('알 수 없는 WebSocket 메시지 타입:', message);
    }
  } catch (error) {
    console.error('WebSocket 메시지 처리 오류:', error);
  }
};

/**
 * 작업 상태 업데이트
 */
const updateJob = (job: WhisperJob) => {
  jobUpdates.update(jobs => {
    const existingIndex = jobs.findIndex(j => j.id === job.id);
    
    if (existingIndex >= 0) {
      jobs[existingIndex] = { ...jobs[existingIndex], ...job };
    } else {
      jobs.push(job);
    }
    
    return jobs;
  });
};

/**
 * 작업 진행률 업데이트
 */
const updateJobProgress = (data: { job_id: string; progress: number; status: string }) => {
  jobUpdates.update(jobs => {
    const existingIndex = jobs.findIndex(j => j.id === data.job_id);
    
    if (existingIndex >= 0) {
      jobs[existingIndex] = { 
        ...jobs[existingIndex], 
        progress: data.progress, 
        status: data.status as WhisperJob['status'] 
      };
    }
    
    return jobs;
  });
};

/**
 * WebSocket 연결
 */
export const connectWebSocket = () => {
  // 이미 연결된 경우 중복 연결 방지
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    console.log('WebSocket이 이미 연결되어 있습니다.');
    return;
  }
  
  // 연결 상태 업데이트
  wsStatus.set('connecting');
  
  try {
    // WebSocket 인스턴스 생성
    ws = new WebSocket(WS_BASE_URL);
    
    // 이벤트 핸들러 등록
    ws.onopen = () => {
      console.log('WebSocket 연결됨');
      wsStatus.set('connected');
      wsReconnectAttempts.set(0);
    };
    
    ws.onmessage = handleMessage;
    
    ws.onclose = () => {
      console.log('WebSocket 연결 종료됨');
      wsStatus.set('disconnected');
      scheduleReconnect();
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket 오류:', error);
      wsStatus.set('error');
    };
  } catch (error) {
    console.error('WebSocket 연결 실패:', error);
    wsStatus.set('error');
    scheduleReconnect();
  }
};

/**
 * WebSocket 재연결 스케줄링
 */
const scheduleReconnect = () => {
  // 이미 재연결 타이머가 설정된 경우 중복 설정 방지
  if (reconnectTimer !== null) {
    return;
  }
  
  wsReconnectAttempts.update(attempts => {
    const newAttempts = attempts + 1;
    
    if (newAttempts <= MAX_RECONNECT_ATTEMPTS) {
      console.log(`WebSocket 재연결 시도 (${newAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
      
      reconnectTimer = window.setTimeout(() => {
        reconnectTimer = null;
        connectWebSocket();
      }, RECONNECT_INTERVAL);
    } else {
      console.error('최대 재연결 시도 횟수 초과. 재연결 중단.');
    }
    
    return newAttempts;
  });
};

/**
 * WebSocket 연결 종료
 */
export const disconnectWebSocket = () => {
  if (ws) {
    ws.close();
    ws = null;
  }
  
  // 재연결 타이머 취소
  if (reconnectTimer !== null) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  
  wsStatus.set('disconnected');
  wsReconnectAttempts.set(0);
};

export default {
  connectWebSocket,
  disconnectWebSocket,
  wsStatus,
  wsReconnectAttempts,
  jobUpdates
}; 