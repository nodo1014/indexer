<script>
  import { createEventDispatcher } from 'svelte';
  import { searchMediaFiles } from '$lib/api';
  import { currentPath } from '$lib/stores/directory';
  
  export let withSubtitle = false;
  
  // 데이터 상태
  let files = [];
  let isLoading = false;
  let error = null;
  let summary = {
    total_files: 0,
    video_count: 0,
    audio_count: 0,
    with_subtitle_count: 0,
    without_subtitle_count: 0
  };
  
  // 선택된 파일 관리
  let selectedFiles = [];
  
  // 이벤트 디스패처
  const dispatch = createEventDispatcher();
  
  // 파일 목록 로드
  async function loadFiles() {
    if (!$currentPath) return;
    
    isLoading = true;
    error = null;
    
    try {
      const result = await searchMediaFiles($currentPath, withSubtitle);
      files = result.files;
      summary = {
        total_files: result.total_files,
        video_count: result.video_count,
        audio_count: result.audio_count,
        with_subtitle_count: result.with_subtitle_count,
        without_subtitle_count: result.without_subtitle_count
      };
      selectedFiles = [];
    } catch (err) {
      error = err.message || '파일 목록을 불러오는 중 오류가 발생했습니다.';
      files = [];
    } finally {
      isLoading = false;
    }
  }
  
  // 현재 경로가 변경될 때마다 파일 목록 다시 로드
  $: $currentPath && loadFiles();
  
  // 전체 선택/해제
  function toggleSelectAll(event) {
    const checked = event.target.checked;
    if (checked) {
      selectedFiles = files
        .filter(file => !file.has_subtitle || withSubtitle)
        .map(file => file.path);
    } else {
      selectedFiles = [];
    }
    
    dispatch('selectionChange', selectedFiles);
  }
  
  // 개별 파일 선택/해제
  function toggleSelect(file, event) {
    const checked = event.target.checked;
    if (checked) {
      selectedFiles = [...selectedFiles, file.path];
    } else {
      selectedFiles = selectedFiles.filter(path => path !== file.path);
    }
    
    dispatch('selectionChange', selectedFiles);
  }
  
  // 파일 크기 포맷팅 (바이트 → 읽기 쉬운 형식)
  function formatFileSize(size) {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`;
    return `${(size / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  }
  
  // 수동으로 파일 목록 새로고침
  function refreshFiles() {
    loadFiles();
  }
</script>

<div class="media-files-table">
  <!-- 요약 정보 -->
  <div class="mb-4 flex justify-between items-center">
    <div>
      <h2 class="text-lg font-semibold">
        {withSubtitle ? '모든 미디어 파일' : '자막 없는 미디어 파일'}
      </h2>
      {#if summary.total_files > 0}
        <p class="text-sm text-gray-600">
          총 {summary.total_files}개 파일 (비디오: {summary.video_count}, 오디오: {summary.audio_count})
          {#if !withSubtitle}
            / 자막 없음: {summary.without_subtitle_count}
          {:else}
            / 자막 있음: {summary.with_subtitle_count}
          {/if}
        </p>
      {/if}
    </div>
    
    <button class="btn btn-secondary btn-sm" on:click={refreshFiles}>
      새로고침
    </button>
  </div>
  
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
      <button class="btn btn-sm mt-2" on:click={refreshFiles}>
        다시 시도
      </button>
    </div>
  
  <!-- 파일 없음 -->
  {:else if files.length === 0}
    <div class="p-8 text-center text-gray-500 border rounded">
      <p>{$currentPath ? '이 폴더에는' : '선택된 경로에는'} {withSubtitle ? '미디어 파일이' : '자막 없는 미디어 파일이'} 없습니다.</p>
    </div>
  
  <!-- 파일 목록 테이블 -->
  {:else}
    <div class="overflow-x-auto">
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-gray-100">
            <th class="p-2 text-left w-12">
              <input 
                type="checkbox" 
                on:change={toggleSelectAll} 
                checked={selectedFiles.length === files.filter(f => !f.has_subtitle || withSubtitle).length && files.length > 0}
              />
            </th>
            <th class="p-2 text-left">파일명</th>
            <th class="p-2 text-left w-24">타입</th>
            <th class="p-2 text-left w-24">크기</th>
            <th class="p-2 text-left w-24">자막</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          {#each files as file}
            <tr class="hover:bg-gray-50">
              <td class="p-2">
                <input 
                  type="checkbox" 
                  disabled={!withSubtitle && file.has_subtitle}
                  checked={selectedFiles.includes(file.path)} 
                  on:change={event => toggleSelect(file, event)}
                />
              </td>
              <td class="p-2 truncate" title={file.name}>
                {file.name}
              </td>
              <td class="p-2">
                <span class={file.type === 'video' ? 'text-blue-600' : 'text-green-600'}>
                  {file.type === 'video' ? '비디오' : '오디오'}
                </span>
              </td>
              <td class="p-2">{formatFileSize(file.size)}</td>
              <td class="p-2">
                {#if file.has_subtitle}
                  <span class="text-green-600">있음</span>
                {:else}
                  <span class="text-red-600">없음</span>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    
    <!-- 선택된 파일 요약 -->
    {#if selectedFiles.length > 0}
      <div class="mt-4 p-2 bg-blue-50 rounded flex justify-between items-center">
        <span class="text-sm font-medium">
          {selectedFiles.length}개 파일 선택됨
        </span>
        <button class="btn btn-sm btn-secondary" on:click={() => selectedFiles = []}>
          선택 해제
        </button>
      </div>
    {/if}
  {/if}
</div> 