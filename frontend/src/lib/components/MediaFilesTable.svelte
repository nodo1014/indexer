<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { searchMediaFiles } from '$lib/api';
  import { currentPath } from '$lib/stores/directory';
  import { filterSettings } from '$lib/stores/settings';
  import type { MediaFile } from '$lib/api';
  
  // 프로퍼티 정의 (외부에서 명시적으로 설정하지 않으면 사용자 필터 설정 사용)
  export let withSubtitle: boolean | null = null;
  export let path: string = ''; // 새로 추가된 프로퍼티
  
  // 데이터 상태
  let files: MediaFile[] = [];
  let isLoading = false;
  let error: string | null = null;
  let summary = {
    total_files: 0,
    video_count: 0,
    audio_count: 0,
    with_subtitle_count: 0,
    without_subtitle_count: 0
  };
  
  // 선택된 파일 관리
  let selectedFiles: string[] = [];
  
  // 이벤트 디스패처
  const dispatch = createEventDispatcher<{
    selectionChange: string[];
  }>();
  
  // 파일 유형 필터링을 위한 계산된 값
  $: effectiveWithSubtitle = withSubtitle !== null ? withSubtitle : $filterSettings.showWithSubtitle;
  
  // 경로 우선순위: 프로퍼티 경로 > 스토어 경로
  $: effectivePath = path || $currentPath;
  
  // 파일 목록 로드
  async function loadFiles() {
    if (!effectivePath) return;
    
    isLoading = true;
    error = null;
    
    try {
      const result = await searchMediaFiles(effectivePath, effectiveWithSubtitle);
      // API에서 받아온 모든 파일
      let allFiles = result.files;
      
      // 필터 설정에 따라 파일 필터링
      if ($filterSettings.videoOnly) {
        allFiles = allFiles.filter(file => file.type === 'video');
      } else if ($filterSettings.audioOnly) {
        allFiles = allFiles.filter(file => file.type === 'audio');
      }
      
      files = allFiles;
      
      summary = {
        total_files: result.total_files,
        video_count: result.video_count,
        audio_count: result.audio_count,
        with_subtitle_count: result.with_subtitle_count,
        without_subtitle_count: result.without_subtitle_count
      };
      selectedFiles = [];
    } catch (err) {
      error = err instanceof Error ? err.message : '파일 목록을 불러오는 중 오류가 발생했습니다.';
      files = [];
    } finally {
      isLoading = false;
    }
  }
  
  // 경로나 필터 설정이 변경될 때마다 파일 목록 다시 로드
  $: effectivePath && effectiveWithSubtitle !== undefined && loadFiles();
  $: $filterSettings && loadFiles();
  $: path && loadFiles(); // 부모에서 path 프로퍼티가 변경되면 로드
  
  // 전체 선택/해제
  function toggleSelectAll(event: Event) {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      selectedFiles = files
        .filter(file => !file.has_subtitle || effectiveWithSubtitle)
        .map(file => file.path);
    } else {
      selectedFiles = [];
    }
    
    dispatch('selectionChange', selectedFiles);
  }
  
  // 개별 파일 선택/해제
  function toggleSelect(file: MediaFile, event: Event) {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      selectedFiles = [...selectedFiles, file.path];
    } else {
      selectedFiles = selectedFiles.filter(path => path !== file.path);
    }
    
    dispatch('selectionChange', selectedFiles);
  }
  
  // 파일 크기 포맷팅 (바이트 → 읽기 쉬운 형식)
  function formatFileSize(size: number): string {
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

<div class="media-files-table card">
  <!-- 요약 정보 -->
  <div class="mb-4 flex justify-between items-center">
    <div>
      <h2 class="text-lg font-semibold">
        {effectiveWithSubtitle ? '모든 미디어 파일' : '자막 없는 미디어 파일'}
        {#if $filterSettings.videoOnly}
          (비디오만)
        {:else if $filterSettings.audioOnly}
          (오디오만)
        {/if}
      </h2>
      {#if summary.total_files > 0}
        <p class="text-sm text-gray-600">
          총 {summary.total_files}개 파일 (비디오: {summary.video_count}, 오디오: {summary.audio_count})
          {#if !effectiveWithSubtitle}
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
      <p>{effectivePath ? '이 폴더에는' : '선택된 경로에는'} {effectiveWithSubtitle ? '미디어 파일이' : '자막 없는 미디어 파일이'} 없습니다.</p>
    </div>
  
  <!-- 파일 목록 테이블 -->
  {:else}
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th class="w-12">
              <input 
                type="checkbox" 
                on:change={toggleSelectAll} 
                checked={selectedFiles.length === files.filter(f => !f.has_subtitle || effectiveWithSubtitle).length && files.length > 0}
              />
            </th>
            <th>파일명</th>
            <th class="w-24">타입</th>
            <th class="w-24">크기</th>
            <th class="w-24">자막</th>
          </tr>
        </thead>
        <tbody>
          {#each files as file}
            <tr>
              <td>
                <input 
                  type="checkbox" 
                  disabled={!effectiveWithSubtitle && file.has_subtitle}
                  checked={selectedFiles.includes(file.path)} 
                  on:change={event => toggleSelect(file, event)}
                />
              </td>
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
        <button class="btn btn-sm btn-secondary" on:click={() => { selectedFiles = []; dispatch('selectionChange', []); }}>
          선택 해제
        </button>
      </div>
    {/if}
  {/if}
</div> 