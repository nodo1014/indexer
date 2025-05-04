// render.js
// 화면 출력 전담 (DOM 렌더링 함수 모음)

export function renderJobList(jobs) {
    const jobList = document.getElementById('job-list');
    if (!jobList) return;
    jobList.innerHTML = '';
    if (!jobs || jobs.length === 0) {
        jobList.innerHTML = '<li style="color:#888;">진행 중인 작업이 없습니다.</li>';
        return;
    }
    let mainJob = jobs.find(j => j.status === '진행중' || j.status === '일시정지') || jobs[0];
    let otherJobs = jobs.filter(j => j !== mainJob);
    if (mainJob) {
        const li = document.createElement('li');
        li.style.display = 'block';
        li.style.marginBottom = '10px';
        li.innerHTML = `
          <div style="font-weight:500;font-size:1em;">
            <span class="job-filename" style="cursor:pointer;color:#1a5dab;" title="상세 보기">${mainJob.filename} <span style='color:#888;font-weight:400;font-size:0.97em;'>(${mainJob.language}, ${mainJob.model})</span></span>
          </div>
          <div style="margin-top:2px;display:flex;align-items:center;gap:4px;">
            <span style="width:54px;">${mainJob.progress}%</span>
            <span style="color:#888;">${mainJob.status}</span>
            <button class="job-btn" data-action="pause" title="일시정지">⏸️</button>
            <button class="job-btn" data-action="stop" title="중단">🛑</button>
            <button class="job-btn" data-action="resume" title="재개">▶️</button>
            <button class="job-btn job-delete" data-action="delete" title="삭제">❌</button>
          </div>
        `;
        li.querySelector('.job-filename').onclick = function() {
            if (window.showProgressModal) window.showProgressModal(mainJob.filename);
        };
        li.querySelector('[data-action="pause"]').disabled = mainJob.status !== '진행중';
        li.querySelector('[data-action="stop"]').disabled = mainJob.status === '완료' || mainJob.status === '중단됨';
        li.querySelector('[data-action="resume"]').disabled = mainJob.status !== '일시정지';
        // 버튼 이벤트는 main.js에서 바인딩
        jobList.appendChild(li);
    }
    if (otherJobs.length > 0) {
        const li = document.createElement('li');
        li.style.display = 'flex';
        li.style.flexWrap = 'wrap';
        li.style.gap = '8px';
        otherJobs.forEach(job => {
            const jobBox = document.createElement('span');
            jobBox.style.display = 'inline-flex';
            jobBox.style.alignItems = 'center';
            jobBox.style.background = '#f3f6fa';
            jobBox.style.borderRadius = '5px';
            jobBox.style.padding = '2px 6px 2px 4px';
            jobBox.style.marginBottom = '2px';
            jobBox.style.fontSize = '0.97em';
            jobBox.innerHTML = `
              <span class="job-filename" style="cursor:pointer;color:#1a5dab;" title="상세 보기">${job.filename} <span style='color:#888;font-weight:400;font-size:0.97em;'>(${job.language}, ${job.model})</span></span>
              <span style="margin:0 4px 0 6px;color:#888;">${job.status}</span>
              <button class="job-btn job-delete" data-action="delete" title="삭제">❌</button>
            `;
            jobBox.querySelector('.job-filename').onclick = function() {
                if (window.showProgressModal) window.showProgressModal(job.filename);
            };
            // 삭제 버튼 이벤트는 main.js에서 바인딩
            li.appendChild(jobBox);
        });
        jobList.appendChild(li);
    }
}

export function renderCompletedFiles() {
    const list = document.getElementById('completed-files');
    if (!list) return;
    if (!window.completedFiles || window.completedFiles.length === 0) {
        list.innerHTML = '<li style="color:#888;">완료된 파일이 없습니다.</li>';
        return;
    }
    list.innerHTML = window.completedFiles.map(f => {
        let statusColor = f.status === 'completed' ? '#2ecc71' : (f.status === 'skipped' ? '#f39c12' : (f.status === 'error' ? '#e74c3c' : '#95a5a6'));
        let statusLabel = f.status === 'completed' ? '완료' : (f.status === 'skipped' ? '건너뜀' : (f.status === 'error' ? '오류' : '취소'));
        let download = f.output_path ? `<a href="/download?file_path=${encodeURIComponent(f.output_path)}" target="_blank" style="color:#3498db;">다운로드</a>` : '';
        let logBtn = `<button onclick="if(window.showProgressModal)window.showProgressModal(${JSON.stringify(f.file_path)})" style="margin-left:8px;">로그 보기</button>`;
        let previewBtn = f.output_path ? `<button onclick="if(window.previewSubtitle)window.previewSubtitle('${f.output_path}', '${f.file_name.replace(/'/g, '\\'')}')" style="margin-left:8px;">자막 미리보기</button>` : '';
        let preview = f.subtitle_preview ? `<pre style='background:#f8f8f8;padding:4px 8px;border-radius:3px;margin:4px 0 0 0;'>${f.subtitle_preview}</pre>` : '';
        return `<li style="margin-bottom:10px;"><b>${f.file_name}</b> <span style="color:${statusColor};font-weight:600;">[${statusLabel}]</span> ${download} ${logBtn} ${previewBtn} ${preview}</li>`;
    }).join('');
}

export function renderMediaList(files) {
    const mediaList = document.getElementById('media-list');
    if (!mediaList) return;
    mediaList.innerHTML = '';
    if (!files || files.length === 0) {
        mediaList.innerHTML = '<div class="media-card media-card-empty">자막 없는 파일을 찾을 수 없습니다.</div>';
        return;
    }
    files.forEach(file => {
        const card = document.createElement('div');
        card.className = 'media-card';
        card.dataset.path = file.path;
        card.innerHTML = `
            <div class="media-main">
                <span class="media-filename">${file.name}</span>
                <span class="media-status">상태: 대기</span>
                <span class="media-lang">🌐 ${file.language || '-'}</span>
                <span class="media-subtitle">자막: ${file.has_subtitle ? '있음' : '없음'}</span>
            </div>
            <div class="media-actions">
                <button class="extract-btn">내장 자막</button>
                <button class="preview-btn">미리보기</button>
            </div>
        `;
        mediaList.appendChild(card);
    });
} 