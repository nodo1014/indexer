/**
 * TabController - 탭 UI를 관리하는 클래스
 * 2025-05-05 리팩토링: 클래스 기반 구조로 변경
 */
class TabController {
    constructor(tabs, defaultTab = null) {
        this.tabs = tabs;
        this.activeTab = null;
        this.defaultTab = defaultTab || tabs[0];
        
        // URL에서 탭 정보 가져오기
        const urlParams = new URLSearchParams(window.location.search);
        const tabFromUrl = urlParams.get('tab');
        
        // 사용자 지정 이벤트
        this.eventListeners = {
            tabChanged: []
        };
    }
    
    init() {
        console.log("탭 컨트롤러 초기화...");
        
        // 탭 버튼에 이벤트 리스너 등록
        this.tabs.forEach(tab => {
            const button = document.getElementById(`tab-${tab}`);
            if (button) {
                button.addEventListener('click', () => this.activateTab(tab, true));
            } else {
                console.warn(`탭 버튼 '${tab}'을 찾을 수 없습니다.`);
            }
        });
        
        // URL에서 탭 지정하거나 기본 탭 활성화
        const urlParams = new URLSearchParams(window.location.search);
        const tabFromUrl = urlParams.get('tab');
        
        if (tabFromUrl && this.tabs.includes(tabFromUrl)) {
            this.activateTab(tabFromUrl, false);
        } else {
            this.activateTab(this.defaultTab, false);
        }
    }
    
    activateTab(tabId, updateUrl = true) {
        console.log(`탭 활성화 중: ${tabId}`);
        
        // 탭 ID가 유효한지 확인
        if (!this.tabs.includes(tabId)) {
            console.error(`유효하지 않은 탭 ID: ${tabId}`);
            return;
        }
        
        // 이전 활성 탭 비활성화
        if (this.activeTab) {
            const prevTabButton = document.getElementById(`tab-${this.activeTab}`);
            const prevTabContent = document.getElementById(`tab-content-${this.activeTab}`);
            
            if (prevTabButton) prevTabButton.classList.remove('active');
            if (prevTabContent) {
                prevTabContent.classList.remove('active');
                prevTabContent.style.display = 'none';  // display 속성도 함께 관리
            }
        }
        
        // 새 탭 활성화
        const newTabButton = document.getElementById(`tab-${tabId}`);
        const newTabContent = document.getElementById(`tab-content-${tabId}`);
        
        if (newTabButton) newTabButton.classList.add('active');
        if (newTabContent) {
            newTabContent.classList.add('active');
            newTabContent.style.display = 'block';  // display 속성도 함께 관리
        }
        
        // 현재 활성 탭 저장
        this.activeTab = tabId;
        
        // URL 업데이트 (필요한 경우)
        if (updateUrl) {
            const url = new URL(window.location);
            url.searchParams.set('tab', tabId);
            window.history.pushState({}, '', url);
        }
        
        // 이벤트 발생
        this.emit('tabChanged', { tab: tabId });
    }
    
    // 이벤트 리스너 추가
    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
        }
        return this; // 체이닝 지원
    }
    
    // 이벤트 발생
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (e) {
                    console.error(`탭 이벤트 핸들러 오류:`, e);
                }
            });
        }
    }
    
    // 현재 활성화된 탭 ID 반환
    getActiveTab() {
        return this.activeTab;
    }
}

// 기존 함수는 하위 호환성을 위해 유지
function showTab(tab) {
    if (window.tabController) {
        window.tabController.activateTab(tab);
    } else {
        const tabs = ['extract', 'sync-ai', 'download', 'whisper'];
        tabs.forEach(t => {
            document.getElementById('tab-' + t).classList.remove('active');
            document.getElementById('tab-content-' + t).classList.remove('active');
            document.getElementById('tab-content-' + t).style.display = 'none';
        });
        document.getElementById('tab-' + tab).classList.add('active');
        document.getElementById('tab-content-' + tab).classList.add('active');
        document.getElementById('tab-content-' + tab).style.display = 'block';
    }
}

// DOMContentLoaded 이벤트 기존 리스너는 그대로 유지
document.addEventListener('DOMContentLoaded', function () {
    // 현재 페이지에 존재하는 탭만 포함하도록 수정
    const tabs = ['extract', 'sync-ai', 'download', 'whisper'];
    
    // 전역 변수로 탭 컨트롤러 생성 (다른 스크립트에서 접근 가능)
    window.tabController = new TabController(tabs, 'extract');
    window.tabController.init();
});