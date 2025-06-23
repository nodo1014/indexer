<script>
  import { onMount } from 'svelte';
  import DirectoryBrowser from '$lib/components/DirectoryBrowser.svelte';
  import MediaFilesTable from '$lib/components/MediaFilesTable.svelte';
  import SubtitleDownloader from '$lib/components/SubtitleDownloader.svelte';
  import { searchMediaFiles } from '$lib/api';
  import { page } from '$app/stores';

  // 상태 관리
  let selectedFile = null;
  let processingFiles = [];
  let completedFiles = [];
  let failedFiles = [];
  let batchProcessing = false;
  let batchProgress = 0;
  let currentBatchFile = '';
  let showCompletedOnly = false;
  
  // 페이지 로드 시 URL 파라미터 확인
  let mediaPath = '';
  
  onMount(() => {
    const pathParam = $page.url.searchParams.get('path');
    if (pathParam) {
      mediaPath = decodeURIComponent(pathParam);
    }
  });
  
  // 파일 선택 처리
  function handleFileSelect(event) {
    const files = event.detail;
    if (files && files.length > 0) {
      selectedFile = files[0]; // 첫 번째 선택된 파일
    } else {
      selectedFile = null;
    }
  }
  
  // 자막 다운로드 완료 처리
  function handleDownloadComplete(event) {
    const result = event.detail;
    
    if (result.success) {
      // 성공한 파일 추가
      completedFiles = [...completedFiles, {
        path: result.originalPath,
        subtitlePath: result.subtitlePath,
        date: new Date().toLocaleString()
      }];
      
      // 처리 중인 파일에서 제거
      processingFiles = processingFiles.filter(f => f.path !== result.originalPath);
    } else {
      // 실패한 파일 추가
      failedFiles = [...failedFiles, {
        path: result.originalPath,
        error: result.error,
        date: new Date().toLocaleString()
      }];
      
      // 처리 중인 파일에서 제거
      processingFiles = processingFiles.filter(f => f.path !== result.originalPath);
    }
    
    // 선택 초기화
    selectedFile = null;
  }
  
  // 자동 처리 완료 처리
  function handleProcessComplete(event) {
    handleDownloadComplete(event); // 기본적으로 다운로드 완료와 동일하게 처리
  }
  
  // 배치 처리 시작
  async function startBatchProcess(files) {
    if (!files || files.length === 0) {
      return;
    }
    
    batchProcessing = true;
    batchProgress = 0;
    
    // 모든 파일을 처리 대기 목록에 추가
    processingFiles = files.map(file => ({
      path: file,
      status: '대기 중'
    }));
    
    // 파일들을 순차적으로 처리
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      currentBatchFile = file.split('/').pop();
      
      // 현재 파일 상태 업데이트
      processingFiles = processingFiles.map(f => 
        f.path === file ? { ...f, status: '처리 중' } : f
      );
      
      // 다운로드 API 호출
      try {
        const response = await fetch('/api/auto_process_subtitle', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            media_path: file,
            language: 'ko', // 기본 언어는 한국어
            use_multilingual: true,
            languages: ['ko', 'en'] // 한국어와 영어 모두 시도
          })
        });
        
        if (!response.ok) {
          throw new Error('API 요청 실패');
        }
        
        const result = await response.json();
        
        if (result.success) {
          // 성공한 파일 기록
          completedFiles = [...completedFiles, {
            path: file,
            subtitlePath: result.subtitle_path,
            adjusted: result.adjusted,
            offset: result.offset,
            date: new Date().toLocaleString()
          }];
          
          // 처리 중인 파일 상태 업데이트
          processingFiles = processingFiles.map(f => 
            f.path === file ? { ...f, status: '완료' } : f
          );
        } else {
          // 실패한 파일 기록
          failedFiles = [...failedFiles, {
            path: file,
            error: result.error || '알 수 없는 오류',
            date: new Date().toLocaleString()
          }];
          
          // 처리 중인 파일 상태 업데이트
          processingFiles = processingFiles.map(f => 
            f.path === file ? { ...f, status: '실패' } : f
          );
        }
      } catch (error) {
        // 오류 발생 시 기록
        failedFiles = [...failedFiles, {
          path: file,
          error: error.message || '알 수 없는 오류',
          date: new Date().toLocaleString()
        }];
        
        // 처리 중인 파일 상태 업데이트
        processingFiles = processingFiles.map(f => 
          f.path === file ? { ...f, status: '실패' } : f
        );
      }
      
      // 진행률 업데이트
      batchProgress = Math.round(((i + 1) / files.length) * 100);
    }
    
    batchProcessing = false;
    currentBatchFile = '';
  }
  
  // 배치 처리 시작 핸들러
  function handleBatchProcess() {
    const files = document.querySelectorAll('#file-list tbody tr input[type="checkbox"]:checked');
    const filePaths = Array.from(files).map(checkbox => {
      const row = checkbox.closest('tr');
      return row.getAttribute('data-path');
    }).filter(Boolean);
    
    if (filePaths.length === 0) {
      alert('처리할 파일을 선택해주세요.');
      return;
    }
    
    startBatchProcess(filePaths);
  }
  
  // 파일 목록 필터링
  function getFilteredProcessingFiles() {
    if (showCompletedOnly) {
      return [];
    }
    return processingFiles;
  }
