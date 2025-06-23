<script lang="ts">
  import { onMount } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import { searchMediaFiles, downloadSubtitle, autoProcessSubtitle } from '$lib/api';
  
  // 이벤트 디스패처 생성
  const dispatch = createEventDispatcher();
  
  // 프로퍼티 정의
  export let mediaPath = ''; // 미디어 파일 경로
  
  // 상태 관리
  let isDownloading = false;
  let isProcessing = false;
  let downloadProgress = 0;
  let currentOperation = '';
  let error: string | null = null;
  let downloadResult: any = null;
  let selectedLanguage = 'ko';
  let useMultilingual = false;
  let supportedLanguages = [
    { code: 'ko', name: '한국어' },
    { code: 'en', name: '영어' },
    { code: 'ja', name: '일본어' },
    { code: 'zh', name: '중국어' }
  ];
  let selectedLanguages = ['ko', 'en'];
  
  // 초기화
  onMount(() => {
    // 웹소켓 이벤트 리스너 설정 등 초기화 작업
  });
  
  // 자막 다운로드 시작
  async function startDownload() {
    if (!mediaPath) {
      error = '미디어 파일이 선택되지 않았습니다.';
      return;
    }
    
    isDownloading = true;
    downloadProgress = 0;
    currentOperation = '자막 검색 중...';
    error = null;
    
    try {
      // API 라이브러리 함수 사용
      downloadResult = await downloadSubtitle(
        mediaPath,
        selectedLanguage,
        useMultilingual,
        useMultilingual ? selectedLanguages : [selectedLanguage]
      );
      
      // 성공 이벤트 발생
      dispatch('downloadComplete', { 
        originalPath: mediaPath,
        subtitlePath: downloadResult.subtitle_path,
        success: true
      });
      
    } catch (err: any) {
      error = err.message || '자막 다운로드 중 오류가 발생했습니다.';
      dispatch('downloadComplete', { 
        originalPath: mediaPath,
        success: false,
        error: error
      });
    } finally {
      isDownloading = false;
      downloadProgress = 100;
    }
  }
  
  // 자동 다운로드 및 싱크 체크 시작 (원클릭 자동화)
  async function startAutoProcess() {
    if (!mediaPath) {
      error = '미디어 파일이 선택되지 않았습니다.';
      return;
    }
    
    isProcessing = true;
    downloadProgress = 0;
    currentOperation = '자막 자동 처리 시작...';
    error = null;
    
    try {
      // API 라이브러리 함수 사용하여 모든 과정 자동 처리
      const result = await autoProcessSubtitle(
        mediaPath,
        selectedLanguage,
        useMultilingual,
        useMultilingual ? selectedLanguages : [selectedLanguage]
      );
      
      downloadProgress = 100;
      currentOperation = '처리 완료';
      
      // 성공 이벤트 발생
      dispatch('processComplete', { 
        originalPath: mediaPath,
        subtitlePath: result.subtitle_path,
        syncStatus: result.sync_status,
        offset: result.offset,
        adjusted: result.adjusted || false,
        success: true
      });
      
    } catch (err: any) {
      error = err.message || '자막 처리 중 오류가 발생했습니다.';
      downloadProgress = 100;
      currentOperation = '오류 발생';
      
      dispatch('processComplete', { 
        originalPath: mediaPath,
        success: false,
        error: error
      });
    } finally {
      isProcessing = false;
    }
  }
  
  // 다중 언어 선택 토글
  function toggleLanguage(lang: string) {
    if (selectedLanguages.includes(lang)) {
      // 이미 선택된 경우 제거 (최소 1개는 유지)
      if (selectedLanguages.length > 1) {
        selectedLanguages = selectedLanguages.filter(l => l !== lang);
      }
    } else {
      // 선택되지 않은 경우 추가
      selectedLanguages = [...selectedLanguages, lang];
    }
  }
</script>

