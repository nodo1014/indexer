<script>
  import { onMount } from 'svelte';
  import DirectoryBrowser from '$lib/components/DirectoryBrowser.svelte';
  import MediaFilesTable from '$lib/components/MediaFilesTable.svelte';
  import JobStatusPanel from '$lib/components/JobStatusPanel.svelte';
  import { runWhisper } from '$lib/api';

  // 선택된 파일 목록
  let selectedFiles = [];
  let whisperLanguage = 'ko';
  let whisperModel = 'small';
  let isRunningWhisper = false;
  let whisperError = null;

  // 선택 파일 변경 핸들러
  function handleSelectionChange(event) {
    selectedFiles = event.detail;
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
      await runWhisper(selectedFiles, whisperLanguage, whisperModel);
      selectedFiles = [];
    } catch (error) {
      whisperError = error.message || 'Whisper 실행 중 오류가 발생했습니다.';
      console.error('Whisper 실행 오류:', error);
    } finally {
      isRunningWhisper = false;
    }
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
  <!-- 왼쪽 사이드바: 디렉토리 탐색기 + 작업 현황 -->
  <div class="md:col-span-1 space-y-6">
    <DirectoryBrowser />
    <JobStatusPanel />
  </div>
  
  <!-- 오른쪽 컨텐츠: 파일 목록 + 컨트롤 패널 -->
  <div class="md:col-span-2 space-y-6">
    <!-- 파일 목록 테이블 -->
    <MediaFilesTable on:selectionChange={handleSelectionChange} />
    
    <!-- Whisper 컨트롤 패널 -->
    {#if selectedFiles.length > 0}
      <div class="card">
        <h3 class="text-lg font-semibold mb-4">Whisper 자막 생성</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <!-- 언어 선택 -->
          <div>
            <label for="language" class="label">언어 선택</label>
            <select id="language" class="input" bind:value={whisperLanguage}>
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
            <select id="model" class="input" bind:value={whisperModel}>
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
  </div>
</div>
