<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { searchMediaFiles } from '$lib/api';
  import type { MediaFile } from '$lib/api';
  import { currentPath } from '$lib/stores/directory';
  
  // 상태 관리
  let files: MediaFile[] = [];
  let loading = true;
  let error: string | null = null;
  
  // 필터 설정
  let showWithSubtitle = false;
  let filterVideo = true;
  let filterAudio = true;
  
  // 통계 데이터
  let stats = {
    totalFiles: 0,
    videoCount: 0,
    audioCount: 0,
    withSubtitleCount: 0,
    withoutSubtitleCount: 0
  };
  
  // 파일 크기 포맷팅
  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
  }
  
  // 파일 목록 로드
  async function loadFiles() {
    const path = $page.url.searchParams.get('path') || '';
    currentPath.set(path);
    
    loading = true;
    error = null;
    
    try {
      const result = await searchMediaFiles(path, showWithSubtitle);
      
      // API 응답에서 필요한 데이터 추출
      files = result.files || [];
      
      // 필터 적용
      if (!filterVideo) {
        files = files.filter(file => file.type !== 'video');
      }
      if (!filterAudio) {
        files = files.filter(file => file.type !== 'audio');
      }
      
      // 통계 업데이트
      stats = {
        totalFiles: result.total_files || files.length,
        videoCount: result.video_count || files.filter(f => f.type === 'video').length,
        audioCount: result.audio_count || files.filter(f => f.type === 'audio').length,
        withSubtitleCount: result.with_subtitle_count || files.filter(f => f.has_subtitle).length,
        withoutSubtitleCount: result.without_subtitle_count || files.filter(f => !f.has_subtitle).length
      };
      
    } catch (err: unknown) {
      console.error('파일 목록 로드 오류:', err);
      error = err instanceof Error ? err.message : '파일 목록을 불러오는 중 오류가 발생했습니다';
    } finally {
      loading = false;
    }
  }
  
  // 필터 변경 시 파일 목록 다시 로드
  function handleFilterChange() {
    loadFiles();
  }
  
  // 초기 로드
  onMount(() => {
    loadFiles();
  });
</script>

