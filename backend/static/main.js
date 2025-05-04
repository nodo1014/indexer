// main.js
// 초기화 및 전체 컨트롤러
// window.onload에서 각 기능 모듈을 불러와 초기화
// 폴더 이동, 필터 적용, 체크박스 관리 등 사용자 입력 중심 코드 포함
// ... (index.html에서 해당 부분만 추출 및 함수화)

// 예시 구조
import { connectWebSocket } from './websocket.js';
import { renderJobList, renderCompletedFiles, renderMediaList } from './render.js';

// 전역 변수 세팅 (템플릿에서 window에 할당 필요)
window.clientId = window.clientId || (window.__CLIENT_ID__ || 'default');
window.currentRelativePath = window.currentRelativePath || (window.__INITIAL_PATH__ || '');
window.isProcessing = false;
window.whisperLogs = {};
window.completedFiles = [];

// 폴더 트리 및 파일 목록 로드
async function loadFileTree(relativePath) {
    const dirList = document.getElementById('directory-list');
    if (!dirList) return;
    dirList.innerHTML = '<li>폴더 트리 로딩 중...</li>';
    try {
        const response = await fetch(`/browse?current_path=${encodeURIComponent(relativePath || '')}`);
        const data = await response.json();
        dirList.innerHTML = '';
        if (data.parent_path && data.parent_path !== relativePath && relativePath !== '') {
            const parentLi = document.createElement('li');
            const parentLink = document.createElement('a');
            parentLink.href = '#';
            parentLink.className = 'parent-node';
            parentLink.textContent = '.. (상위 폴더)';
            parentLink.onclick = (e) => { e.preventDefault(); navigateTo(data.parent_path); };
            parentLi.appendChild(parentLink);
            dirList.appendChild(parentLi);
        }
        if (data.directories && data.directories.length > 0) {
            data.directories.forEach(dir => {
                const li = document.createElement('li');
                const link = document.createElement('a');
                link.href = '#';
                link.textContent = `📁 ${dir.name}`;
                link.onclick = (e) => { e.preventDefault(); navigateTo(dir.path); };
                li.appendChild(link);
                dirList.appendChild(li);
            });
        } else if (dirList.children.length === 0) {
            dirList.innerHTML = '<li><span class="empty-node">하위 폴더가 없습니다</span></li>';
        }
    } catch (error) {
        dirList.innerHTML = `<li>탐색기 로드 실패: ${error.message}</li>`;
    }
}

async function loadFileList(relativePath) {
    const fileListBody = document.getElementById('file-list');
    if (fileListBody) fileListBody.innerHTML = '<tr><td colspan="8">파일 목록 로딩 중...</td></tr>';
    const filterVideo = document.getElementById('filter-video').checked;
    const filterAudio = document.getElementById('filter-audio').checked;
    const subtitleFilter = document.getElementById('subtitle-filter').value;
    try {
        const response = await fetch(`/api/files?scan_path=${encodeURIComponent(relativePath || '')}&filter_video=${filterVideo}&filter_audio=${filterAudio}&subtitle_filter=${subtitleFilter}`);
        const data = await response.json();
        if (fileListBody) fileListBody.innerHTML = '';
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const row = document.createElement('tr');
                row.dataset.path = file.path;
                row.dataset.type = file.type;
                row.innerHTML = `
                    <td><input type="checkbox" class="file-checkbox" ${file.has_subtitle ? 'disabled' : ''}></td>
                    <td class="status">대기</td>
                    <td class="progress">-</td>
                    <td class="filename">${file.name}</td>
                    <td class="lang-code">${file.language || '-'}</td>
                    <td class="subtitle-status">${file.has_subtitle ? 'O' : 'X'}</td>
                    <td class="subtitle-preview">-</td>
                    <td class="extract-embedded"><button class="extract-btn" title="내장 자막 추출">📝</button></td>
                `;
                fileListBody.appendChild(row);
            });
        } else {
            if (fileListBody) fileListBody.innerHTML = '<tr><td colspan="8">자막 없는 파일을 찾을 수 없습니다.</td></tr>';
        }
    } catch (error) {
        if (fileListBody) fileListBody.innerHTML = `<tr><td colspan="8">파일 목록 로드 중 오류: ${error.message}</td></tr>`;
    }
}

// 폴더 이동 및 UI 갱신
async function navigateTo(relativePath) {
    window.currentRelativePath = relativePath || '';
    const url = relativePath ? `/?scan_path=${encodeURIComponent(relativePath)}` : '/';
    history.pushState({ path: relativePath }, '', url);
    const pathDisplay = document.getElementById('current-path-display');
    if (pathDisplay) pathDisplay.textContent = `현재 경로: /${relativePath || ''}`;
    const fileListHeader = document.getElementById('file-list-header');
    if (fileListHeader) fileListHeader.textContent = '미디어 파일 목록 (' + (relativePath ? '/' + relativePath : '루트') + ')';
    await loadFileTree(relativePath);
    const fileListBody = document.getElementById('file-list');
    if (fileListBody) fileListBody.innerHTML = '<tr><td colspan="8">이 폴더의 미디어 파일을 검색하려면 "현재 폴더 검색" 버튼을 클릭하세요.</td></tr>';
}
window.navigateTo = navigateTo;

// 현재 폴더 검색
async function scanCurrentDirectory() {
    document.getElementById('batch-status').textContent = '파일 검색 중...';
    await loadFileList(window.currentRelativePath);
}
window.scanCurrentDirectory = scanCurrentDirectory;

// 체크박스 전체 선택/해제
function bindCheckboxEvents() {
    const selectAllHeader = document.getElementById('select-all-header');
    if (selectAllHeader) {
        selectAllHeader.addEventListener('change', (event) => {
            document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
                if (!checkbox.disabled && checkbox.closest('tr').style.display !== 'none') {
                    checkbox.checked = event.target.checked;
                }
            });
        });
    }
    const selectAllBtn = document.getElementById('select-all');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', () => {
            document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
                if (!checkbox.disabled && checkbox.closest('tr').style.display !== 'none') {
                    checkbox.checked = true;
                }
            });
        });
    }
    const deselectAllBtn = document.getElementById('deselect-all');
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', () => {
            document.querySelectorAll('#file-list .file-checkbox').forEach(checkbox => {
                if (!checkbox.disabled && checkbox.closest('tr').style.display !== 'none') {
                    checkbox.checked = false;
                }
            });
        });
    }
}

// 필터/검색 이벤트 바인딩
function bindFilterEvents() {
    const subtitleFilter = document.getElementById('subtitle-filter');
    if (subtitleFilter) {
        subtitleFilter.addEventListener('change', () => {
            scanCurrentDirectory();
        });
    }
    const scanBtn = document.getElementById('scan-directory');
    if (scanBtn) {
        scanBtn.addEventListener('click', () => {
            scanCurrentDirectory();
        });
    }
}

// 작업 현황 폴링
async function fetchAndRenderJobs() {
    try {
        const res = await fetch('/api/jobs');
        const data = await res.json();
        if (data.jobs) {
            renderJobList(data.jobs);
        } else {
            renderJobList([]);
        }
    } catch (e) {
        renderJobList([]);
    }
}
window.fetchAndRenderJobs = fetchAndRenderJobs;

// 초기화
window.onload = () => {
    connectWebSocket();
    navigateTo(window.currentRelativePath);
    fetchAndRenderJobs();
    bindCheckboxEvents();
    bindFilterEvents();
    // 기타 초기화 및 이벤트 바인딩 추가 가능
}; 