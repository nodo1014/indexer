<script lang="ts">
  import { onMount } from 'svelte';
  import { currentPath } from '$lib/stores/directory';
  import { createEventDispatcher } from 'svelte';
  
  // 디렉토리 정보 타입 정의
  interface Directory {
    name: string;
    path: string;
    video_count: number;
    audio_count: number;
  }
  
  // 이벤트 디스패처 생성
  const dispatch = createEventDispatcher();
  
  // 상태 관리
  let directories: Directory[] = [];
  let loading = false;
  let error: string | null = null;
  
  // 디렉토리 불러오기
  async function loadDirectories(path = '') {
    loading = true;
    error = null;
    
    try {
      const response = await fetch(`/api/browse?current_path=${encodeURIComponent(path)}`);
      if (!response.ok) {
        throw new Error(`서버 오류: ${response.status}`);
      }
      
      const data = await response.json();
      directories = data.directories || [];
      
      // 현재 경로 업데이트 (directory 스토어에 저장)
      currentPath.set(data.current_relative_path || '');
      
    } catch (err: unknown) {
      console.error('디렉토리 로드 오류:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      error = `디렉토리를 불러오는 중 오류가 발생했습니다: ${errorMessage}`;
    } finally {
      loading = false;
    }
  }
  
  // 미디어 파일 검색 - 현재 경로의 모든 미디어 파일을 표시
  async function searchMediaFiles() {
    if (!$currentPath) {
      return; // 경로가 없으면 검색하지 않음
    }
    
    // 부모 컴포넌트에 검색 이벤트 발송
    dispatch('searchMedia', {
      path: $currentPath
    });
  }
  
  // 디렉토리 클릭 핸들러
  function handleDirectoryClick(path: string) {
    loadDirectories(path);
  }
  
  // 초기 로드
  onMount(() => {
    loadDirectories();
  });
</script>

<div class="directory-browser card">
  <h2 class="text-lg font-semibold mb-4">디렉토리 탐색기</h2>
  
  <!-- 경로 내비게이션 -->
  <div class="mb-4 text-sm overflow-x-auto whitespace-nowrap">
    <div class="flex items-center">
      <button 
        class="hover:text-blue-600" 
        on:click={() => loadDirectories('')}
      >
        루트
      </button>
      
      {#if $currentPath}
        <span class="mx-1">/</span>
        {#each $currentPath.split('/').filter(Boolean) as part, index}
          <button 
            class="hover:text-blue-600" 
            on:click={() => {
              const pathParts = $currentPath.split('/').filter(Boolean);
              const newPath = pathParts.slice(0, index + 1).join('/');
              loadDirectories(newPath);
            }}
          >
            {part}
          </button>
          {#if index < $currentPath.split('/').filter(Boolean).length - 1}
            <span class="mx-1">/</span>
          {/if}
        {/each}
      {/if}
    </div>
  </div>
  
  <!-- 디렉토리 목록 -->
  {#if loading}
    <div class="p-4 text-center">
      <span class="inline-block animate-spin mr-2">⟳</span> 불러오는 중...
    </div>
  {:else if error}
    <div class="p-4 text-red-600 dark:text-red-400">
      {error}
    </div>
  {:else if directories.length === 0}
    <div class="p-4 text-center text-gray-500">
      디렉토리가 없습니다.
    </div>
  {:else}
    <div class="max-h-80 overflow-y-auto border rounded">
      <ul class="divide-y">
        {#each directories as dir}
          <li>
            <button 
              class="w-full p-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 flex justify-between items-center"
              on:click={() => handleDirectoryClick(dir.path)}
            >
              <span class="truncate">{dir.name}</span>
              <span class="text-xs text-gray-500">
                {#if dir.video_count > 0 || dir.audio_count > 0}
                  <span class="ml-2">(
                    {#if dir.video_count > 0}비디오: {dir.video_count}{/if}
                    {#if dir.video_count > 0 && dir.audio_count > 0}, {/if}
                    {#if dir.audio_count > 0}오디오: {dir.audio_count}{/if}
                  )</span>
                {/if}
              </span>
            </button>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
  
  <!-- 작업 버튼 영역 -->
  <div class="mt-4 grid grid-cols-2 gap-2">
    <button 
      class="btn btn-primary"
      on:click={() => loadDirectories($currentPath)}
      disabled={loading}
    >
      {#if loading}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      새로고침
    </button>
    
    <button 
      class="btn btn-secondary"
      on:click={searchMediaFiles}
      disabled={loading || !$currentPath}
      title={!$currentPath ? '폴더를 먼저 선택해주세요' : '현재 폴더의 미디어 파일 검색'}
    >
      미디어 파일 검색
    </button>
  </div>
</div> 