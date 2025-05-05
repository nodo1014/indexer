/**
 * download-tab.js - AI 자막 다운로드 탭 기능
 * 2025-05-05: 모듈화 리팩토링
 */

/**
 * 자막 다운로드 탭 컨트롤러 클래스
 */
class DownloadTabController {
    constructor() {
        console.log('DownloadTabController 생성자 호출');
        
        // DOM 요소 참조 - 초기화시 요소가 없을 수 있으므로 null 할당 허용
        this.fileTable = document.querySelector('#download-file-list') || document.querySelector('#file-list');
        
        // DOM 요소 확인 로그
        console.log('파일 테이블 참조:', this.fileTable ? 'OK' : 'Not found');
        
        // 버튼 및 기타 요소들
        this.selectAllBtn = document.getElementById('select-all-download');
        this.deselectAllBtn = document.getElementById('deselect-all-download');
        this.runDownloadBtn = document.getElementById('run-download');
        this.runAutoDownloadBtn = document.getElementById('run-auto-download');
        this.runMultilingualDownloadBtn = document.getElementById('run-multilingual-download');
        this.downloadLangSelect = document.getElementById('download-lang');
        this.useMultilingualCheckbox = document.getElementById('use-multilingual');
        this.downloadStatusSpan = document.getElementById('download-status');
        this.pathInput = document.getElementById('path-input-download');
        this.browseBtn = document.getElementById('browse-btn-download');
        
        console.log('DownloadTabController 초기화, fileTable:', this.fileTable);
        console.log('버튼 초기화:', {
            selectAll: this.selectAllBtn,
            deselectAll: this.deselectAllBtn,
            download: this.runDownloadBtn,
            autoDownload: this.runAutoDownloadBtn,
            multilingual: this.runMultilingualDownloadBtn
        });
        
        // 이벤트 리스너 등록
        this.registerEventListeners();
        
        // 파일 목록 초기화
        // 로딩 지연 - DOM이 완전히 로드된 후 초기화
        setTimeout(() => this.initializeFileList(), 500);
    }
    
    /**
     * 이벤트 리스너 등록
     */
    registerEventListeners() {
        console.log('이벤트 리스너 등록 시작');
        
        // DOM 요소가 없을 수 있으므로 모든 이벤트 등록 전에 null 체크
        if (this.selectAllBtn) {
            console.log('전체 선택 버튼 리스너 등록');
            this.selectAllBtn.addEventListener('click', () => this.selectAllFiles());
        } else {
            console.warn('전체 선택 버튼이 없습니다!');
        }
        
        if (this.deselectAllBtn) {
            console.log('전체 해제 버튼 리스너 등록');
            this.deselectAllBtn.addEventListener('click', () => this.deselectAllFiles());
        } else {
            console.warn('전체 해제 버튼이 없습니다!');
        }
        
        if (this.runDownloadBtn) {
            console.log('다운로드 버튼 리스너 등록');
            this.runDownloadBtn.addEventListener('click', () => this.handleDownload());
        } else {
            console.warn('다운로드 버튼이 없습니다!');
        }
        
        // 원클릭 자막 처리 버튼
        if (this.runAutoDownloadBtn) {
            console.log('원클릭 자막 처리 버튼 리스너 등록');
            this.runAutoDownloadBtn.addEventListener('click', () => {
                console.log('원클릭 자막 처리 버튼 클릭됨');
                this.handleAutoDownload();
            });
        } else {
            console.warn('원클릭 자막 처리 버튼이 없습니다!');
        }
        
        // 다국어 자동 검색 버튼
        if (this.runMultilingualDownloadBtn) {
            console.log('다국어 자동 검색 버튼 리스너 등록');
            this.runMultilingualDownloadBtn.addEventListener('click', () => {
                console.log('다국어 자동 검색 버튼 클릭됨');
                this.handleMultilingualDownload();
            });
        } else {
            console.warn('다국어 자동 검색 버튼이 없습니다!');
        }
        
        console.log('이벤트 리스너 등록 완료');
    }
    
