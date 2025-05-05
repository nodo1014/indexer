/**
 * directory-browser.js
 * 디렉토리 탐색기 기능 구현
 * 2025-05-05: 사이드바 탐색기 기능 복구 및 개선
 */

// 전역 상태 변수
window.currentRelativePath = '';  // 현재 상대 경로
window.directoryHistory = [];     // 디렉토리 방문 기록

/**
 * 페이지 로드시 디렉토리 탐색기 초기화
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('디렉토리 탐색기 초기화...');
    
    // 초기화 설정
    initDirectoryBrowser();
    
    // 디렉토리 브라우저 요소가 있는지 확인
    const directoryBrowser = document.getElementById('directory-browser');
    if (directoryBrowser) {
        console.log('디렉토리 브라우저 요소 존재 확인');
        // 모바일 환경에서도 기본적으로 표시되도록 설정
        if (window.innerWidth > 900) {
            directoryBrowser.style.display = 'block';
        }
    } else {
        console.error('디렉토리 브라우저 요소를 찾을 수 없음');
    }
    
    // 앱 타이틀 클릭 시 루트로 이동
    const appTitle = document.getElementById('app-title');
    if (appTitle) {
        appTitle.addEventListener('click', function() {
            navigateTo('');
        });
    }
    
    // 스캔 버튼 이벤트 연결
    const scanButton = document.getElementById('scan-directory');
    if (scanButton) {
        scanButton.addEventListener('click', function() {
            scanCurrentDirectory();
        });
    }
});

/**
 * 디렉토리 탐색기 초기화
 */
function initDirectoryBrowser() {
    // 현재 경로 초기화 (URL 파라미터 사용)
    const urlParams = new URLSearchParams(window.location.search);
    const pathParam = urlParams.get('path') || '';
    
    // 현재 경로 설정 및 파일 트리 로드
    window.currentRelativePath = pathParam;
    loadFileTree();
    
    // 자막 필터 이벤트 리스너 등록
    const subtitleFilter = document.getElementById('subtitle-filter');
    if (subtitleFilter) {
        subtitleFilter.addEventListener('change', function() {
            filterTableClientSide();
        });
    }
    
    // 파일 검색창 이벤트 리스너 등록
    const fileSearch = document.getElementById('file-search');
    if (fileSearch) {
        fileSearch.addEventListener('input', function() {
            filterTableClientSide();
        });
    }
    
    // 창 크기에 따라 탐색기 표시/숨김 설정
    updateDirectoryBrowserVisibility();
    window.addEventListener('resize', updateDirectoryBrowserVisibility);
}

/**
 * 창 크기에 따라 디렉토리 탐색기 표시/숨김 설정
 */
function updateDirectoryBrowserVisibility() {
    const directoryBrowser = document.getElementById('directory-browser');
    if (!directoryBrowser) return;
    
    if (window.innerWidth > 900) {
        // 데스크톱 환경에서는 항상 표시
        directoryBrowser.style.display = 'block';
        directoryBrowser.classList.remove('open');
    } else {
        // 모바일 환경에서는 토글 버튼으로 제어
        if (!directoryBrowser.classList.contains('open')) {
            directoryBrowser.style.display = 'none';
        }
    }
}

/**
 * 파일 트리 로드
 * API 호출하여 디렉토리 구조 가져오기
 */
async function loadFileTree() {
    try {
        // 현재 경로 표시 업데이트
        updateDirectoryPath();
        
        // 기존 /browse API 엔드포인트에서 디렉토리 목록 가져오기
        const response = await fetch(`/browse?current_path=${encodeURIComponent(window.currentRelativePath)}`, {
            method: 'GET'
        });
        
        // 응답 처리
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 디렉토리 목록 렌더링
        renderDirectoryList(data.directories);
        
        // URL 업데이트 (디렉토리 변경 시에만)
        const url = new URL(window.location);
        url.searchParams.set('path', window.currentRelativePath);
        window.history.pushState({}, '', url);
        
        // 디렉토리 변경 시에는 파일 목록을 초기화만 하고 자동으로 로드하지 않음
        const fileListElement = document.getElementById('file-list');
        if (fileListElement) {
            fileListElement.innerHTML = '<tr><td colspan="8">폴더 내 파일을 보려면 "현재 폴더 검색" 버튼을 클릭하세요.</td></tr>';
        }
        
        // 파일 헤더 업데이트
        updateFileListHeader();
    } catch (error) {
        console.error('파일 트리 로드 오류:', error);
        
        // 오류 시 UI 업데이트
        const directoryList = document.getElementById('directory-list');
        if (directoryList) {
            directoryList.innerHTML = `<li style="color: red; padding: 10px;">오류: ${error.message}</li>`;
        }
    }
}

/**
 * 디렉토리 목록 렌더링
 * @param {Array} directories - 디렉토리 목록
 */
