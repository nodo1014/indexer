<script lang="ts">
  import { onMount } from 'svelte';
  import DirectoryBrowser from '$lib/components/DirectoryBrowser.svelte';
  import MediaFilesTable from '$lib/components/MediaFilesTable.svelte';
  import JobStatusPanel from '$lib/components/JobStatusPanel.svelte';
  import SettingsPanel from '$lib/components/SettingsPanel.svelte';
  import { runWhisper, searchMediaFiles } from '$lib/api';
  import { whisperSettings } from '$lib/stores/settings';
  import { currentPath } from '$lib/stores/directory';

  // 선택된 파일 목록
  let selectedFiles: string[] = [];
  let isRunningWhisper = false;
  let whisperError: string | null = null;
  let showSettings = false;
  
  // 미디어 파일 로드 상태
  let isLoadingFiles = false;
  let showMediaFiles = false;
  let searchPath = '';

  // 선택 파일 변경 핸들러
  function handleSelectionChange(event: CustomEvent<string[]>) {
    selectedFiles = event.detail;
    
    // 자동 시작 설정이 활성화되어 있고, 파일이 선택된 경우 자동으로 Whisper 실행
    if ($whisperSettings.autoStart && selectedFiles.length > 0) {
      handleRunWhisper();
    }
  }

  // Whisper 실행
  async function handleRunWhisper() {
    if (selectedFiles.length === 0) {
      whisperError = '선택된 파일이 없습니다.';
      return;
    }

    isRunningWhisper = true;
    whisperError = null;

    try {
      await runWhisper(selectedFiles, $whisperSettings.language, $whisperSettings.model);
      selectedFiles = [];
    } catch (error: unknown) {
      whisperError = error instanceof Error ? error.message : 'Whisper 실행 중 오류가 발생했습니다.';
      console.error('Whisper 실행 오류:', error);
    } finally {
      isRunningWhisper = false;
    }
  }
  
  // 설정 패널 토글
  function toggleSettings() {
    showSettings = !showSettings;
  }
  
  // DirectoryBrowser에서 미디어 파일 검색 요청을 처리
  async function handleSearchMedia(event: CustomEvent<{path: string}>) {
    searchPath = event.detail.path;
    isLoadingFiles = true;
    showMediaFiles = true;
    
    try {
      // MediaFilesTable 컴포넌트가 searchPath 값을 감지하여 자동으로 로드하므로
      // 여기서는 상태 값만 설정합니다.
    } catch (error: unknown) {
      console.error('미디어 파일 검색 오류:', error);
    } finally {
      isLoadingFiles = false;
    }
  }
</script>

<svelte:head>
  <title>AI 자막 생성 - 자막 인덱서</title>
</svelte:head>

<div class="p-4">
  <!-- 페이지 헤더 -->
  <header class="flex justify-between items-center mb-6">
    <h1 class="text-2xl font-bold">AI 자막 생성</h1>
    
    <button 
      class="btn btn-secondary flex items-center" 
      on:click={toggleSettings}
    >
      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
      </svg>
      설정
    </button>
  </header>
  
  {#if showSettings}
    <!-- 설정 패널 -->
    <div class="mb-6">
      <SettingsPanel />
    </div>
  {/if}
  
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- 왼쪽 사이드바: 디렉토리 탐색기 + 작업 현황 -->
    <div class="md:col-span-1 space-y-6">
      <DirectoryBrowser on:searchMedia={handleSearchMedia} />
      <JobStatusPanel />
    </div>
    
    <!-- 오른쪽 컨텐츠: 파일 목록 + 컨트롤 패널 -->
    <div class="md:col-span-2 space-y-6">
      <!-- Whisper 컨트롤 패널 - 위치 변경: 미디어 파일 테이블 위로 이동 -->
      {#if selectedFiles.length > 0}
        <div class="card">
          <h3 class="text-lg font-semibold mb-4">Whisper 자막 생성</h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <!-- 언어 선택 -->
            <div>
              <label for="language" class="label">언어 선택</label>
              <select id="language" class="input" bind:value={$whisperSettings.language}>
                <option value="ko">한국어</option>
                <option value="en">영어</option>
                <option value="ja">일본어</option>
                <option value="zh">중국어</option>
                <option value="auto">자동 감지</option>
              </select>
            </div>
            
            <!-- 모델 선택 -->
            <div>
              <label for="model" class="label">모델 선택</label>
              <select id="model" class="input" bind:value={$whisperSettings.model}>
                <option value="tiny">Tiny (빠름, 낮은 정확도)</option>
                <option value="base">Base (기본)</option>
                <option value="small">Small (권장)</option>
                <option value="medium">Medium (높은 정확도, 느림)</option>
                <option value="large">Large (최고 정확도, 매우 느림)</option>
              </select>
            </div>
          </div>
          
          {#if whisperError}
            <div class="p-3 mb-4 bg-red-100 text-red-800 rounded">
              {whisperError}
            </div>
          {/if}
          
          <div class="flex justify-end">
            <button 
              class="btn btn-primary" 
              on:click={handleRunWhisper} 
              disabled={isRunningWhisper || selectedFiles.length === 0}
            >
              {#if isRunningWhisper}
                <span class="inline-block animate-spin mr-2">⟳</span>
              {/if}
              Whisper 자막 생성
            </button>
          </div>
        </div>
      {/if}

      <!-- 파일 목록 테이블 - 검색 시에만 표시 -->
      {#if showMediaFiles}
        <MediaFilesTable 
          path={searchPath} 
          on:selectionChange={handleSelectionChange} 
        />
      {:else}
        <div class="card p-6 text-center text-gray-500">
          <p>왼쪽 디렉토리 탐색기에서 폴더를 선택한 후 미디어 파일 검색 버튼을 클릭하세요.</p>
        </div>
      {/if}
      
    </div>
  </div>
</div> 