<svelte:head>
  <title>미디어 파일 목록 - 자막 인덱서</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 py-8">
  <div class="mb-6">
    <h1 class="text-2xl font-bold mb-2">미디어 파일 목록</h1>
    <p class="text-gray-600">
      현재 경로: {$currentPath || '루트'}
    </p>
  </div>
  
  <!-- 필터 설정 -->
  <div class="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
    <h2 class="text-lg font-medium mb-3">필터 설정</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <label class="flex items-center cursor-pointer">
          <input 
            type="checkbox" 
            bind:checked={showWithSubtitle} 
            on:change={handleFilterChange}
            class="form-checkbox h-5 w-5 text-blue-600"
          >
          <span class="ml-2">자막 있는 파일도 표시</span>
        </label>
      </div>
      
      <div>
        <label class="flex items-center cursor-pointer">
          <input 
            type="checkbox" 
            bind:checked={filterVideo} 
            on:change={handleFilterChange}
            class="form-checkbox h-5 w-5 text-blue-600"
          >
          <span class="ml-2">비디오 파일 표시</span>
        </label>
      </div>
      
      <div>
        <label class="flex items-center cursor-pointer">
          <input 
            type="checkbox" 
            bind:checked={filterAudio} 
            on:change={handleFilterChange}
            class="form-checkbox h-5 w-5 text-blue-600"
          >
          <span class="ml-2">오디오 파일 표시</span>
        </label>
      </div>
    </div>
  </div>
  
  <!-- 통계 정보 -->
  <div class="mb-6 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
    <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-3 text-center">
      <div class="text-lg font-bold">{stats.totalFiles}</div>
      <div class="text-sm text-gray-600 dark:text-gray-400">전체 파일</div>
    </div>
    <div class="bg-blue-100 dark:bg-blue-900 dark:bg-opacity-30 rounded-lg p-3 text-center">
      <div class="text-lg font-bold">{stats.videoCount}</div>
      <div class="text-sm text-gray-600 dark:text-gray-400">비디오</div>
    </div>
    <div class="bg-green-100 dark:bg-green-900 dark:bg-opacity-30 rounded-lg p-3 text-center">
      <div class="text-lg font-bold">{stats.audioCount}</div>
      <div class="text-sm text-gray-600 dark:text-gray-400">오디오</div>
    </div>
    <div class="bg-purple-100 dark:bg-purple-900 dark:bg-opacity-30 rounded-lg p-3 text-center">
      <div class="text-lg font-bold">{stats.withSubtitleCount}</div>
      <div class="text-sm text-gray-600 dark:text-gray-400">자막 있음</div>
    </div>
    <div class="bg-yellow-100 dark:bg-yellow-900 dark:bg-opacity-30 rounded-lg p-3 text-center">
      <div class="text-lg font-bold">{stats.withoutSubtitleCount}</div>
      <div class="text-sm text-gray-600 dark:text-gray-400">자막 없음</div>
    </div>
  </div>
  
  <!-- 파일 목록 -->
  {#if loading}
    <div class="p-12 text-center">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600 mb-4"></div>
      <p class="text-gray-600">파일 목록을 불러오는 중...</p>
    </div>
  {:else if error}
    <div class="p-6 bg-red-100 text-red-800 dark:bg-red-900 dark:bg-opacity-30 dark:text-red-200 rounded-lg">
      <p>{error}</p>
      <button class="btn btn-sm mt-3" on:click={loadFiles}>다시 시도</button>
    </div>
  {:else if files.length === 0}
    <div class="p-12 text-center bg-gray-50 dark:bg-gray-800 rounded-lg">
      <p class="text-gray-600 mb-3">
        {#if !filterVideo && !filterAudio}
          필터 조건에 맞는 파일이 없습니다. 필터 설정을 확인해 주세요.
        {:else if !showWithSubtitle}
          자막이 없는 미디어 파일이 없습니다.
        {:else}
          미디어 파일이 없습니다.
        {/if}
      </p>
      <button class="btn btn-primary" on:click={() => window.history.back()}>돌아가기</button>
    </div>
  {:else}
    <div class="overflow-x-auto">
      <table class="min-w-full border rounded-lg">
        <thead class="bg-gray-100 dark:bg-gray-700">
          <tr>
            <th class="py-3 px-4 text-left">파일명</th>
            <th class="py-3 px-4 text-center w-24">유형</th>
            <th class="py-3 px-4 text-center w-24">크기</th>
            <th class="py-3 px-4 text-center w-28">자막</th>
            <th class="py-3 px-4 text-center w-28">작업</th>
          </tr>
        </thead>
        <tbody class="bg-white dark:bg-gray-800 divide-y">
          {#each files as file}
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td class="py-3 px-4">
                <div class="font-medium truncate max-w-md" title={file.name}>
                  {file.name}
                </div>
              </td>
              <td class="py-3 px-4 text-center">
                <span class={file.type === 'video' ? 'text-blue-600' : 'text-green-600'}>
                  {file.type === 'video' ? '비디오' : '오디오'}
                </span>
              </td>
              <td class="py-3 px-4 text-center text-gray-600">
                {formatFileSize(file.size)}
              </td>
              <td class="py-3 px-4 text-center">
                {#if file.has_subtitle}
                  <span class="text-green-600">있음</span>
                {:else}
                  <span class="text-red-600">없음</span>
                {/if}
              </td>
              <td class="py-3 px-4 text-center">
                {#if !file.has_subtitle}
                  <a 
                    href={`/subtitle-download?path=${encodeURIComponent(file.path)}`}
                    class="btn btn-xs btn-primary"
                  >
                    자막 다운로드
                  </a>
                {:else if file.subtitle_files && file.subtitle_files.length > 0}
                  <a 
                    href={`/sync-check?media=${encodeURIComponent(file.path)}&subtitle=${encodeURIComponent(file.subtitle_files[0])}`}
                    class="btn btn-xs btn-secondary"
                  >
                    싱크 확인
                  </a>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
  
  <!-- 버튼 영역 -->
  <div class="mt-6 flex justify-between">
    <button class="btn btn-secondary" on:click={() => window.history.back()}>
      돌아가기
    </button>
    <button class="btn btn-primary" on:click={loadFiles}>
      {#if loading}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      새로고침
    </button>
  </div>
</div> 