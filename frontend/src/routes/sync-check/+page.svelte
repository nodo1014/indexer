<script>
  import { onMount } from 'svelte';
  import SubtitleSyncChecker from '$lib/components/SubtitleSyncChecker.svelte';
  import { searchMediaFiles } from '$lib/api';
  import { currentPath } from '$lib/stores/directory';
  
  // 상태 관리
  let files = [];
  let isLoading = false;
  let error = null;
  let selectedMediaFile = null;
  let selectedSubtitleFile = null;
  
  // 목록에서 미디어 파일 선택
  function selectMediaFile(file) {
    selectedMediaFile = file;
    
    // 자동으로 관련된 자막 파일 선택 시도
    if (file.subtitle_files && file.subtitle_files.length > 0) {
      selectedSubtitleFile = file.subtitle_files[0];
    } else {
      selectedSubtitleFile = null;
    }
  }
  
  // 목록에서 자막 파일 선택
  function selectSubtitleFile(path) {
    selectedSubtitleFile = path;
  }
  
  // 싱크 조정 성공 핸들러
  function handleSyncAdjusted(event) {
    const { adjustedPath } = event.detail;
    
    // 선택된 미디어 파일의 자막 목록에 조정된 자막 추가
    if (selectedMediaFile && adjustedPath) {
      if (!selectedMediaFile.subtitle_files) {
        selectedMediaFile.subtitle_files = [];
      }
      
      if (!selectedMediaFile.subtitle_files.includes(adjustedPath)) {
        selectedMediaFile.subtitle_files.push(adjustedPath);
      }
      
      // 조정된 자막을 현재 선택된 자막으로 변경
      selectedSubtitleFile = adjustedPath;
    }
  }
  
  // 파일 목록 로드
  async function loadFiles() {
    if (!$currentPath) return;
    
    isLoading = true;
    error = null;
    
    try {
      // 자막 있는 파일도 모두 포함하여 검색
      const result = await searchMediaFiles($currentPath, true);
      files = result.files;
      selectedMediaFile = null;
      selectedSubtitleFile = null;
    } catch (err) {
      error = err.message || '파일 목록을 불러오는 중 오류가 발생했습니다.';
      files = [];
    } finally {
      isLoading = false;
    }
  }
  
  // 현재 경로가 변경될 때마다 파일 목록 다시 로드
  $: $currentPath && loadFiles();
  
  // 파일 크기 포맷팅 (바이트 → 읽기 쉬운 형식)
  function formatFileSize(size) {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }
  
  // 페이지 마운트 시 파일 목록 로드
  onMount(() => {
    if ($currentPath) {
      loadFiles();
    }
  });
</script>

<div class="p-4">
  <h1 class="text-2xl font-bold mb-6">자막 싱크 검증 및 조정</h1>
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- 왼쪽: 파일 목록 및 선택 -->
    <div class="space-y-6">
      <!-- 미디어 파일 선택 -->
      <div class="card">
        <h2 class="text-lg font-semibold mb-4">미디어 파일 선택</h2>
        
        <!-- 로딩 인디케이터 -->
        {#if isLoading}
          <div class="p-8 text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-gray-600">파일 목록 로딩 중...</p>
          </div>
        
        <!-- 에러 메시지 -->
        {:else if error}
          <div class="p-4 bg-red-100 text-red-800 rounded">
            <p>{error}</p>
            <button class="btn btn-sm mt-2" on:click={loadFiles}>
              다시 시도
            </button>
          </div>
        
        <!-- 파일 없음 -->
        {:else if files.length === 0}
          <div class="p-8 text-center text-gray-500 border rounded">
            <p>{$currentPath ? '이 폴더에는 미디어 파일이 없습니다.' : '폴더를 선택해주세요.'}</p>
          </div>
        
        <!-- 미디어 파일 목록 -->
        {:else}
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>파일명</th>
                  <th class="w-20">타입</th>
                  <th class="w-20">크기</th>
                  <th class="w-16">자막</th>
                </tr>
              </thead>
              <tbody>
                {#each files as file}
                  <tr 
                    class={selectedMediaFile === file ? 'bg-blue-50 dark:bg-blue-900 dark:bg-opacity-20' : ''}
                    on:click={() => selectMediaFile(file)}
                    style="cursor: pointer;"
                  >
                    <td class="truncate" title={file.name}>
                      {file.name}
                    </td>
                    <td>
                      <span class={file.type === 'video' ? 'text-blue-600' : 'text-green-600'}>
                        {file.type === 'video' ? '비디오' : '오디오'}
                      </span>
                    </td>
                    <td>{formatFileSize(file.size)}</td>
                    <td>
                      {#if file.has_subtitle}
                        <span class="text-green-600">{file.subtitle_files?.length || 0}개</span>
                      {:else}
                        <span class="text-red-600">없음</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
      
      <!-- 자막 파일 선택 (미디어 파일 선택 시) -->
      {#if selectedMediaFile && selectedMediaFile.has_subtitle}
        <div class="card">
          <h2 class="text-lg font-semibold mb-4">자막 파일 선택</h2>
          
          <div class="space-y-2">
            {#each selectedMediaFile.subtitle_files || [] as subtitlePath}
              <div 
                class="p-2 border rounded flex items-center justify-between {selectedSubtitleFile === subtitlePath ? 'bg-blue-50 border-blue-200 dark:bg-blue-900 dark:bg-opacity-20 dark:border-blue-800' : ''}"
                on:click={() => selectSubtitleFile(subtitlePath)}
                style="cursor: pointer;"
              >
                <span class="truncate">{subtitlePath.split('/').pop()}</span>
                <span class="text-xs text-gray-500">{subtitlePath.split('.').pop().toUpperCase()}</span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    </div>
    
    <!-- 오른쪽: 싱크 검증 도구 -->
    <div>
      <SubtitleSyncChecker 
        mediaPath={selectedMediaFile?.path || ''}
        subtitlePath={selectedSubtitleFile || ''}
        on:syncAdjusted={handleSyncAdjusted}
      />
    </div>
  </div>
</div> 