    /**
     * 파일 목록 초기화
     */
    async initializeFileList() {
        try {
            // currentPath 대신 전역 변수 사용
            const currentPath = window.currentRelativePath || '';
            console.log('파일 목록 초기화, 경로:', currentPath);
            
            // /api/list_files 대신 /api/files 사용 (올바른 쿼리 파라미터 적용)
            const response = await fetch(`/api/files?scan_path=${encodeURIComponent(currentPath)}&filter_video=true&filter_audio=true`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('파일 목록을 가져왔습니다:', data);
            this.renderFileTable(data.files);
        } catch (error) {
            console.error('파일 목록 로딩 오류:', error);
            this.showError('파일 목록을 불러올 수 없습니다: ' + error.message);
        }
    }
    
    /**
     * 파일 목록 테이블 렌더링
     * @param {Array} files - 파일 목록 배열
     */
    renderFileTable(files) {
        console.log('renderFileTable 호출됨:', files.length, '개 파일');
        
        if (!this.fileTable) {
            console.error('파일 테이블이 존재하지 않습니다!');
            return;
        }
        
        const tbody = this.fileTable.querySelector('tbody');
        if (!tbody) {
            console.error('테이블 body가 존재하지 않습니다!');
            return;
        }
        
        // 기존 내용 비우기
        tbody.innerHTML = '';
        
        // 비디오/오디오 파일만 필터링
        const mediaFiles = files.filter(file => 
            file.type === 'video' || file.type === 'audio'
        );
        
        console.log('미디어 파일 수:', mediaFiles.length);
        
        if (mediaFiles.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="6">미디어 파일이 없습니다.</td>';
            tbody.appendChild(row);
            return;
        }
        
        // 각 파일에 대한 행 추가
        mediaFiles.forEach(file => {
            const row = document.createElement('tr');
            row.setAttribute('data-path', file.path);
            row.setAttribute('data-filename', file.name || '');
            row.setAttribute('data-type', file.type || '');
            
            row.innerHTML = `
                <td><input type="checkbox" class="file-checkbox"></td>
                <td class="file-name">${file.name}</td>
                <td class="language">${this.downloadLangSelect ? this.downloadLangSelect.value : 'en'}</td>
                <td class="status">대기 중</td>
                <td class="actions">
                    <button class="download-btn">다운로드</button>
                </td>
                <td class="subtitle-preview"></td>
            `;
            
            // 행 버튼에 이벤트 리스너 추가
            const downloadBtn = row.querySelector('.download-btn');
            downloadBtn.addEventListener('click', () => this.downloadSubtitle(file.path));
            
            tbody.appendChild(row);
        });
        
        console.log('테이블 렌더링 완료');
        
        // 체크박스 이벤트 리스너 추가
        const headerCheckbox = this.fileTable.querySelector('thead input[type="checkbox"]');
        if (headerCheckbox) {
            headerCheckbox.addEventListener('change', (e) => {
                const checkboxes = this.fileTable.querySelectorAll('tbody input[type="checkbox"]');
                checkboxes.forEach(checkbox => checkbox.checked = e.target.checked);
            });
        }
    }
    
    /**
     * 전체 파일 선택
     */
    selectAllFiles() {
        const checkboxes = this.fileTable.querySelectorAll('tbody input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = true);
    }
    
    /**
     * 전체 파일 선택 해제
     */
    deselectAllFiles() {
        const checkboxes = this.fileTable.querySelectorAll('tbody input[type="checkbox"]');
        checkboxes.forEach(checkbox => checkbox.checked = false);
    }
    
    /**
     * 선택된 파일 경로 배열 가져오기
     * @returns {Array} 선택된 파일 경로 배열
     */
    getSelectedFilePaths() {
        // 먼저 다운로드 탭 내의 체크박스 확인 (file-select 클래스)
        let selectedRows = this.fileTable.querySelectorAll('tbody tr input[type="checkbox"]:checked');
        
        if (selectedRows.length === 0) {
            // 다운로드 탭에서 선택된 항목이 없으면 메인 파일 목록에서 확인 (file-checkbox 클래스)
            console.log('다운로드 탭에서 선택된 항목이 없어 메인 파일 목록 확인');
            selectedRows = document.querySelectorAll('#file-list tr input.file-checkbox:checked');
        }
        
        console.log('선택된 파일 행 수:', selectedRows.length);
        
        // 각 선택된 행에서 경로 추출
        const paths = Array.from(selectedRows).map(checkbox => {
            const row = checkbox.closest('tr');
            const path = row.getAttribute('data-path') || row.dataset.path;
            console.log('선택된 파일 경로:', path);
            return path;
        }).filter(Boolean); // null/undefined 제거
        
        console.log('총 선택된 파일 수:', paths.length);
        return paths;
    }
    
    /**
     * 자막 다운로드 API 호출
     * @param {string} filePath - 미디어 파일 경로
     * @returns {Promise<Object>} - 다운로드 결과
     */
    async downloadSubtitle(filePath) {
        try {
            // 언어 코드 가져오기
            const language = this.downloadLangSelect ? this.downloadLangSelect.value : 'en';
            
            // 다국어 자동 시도 옵션 확인
            const useMultilingual = this.useMultilingualCheckbox && this.useMultilingualCheckbox.checked;
            
            // 다국어 자동 시도가 활성화된 경우
            if (useMultilingual) {
                return await this.downloadMultilingualSubtitle(filePath, this.getPriorityLanguages(language));
            }
            
            // 파일 이름 추출
            const filename = this.getFileNameFromPath(filePath);
            console.log(`자막 다운로드 요청: 파일명=${filename}, 언어=${language}`);
            
            // 단일 언어 다운로드
            const response = await fetch('/api/download_subtitle', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    filename: filename,
                    language: language
                })
            });
            
            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('자막 다운로드 응답:', data);
            
            // 결과 업데이트
            const row = this.fileTable.querySelector(`tr[data-path="${filePath}"]`);
            if (row) {
                const statusCell = row.querySelector('.status');
                const previewCell = row.querySelector('.subtitle-preview');
                
                if (data.success) {
                    statusCell.textContent = '성공';
                    statusCell.style.color = 'green';
                    
                    if (data.subtitle_text) {
                        previewCell.textContent = data.subtitle_text.split('\n').slice(0, 2).join(' ');
                    }
                } else {
                    statusCell.textContent = '실패';
                    statusCell.style.color = 'red';
                }
            }
            
            return data;
        } catch (error) {
            console.error('자막 다운로드 오류:', error);
            
            // 실패 상태 업데이트
            this.updateRowStatus(filePath, '오류', 'red');
            
            return { success: false, error: error.message };
        }
    }

    /**
     * 다국어 자막 다운로드 API 호출
     * @param {string} filePath - 미디어 파일 경로
     * @param {string[]} languages - 시도할 언어 코드 배열
     * @returns {Promise<Object>} - 다운로드 결과
     */
    async downloadMultilingualSubtitle(filePath, languages) {
        try {
            console.log(`다국어 자막 검색: 경로=${filePath}, 언어=${languages.join(',')}`);
            
            const response = await fetch('/api/multilingual_subtitle_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    media_path: filePath,
                    languages: languages
                })
            });

            if (!response.ok) {
                throw new Error(`서버 오류: ${response.status}`);
            }

            const data = await response.json();
            console.log('다국어 자막 검색 응답:', data);
            
            // 결과 업데이트
            const row = this.fileTable.querySelector(`tr[data-path="${filePath}"]`);
            if (row) {
                const statusCell = row.querySelector('.status');
                const previewCell = row.querySelector('.subtitle-preview');
                
                if (data.success) {
                    statusCell.textContent = `성공 (${data.language})`;
                    statusCell.style.color = 'green';
                    
                    if (data.subtitle_text) {
                        previewCell.textContent = data.subtitle_text.split('\n').slice(0, 2).join(' ');
                    }
                } else {
                    statusCell.textContent = '실패';
                    statusCell.style.color = 'red';
                    
                    // 모든 언어에서 실패한 경우 알림 표시
                    this.showSubtitleNotFoundAlert(this.getFileNameFromPath(filePath));
                }
            }
            
            return data;
        } catch (error) {
            console.error('다국어 자막 다운로드 오류:', error);
            
            // 실패 상태 업데이트
            this.updateRowStatus(filePath, '오류', 'red');
            
            return { success: false, error: error.message };
        }
    }

    /**
     * 우선순위 언어 목록 가져오기
     * @param {string} primaryLanguage - 사용자가 선택한 주 언어
     * @returns {string[]} - 우선순위가 적용된 언어 코드 배열
     */
    getPriorityLanguages(primaryLanguage) {
        // 기본 우선순위 언어 배열
        const defaultLanguages = ['en', 'ko', 'ja', 'zh', 'es', 'fr', 'de', 'it'];
        
        // 주 언어가 이미 우선순위에 있다면 제거 (나중에 첫번째로 추가)
        const filteredLanguages = defaultLanguages.filter(lang => lang !== primaryLanguage);
        
        // 주 언어를 첫번째로 추가
        return [primaryLanguage, ...filteredLanguages];
    }

    /**
     * 파일 경로에서 파일명 추출
     * @param {string} filePath - 파일 경로
     * @returns {string} - 파일명
     */
    getFileNameFromPath(filePath) {
        const parts = filePath.split('/');
        return parts[parts.length - 1];
    }

    /**
     * 자막을 찾을 수 없을 때 알림 표시
     * @param {string} fileName - 미디어 파일 이름
     */
    showSubtitleNotFoundAlert(fileName) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning';
        alertDiv.textContent = `${fileName} 파일의 자막을 어떤 언어로도 찾을 수 없습니다.`;
        alertDiv.style.cssText = `
            background-color: #fcf8e3;
            color: #8a6d3b;
            padding: 10px 15px;
            border: 1px solid #faebcc;
            border-radius: 4px;
            margin: 10px 0;
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
        `;
        document.body.appendChild(alertDiv);
        
        // 알림 5초 후 자동 제거
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
    
    /**
     * 행 상태 업데이트
     * @param {string} filePath - 파일 경로
     * @param {string} status - 상태 텍스트
     * @param {string} color - 상태 색상
     */
    updateRowStatus(filePath, status, color = null) {
        const row = this.fileTable.querySelector(`tr[data-path="${filePath}"]`);
        if (!row) return;
        
        const statusCell = row.querySelector('.status');
        if (statusCell) {
            statusCell.textContent = status;
            if (color) {
                statusCell.style.color = color;
            }
        }
    }
    
    /**
     * 자막 다운로드 처리 (통합 함수)
     * - 선택된 언어로 검색하고 체크박스에 따라 다국어 시도 여부 결정
     */
    async handleAutoDownload() {
        const selectedFiles = this.getSelectedFilePaths();
        if (selectedFiles.length === 0) {
            alert('처리할 파일을 선택해주세요.');
            return;
        }
        
        this.downloadStatusSpan.textContent = '자막 처리 중...';
        
        // 언어 코드 가져오기
        const language = this.downloadLangSelect ? this.downloadLangSelect.value : 'en';
        
        // 다국어 자동 시도 옵션 확인
        const useMultilingual = this.useMultilingualCheckbox && this.useMultilingualCheckbox.checked;
        
        // 언어 목록 설정 (다국어 체크박스에 따라 다르게 설정)
        let languages = [];
        if (useMultilingual) {
            // 다국어 자동 시도가 체크되었을 경우: 우선순위 언어 목록 사용
            languages = this.getPriorityLanguages(language);
            console.log(`다국어 자막 처리: 선택된 파일 ${selectedFiles.length}개, 우선 언어: ${languages.join(', ')}`);
        } else {
            // 다국어 자동 시도가 체크되지 않았을 경우: 선택된 언어만 사용
            languages = [language];
            console.log(`단일 언어 자막 처리: 선택된 파일 ${selectedFiles.length}개, 언어: ${language}`);
        }
        
        // 순차적으로 처리
        let successCount = 0;
        let failCount = 0;
        
        for (const filePath of selectedFiles) {
            this.updateRowStatus(filePath, '처리 중...');
            
            try {
                let api = useMultilingual ? '/api/multilingual_subtitle_search' : '/api/download_subtitle';
                let requestData = {};
                
                if (useMultilingual) {
                    // 다국어 검색 API 사용 (여러 언어 순차 시도)
                    requestData = {
                        media_path: filePath,
                        languages: languages,
                        min_similarity: 50.0  // 최소 유사도 (%)
                    };
                } else {
                    // 단일 언어 검색 API 사용
                    requestData = {
                        filename: this.getFileNameFromPath(filePath),
                        language: language
                    };
                }
                
                console.log(`자막 요청: API=${api}, 데이터=`, requestData);
                
                // API 호출
                const response = await fetch(api, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });
                
                if (!response.ok) {
                    throw new Error(`서버 오류: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('자막 검색 결과:', result);
                
                if (result.success) {
                    // 자막 찾기 성공
                    
                    // 상태 업데이트
                    this.updateRowStatus(filePath, '완료', 'green');
                    successCount++;
                    
                    // 추가 정보 표시
                    const row = this.fileTable.querySelector(`tr[data-path="${filePath}"]`);
                    if (row) {
                        const previewCell = row.querySelector('.subtitle-preview');
                        if (previewCell) {
                            let statusInfo = '';
                            
                            if (useMultilingual) {
                                // 다국어 검색 결과 표시
                                const langInfo = result.language ? `(${result.language})` : '';
                                let syncStatus = '동기화 확인됨';
                                
                                if (result.sync_info && !result.sync_info.in_sync) {
                                    syncStatus = `동기화 필요함 (오프셋: ${result.sync_info.avg_offset || 0}ms)`;
                                }
                                
                                statusInfo = `자막 저장됨 ${langInfo} - ${syncStatus}`;
                            } else {
                                // 단일 언어 검색 결과 표시
                                statusInfo = `자막 저장됨 (${language})`;
                                if (result.subtitle_text) {
                                    previewCell.title = result.subtitle_text.split('\n').slice(0, 5).join('\n');
                                }
                            }
                            
                            previewCell.textContent = statusInfo;
                        }
                    }
                } else {
                    // 실패
                    this.updateRowStatus(filePath, '실패', 'red');
                    failCount++;
                    
                    // 실패 이유 표시
                    const row = this.fileTable.querySelector(`tr[data-path="${filePath}"]`);
                    if (row) {
                        const previewCell = row.querySelector('.subtitle-preview');
                        if (previewCell) {
                            previewCell.textContent = `실패: ${result.error || '적합한 자막 없음'}`;
                        }
                    }
                }
            } catch (error) {
                console.error('자막 처리 오류:', error);
                this.updateRowStatus(filePath, '오류', 'red');
                failCount++;
            }
        }
        
        this.downloadStatusSpan.textContent = `완료: 성공 ${successCount}, 실패 ${failCount}`;
    }
    
    /**
     * 다국어 자동 검색 처리
     */
    async handleMultilingualDownload() {
        // 다국어 자동 시도 옵션 활성화
        if (this.useMultilingualCheckbox) {
            this.useMultilingualCheckbox.checked = true;
        }
        
        // 자막 자동 처리 메서드 호출
        await this.handleAutoDownload();
    }
    
    /**
     * 선택 다운로드 처리
     */
    async handleDownload() {
        // 기본적으로 원클릭 자막 처리와 동일하게 동작
        await this.handleAutoDownload();
    }
    
    /**
     * 오류 메시지 표시
     * @param {string} message - 오류 메시지
     */
    showError(message) {
        console.error(message);
        if (this.downloadStatusSpan) {
            this.downloadStatusSpan.textContent = `오류: ${message}`;
            this.downloadStatusSpan.style.color = 'red';
        }
    }
    
    /**
     * 폴더 경로 탐색
     */
    browsePath() {
        alert('폴더 탐색 기능은 개발 중입니다.');
    }

    /**
     * UI 새로고침
     */
    refreshView() {
        console.log('다운로드 탭 UI 새로고침');
        
        // DOM 요소 참조 갱신
        this.fileTable = document.querySelector('#download-file-list') || document.querySelector('#file-list');
        
        if (!this.fileTable) {
            console.error('파일 테이블 요소를 찾을 수 없습니다.');
        }
        
        // 파일 목록 갱신 (필요시)
        // this.initializeFileList();
    }
}

// 다운로드 탭 컨트롤러 생성 및 전역 변수로 저장
class DownloadTab {
    constructor() {
        console.log('DownloadTab 클래스 초기화');
        this.controller = null; // 필요할 때만 초기화
    }
    
    init() {
        console.log('DownloadTab init 호출됨');
        // 컨트롤러 초기화
        if (!this.controller) {
            this.controller = new DownloadTabController();
        }
        return this;
    }
    
    onActivate() {
        console.log('다운로드 탭 활성화됨');
        // 탭이 활성화될 때 컨트롤러 초기화 또는 재활성화
        if (!this.controller) {
            this.controller = new DownloadTabController();
        } else {
            // 필요한 경우 컨트롤러 재활성화 로직
            if (typeof this.controller.refreshView === 'function') {
                this.controller.refreshView();
            }
        }
        
        // 다운로드 탭 UI 요소 표시
        const downloadContent = document.getElementById('tab-content-download');
        if (downloadContent) {
            downloadContent.style.display = 'block';
        }
        
        // 파일 목록이 비어있으면 다시 로드
        const tbody = document.querySelector('#download-file-list tbody');
        if (tbody && (!tbody.children.length || tbody.children.length === 1 && tbody.children[0].textContent.includes('로딩'))) {
            this.controller.initializeFileList();
        }
    }
}

// 전역 변수로 등록
window.DownloadTab = DownloadTab;

// DownloadTab 탭 클래스 초기화 함수 정의 (main.js에서 사용)
document.addEventListener('DOMContentLoaded', function() {
    console.log('다운로드 탭 초기화 리스너 등록됨');
});

// 명시적 초기화를 위한 함수 추가 (필요시 직접 호출)
function initDownloadTab() {
    console.log('다운로드 탭 초기화 시작');
    if (!window.downloadTab) {
        window.downloadTab = new DownloadTabController();
    }
    return window.downloadTab;
}
