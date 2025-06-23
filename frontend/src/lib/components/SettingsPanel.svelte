<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    whisperSettings, 
    uiSettings, 
    filterSettings,
    systemSettings,
    updateWhisperSettings,
    updateUISettings,
    updateFilterSettings,
    updateSystemSettings
  } from '$lib/stores/settings';
  import { getSystemSettings, updateSystemSettings as updateSystemSettingsAPI } from '$lib/api';
  
  // 시스템 설정 로딩 상태
  let isLoadingSystemSettings = false;
  let isSavingSystemSettings = false;
  let systemSettingsError = '';
  let systemSettingsSuccess = '';
  
  // 폼 입력 값
  let nasMediaPath = '';
  let openSubtitlesApiKey = '';
  
  // 시스템 설정을 서버에서 로드
  async function loadSystemSettings() {
    isLoadingSystemSettings = true;
    systemSettingsError = '';
    
    try {
      const settings = await getSystemSettings();
      nasMediaPath = settings.nas_media_path || '';
      openSubtitlesApiKey = settings.opensubtitles_api_key || '';
      
      // 로컬 설정 업데이트
      updateSystemSettings({
        nasMediaPath,
        openSubtitlesApiKey
      });
    } catch (error) {
      console.error('시스템 설정 로드 오류:', error);
      systemSettingsError = '서버 설정을 불러오는 중 오류가 발생했습니다.';
    } finally {
      isLoadingSystemSettings = false;
    }
  }
  
  // 시스템 설정을 서버에 저장
  async function saveSystemSettings() {
    isSavingSystemSettings = true;
    systemSettingsError = '';
    systemSettingsSuccess = '';
    
    try {
      await updateSystemSettingsAPI({
        nas_media_path: nasMediaPath,
        opensubtitles_api_key: openSubtitlesApiKey
      });
      
      // 로컬 설정 업데이트
      updateSystemSettings({
        nasMediaPath,
        openSubtitlesApiKey
      });
      
      systemSettingsSuccess = '설정이 저장되었습니다.';
      
      // 3초 후 성공 메시지 숨김
      setTimeout(() => {
        systemSettingsSuccess = '';
      }, 3000);
    } catch (error) {
      console.error('시스템 설정 저장 오류:', error);
      systemSettingsError = '설정을 저장하는 중 오류가 발생했습니다.';
    } finally {
      isSavingSystemSettings = false;
    }
  }
  
  // Whisper 설정 변경 핸들러
  const handleWhisperLanguageChange = (event: Event) => {
    updateWhisperSettings({ language: (event.target as HTMLSelectElement).value });
  };
  
  const handleWhisperModelChange = (event: Event) => {
    updateWhisperSettings({ model: (event.target as HTMLSelectElement).value });
  };
  
  const handleWhisperAutoStartChange = (event: Event) => {
    updateWhisperSettings({ autoStart: (event.target as HTMLInputElement).checked });
  };
  
  // UI 설정 변경 핸들러
  const handleDarkModeChange = (event: Event) => {
    updateUISettings({ darkMode: (event.target as HTMLInputElement).checked });
  };
  
  const handleRowsPerPageChange = (event: Event) => {
    updateUISettings({ tableRowsPerPage: Number((event.target as HTMLSelectElement).value) });
  };
  
  const handleShowHiddenFilesChange = (event: Event) => {
    updateUISettings({ showHiddenFiles: (event.target as HTMLInputElement).checked });
  };
  
  // 필터 설정 변경 핸들러
  const handleShowWithSubtitleChange = (event: Event) => {
    updateFilterSettings({ showWithSubtitle: (event.target as HTMLInputElement).checked });
  };
  
  const handleVideoOnlyChange = (event: Event) => {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked && $filterSettings.audioOnly) {
      updateFilterSettings({ 
        videoOnly: true, 
        audioOnly: false 
      });
    } else {
      updateFilterSettings({ videoOnly: checked });
    }
  };
  
  const handleAudioOnlyChange = (event: Event) => {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked && $filterSettings.videoOnly) {
      updateFilterSettings({ 
        audioOnly: true, 
        videoOnly: false 
      });
    } else {
      updateFilterSettings({ audioOnly: checked });
    }
  };
  
  // 시스템 설정 변경 핸들러
  const handleNasMediaPathChange = (event: Event) => {
    nasMediaPath = (event.target as HTMLInputElement).value;
  };
  
  const handleOpenSubtitlesApiKeyChange = (event: Event) => {
    openSubtitlesApiKey = (event.target as HTMLInputElement).value;
  };
  
  // 초기 로드
  onMount(() => {
    loadSystemSettings();
  });
</script>