<div>
  <!-- 파일 정보 -->
  {#if mediaPath}
    <div class="bg-gray-100 dark:bg-gray-700 p-3 rounded">
      <div class="flex items-center text-sm">
        <span class="font-medium mr-2">미디어:</span>
        <span class="truncate">{mediaPath.split('/').pop()}</span>
      </div>
    </div>
  {/if}
  
  <!-- 오류 메시지 -->
  {#if error}
    <div class="mt-4 p-3 bg-red-100 text-red-800 rounded">
      {error}
    </div>
  {/if}
  
  <!-- 다운로드 진행 상태 -->
  {#if isDownloading || isProcessing}
    <div class="mt-4">
      <div class="mb-1 flex justify-between">
        <span class="text-sm">{currentOperation}</span>
        <span class="text-sm">{downloadProgress}%</span>
      </div>
      <div class="relative pt-1">
        <div class="overflow-hidden h-2 text-xs flex rounded bg-gray-200">
          <div 
            style="width:{downloadProgress}%" 
            class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500 transition-all duration-300"
          ></div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- 설정 패널 -->
  <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- 언어 선택 -->
    <div>
      <label class="label">기본 언어</label>
      <select 
        class="input w-full"
        bind:value={selectedLanguage}
        disabled={isDownloading || isProcessing}
      >
        {#each supportedLanguages as lang}
          <option value={lang.code}>{lang.name}</option>
        {/each}
      </select>
    </div>
    
    <!-- 다중 언어 지원 -->
    <div>
      <label class="inline-flex items-center mt-3">
        <input 
          type="checkbox" 
          bind:checked={useMultilingual} 
          class="form-checkbox h-5 w-5 text-blue-600"
          disabled={isDownloading || isProcessing}
        />
        <span class="ml-2 text-gray-700 dark:text-gray-300">다중 언어 검색</span>
      </label>
      
      {#if useMultilingual}
        <div class="mt-2 flex flex-wrap gap-2">
          {#each supportedLanguages as lang}
            <button 
              type="button"
              class="px-2 py-1 text-xs rounded {selectedLanguages.includes(lang.code) ? 'bg-blue-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}"
              on:click={() => toggleLanguage(lang.code)}
              disabled={isDownloading || isProcessing}
            >
              {lang.name}
            </button>
          {/each}
        </div>
        <p class="text-xs text-gray-500 mt-1">선택한 언어 순서대로 검색합니다.</p>
      {/if}
    </div>
  </div>
  
  <!-- 버튼 영역 -->
  <div class="mt-6 flex justify-end space-x-4">
    <button 
      class="btn btn-primary {(isDownloading || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}"
      on:click={startDownload}
      disabled={isDownloading || isProcessing || !mediaPath}
    >
      {#if isDownloading}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      자막 다운로드
    </button>
    
    <button 
      class="btn btn-secondary {(isDownloading || isProcessing) ? 'opacity-50 cursor-not-allowed' : ''}"
      on:click={startAutoProcess}
      disabled={isDownloading || isProcessing || !mediaPath}
    >
      {#if isProcessing}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      자동 자막 처리
    </button>
  </div>
  
  <!-- 다운로드 결과 -->
  {#if downloadResult && downloadResult.success && !isDownloading && !isProcessing}
    <div class="mt-4 p-3 bg-green-100 text-green-800 rounded">
      <p>자막 다운로드 완료!</p>
      {#if downloadResult.subtitle_path}
        <div class="mt-2">
          <a 
            href={`/download?path=${encodeURIComponent(downloadResult.subtitle_path)}`} 
            class="text-blue-600 hover:underline"
          >
            자막 파일 다운로드
          </a>
        </div>
      {/if}
      {#if downloadResult.adjusted}
        <p class="mt-1 text-sm">자막 싱크가 {downloadResult.offset.toFixed(2)}초 조정되었습니다.</p>
      {/if}
    </div>
  {/if}
</div> 