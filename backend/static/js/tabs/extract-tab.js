/**
 * extract-tab.js - 자막 변환 및 추출 탭 기능
 * 2025-05-05: 모듈화 리팩토링
 */

class ExtractTab {
    constructor() {
        this.initialized = false;
        this.tabId = 'extract';
    }

    /**
     * 탭 초기화
     */
    init() {
        if (this.initialized) return;
        
        console.log('자막 변환 및 추출 탭 초기화...');
        
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
        // 기존 내용 비우기
        this.tabContent.innerHTML = '';
        
        // 탭 UI 컴포넌트 생성
        const tabContainerHtml = `
            <div class="extract-tab-container">
                <div class="action-panel">
                    <h3>내장 자막 추출 및 변환</h3>
                    <p class="description">선택한 미디어 파일에서 내장된 자막을 추출하고 SRT 형식으로 변환합니다.</p>
                    <div class="actions">
                        <button id="extract-select-all" class="action-button">전체 선택</button>
                        <button id="extract-deselect-all" class="action-button">전체 해제</button>
                        <button id="run-extract" class="cta-button">선택 파일 자막 추출</button>
                    </div>
                </div>
                
                <div class="options-panel">
                    <h4>추출 옵션</h4>
                    <div class="option-group">
                        <label>
                            <input type="checkbox" id="extract-auto-save" checked>
                            자동으로 SRT 저장
                        </label>
                    </div>
                    <div class="option-group">
                        <label for="extract-language">선호 언어:</label>
                        <select id="extract-language">
                            <option value="auto">자동 감지</option>
                            <option value="ko">한국어 (ko)</option>
                            <option value="en">영어 (en)</option>
                            <option value="ja">일본어 (ja)</option>
                            <option value="zh">중국어 (zh)</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
        
        this.tabContent.innerHTML = tabContainerHtml;
    }
    
    /**
     * 이벤트 리스너 등록
     */
    registerEventListeners() {
        // 버튼 요소 가져오기
        const selectAllBtn = document.getElementById('extract-select-all');
        const deselectAllBtn = document.getElementById('extract-deselect-all');
        const runExtractBtn = document.getElementById('run-extract');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.handleSelectAll());
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.handleDeselectAll());
        }
        
        if (runExtractBtn) {
            runExtractBtn.addEventListener('click', () => this.handleRunExtract());
        }
    }
    
    /**
     * 탭이 활성화될 때 호출되는 메서드
     */
    onActivate() {
        console.log('자막 변환 및 추출 탭 활성화');
        // 필요한 경우 상태 업데이트
        this.updateUI();
    }
    
    /**
     * UI 상태 업데이트
     */
    updateUI() {
        // 현재 파일 목록에 따라 버튼 활성화/비활성화 등 업데이트
        const hasSelectedFiles = this.getSelectedFiles().length > 0;
        const runExtractBtn = document.getElementById('run-extract');
        
        if (runExtractBtn) {
            runExtractBtn.disabled = !hasSelectedFiles;
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
     * 자막 추출 실행
     */
    async handleRunExtract() {
        const selectedFiles = this.getSelectedFiles();
        
        if (selectedFiles.length === 0) {
            alert('자막을 추출할 파일을 하나 이상 선택해주세요.');
            return;
        }
        
        const autoSave = document.getElementById('extract-auto-save').checked;
        const language = document.getElementById('extract-language').value;
        
        console.log(`자막 추출 시작: ${selectedFiles.length}개 파일, 자동저장: ${autoSave}, 언어: ${language}`);
        
        // 작업 상태 업데이트
        document.getElementById('batch-status').textContent = '자막 추출 중...';
        
        try {
            for (const filePath of selectedFiles) {
                await this.extractSubtitle(filePath, { autoSave, language });
            }
            
            document.getElementById('batch-status').textContent = `자막 추출 완료: ${selectedFiles.length}개 파일 처리됨`;
        } catch (error) {
            console.error('자막 추출 중 오류:', error);
            document.getElementById('batch-status').textContent = `자막 추출 오류: ${error.message}`;
            alert(`자막 추출 중 오류가 발생했습니다: ${error.message}`);
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
     * 단일 파일 자막 추출 처리
     * @param {string} filePath - 미디어 파일 경로
     * @param {Object} options - 추출 옵션 (autoSave, language)
     */
    async extractSubtitle(filePath, options) {
        const fileName = filePath.split(/[/\\]/).pop();
        const fileRow = document.querySelector(`tr[data-path="${filePath.replace(/"/g, '\\"')}"]`);
        
        if (fileRow) {
            const statusCell = fileRow.querySelector('.status');
            if (statusCell) {
                statusCell.textContent = '자막 추출 중...';
            }
        }
        
        try {
            const response = await fetch('/api/extract_subtitles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    media_path: filePath,
                    auto_save: options.autoSave,
                    language: options.language
                }),
            });
            
            const data = await response.json();
            
            if (!response.ok || data.error) {
                throw new Error(data.error || '알 수 없는 오류');
            }
            
            // 추출 결과 처리
            if (fileRow) {
                const statusCell = fileRow.querySelector('.status');
                if (statusCell) {
                    const tracks = data.tracks || [];
                    if (tracks.length === 0) {
                        statusCell.textContent = '자막 없음';
                    } else {
                        statusCell.textContent = `${tracks.length}개 트랙 추출됨`;
                        
                        // 자동 저장 옵션이 켜져 있으면 미리보기 셀에 추출된 자막 정보 표시
                        if (options.autoSave) {
                            const previewCell = fileRow.querySelector('.subtitle-preview');
                            if (previewCell && data.preview) {
                                previewCell.innerHTML = `<pre>${this.escapeHtml(data.preview)}</pre>`;
                            }
                        }
                    }
                }
            }
            
            return data;
        } catch (error) {
            console.error(`${fileName} 자막 추출 실패:`, error);
            
            if (fileRow) {
                const statusCell = fileRow.querySelector('.status');
                if (statusCell) {
                    statusCell.textContent = `추출 실패: ${error.message}`;
                }
            }
            
            throw error;
        }
    }
    
    /**
     * HTML 이스케이프 함수
     * @param {string} unsafe - 안전하지 않은 문자열
     * @returns {string} 이스케이프된 문자열
     */
    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// 모듈 내보내기 (브라우저에서 바로 사용 가능하도록)
window.ExtractTab = ExtractTab;