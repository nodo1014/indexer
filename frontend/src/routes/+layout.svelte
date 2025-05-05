<script>
  import '../app.postcss';
  import { onMount } from 'svelte';
  import { connectWebSocket, disconnectWebSocket } from '$lib/api/websocket';

  // 웹소켓 연결/해제
  onMount(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  });
</script>

<div class="min-h-screen flex flex-col">
  <header class="bg-white shadow-sm">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-blue-600">Whisper 자막 생성기</h1>
        <nav>
          <ul class="flex space-x-4">
            <li><a href="/" class="text-gray-600 hover:text-blue-600">홈</a></li>
            <li><a href="/about" class="text-gray-600 hover:text-blue-600">About</a></li>
          </ul>
        </nav>
      </div>
    </div>
  </header>
  
  <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <slot />
  </main>
  
  <footer class="bg-gray-100 border-t">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <p class="text-center text-gray-500 text-sm">
        &copy; 2024 Whisper 자막 생성기 | 
        <a href="https://github.com/nodo1014/indexer" class="hover:text-blue-600" target="_blank" rel="noopener noreferrer">GitHub</a>
      </p>
    </div>
  </footer>
</div> 