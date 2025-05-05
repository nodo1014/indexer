/**
 * whisper-tab.js - 음성으로 자막 생성 탭 기능
 * 2025-05-05: 모듈화 리팩토링
 */

class WhisperTab {
    constructor() {
        this.initialized = false;
        this.tabId = 'whisper';
        this.isProcessing = false;
    }

    /**
     * 탭 초기화
     */
    init() {
        if (this.initialized) return;
        
        console.log('Whisper 자막 생성 탭 초기화...');
        
        // 탭 컨텐츠 엘리먼트 가져오기
        this.tabContent = document.getElementById(`tab-content-${this.tabId}`);
        if (!this.tabContent) {
            console.error(`탭 컨텐츠 요소를 찾을 수 없음: tab-content-${this.tabId}`);
            return;
        }
        
        // UI 구성요소 초기화
        this.initUI();
        
        // 이벤트 리스너 등록
        this.registerEventListeners();
        
        this.initialized = true;
    }
    
    /**
     * 탭 UI 구성요소 초기화
     */
    initUI() {
        // 기존 내용은 유지하고 추가 기능만 강화 (이미 HTML에 기본 구조 존재)
        const modelDescriptions = {
            tiny: "가장 빠름, 저사양 PC/테스트용 (권장: 1분 미만/1시간 영상)",
            base: "빠름, 일상적 사용/저사양 PC (권장: 2~3분/1시간 영상)",
            small: "중간 속도, 일반 PC/서버 (권장: 5~10분/1시간 영상)",
            medium: "느림, 고성능 PC/서버 (권장: 15~30분/1시간 영상)",
            large: "매우 느림, 고성능 GPU 필수 (권장: 30분 이상/1시간 영상)"
        };
        
        this.modelDescriptions = modelDescriptions;
        
        // 모델 설명 업데이트
        this.updateModelDescription();
        
        // 언어 설명 업데이트
        this.updateLanguageDescription();
    }
    
    /**
     * 모델 설명 업데이트
     */
    updateModelDescription() {
        const modelSelect = document.getElementById('model-select');
        const modelDesc = document.getElementById('model-desc');
        
        if (modelSelect && modelDesc) {
            modelDesc.textContent = this.modelDescriptions[modelSelect.value] || '';
        }
    }
    
    /**
     * 언어 설명 업데이트
     */
    updateLanguageDescription() {
        const langSelect = document.getElementById('whisper-lang');
        const langDesc = document.getElementById('lang-desc');
        
        if (langSelect && langDesc) {
            const langDescriptions = {
                auto: "자동 인식: 대부분의 경우 권장 (언어 혼합/불확실 시)",
                en: "영어: 영어만 포함된 영상에 권장",
                ko: "한국어: 한국어만 포함된 영상에 권장",
                ja: "일본어: 일본어만 포함된 영상에 권장",
                zh: "중국어: 중국어만 포함된 영상에 권장",
                fr: "프랑스어: 프랑스어만 포함된 영상에 권장"
            };
            
            langDesc.textContent = langDescriptions[langSelect.value] || '';
        }
    }
    
