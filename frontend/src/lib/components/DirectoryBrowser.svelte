<script>
  import { onMount } from 'svelte';
  import { 
    currentPath, 
    directoryItems, 
    isLoading, 
    errorMessage, 
    loadDirectory,
    navigateUp
  } from '$lib/stores/directory';

  // 컴포넌트 마운트 시 디렉토리 로드
  onMount(() => {
    loadDirectory('');
  });

  // 디렉토리 클릭 핸들러
  const handleDirectoryClick = (path) => {
    loadDirectory(path);
  };
</script>

<div class="directory-browser card">
  <div class="flex items-center justify-between mb-4">
    <h2 class="text-lg font-semibold">디렉토리 탐색기</h2>
    <button 
      class="btn btn-secondary btn-sm" 
      on:click={navigateUp} 
      disabled={!$currentPath}
    >
      상위 폴더
    </button>
  </div>
  
  <!-- 현재 경로 표시 -->
  <div class="bg-gray-100 p-2 rounded mb-4 text-sm flex items-center overflow-x-auto">
    <button class="mr-1 hover:text-blue-600" on:click={() => loadDirectory('')}>
      루트
    </button>
    {#if $currentPath}
      <span class="mx-1">/</span>
      {#each $currentPath.split('/').filter(Boolean) as part, i, arr}
        <button 
          class="hover:text-blue-600" 
          on:click={() => loadDirectory($currentPath.split('/').slice(0, i + 1).join('/'))}
        >
          {part}
        </button>
        {#if i < arr.length - 1}
          <span class="mx-1">/</span>
        {/if}
      {/each}
    {/if}
  </div>
  
  <!-- 로딩 상태 표시 -->
  {#if $isLoading}
    <div class="p-4 text-center">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-gray-600">로딩 중...</p>
    </div>
  {:else if $errorMessage}
    <div class="p-4 bg-red-100 text-red-800 rounded">
      <p>{$errorMessage}</p>
      <button class="btn btn-sm mt-2" on:click={() => loadDirectory($currentPath)}>
        다시 시도
      </button>
    </div>
  <!-- 디렉토리 목록 -->
  {:else if $directoryItems.length === 0}
    <div class="p-4 text-center text-gray-500">
      <p>디렉토리가 비어있습니다.</p>
    </div>
  {:else}
    <ul class="divide-y divide-gray-200">
      {#each $directoryItems as item}
        {#if item.is_directory}
          <li>
            <button 
              class="w-full text-left p-2 hover:bg-gray-100 flex items-center"
              on:click={() => handleDirectoryClick(item.path)}
            >
              <svg class="w-5 h-5 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"></path>
              </svg>
              <span>{item.name}</span>
              <span class="ml-2 text-xs text-gray-500">
                (영상 {item.video_count}, 오디오 {item.audio_count})
              </span>
            </button>
          </li>
        {/if}
      {/each}
    </ul>
  {/if}
</div> 