/**
 * main.js - 메인 애플리케이션 초기화 및 통합
 * 2025-05-05: 모듈화 리팩토링
 */

// 앱 네임스페이스
window.App = {
    // 탭 인스턴스
    tabs: {},
    
    // 초기화
    init: function() {
        console.log('애플리케이션 초기화...');
        
        // 웹소켓 및 필수 리소스 초기화
        this.initializeResources();
        
        // 탭 초기화
        this.initializeTabs();
        
        // 이벤트 핸들러 등록
        this.registerEventHandlers();
    },
    
    // 필수 리소스 초기화 (웹소켓 등)
    initializeResources: function() {
        // WebSocket이 있는 경우 초기화
        if (!window.websocket) {
            // connectWebSocket 함수가 있으면 호출
            if (typeof connectWebSocket === 'function') {
                connectWebSocket();
            } else {
                console.warn('WebSocket 연결 함수를 찾을 수 없습니다.');
            }
        }
    },
    
    // 탭 초기화
    initializeTabs: function() {
        try {
            console.log('탭 초기화 시작...');
            
            // 모든 탭 클래스 인스턴스 생성
            const tabClasses = {
                'extract': window.ExtractTab,
                'sync-ai': window.SyncTab,
                'download': window.DownloadTab,
                'whisper': window.WhisperTab
            };
            
            // 각 탭 인스턴스 생성
            for (const [tabId, TabClass] of Object.entries(tabClasses)) {
                console.log(`${tabId} 탭 클래스 초기화 시도...`, TabClass);
                
                if (typeof TabClass === 'function') {
                    console.log(`${tabId} 탭 인스턴스 생성`);
                    this.tabs[tabId] = new TabClass();
                    
                    // 타입별 전역 변수 설정 - API 새로고침 기능 등을 위해
                    if (tabId === 'download') {
                        window.downloadTab = this.tabs[tabId];
                    } else if (tabId === 'whisper') {
                        window.whisperTab = this.tabs[tabId];
                    } else if (tabId === 'extract') {
                        window.extractTab = this.tabs[tabId];
                    } else if (tabId === 'sync-ai') {
                        window.syncTab = this.tabs[tabId];
                    }
                    
                    // 초기화 메서드가 있으면 호출
                    if (typeof this.tabs[tabId].init === 'function') {
                        console.log(`${tabId} 탭 초기화 호출`);
                        this.tabs[tabId].init();
                    }
                } else {
                    console.warn(`탭 클래스를 찾을 수 없음: ${tabId}`, TabClass);
                }
            }
            
            // tabController 이벤트 리스너 등록
            if (window.tabController) {
                console.log('tabController에 이벤트 리스너 등록');
                window.tabController.on('tabChanged', (data) => {
                    this.onTabChanged(data.tab);
                });
                
                // 현재 활성화된 탭에 onActivate 호출
                const activeTab = window.tabController.getActiveTab();
                if (activeTab && this.tabs[activeTab] && typeof this.tabs[activeTab].onActivate === 'function') {
                    console.log(`초기 활성 탭 ${activeTab}에 onActivate 호출`);
                    this.tabs[activeTab].onActivate();
                }
                
                // WebSocket 메시지 처리자 등록 (필요 시)
                if (typeof handleWebSocketMessage === 'function') {
                    // 기존 함수 저장
                    const originalHandler = handleWebSocketMessage;
                    
                    // 새로운 처리자로 오버라이드
                    window.handleWebSocketMessage = function(message) {
                        // 원래 처리 수행
                        originalHandler(message);
                        
                        try {
                            const data = JSON.parse(message);
                            
                            // 배치 완료 또는 취소 메시지 처리
                            if (data.type === "batch_complete" || data.type === "batch_cancelled") {
                                // Whisper 탭의 처리 상태 업데이트
                                if (App.tabs.whisper) {
                                    App.tabs.whisper.setProcessingComplete();
                                }
                            }
                        } catch (e) {
                            console.warn('WebSocket 메시지 처리 중 오류:', e);
                        }
                    };
                }
            } else {
                console.warn('tabController를 찾을 수 없어 탭 변경 이벤트를 등록할 수 없습니다.');
            }
        } catch (error) {
            console.error('탭 초기화 중 오류 발생:', error);
        }
    },
    
    // 탭 변경 시 호출되는 이벤트 핸들러
    onTabChanged: function(tabId) {
        console.log(`탭 변경됨: ${tabId}`);
        
        // 해당 탭의 onActivate 메서드 호출
        if (this.tabs[tabId] && typeof this.tabs[tabId].onActivate === 'function') {
            this.tabs[tabId].onActivate();
        } else {
            console.warn(`${tabId} 탭에 onActivate 메서드가 없거나 탭 인스턴스를 찾을 수 없습니다.`);
        }
    },
    
    // 글로벌 이벤트 핸들러 등록
    registerEventHandlers: function() {
        // 사이드바 토글 재연결 (필요한 경우)
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('directory-browser');
        
        if (sidebarToggle && sidebar) {
            console.log('사이드바 토글 이벤트 등록');
            sidebarToggle.onclick = function(e) {
                e.stopPropagation();
                sidebar.classList.toggle('open');
                
                // 오버레이 추가(모바일)
                if (sidebar.classList.contains('open')) {
                    let overlay = document.createElement('div');
                    overlay.id = 'sidebar-overlay';
                    overlay.style.position = 'fixed';
                    overlay.style.top = '0';
                    overlay.style.left = '0';
                    overlay.style.width = '100vw';
                    overlay.style.height = '100vh';
                    overlay.style.background = 'rgba(0,0,0,0.08)';
                    overlay.style.zIndex = '999';
                    overlay.onclick = function() {
                        sidebar.classList.remove('open');
                        overlay.remove();
                    };
                    document.body.appendChild(overlay);
                } else {
                    const overlay = document.getElementById('sidebar-overlay');
                    if (overlay) overlay.remove();
                }
            };
        }
    }
};

// 문서 로드 완료 시 앱 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded 이벤트 발생: 앱 초기화 시작');
    
    // 일정 시간 후 앱 초기화 (탭 컨트롤러가 먼저 초기화되도록 보장)
    setTimeout(() => {
        console.log('앱 초기화 타이머 실행');
        if (window.tabController) {
            console.log('tabController 존재: 앱 초기화 시작');
            window.App.init();
            
            // URL에서 탭 정보 추출하여 해당 탭 활성화
            const urlParams = new URLSearchParams(window.location.search);
            const tabFromUrl = urlParams.get('tab');
            
            if (tabFromUrl && ['extract', 'download', 'sync-ai', 'whisper'].includes(tabFromUrl)) {
                console.log(`URL에서 탭 감지: ${tabFromUrl}`);
                window.tabController.activateTab(tabFromUrl);
            }
        } else {
            console.warn('tabController가 초기화되지 않아 앱 초기화를 건너뜁니다.');
        }
    }, 300);
});