<div class="settings-panel card">
  <h2 class="text-lg font-semibold mb-4">환경설정</h2>
  
  <!-- 시스템 설정 섹션 -->
  <section class="mb-6">
    <h3 class="text-md font-medium mb-3 border-b pb-2">시스템 설정</h3>
    
    {#if systemSettingsError}
      <div class="bg-red-100 border border-red-200 text-red-700 px-4 py-2 rounded mb-4">
        {systemSettingsError}
      </div>
    {/if}
    
    {#if systemSettingsSuccess}
      <div class="bg-green-100 border border-green-200 text-green-700 px-4 py-2 rounded mb-4">
        {systemSettingsSuccess}
      </div>
    {/if}
    
    <div class="space-y-4">
      <!-- NAS 경로 설정 -->
      <div>
        <label for="nas-media-path" class="label">NAS 미디어 경로</label>
        <input 
          type="text" 
          id="nas-media-path" 
          class="input" 
          bind:value={nasMediaPath} 
          on:change={handleNasMediaPathChange}
          placeholder="/mnt/nas"
          disabled={isLoadingSystemSettings || isSavingSystemSettings}
        />
        <p class="text-xs text-gray-500 mt-1">NAS 미디어 파일이 저장된 경로를 입력하세요.</p>
      </div>
      
      <!-- API 키 설정 -->
      <div>
        <label for="opensubtitles-api-key" class="label">OpenSubtitles API 키</label>
        <input 
          type="text" 
          id="opensubtitles-api-key" 
          class="input" 
          bind:value={openSubtitlesApiKey} 
          on:change={handleOpenSubtitlesApiKeyChange}
          placeholder="API 키를 입력하세요"
          disabled={isLoadingSystemSettings || isSavingSystemSettings}
        />
        <p class="text-xs text-gray-500 mt-1">
          <a href="https://www.opensubtitles.com/en/users/sign_up" target="_blank" class="text-blue-500 hover:underline">
            OpenSubtitles 사이트
          </a>에서 API 키를 발급받으세요.
        </p>
      </div>
      
      <div class="flex justify-end pt-2">
        <button 
          class="btn btn-primary" 
          on:click={saveSystemSettings}
          disabled={isLoadingSystemSettings || isSavingSystemSettings}
        >
          {#if isSavingSystemSettings}
            <span class="inline-block animate-spin mr-2">⟳</span>
          {/if}
          저장
        </button>
      </div>
    </div>
  </section>
  
  <!-- Whisper 설정 섹션 -->
  <section class="mb-6">
    <h3 class="text-md font-medium mb-3 border-b pb-2">Whisper 설정</h3>
    
    <div class="space-y-4">
      <!-- 언어 설정 -->
      <div>
        <label for="whisper-language" class="label">기본 언어</label>
        <select 
          id="whisper-language" 
          class="input" 
          value={$whisperSettings.language} 
          on:change={handleWhisperLanguageChange}
        >
          <option value="ko">한국어</option>
          <option value="en">영어</option>
          <option value="ja">일본어</option>
          <option value="zh">중국어</option>
          <option value="auto">자동 감지</option>
        </select>
      </div>
      
      <!-- 모델 설정 -->
      <div>
        <label for="whisper-model" class="label">기본 모델</label>
        <select 
          id="whisper-model" 
          class="input" 
          value={$whisperSettings.model} 
          on:change={handleWhisperModelChange}
        >
          <option value="tiny">Tiny (빠름, 낮은 정확도)</option>
          <option value="base">Base (기본)</option>
          <option value="small">Small (권장)</option>
          <option value="medium">Medium (높은 정확도, 느림)</option>
          <option value="large">Large (최고 정확도, 매우 느림)</option>
        </select>
      </div>
      
      <!-- 자동 시작 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="auto-start" 
          class="mr-2"
          checked={$whisperSettings.autoStart} 
          on:change={handleWhisperAutoStartChange} 
        />
        <label for="auto-start">파일 선택 시 자동으로 Whisper 시작</label>
      </div>
    </div>
  </section>
  
  <!-- UI 설정 섹션 -->
  <section class="mb-6">
    <h3 class="text-md font-medium mb-3 border-b pb-2">UI 설정</h3>
    
    <div class="space-y-4">
      <!-- 다크 모드 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="dark-mode" 
          class="mr-2"
          checked={$uiSettings.darkMode} 
          on:change={handleDarkModeChange} 
        />
        <label for="dark-mode">다크 모드</label>
      </div>
      
      <!-- 테이블 행 개수 설정 -->
      <div>
        <label for="rows-per-page" class="label">페이지 당 행 수</label>
        <select 
          id="rows-per-page" 
          class="input" 
          value={$uiSettings.tableRowsPerPage} 
          on:change={handleRowsPerPageChange}
        >
          <option value="5">5</option>
          <option value="10">10</option>
          <option value="20">20</option>
          <option value="50">50</option>
        </select>
      </div>
      
      <!-- 숨김 파일 표시 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="show-hidden-files" 
          class="mr-2"
          checked={$uiSettings.showHiddenFiles} 
          on:change={handleShowHiddenFilesChange} 
        />
        <label for="show-hidden-files">숨김 파일 표시</label>
      </div>
    </div>
  </section>
  
  <!-- 필터 설정 섹션 -->
  <section>
    <h3 class="text-md font-medium mb-3 border-b pb-2">필터 설정</h3>
    
    <div class="space-y-4">
      <!-- 자막 있는 파일 표시 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="show-with-subtitle" 
          class="mr-2"
          checked={$filterSettings.showWithSubtitle} 
          on:change={handleShowWithSubtitleChange} 
        />
        <label for="show-with-subtitle">자막 있는 파일도 함께 표시</label>
      </div>
      
      <!-- 비디오만 표시 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="video-only" 
          class="mr-2"
          checked={$filterSettings.videoOnly} 
          on:change={handleVideoOnlyChange} 
        />
        <label for="video-only">비디오 파일만 표시</label>
      </div>
      
      <!-- 오디오만 표시 설정 -->
      <div class="flex items-center">
        <input 
          type="checkbox" 
          id="audio-only" 
          class="mr-2"
          checked={$filterSettings.audioOnly} 
          on:change={handleAudioOnlyChange} 
        />
        <label for="audio-only">오디오 파일만 표시</label>
      </div>
    </div>
  </section>
</div> 