    /**
     * 이벤트 리스너 등록
     */
    registerEventListeners() {
        // 모델 선택 변경 이벤트
        const modelSelect = document.getElementById('model-select');
        if (modelSelect) {
            modelSelect.addEventListener('change', () => this.updateModelDescription());
        }
        
        // 언어 선택 변경 이벤트
        const langSelect = document.getElementById('whisper-lang');
        if (langSelect) {
            langSelect.addEventListener('change', () => this.updateLanguageDescription());
        }
        
        // 전체 선택 버튼
        const selectAllBtn = document.getElementById('select-all');
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.handleSelectAll());
        }
        
        // 전체 해제 버튼
        const deselectAllBtn = document.getElementById('deselect-all');
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.handleDeselectAll());
        }
        
        // 실행 버튼
        const runWhisperBtn = document.getElementById('run-whisper');
        if (runWhisperBtn) {
            runWhisperBtn.addEventListener('click', () => this.handleRunWhisper());
        }
        
        // 중지 버튼
        const stopWhisperBtn = document.getElementById('stop-whisper');
        if (stopWhisperBtn) {
            stopWhisperBtn.addEventListener('click', () => this.handleStopWhisper());
        }
    }
    
    /**
     * 탭이 활성화될 때 호출되는 메서드
     */
    onActivate() {
        console.log('Whisper 자막 생성 탭 활성화');
        // 필요한 경우 상태 업데이트
        this.updateUI();
    }
    
    /**
     * UI 상태 업데이트
     */
    updateUI() {
        // 현재 처리 상태에 따라 버튼 활성화/비활성화 등 업데이트
        const hasSelectedFiles = this.getSelectedFiles().length > 0;
        const runWhisperBtn = document.getElementById('run-whisper');
        const stopWhisperBtn = document.getElementById('stop-whisper');
        
        if (runWhisperBtn) {
            runWhisperBtn.disabled = !hasSelectedFiles || this.isProcessing;
        }
        
        if (stopWhisperBtn) {
            stopWhisperBtn.style.display = this.isProcessing ? 'inline-block' : 'none';
        }
        
        // 체크박스 상태 업데이트
        document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
            if (this.isProcessing) {
                checkbox.disabled = true;
            } else {
                // 이미 완료된 파일은 체크 불가능하게 유지
                const row = checkbox.closest('tr');
                if (row && !row.className.includes('status-completed') &&
                    !row.className.includes('status-skipped') &&
                    !row.className.includes('status-error') &&
                    !row.className.includes('status-cancelled')) {
                    checkbox.disabled = false;
                }
            }
        });
        
        // 모델 선택 비활성화/활성화
        const modelSelect = document.getElementById('model-select');
        if (modelSelect) {
            modelSelect.disabled = this.isProcessing;
        }
    }
    
    /**
     * 전체 선택 처리
     */
    handleSelectAll() {
        document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
            if (!checkbox.disabled && checkbox.closest('tr').style.display !== 'none') {
                checkbox.checked = true;
            }
        });
        
        // 헤더 체크박스도 체크
        const selectAllHeader = document.getElementById('select-all-header');
        if (selectAllHeader) selectAllHeader.checked = true;
        
        this.updateUI();
    }
    
    /**
     * 전체 해제 처리
     */
    handleDeselectAll() {
        document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // 헤더 체크박스도 체크 해제
        const selectAllHeader = document.getElementById('select-all-header');
        if (selectAllHeader) selectAllHeader.checked = false;
        
        this.updateUI();
    }
    
    /**
     * Whisper 자막 생성 실행
     */
    async handleRunWhisper() {
        const selectedFiles = this.getSelectedFiles();
        
        if (selectedFiles.length === 0) {
            alert('자막을 생성할 파일을 하나 이상 선택해주세요.');
            return;
        }
        
        const modelSize = document.getElementById('model-select').value;
        const language = document.getElementById('whisper-lang').value;
        
        console.log(`Whisper 자막 생성 시작: ${selectedFiles.length}개 파일, 모델: ${modelSize}, 언어: ${language}`);
        
        // 작업 상태 업데이트
        document.getElementById('batch-status').textContent = '서버에 처리 요청 중...';
        
        try {
            const response = await fetch('/run-whisper', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: selectedFiles,
                    client_id: window.clientId,
                    model_size: modelSize,
                    language: language
                }),
            });
            
            const result = await response.json();
            
            if (response.ok) {
                console.log("Whisper 작업 시작됨:", result);
                document.getElementById("batch-status").textContent = result.message;
                
                // 처리 상태 업데이트
                this.isProcessing = true;
                this.updateUI();
            } else {
                console.error("Whisper 작업 시작 실패:", result);
                document.getElementById("batch-status").textContent = `오류: ${result.detail || '알 수 없는 오류'}`;
                alert(`오류: ${result.detail || 'Whisper 작업 시작에 실패했습니다.'}`);
            }
        } catch (error) {
            console.error('Whisper 요청 중 네트워크 오류:', error);
            document.getElementById("batch-status").textContent = "오류: 서버 연결 실패";
            alert('서버에 연결할 수 없습니다.');
        }
    }
    
    /**
     * Whisper 자막 생성 중지
     */
    handleStopWhisper() {
        if (window.websocket && window.websocket.readyState === WebSocket.OPEN) {
            console.log("Whisper 처리 중지 요청 전송");
            window.websocket.send(JSON.stringify({ type: 'stop_processing' }));
        } else {
            console.warn("WebSocket이 연결되지 않아 중지 요청을 보낼 수 없습니다.");
            alert("서버와의 연결이 끊어졌습니다. 페이지를 새로고침해 주세요.");
        }
    }
    
    /**
     * 선택된 파일 목록 가져오기
     * @returns {string[]} 선택된 파일 경로 배열
     */
    getSelectedFiles() {
        const selectedFiles = [];
        
        document.querySelectorAll('#file-list .file-checkbox:checked').forEach(checkbox => {
            const row = checkbox.closest('tr');
            if (row && row.style.display !== 'none') {
                selectedFiles.push(row.dataset.path);
            }
        });
        
        return selectedFiles;
    }
    
    /**
     * 처리 완료 상태 설정
     * 외부(WebSocket 이벤트 등)에서 호출할 수 있도록 public 메서드로 제공
     */
    setProcessingComplete() {
        this.isProcessing = false;
        this.updateUI();
    }
}

// 모듈 내보내기 (브라우저에서 바로 사용 가능하도록)
window.WhisperTab = WhisperTab;