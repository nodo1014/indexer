<script>
  import { onMount } from 'svelte';
  import { jobUpdates } from '$lib/api/websocket';
  import { getJobs, controlJob } from '$lib/api';
  
  let isLoading = true;
  
  // 작업 목록 초기 로드
  onMount(async () => {
    try {
      const jobs = await getJobs();
      $jobUpdates = jobs;
    } catch (error) {
      console.error('작업 목록 로드 오류:', error);
    } finally {
      isLoading = false;
    }
  });
  
  // 작업 상태별 필터링
  $: activeJobs = $jobUpdates.filter(job => 
    job.status === 'queued' || 
    job.status === 'processing' || 
    job.status === 'paused'
  );
  
  $: completedJobs = $jobUpdates.filter(job => 
    job.status === 'completed' || 
    job.status === 'failed'
  );
  
  // 작업 제어 함수들
  async function pauseJob(jobId) {
    await controlJob(jobId, 'pause');
  }
  
  async function resumeJob(jobId) {
    await controlJob(jobId, 'resume');
  }
  
  async function cancelJob(jobId) {
    await controlJob(jobId, 'cancel');
  }
  
  // 상태 텍스트 변환
  function getStatusText(status) {
    switch (status) {
      case 'queued': return '대기 중';
      case 'processing': return '진행 중';
      case 'completed': return '완료';
      case 'failed': return '실패';
      case 'paused': return '일시정지';
      default: return status;
    }
  }
  
  // 상태에 따른 색상 클래스
  function getStatusColorClass(status) {
    switch (status) {
      case 'processing': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'paused': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  }
  
  // 작업 파일 이름 짧게 표시
  function getShortFileName(path) {
    const parts = path.split('/');
    return parts[parts.length - 1];
  }
</script>

<div class="job-status-panel">
  <h2 class="text-lg font-semibold mb-4">작업 현황</h2>
  
  <!-- 로딩 인디케이터 -->
  {#if isLoading}
    <div class="p-4 text-center">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-gray-600">작업 목록 로딩 중...</p>
    </div>
  
  <!-- 활성 작업 없음 -->
  {:else if activeJobs.length === 0 && completedJobs.length === 0}
    <div class="p-4 text-center text-gray-500 border rounded">
      <p>진행 중인 작업이 없습니다.</p>
    </div>
  
  <!-- 작업 목록 -->
  {:else}
    <!-- 활성 작업 -->
    {#if activeJobs.length > 0}
      <div class="mb-4">
        <h3 class="text-md font-medium mb-2">진행 중인 작업</h3>
        <div class="space-y-3">
          {#each activeJobs as job}
            <div class="card p-3">
              <div class="flex justify-between items-center mb-1">
                <div class="font-medium truncate" title={job.file_path}>
                  {getShortFileName(job.file_path)}
                </div>
                <div class={getStatusColorClass(job.status)}>
                  {getStatusText(job.status)}
                </div>
              </div>
              
              <div class="mb-2">
                <div class="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="h-full bg-blue-600 rounded-full" 
                    style="width: {job.progress}%;"
                  ></div>
                </div>
                <div class="text-xs text-right mt-1">{job.progress}%</div>
              </div>
              
              <div class="flex justify-end space-x-2 text-xs">
                {#if job.status === 'processing'}
                  <button 
                    class="btn btn-sm btn-secondary" 
                    on:click={() => pauseJob(job.id)}
                  >
                    일시정지
                  </button>
                {:else if job.status === 'paused'}
                  <button 
                    class="btn btn-sm btn-secondary" 
                    on:click={() => resumeJob(job.id)}
                  >
                    재개
                  </button>
                {/if}
                
                <button 
                  class="btn btn-sm btn-secondary" 
                  on:click={() => cancelJob(job.id)}
                >
                  취소
                </button>
              </div>
            </div>
          {/each}
        </div>
      </div>
    {/if}
    
    <!-- 완료된 작업 -->
    {#if completedJobs.length > 0}
      <div>
        <h3 class="text-md font-medium mb-2">최근 완료된 작업</h3>
        <div class="space-y-2">
          {#each completedJobs.slice(0, 5) as job}
            <div class="card p-2">
              <div class="flex justify-between items-center">
                <div class="truncate" title={job.file_path}>
                  {getShortFileName(job.file_path)}
                </div>
                <div class={getStatusColorClass(job.status)}>
                  {getStatusText(job.status)}
                </div>
              </div>
              
              {#if job.subtitle_path}
                <div class="text-right mt-1">
                  <a 
                    href={`/download?path=${encodeURIComponent(job.subtitle_path)}`} 
                    class="text-xs text-blue-600 hover:underline"
                  >
                    자막 다운로드
                  </a>
                </div>
              {/if}
              
              {#if job.error}
                <div class="text-xs text-red-600 mt-1">{job.error}</div>
              {/if}
            </div>
          {/each}
          
          {#if completedJobs.length > 5}
            <div class="text-center text-sm text-gray-500">
              외 {completedJobs.length - 5}개 작업
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {/if}
</div> 