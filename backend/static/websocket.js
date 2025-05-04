// websocket.js
// WebSocket 연결 및 실시간 통신 처리
// 진행률/상태 업데이트 렌더링
import { renderCompletedFiles } from './render.js';

export function connectWebSocket() {
    const clientId = window.clientId;
    const wsUrl = `ws://${window.location.host}/ws/${clientId}`;
    if (window.websocket && window.websocket.readyState !== WebSocket.CLOSED) {
        window.websocket.close();
    }
    window.websocket = new WebSocket(wsUrl);
    window.websocket.onopen = (event) => {
        console.log('WebSocket 연결 성공');
    };
    window.websocket.onmessage = (event) => {
        handleWebSocketMessage(event.data);
    };
    window.websocket.onclose = (event) => {
        console.log('WebSocket 연결 끊김. 코드:', event.code, '이유:', event.reason);
        window.isProcessing = false;
        if (typeof window.updateUIState === 'function') window.updateUIState();
        setTimeout(() => {
            if (!window.isProcessing) {
                console.log('WebSocket 재연결 시도...');
                connectWebSocket();
            }
        }, 10000);
    };
    window.websocket.onerror = (error) => {
        console.error('WebSocket 오류 발생:', error);
        window.isProcessing = false;
        if (typeof window.updateUIState === 'function') window.updateUIState();
    };
}

export function handleWebSocketMessage(message) {
    try {
        const data = JSON.parse(message);
        console.log('WebSocket 메시지 수신:', data);
        // 진행상황/완료 파일 등 업데이트
        if (data.file_path) {
            if (!window.whisperLogs) window.whisperLogs = {};
            if (!window.whisperLogs[data.file_path]) window.whisperLogs[data.file_path] = [];
            if (data.type === 'status_update' || data.type === 'log') {
                window.whisperLogs[data.file_path].push({
                    time: new Date().toLocaleTimeString(),
                    status: data.status,
                    message: data.message,
                    progress: data.progress_percent,
                    type: data.type
                });
            }
        }
        if (data.type === 'status_update' && ['completed','skipped','error','cancelled'].includes(data.status)) {
            if (!window.completedFiles) window.completedFiles = [];
            if (!window.completedFiles.find(f => f.file_path === data.file_path && f.status === data.status)) {
                window.completedFiles.push({
                    file_path: data.file_path,
                    file_name: data.file_path ? data.file_path.split(/[\\\/]/).pop() : '',
                    status: data.status,
                    output_path: data.output_path,
                    message: data.message,
                    language: data.language,
                    subtitle_preview: data.subtitle_preview
                });
                renderCompletedFiles();
            }
        }
        // ... (상태별 추가 UI 업데이트는 main.js에서)
    } catch (error) {
        console.error('WebSocket 메시지 처리 오류:', error, '원본 메시지:', message);
    }
} 