</script>

<svelte:head>
  <title>자막 다운로드 - 자막 인덱서</title>
</svelte:head>

<div class="p-4">
  <!-- 페이지 헤더 -->
  <header class="mb-6">
    <h1 class="text-2xl font-bold">자막 자동 다운로드</h1>
    <p class="text-gray-600 dark:text-gray-400 mt-1">
      AI 기반 자막 자동 검색 / 다운로드 / 싱크 검증 / 조정 시스템
    </p>
  </header>
  
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- 왼쪽 사이드바: 디렉토리 탐색기 -->
    <div class="md:col-span-1 space-y-6">
      <DirectoryBrowser />
      
      <!-- 처리 현황 -->
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">처리 현황</h2>
        
        <div class="flex justify-between mb-2">
          <div>처리 완료: <span class="font-medium">{completedFiles.length}</span></div>
          <div>실패: <span class="font-medium text-red-600">{failedFiles.length}</span></div>
        </div>
        
        <!-- 진행 중인 일괄 처리 -->
        {#if batchProcessing}
          <div class="mb-4">
            <div class="mb-1 flex justify-between text-sm">
              <span>처리 중: {currentBatchFile}</span>
              <span>{batchProgress}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div 
                class="bg-blue-600 h-2.5 rounded-full" 
                style="width: {batchProgress}%"
              ></div>
            </div>
          </div>
        {/if}
        
        <!-- 처리 중/완료된 파일 목록 -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-medium">파일 목록</h3>
            <div class="flex items-center">
              <input 
                type="checkbox" 
                id="show-completed" 
                class="mr-2" 
                bind:checked={showCompletedOnly}
              />
              <label for="show-completed" class="text-sm">완료된 항목만 표시</label>
            </div>
          </div>
          
          <div class="max-h-60 overflow-y-auto border rounded">
            {#if (!showCompletedOnly && processingFiles.length === 0) && completedFiles.length === 0}
              <div class="p-3 text-center text-gray-500">처리된 파일이 없습니다.</div>
            {:else}
              <div class="divide-y">
                {#if !showCompletedOnly}
                  {#each processingFiles as file}
                    <div class="p-2 text-sm">
                      <div class="flex justify-between">
                        <span class="truncate">{file.path.split('/').pop()}</span>
                        <span class={file.status === '완료' ? 'text-green-600' : file.status === '실패' ? 'text-red-600' : 'text-blue-600'}>
                          {file.status}
                        </span>
                      </div>
                    </div>
                  {/each}
                {/if}
                
                {#each completedFiles as file}
                  <div class="p-2 text-sm">
                    <div class="flex justify-between">
                      <span class="truncate">{file.path.split('/').pop()}</span>
                      <span class="text-green-600">완료</span>
                    </div>
                    <div class="text-xs text-gray-500">{file.date}</div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        </div>
        
        <!-- 배치 처리 버튼 -->
        <button 
          class="btn btn-primary w-full" 
          on:click={handleBatchProcess} 
          disabled={batchProcessing}
        >
          {#if batchProcessing}
            <span class="inline-block animate-spin mr-2">⟳</span>
          {/if}
          선택한 모든 파일 자동 처리
        </button>
      </div>
    </div>
    
    <!-- 오른쪽 컨텐츠: 파일 목록 + 다운로더 -->
    <div class="md:col-span-2 space-y-6">
      <!-- 파일 목록 테이블 -->
      <MediaFilesTable on:selectionChange={handleFileSelect} />
      
      <!-- 자막 다운로더 -->
      {#if selectedFile}
        <SubtitleDownloader 
          mediaPath={selectedFile} 
          on:downloadComplete={handleDownloadComplete}
          on:processComplete={handleProcessComplete}
        />
      {:else}
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">자막 자동 다운로드</h2>
          <p class="text-center p-4 text-gray-500">
            자막을 다운로드할 미디어 파일을 선택해주세요.
          </p>
        </div>
      {/if}
      
      <!-- 실패한 파일 목록 -->
      {#if failedFiles.length > 0}
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">실패한 파일</h2>
          
          <div class="space-y-2">
            {#each failedFiles as file}
              <div class="p-3 bg-red-50 dark:bg-red-900 dark:bg-opacity-20 text-red-800 dark:text-red-200 rounded text-sm">
                <div class="font-medium">{file.path.split('/').pop()}</div>
                <div class="mt-1">{file.error}</div>
                <div class="text-xs text-gray-500 mt-1">{file.date}</div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  </div>
</div> 