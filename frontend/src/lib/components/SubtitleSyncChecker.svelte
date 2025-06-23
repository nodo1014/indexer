<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { checkSubtitleSync, adjustSubtitleOffset } from '$lib/api';
  import type { SyncCheckResult, SyncSegment } from '$lib/api';
  
  // 프로퍼티 정의
  export let mediaPath: string = '';
  export let subtitlePath: string = '';
  
  // 이벤트 디스패처 생성
  const dispatch = createEventDispatcher();
  
  // 상태 관리
  let isChecking: boolean = false;
  let isAdjusting: boolean = false;
  let syncResult: SyncCheckResult | null = null;
  let error: string | null = null;
  let adjustedSubtitlePath: string | null = null;
  
  // 싱크 검증 시작
  async function startSyncCheck() {
    if (!mediaPath || !subtitlePath) {
      error = '미디어 파일과 자막 파일을 모두 선택해주세요.';
      return;
    }
    
    isChecking = true;
    error = null;
    syncResult = null;
    
    try {
      // API 호출
      syncResult = await checkSubtitleSync(mediaPath, subtitlePath);
      
      // 이벤트 발생
      dispatch('syncCheckComplete', { 
        success: true,
        result: syncResult
      });
      
    } catch (err) {
      error = err.message || '싱크 검증 중 오류가 발생했습니다.';
      dispatch('syncCheckComplete', { 
        success: false,
        error: error
      });
    } finally {
      isChecking = false;
    }
  }
  
  // 자막 조정 시작
  async function startAdjustment() {
    if (!syncResult || !subtitlePath) {
      error = '먼저 싱크 검증을 완료해주세요.';
      return;
    }
    
    isAdjusting = true;
    error = null;
    
    try {
      // API 호출
      const result = await adjustSubtitleOffset(subtitlePath, syncResult.offset);
      adjustedSubtitlePath = result.adjusted_subtitle_path;
      
      // 이벤트 발생
      dispatch('adjustmentComplete', { 
        success: true,
        originalPath: subtitlePath,
        adjustedPath: adjustedSubtitlePath,
        offset: syncResult.offset
      });
      
    } catch (err) {
      error = err.message || '자막 조정 중 오류가 발생했습니다.';
      dispatch('adjustmentComplete', { 
        success: false,
        error: error
      });
    } finally {
      isAdjusting = false;
    }
  }
  
  // 싱크 상태에 따른 클래스
  function getSyncStatusClass(status: string): string {
    switch (status) {
      case 'good':
        return 'text-green-600';
      case 'needs_adjustment':
        return 'text-yellow-600';
      case 'bad':
        return 'text-red-600';
      default:
        return '';
    }
  }
  
  // 오프셋 시간 포맷
  function formatOffset(offset: number): string {
    const sign = offset >= 0 ? '+' : '-';
    const absOffset = Math.abs(offset);
    return `${sign}${absOffset.toFixed(3)}초`;
  }
</script>