function renderDirectoryList(directories) {
    const directoryList = document.getElementById('directory-list');
    if (!directoryList) return;
    
    // 디렉토리 목록 초기화
    directoryList.innerHTML = '';
    
    // 상위 디렉토리로 이동 항목 추가 (루트가 아닌 경우)
    if (window.currentRelativePath) {
        const parentItem = document.createElement('li');
        parentItem.innerHTML = '<a href="javascript:void(0);" class="parent-dir"><b>📁 ..</b> (상위 폴더)</a>';
        parentItem.querySelector('a').addEventListener('click', function() {
            // 경로에서 마지막 디렉토리 제거하여 상위 이동
            const pathParts = window.currentRelativePath.split('/');
            pathParts.pop();
            navigateTo(pathParts.join('/'));
        });
        directoryList.appendChild(parentItem);
    }
    
    // 디렉토리 항목 추가
    if (directories && directories.length > 0) {
        directories.forEach(dir => {
            const li = document.createElement('li');
            // 미디어 개수 표시 추가
            let countStr = '';
            if (typeof dir.video_count === 'number' && typeof dir.audio_count === 'number') {
                countStr = ` <span style="color:#888;font-size:0.97em;">(영상 ${dir.video_count}, 오디오 ${dir.audio_count})</span>`;
            }
            li.innerHTML = `<a href="javascript:void(0);" class="directory">📁 ${dir.name}${countStr}</a>`;
            li.querySelector('a').addEventListener('click', function() {
                // 현재 경로 + 선택한 디렉토리로 이동
                const newPath = window.currentRelativePath 
                    ? `${window.currentRelativePath}/${dir.name}` 
                    : dir.name;
                navigateTo(newPath);
            });
            directoryList.appendChild(li);
        });
    } else if (directories && directories.length === 0 && window.currentRelativePath === '') {
        // 루트에서 디렉토리가 없는 경우
        directoryList.innerHTML = '<li style="color: #888; padding: 10px;">루트 디렉토리에 하위 폴더가 없습니다.</li>';
    } else if (directories && directories.length === 0) {
        // 현재 디렉토리에 하위 디렉토리가 없는 경우 - 상위 폴더로 가는 링크는 항상 유지
        const noSubdirsMessage = document.createElement('li');
        noSubdirsMessage.style.color = '#888';
        noSubdirsMessage.style.padding = '10px';
        noSubdirsMessage.textContent = '이 폴더에 하위 폴더가 없습니다.';
        directoryList.appendChild(noSubdirsMessage);
    }
}

/**
 * 파일 목록 업데이트
 * @param {Array} files - 파일 목록
 */
function updateFileList(files) {
    console.log('updateFileList 함수 시작:', files.length);
    
    // 파일 목록 요소 가져오기
    const fileListElement = document.getElementById('file-list');
    if (!fileListElement) {
        console.error('파일 목록 요소(#file-list)를 찾을 수 없습니다.');
        return;
    }
    
    // 기존 모든 행 완전히 제거 (innerHTML = '' 대신 더 확실한 방법)
    while (fileListElement.firstChild) {
        fileListElement.removeChild(fileListElement.firstChild);
    }
    
    console.log('파일 목록 초기화 완료');
    
    if (!files || files.length === 0) {
        // 파일이 없는 경우
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="8">이 폴더에 미디어 파일이 없습니다.</td>';
        fileListElement.appendChild(emptyRow);
        console.log('빈 파일 메시지 추가됨');
        return;
    }
    
    // 파일 목록 렌더링
    files.forEach((file, index) => {
        const tr = document.createElement('tr');
        tr.dataset.path = file.path;
        tr.dataset.type = file.type || '';
        tr.dataset.filename = file.name || '';
        
        tr.innerHTML = `
            <td><input type="checkbox" class="file-checkbox"></td>
            <td class="status"></td>
            <td class="progress"></td>
            <td>${file.name}</td>
            <td class="lang-code" title="언어">${file.language || '-'}</td>
            <td class="subtitle-status">${file.has_subtitle ? 'O' : 'X'}</td>
            <td class="subtitle-preview"></td>
            <td class="extract-embedded">
                ${file.has_embedded ? '<button class="extract-btn" title="내장자막 추출">E</button>' : '-'}
            </td>
        `;
        
        // 내장 자막 추출 버튼 이벤트 (필요 시)
        const extractBtn = tr.querySelector('.extract-btn');
        if (extractBtn) {
            extractBtn.addEventListener('click', function() {
                if (typeof extractEmbeddedSubtitle === 'function') {
                    extractEmbeddedSubtitle(file.path);
                }
            });
        }
        
        fileListElement.appendChild(tr);
        
        // 일부 파일마다 로그 추가 (첫 3개와 마지막 3개만)
        if (index < 3 || index >= files.length - 3) {
            console.log(`파일 ${index+1}/${files.length} 추가: ${file.name}`);
        }
    });
    
    // 탭 활성화 코드 제거 - 이 부분이 파일 목록을 덮어쓰는 원인일 가능성이 높음
    console.log(`파일 목록 업데이트 완료: ${files.length}개 파일 표시됨`);
    
    /* 아래 코드 제거
    // 현재 탭 기반으로 UI 업데이트
    if (window.App && window.App.tabs) {
        const activeTab = window.tabController.getActiveTab();
        if (activeTab && window.App.tabs[activeTab] && typeof window.App.tabs[activeTab].onActivate === 'function') {
            window.App.tabs[activeTab].onActivate();
        }
    }
    */
}

