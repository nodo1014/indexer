<script lang="ts">
  import '../app.postcss';
  import { onMount } from 'svelte';
  import { connectWebSocket, disconnectWebSocket } from '$lib/api/websocket';
  import { uiSettings } from '$lib/stores/settings';
  import { page } from '$app/stores';

  // 웹소켓 연결/해제
  onMount(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  });
  
  // 현재 활성화된 경로 확인
  $: isActive = (path: string) => $page.url.pathname === path;
</script>

<div class="min-h-screen flex flex-col {$uiSettings.darkMode ? 'dark' : ''}">
  <header class="bg-white dark:bg-gray-800 shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-blue-600 dark:text-blue-400">Whisper 자막 생성기</h1>
        <nav>
          <ul class="flex space-x-4">
            <li>
              <a 
                href="/" 
                class="
                  text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400
                  {isActive('/') ? 'font-medium text-blue-600 dark:text-blue-400' : ''}
                "
              >
                자막 다운로드
              </a>
            </li>
            <li>
              <a 
                href="/whisper-transcribe" 
                class="
                  text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400
                  {isActive('/whisper-transcribe') ? 'font-medium text-blue-600 dark:text-blue-400' : ''}
                "
              >
                AI 자막 생성
              </a>
            </li>
            <li>
              <a 
                href="/sync-check" 
                class="
                  text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400
                  {isActive('/sync-check') ? 'font-medium text-blue-600 dark:text-blue-400' : ''}
                "
              >
                자막 싱크 검증
              </a>
            </li>
            <li>
              <a 
                href="/about" 
                class="
                  text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400
                  {isActive('/about') ? 'font-medium text-blue-600 dark:text-blue-400' : ''}
                "
              >
                About
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </header>
  
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 dark:bg-gray-900">
    <slot />
  </main>
  
  <footer class="bg-gray-100 dark:bg-gray-800 border-t dark:border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <p class="text-center text-gray-500 dark:text-gray-400 text-sm">
        &copy; 2024 Whisper 자막 생성기 | 
        <a href="https://github.com/nodo1014/indexer" class="hover:text-blue-600 dark:hover:text-blue-400" target="_blank" rel="noopener noreferrer">GitHub</a>
      </p>
    </div>
  </footer>
</div> 