<div class="subtitle-sync-checker card">
  <h2 class="text-lg font-semibold mb-4">자막 싱크 검증</h2>
  
  <!-- 파일 정보 -->
  <div class="mb-4">
    {#if mediaPath && subtitlePath}
      <div class="bg-gray-100 dark:bg-gray-700 p-3 rounded mb-2">
        <div class="flex items-center text-sm">
          <span class="font-medium mr-2">미디어:</span>
          <span class="truncate">{mediaPath.split('/').pop()}</span>
        </div>
      </div>
      <div class="bg-gray-100 dark:bg-gray-700 p-3 rounded">
        <div class="flex items-center text-sm">
          <span class="font-medium mr-2">자막:</span>
          <span class="truncate">{subtitlePath.split('/').pop()}</span>
        </div>
      </div>
    {:else}
      <div class="p-3 bg-yellow-50 dark:bg-yellow-900 dark:bg-opacity-20 text-yellow-800 dark:text-yellow-200 text-sm rounded">
        미디어 파일과 자막 파일을 모두 선택해주세요.
      </div>
    {/if}
  </div>
  
  <!-- 진행률 표시 -->
  {#if isChecking || isAdjusting}
    <div class="mb-4">
      <div class="mb-1 text-sm">
        {isChecking ? '싱크 검증 중...' : '자막 조정 중...'}
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
        <div 
          class="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out animate-pulse" 
          style="width: 100%"
        ></div>
      </div>
    </div>
  {/if}
  
  <!-- 에러 메시지 -->
  {#if error}
    <div class="p-3 mb-4 bg-red-100 text-red-800 dark:bg-red-900 dark:bg-opacity-30 dark:text-red-200 rounded">
      {error}
    </div>
  {/if}
  
  <!-- 검증 결과 -->
  {#if syncResult}
    <div class="mb-4">
      <h3 class="font-medium mb-2">검증 결과</h3>
      <div class="p-4 bg-gray-100 dark:bg-gray-800 rounded">
        <div class="mb-3">
          <div class="flex justify-between">
            <span>싱크 상태:</span>
            <span class={getSyncStatusClass(syncResult.sync_status)}>
              {#if syncResult.sync_status === 'good'}
                좋음
              {:else if syncResult.sync_status === 'needs_adjustment'}
                조정 필요
              {:else}
                나쁨
              {/if}
            </span>
          </div>
          <div class="flex justify-between">
            <span>오프셋:</span>
            <span class={Math.abs(syncResult.offset) > 0.5 ? 'text-yellow-600' : 'text-green-600'}>
              {formatOffset(syncResult.offset)}
            </span>
          </div>
          <div class="flex justify-between">
            <span>신뢰도:</span>
            <span>{(syncResult.confidence_score * 100).toFixed(1)}%</span>
          </div>
        </div>
        
        {#if syncResult.segments && syncResult.segments.length > 0}
          <div>
            <h4 class="text-sm font-medium mb-1">세그먼트 분석</h4>
            <div class="max-h-60 overflow-y-auto">
              <table class="w-full text-sm">
                <thead class="bg-gray-200 dark:bg-gray-700">
                  <tr>
                    <th class="p-2 text-left">위치</th>
                    <th class="p-2 text-right">시간</th>
                    <th class="p-2 text-right">오프셋</th>
                    <th class="p-2 text-right">유사도</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                  {#each syncResult.segments as segment}
                    <tr>
                      <td class="p-2">
                        {#if segment.position === 'start'}
                          시작
                        {:else if segment.position === 'middle'}
                          중간
                        {:else}
                          끝
                        {/if}
                      </td>
                      <td class="p-2 text-right">{segment.time_position.toFixed(1)}초</td>
                      <td class="p-2 text-right">{formatOffset(segment.offset)}</td>
                      <td class="p-2 text-right">{(segment.similarity_score * 100).toFixed(1)}%</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      </div>
    </div>
    
    <!-- 조정 결과 -->
    {#if adjustedSubtitlePath}
      <div class="p-3 mb-4 bg-green-100 text-green-800 dark:bg-green-900 dark:bg-opacity-30 dark:text-green-200 rounded">
        <p class="font-medium">자막을 성공적으로 조정했습니다.</p>
        <p class="text-sm mt-1">오프셋 조정: {formatOffset(syncResult.offset)}</p>
        <p class="text-sm mt-1">저장 위치: {adjustedSubtitlePath.split('/').pop()}</p>
      </div>
    {/if}
  {/if}
  
  <!-- 버튼 영역 -->
  <div class="flex flex-col sm:flex-row gap-2">
    <button 
      class="btn btn-primary flex-1" 
      on:click={startSyncCheck} 
      disabled={isChecking || isAdjusting || !mediaPath || !subtitlePath}
    >
      {#if isChecking}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      싱크 검증
    </button>
    
    <button 
      class="btn btn-secondary flex-1" 
      on:click={startAdjustment} 
      disabled={isAdjusting || !syncResult || Math.abs(syncResult?.offset || 0) <= 0.1}
    >
      {#if isAdjusting}
        <span class="inline-block animate-spin mr-2">⟳</span>
      {/if}
      자막 조정
    </button>
  </div>
</div> 