/**
 * 파일 테이블 필터링 (클라이언트 측)
 * 자막 필터, 파일 타입 및 검색어 기준으로 필터링
 */
function filterTableClientSide() {
    const rows = document.querySelectorAll('#file-list tr');
    if (!rows.length) return;
    
    // 디버그용 로그 추가
    console.log(`필터링 시작: ${rows.length}개 행 발견`);
    
    // 필터 값 가져오기 - 요소가 없는 경우 기본값 사용
    const subtitleFilter = document.getElementById('subtitle-filter') ? document.getElementById('subtitle-filter').value : 'all';
    const filterVideo = document.getElementById('filter-video') ? document.getElementById('filter-video').checked : true;
    const filterAudio = document.getElementById('filter-audio') ? document.getElementById('filter-audio').checked : true;
    const searchQuery = document.getElementById('file-search') ? document.getElementById('file-search').value.toLowerCase().trim() : '';
    
    // 필터 상태 로깅
    console.log(`필터 상태: 자막=${subtitleFilter}, 비디오=${filterVideo}, 오디오=${filterAudio}, 검색어="${searchQuery}"`);
    
    // 각 행 필터링
    let visibleCount = 0;
    rows.forEach(row => {
        const subtitleStatus = row.querySelector('.subtitle-status');
        const filename = row.dataset.filename ? row.dataset.filename.toLowerCase() : '';
        const fileType = row.dataset.type ? row.dataset.type.toLowerCase() : '';
        
        // 디버그용 로그 (첫 몇 개 행에 대해서만)
        if (visibleCount < 3) {
            console.log(`행 정보: filename=${filename}, type=${fileType}, 자막=${subtitleStatus ? subtitleStatus.textContent : 'N/A'}`);
        }
        
        // 기본 표시 여부 - 필터 요소가 없으면 모두 표시하도록 변경
        let show = true;
        
        // 자막 필터 적용
        if (subtitleFilter !== 'all' && subtitleStatus) {
            const hasSubtitle = subtitleStatus.textContent.trim() === 'O';
            if (subtitleFilter === 'no_subtitle' && hasSubtitle) show = false;
            if (subtitleFilter === 'has_subtitle' && !hasSubtitle) show = false;
        }
        
        // 파일 타입 필터 적용
        if (!fileType) {
            // 파일 타입이 없는 경우 (헤더 행 등) 표시
        } else if (fileType.includes('video') && !filterVideo) {
            show = false;
        } else if (fileType.includes('audio') && !filterAudio) {
            show = false;
        } else if (!fileType.includes('video') && !fileType.includes('audio')) {
            // 비디오/오디오가 아닌 행은 헤더 또는 특수행이므로 표시
        }
        
        // 검색어 필터 적용
        if (searchQuery && !filename.includes(searchQuery)) {
            show = false;
        }
        
        // 행 표시/숨김 설정
        row.style.display = show ? '' : 'none';
        if (show) visibleCount++;
    });
    
    // 필터링 결과 표시
    console.log(`필터링 결과: ${visibleCount}개 파일 표시됨`);
    const batchStatus = document.getElementById('batch-status');
    if (batchStatus) {
        batchStatus.textContent = `현재 폴더에서 필터링된 미디어 파일: ${visibleCount}개`;
    }
}

/**
 * 현재 디렉토리 경로 업데이트
 */
function updateDirectoryPath() {
    const pathElement = document.getElementById('current-path-display');
    if (pathElement) {
        if (window.currentRelativePath) {
            pathElement.textContent = `현재 경로: /${window.currentRelativePath}`;
        } else {
            pathElement.textContent = `현재 경로: /`;
        }
    }
}

/**
 * 특정 디렉토리로 이동
 * @param {string} relativePath - 이동할 상대 경로
 */
async function navigateTo(relativePath) {
    // 현재 경로 업데이트
    window.currentRelativePath = relativePath;
    
    // 파일 트리 다시 로드
    await loadFileTree();
    
    // 파일 헤더 업데이트
    updateFileListHeader();
}

