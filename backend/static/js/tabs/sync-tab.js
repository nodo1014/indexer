/**
 * sync-tab.js - 자막 씽크 AI 맞춤 탭 기능
 * 2025-05-05: 모듈 추가
 */

class SyncTab {
    constructor() {
        this.initialized = false;
        this.tabId = 'sync-ai';
    }

    /**
     * 탭 초기화
     */
    init() {
        if (this.initialized) return;
        
        console.log('자막 씽크 AI 맞춤 탭 초기화...');
        
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
            <div class="sync-tab-container">
                <div class="action-panel">
                    <h3>자막 씽크 AI 맞춤</h3>
                    <p class="description">기존 자막의 씽크가 안 맞는 경우, AI를 활용하여 자막의 타이밍을 자동으로 조정합니다.</p>
                    <div class="actions">
                        <button id="sync-select-all" class="action-button">전체 선택</button>
                        <button id="sync-deselect-all" class="action-button">전체 해제</button>
                        <button id="run-sync" class="cta-button">선택 파일 자막 씽크 맞춤</button>
                        <span id="sync-status" style="margin-left:12px;color:#888;font-size:0.97em;"></span>
                    </div>
                </div>
                
                <div class="options-panel">
                    <h4>씽크 조정 옵션</h4>
                    <div class="option-group">
                        <label>
                            <input type="checkbox" id="sync-auto-save" checked>
                            원본 자막 자동 대체
                        </label>
                        <p style="margin:4px 0 0 24px;color:#888;font-size:0.95em;">
                            체크 해제 시 *_synced.srt 파일로 별도 저장됩니다.
                        </p>
                    </div>
                    <div class="option-group">
                        <label for="sync-language">영상 주요 언어:</label>
                        <select id="sync-language">
                            <option value="auto">자동 감지</option>
                            <option value="ko">한국어 (ko)</option>
                            <option value="en">영어 (en)</option>
                            <option value="ja">일본어 (ja)</option>
                            <option value="zh">중국어 (zh)</option>
                        </select>
                    </div>
                    <div class="option-group">
                        <label for="sync-threshold">씽크 오차 허용 범위:</label>
                        <select id="sync-threshold">
                            <option value="0.5">정밀 (오차 ±0.5초)</option>
                            <option value="1.0" selected>표준 (오차 ±1.0초)</option>
                            <option value="2.0">느슨하게 (오차 ±2.0초)</option>
                        </select>
                    </div>
                    <div class="option-group">
                        <label for="sync-model">AI 모델:</label>
                        <select id="sync-model">
                            <option value="tiny" title="빠름, 저사양 PC/테스트용">Tiny (빠름/저정확도)</option>
                            <option value="base" selected title="고속, 일상적 사용/저사양 PC">Base (권장)</option>
                            <option value="small" title="중속, 일반 PC/서버">Small (고정확도)</option>
                        </select>
                    </div>
                </div>
                
                <div class="note-panel" style="margin-top:12px;padding:12px;background:#fff8e1;border-radius:6px;border-left:3px solid #ffc107;">
                    <h4 style="margin-top:0;color:#f57c00;">참고사항</h4>
                    <ul style="margin-bottom:0;">
                        <li>자막 씽크 맞춤은 <strong>이미 자막이 있는</strong> 미디어 파일에만 적용됩니다.</li>
                        <li>인공지능이 음성을 인식하여 기존 자막의 타이밍을 자동으로 조정합니다.</li>
                        <li>자막 언어와 영상 음성 언어가 다른 경우, 영상 주요 언어를 올바르게 선택하세요.</li>
                        <li>씽크 조정은 자막 내용을 수정하지 않고 타이밍만 조정합니다.</li>
                    </ul>
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
        const selectAllBtn = document.getElementById('sync-select-all');
        const deselectAllBtn = document.getElementById('sync-deselect-all');
        const runSyncBtn = document.getElementById('run-sync');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => this.handleSelectAll());
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => this.handleDeselectAll());
        }
        
        if (runSyncBtn) {
            runSyncBtn.addEventListener('click', () => this.handleRunSync());
        }
    }
    
    /**
     * 탭이 활성화될 때 호출되는 메서드
     */
    onActivate() {
        console.log('자막 씽크 AI 맞춤 탭 활성화');
        // 파일 목록 필터링 - 자막이 있는 파일만 보이도록
        this.filterFilesWithSubtitles(true);
        // 필요한 경우 상태 업데이트
        this.updateUI();
    }
    
    /**
     * 탭이 비활성화될 때 호출되는 메서드
     */
    onDeactivate() {
        // 필터 초기화
        this.filterFilesWithSubtitles(false);
    }
    
    /**
     * 자막이 있는 파일만 표시하거나 모든 파일 표시
     * @param {boolean} showOnlyWithSubtitles - true일 경우 자막이 있는 파일만 표시
     */
    filterFilesWithSubtitles(showOnlyWithSubtitles) {
        const rows = document.querySelectorAll('#file-list tr');
        
        rows.forEach(row => {
            const subtitleCell = row.querySelector('.subtitle-status');
            if (!subtitleCell) return;
            
            if (showOnlyWithSubtitles) {
                // 자막이 있는 파일(O 표시)만 보이도록
                row.style.display = subtitleCell.textContent.trim() === 'O' ? '' : 'none';
            } else {
                // 모든 파일 표시
                row.style.display = '';
            }
        });
        
        // 체크박스 해제
        document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // 헤더 체크박스도 체크 해제
        const selectAllHeader = document.getElementById('select-all-header');
        if (selectAllHeader) selectAllHeader.checked = false;
    }
    
    /**
     * UI 상태 업데이트
     */
    updateUI() {
        // 현재 파일 목록에 따라 버튼 활성화/비활성화 등 업데이트
        const hasSelectedFiles = this.getSelectedFiles().length > 0;
        const runSyncBtn = document.getElementById('run-sync');
        
        if (runSyncBtn) {
            runSyncBtn.disabled = !hasSelectedFiles;
        }
    }
    
    /**
     * 전체 선택 처리
     */
    handleSelectAll() {
        document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
            // 자막이 있고(O 표시) 보이는 행(display != none)인 경우만 선택
            const row = checkbox.closest('tr');
            const subtitleCell = row.querySelector('.subtitle-status');
            
            if (subtitleCell && subtitleCell.textContent.trim() === 'O' && row.style.display !== 'none') {
                checkbox.checked = true;
            }
        });
        
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
     * 자막 씽크 맞춤 실행
     */
    async handleRunSync() {
        const selectedFiles = this.getSelectedFiles();
        
        if (selectedFiles.length === 0) {
            alert('씽크를 조정할 자막 파일을 하나 이상 선택해주세요.');
            return;
        }
        
        const autoSave = document.getElementById('sync-auto-save').checked;
        const language = document.getElementById('sync-language').value;
        const threshold = document.getElementById('sync-threshold').value;
        const model = document.getElementById('sync-model').value;
        
        const statusText = document.getElementById('sync-status');
        
        if (statusText) {
            statusText.textContent = '씽크 조정 준비 중...';
        }
        
        console.log(`자막 씽크 맞춤 시작: ${selectedFiles.length}개 파일, 자동 저장: ${autoSave}, 언어: ${language}, 임계값: ${threshold}, 모델: ${model}`);
        
        // 작업 상태 업데이트
        document.getElementById('batch-status').textContent = '자막 씽크 AI 맞춤 중...';
        
        try {
            let successCount = 0;
            let errorCount = 0;
            
            // 각 파일별로 처리
            for (let i = 0; i < selectedFiles.length; i++) {
                const filePath = selectedFiles[i];
                const fileName = filePath.split(/[/\\]/).pop();
                
                if (statusText) {
                    statusText.textContent = `맞춤 중 (${i + 1}/${selectedFiles.length}): ${fileName}`;
                }
                
                const fileRow = document.querySelector(`tr[data-path="${filePath.replace(/"/g, '\\"')}"]`);
                if (fileRow) {
                    const statusCell = fileRow.querySelector('.status');
                    if (statusCell) {
                        statusCell.textContent = '씽크 맞춤 중...';
                    }
                }
                
                try {
                    const result = await this.syncSubtitle(filePath, { autoSave, language, threshold, model });
                    
                    if (result && result.success) {
                        successCount++;
                    } else {
                        errorCount++;
                    }
                } catch (error) {
                    console.error(`${fileName} 자막 씽크 맞춤 실패:`, error);
                    errorCount++;
                    
                    if (fileRow) {
                        const statusCell = fileRow.querySelector('.status');
                        if (statusCell) {
                            statusCell.textContent = `씽크 맞춤 실패: ${error.message}`;
                        }
                    }
                }
            }
            
            if (statusText) {
                statusText.textContent = `완료: ${successCount}개 성공, ${errorCount}개 실패`;
            }
            
            document.getElementById('batch-status').textContent = 
                `자막 씽크 맞춤 완료: 총 ${selectedFiles.length}개 중 ${successCount}개 성공, ${errorCount}개 실패`;
            
            if (errorCount > 0) {
                alert(`자막 씽크 맞춤 완료: 총 ${selectedFiles.length}개 중 ${successCount}개 성공, ${errorCount}개 실패`);
            }
        } catch (error) {
            console.error('자막 씽크 맞춤 중 오류:', error);
            document.getElementById('batch-status').textContent = `자막 씽크 맞춤 오류: ${error.message}`;
            
            if (statusText) {
                statusText.textContent = `오류: ${error.message}`;
            }
            
            alert(`자막 씽크 맞춤 중 오류가 발생했습니다: ${error.message}`);
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
            const subtitleCell = row.querySelector('.subtitle-status');
            
            if (row && subtitleCell && subtitleCell.textContent.trim() === 'O' && row.style.display !== 'none') {
                selectedFiles.push(row.dataset.path);
            }
        });
        
        return selectedFiles;
    }
    
    /**
     * 단일 파일 자막 씽크 맞춤 처리
     * @param {string} filePath - 미디어 파일 경로
     * @param {Object} options - 씽크 조정 옵션 (autoSave, language, threshold, model)
     * @returns {Promise<Object>} 처리 결과
     */
    async syncSubtitle(filePath, options) {
        const fileName = filePath.split(/[/\\]/).pop();
        const fileRow = document.querySelector(`tr[data-path="${filePath.replace(/"/g, '\\"')}"]`);
        
        if (fileRow) {
            const statusCell = fileRow.querySelector('.status');
            if (statusCell) {
                statusCell.textContent = '씽크 맞춤 중...';
            }
        }
        
        try {
            // API 요청
            const response = await fetch('/api/sync_subtitle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    media_path: filePath,
                    auto_save: options.autoSave,
                    language: options.language,
                    threshold: parseFloat(options.threshold),
                    model: options.model
                }),
            });
            
            const data = await response.json();
            
            if (!response.ok || data.error) {
                throw new Error(data.error || '알 수 없는 오류');
            }
            
            // 처리 결과 UI 업데이트
            if (fileRow) {
                const statusCell = fileRow.querySelector('.status');
                const previewCell = fileRow.querySelector('.subtitle-preview');
                
                if (statusCell) {
                    if (data.subtitle_path) {
                        statusCell.innerHTML = `<a href="/download?file_path=${encodeURIComponent(data.subtitle_path)}" target="_blank">다운로드</a>`;
                        
                        // 미리보기 셀에 씽크 조정 결과 표시
                        if (previewCell && data.changes_summary) {
                            previewCell.innerHTML = `<pre>${this.escapeHtml(data.changes_summary)}</pre>`;
                        }
                    } else {
                        statusCell.textContent = '씽크 조정 완료';
                    }
                }
            }
            
            return data;
        } catch (error) {
            console.error(`${fileName} 자막 씽크 맞춤 실패:`, error);
            
            if (fileRow) {
                const statusCell = fileRow.querySelector('.status');
                if (statusCell) {
                    statusCell.textContent = `씽크 맞춤 실패: ${error.message}`;
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
window.SyncTab = SyncTab;