/**
 * 현재 디렉토리 스캔 (미디어 파일 검색)
 */
async function scanCurrentDirectory() {
    try {
        // 스캔 중 UI 업데이트
        const scanButton = document.getElementById('scan-directory');
        if (scanButton) {
            scanButton.disabled = true;
            scanButton.textContent = '스캔 중...';
        }
        const batchStatus = document.getElementById('batch-status');
        if (batchStatus) {
            batchStatus.textContent = '디렉토리 스캔 중...';
        }
        
        // 스캔 전에 파일 목록 초기화 (즉시 로딩 중 메시지 표시)
        const fileListElement = document.getElementById('file-list');
        if (fileListElement) {
            // 기존 모든 행 제거
            while (fileListElement.firstChild) {
                fileListElement.removeChild(fileListElement.firstChild);
            }
            
            // 로딩 중 메시지 표시
            const loadingRow = document.createElement('tr');
            loadingRow.innerHTML = '<td colspan="8">파일 목록 스캔 중...</td>';
            fileListElement.appendChild(loadingRow);
            console.log('스캔 전 파일 목록 초기화 완료');
        }
        
        // 필터 설정 가져오기 - 요소가 없는 경우 기본값 사용
        const filterVideo = document.getElementById('filter-video') ? document.getElementById('filter-video').checked : true;
        const filterAudio = document.getElementById('filter-audio') ? document.getElementById('filter-audio').checked : true;
        
        console.log(`스캔 시작: 경로=${window.currentRelativePath}, 비디오=${filterVideo}, 오디오=${filterAudio}`);
        
        // 기존 /api/files 엔드포인트 사용
        const response = await fetch(`/api/files?scan_path=${encodeURIComponent(window.currentRelativePath)}&filter_video=${filterVideo}&filter_audio=${filterAudio}`, {
            method: 'GET'
        });
        
        const data = await response.json();
        
        // 디버깅용 로그 추가
        console.log('scanCurrentDirectory fetch 응답:', data);
        
        if (!response.ok) {
            throw new Error(data.error || '디렉토리 스캔에 실패했습니다.');
        }
        
        // 결과 처리
        if (data.files) {
            console.log('data.files:', data.files);
            
            // 파일 목록 요소 다시 확인
            if (!fileListElement) {
                console.error('파일 목록 요소(#file-list)를 찾을 수 없습니다.');
                throw new Error('파일 목록 요소를 찾을 수 없습니다.');
            }
            
            // 업데이트 전 파일 목록 요소 현재 상태 로깅
            console.log('파일 목록 업데이트 전 상태:', fileListElement.innerHTML);
            
            // 파일 목록 업데이트
            updateFileList(data.files);
            
            // 업데이트 후 파일 목록 요소 상태 로깅
            console.log('파일 목록 업데이트 후 행 수:', document.querySelectorAll('#file-list tr').length);
            
            // 완료 메시지
            if (batchStatus) {
                batchStatus.textContent = `스캔 완료: ${data.files.length}개의 미디어 파일 발견`;
            }
            
            // 필터 적용
            filterTableClientSide();
        } else {
            throw new Error('스캔 결과가 없습니다.');
        }
    } catch (error) {
        console.error('디렉토리 스캔 오류:', error);
        
        // 오류 메시지 표시
        const batchStatus = document.getElementById('batch-status');
        if (batchStatus) {
            batchStatus.textContent = `스캔 오류: ${error.message}`;
        }
        
        // 파일 목록 비우기
        const fileListElement = document.getElementById('file-list');
        if (fileListElement) {
            // 기존 모든 행 제거 후 오류 메시지 추가
            while (fileListElement.firstChild) {
                fileListElement.removeChild(fileListElement.firstChild);
            }
            const errorRow = document.createElement('tr');
            errorRow.innerHTML = `<td colspan="8" style="color:red;">스캔 오류: ${error.message}</td>`;
            fileListElement.appendChild(errorRow);
        }
    } finally {
        // 버튼 상태 복구
        const scanButton = document.getElementById('scan-directory');
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.textContent = '현재 폴더 검색';
        }
    }
}

/**
 * 파일 목록 헤더 업데이트
 */
function updateFileListHeader() {
    const fileListHeader = document.getElementById('file-list-header');
    if (fileListHeader) {
        fileListHeader.textContent = '미디어 파일 목록 (' + (window.currentRelativePath ? '/' + window.currentRelativePath : '루트') + ')';
    }
}

// 함수를 전역 스코프로 내보내기 (다른 스크립트에서 사용 가능하도록)
window.navigateTo = navigateTo;
window.loadFileTree = loadFileTree;
window.filterTableClientSide = filterTableClientSide;
window.scanCurrentDirectory = scanCurrentDirectory;
window.updateFileListHeader = updateFileListHeader;