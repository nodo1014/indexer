<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    isLoadingJobs, 
    jobsError, 
    activeJobs, 
    completedJobs, 
    loadJobs, 
    pauseJob, 
    resumeJob, 
    cancelJob 
  } from '$lib/stores/jobs';
  
  // 작업 타입 정의
  interface Job {
    id: string;
    file_path: string;
    status: 'queued' | 'processing' | 'completed' | 'failed' | 'paused';
    progress: number;
    job_type?: string;
    subtitle_path?: string;
    error?: string;
    created_at: string;
    updated_at?: string;
  }
  
  // 모달 상태
  let showModal = false;
  let selectedJob: Job | null = null;
  
  // 작업 목록 초기 로드
  onMount(() => {
    loadJobs();
  });
  
  // 작업 제어 함수들
  async function handlePauseJob(jobId: string) {
    try {
      await pauseJob(jobId);
    } catch (error) {
      console.error('작업 일시정지 오류:', error);
    }
  }
  
  async function handleResumeJob(jobId: string) {
    try {
      await resumeJob(jobId);
    } catch (error) {
      console.error('작업 재개 오류:', error);
    }
  }
  
  async function handleCancelJob(jobId: string) {
    try {
      await cancelJob(jobId);
    } catch (error) {
      console.error('작업 취소 오류:', error);
    }
  }
  
  // 상태 텍스트 변환
  function getStatusText(status: string) {
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
  function getStatusColorClass(status: string) {
    switch (status) {
      case 'processing': return 'text-blue-600';
      case 'completed': return 'text-green-600';
      case 'failed': return 'text-red-600';
      case 'paused': return 'text-yellow-600';
      default: return 'text-gray-600';
    }
  }
  
  // 작업 파일 이름 짧게 표시
  function getShortFileName(path: string) {
    const parts = path.split('/');
    return parts[parts.length - 1];
  }
  
  // 작업 상세 정보 보기
  function showJobDetails(job: Job) {
    selectedJob = job;
    showModal = true;
  }
  
  // 모달 닫기
  function closeModal() {
    showModal = false;
    selectedJob = null;
  }
  
  // 에러 단계 타입 정의
  interface ErrorStep {
    name: string;
    status: 'completed' | 'failed';
    message: string;
  }
  
  // 에러 상세 정보 생성
  function getErrorDetails(error: string | undefined): ErrorStep[] {
    if (!error) return [];
    
    // 오류 메시지에서 작업 단계 파악
    const steps: ErrorStep[] = [];
    
    if (error.includes('다운로드') || error.includes('download') || error.includes('API')) {
      steps.push({ name: '자막 다운로드', status: 'failed', message: '자막 다운로드 중 오류 발생' });
    } else if (error.includes('싱크') || error.includes('sync')) {
      steps.push({ name: '자막 다운로드', status: 'completed', message: '성공' });
      steps.push({ name: '싱크 검증', status: 'failed', message: '싱크 검증 중 오류 발생' });
    } else if (error.includes('조정') || error.includes('adjust')) {
      steps.push({ name: '자막 다운로드', status: 'completed', message: '성공' });
      steps.push({ name: '싱크 검증', status: 'completed', message: '성공' });
      steps.push({ name: '자막 조정', status: 'failed', message: '자막 조정 중 오류 발생' });
    } else if (error.includes('Whisper') || error.includes('whisper')) {
      steps.push({ name: 'Whisper 자막 생성', status: 'failed', message: 'Whisper 실행 중 오류 발생' });
    } else {
      steps.push({ name: '알 수 없는 단계', status: 'failed', message: error });
    }
    
    return steps;
  }
</script>

<div class="job-status-panel card">
  <h2 class="text-lg font-semibold mb-4">작업 현황</h2>
  
  <!-- 로딩 인디케이터 -->
  {#if $isLoadingJobs}
    <div class="p-4 text-center">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-gray-600">작업 목록 로딩 중...</p>
    </div>
  
  <!-- 오류 메시지 -->
  {:else if $jobsError}
    <div class="p-4 bg-red-100 text-red-800 rounded">
      <p>{$jobsError}</p>
      <button class="btn btn-sm mt-2" on:click={loadJobs}>
        다시 시도
      </button>
    </div>
    
  <!-- 활성 작업 없음 -->
  {:else if $activeJobs.length === 0 && $completedJobs.length === 0}
    <div class="p-4 text-center text-gray-500 border rounded">
      <p>진행 중인 작업이 없습니다.</p>
    </div>
  
  <!-- 작업 목록 -->
  {:else}
    <!-- 활성 작업 -->
    {#if $activeJobs.length > 0}
      <div class="mb-4">
        <h3 class="text-md font-medium mb-2">진행 중인 작업</h3>
        <div class="space-y-3">
          {#each $activeJobs as job}
            <div 
              class="p-3 border rounded-lg bg-gray-50 cursor-pointer hover:bg-gray-100" 
              on:click={() => showJobDetails(job)}
            >
              <div class="flex justify-between items-center mb-1">
                <div class="font-medium truncate" title={job.file_path}>
                  {getShortFileName(job.file_path)}
                </div>
                <div class={getStatusColorClass(job.status)}>
                  {getStatusText(job.status)}
                </div>
              </div>
              
              <div class="mb-2">
                <div class="progress-bar">
                  <div 
                    class="progress-bar-fill" 
                    style="width: {job.progress}%;"
                  ></div>
                </div>
                <div class="text-xs text-right mt-1">{job.progress}%</div>
              </div>
              
              <div class="flex justify-end space-x-2 text-xs">
                {#if job.status === 'processing'}
                  <button 
                    class="btn btn-sm btn-secondary" 
                    on:click={(e) => { e.stopPropagation(); handlePauseJob(job.id); }}
                  >
                    일시정지
                  </button>
                {:else if job.status === 'paused'}
                  <button 
                    class="btn btn-sm btn-secondary" 
                    on:click={(e) => { e.stopPropagation(); handleResumeJob(job.id); }}
                  >
                    재개
                  </button>
                {/if}
                
                <button 
                  class="btn btn-sm btn-secondary" 
                  on:click={(e) => { e.stopPropagation(); handleCancelJob(job.id); }}
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
    {#if $completedJobs.length > 0}
      <div>
        <h3 class="text-md font-medium mb-2">최근 완료된 작업</h3>
        <div class="space-y-2">
          {#each $completedJobs.slice(0, 5) as job}
            <div 
              class="p-2 border rounded-lg bg-gray-50 cursor-pointer hover:bg-gray-100" 
              on:click={() => showJobDetails(job)}
            >
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
                    on:click={(e) => e.stopPropagation()}
                  >
                    자막 다운로드
                  </a>
                </div>
              {/if}
              
              {#if job.error}
                <div class="text-xs text-red-600 mt-1 truncate" title={job.error}>
                  오류: {job.error.substring(0, 50)}{job.error.length > 50 ? '...' : ''}
                </div>
              {/if}
            </div>
          {/each}
          
          {#if $completedJobs.length > 5}
            <div class="text-center text-sm text-gray-500">
              외 {$completedJobs.length - 5}개 작업
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {/if}
  
  <!-- 작업 상세 정보 모달 -->
  {#if showModal && selectedJob}
    <div class="modal-backdrop" on:click={closeModal}>
      <div class="modal-content" on:click={(e) => e.stopPropagation()}>
        <div class="modal-header">
          <h3 class="text-lg font-semibold">작업 상세 정보</h3>
          <button class="modal-close" on:click={closeModal}>&times;</button>
        </div>
        <div class="modal-body">
          <div class="mb-4">
            <div class="text-sm text-gray-600">파일</div>
            <div class="font-medium">{getShortFileName(selectedJob.file_path)}</div>
            <div class="text-xs text-gray-500 mt-1">{selectedJob.file_path}</div>
          </div>
          
          <div class="mb-4">
            <div class="text-sm text-gray-600">상태</div>
            <div class={getStatusColorClass(selectedJob.status)}>
              {getStatusText(selectedJob.status)}
            </div>
          </div>
          
          {#if selectedJob.job_type}
            <div class="mb-4">
              <div class="text-sm text-gray-600">작업 유형</div>
              <div>{selectedJob.job_type}</div>
            </div>
          {/if}
          
          {#if selectedJob.progress !== undefined}
            <div class="mb-4">
              <div class="text-sm text-gray-600">진행률</div>
              <div class="progress-bar mt-1">
                <div 
                  class="progress-bar-fill" 
                  style="width: {selectedJob.progress}%;"
                ></div>
              </div>
              <div class="text-right mt-1">{selectedJob.progress}%</div>
            </div>
          {/if}
          
          {#if selectedJob.subtitle_path}
            <div class="mb-4">
              <div class="text-sm text-gray-600">자막 파일</div>
              <div class="break-all">{selectedJob.subtitle_path}</div>
              <div class="mt-2">
                <a 
                  href={`/download?path=${encodeURIComponent(selectedJob.subtitle_path)}`} 
                  class="btn btn-sm btn-primary"
                >
                  자막 다운로드
                </a>
              </div>
            </div>
          {/if}
          
          {#if selectedJob.error}
            <div class="mb-4">
              <div class="text-sm text-gray-600">오류 정보</div>
              <div class="p-3 bg-red-50 text-red-800 rounded mt-1">
                {selectedJob.error}
              </div>
              
              <!-- 오류 단계 표시 -->
              <div class="mt-3">
                <div class="text-sm text-gray-600 mb-2">작업 단계</div>
                <div class="space-y-2">
                  {#each getErrorDetails(selectedJob.error) as step}
                    <div class="flex items-center">
                      <div class={`w-2 h-2 rounded-full ${step.status === 'completed' ? 'bg-green-500' : 'bg-red-500'} mr-2`}></div>
                      <div class="flex-1">{step.name}</div>
                      <div class={step.status === 'completed' ? 'text-green-600' : 'text-red-600'}>
                        {step.message}
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          {/if}
          
          <div class="mb-4">
            <div class="text-sm text-gray-600">생성 시간</div>
            <div>{new Date(selectedJob.created_at).toLocaleString()}</div>
          </div>
          
          {#if selectedJob.updated_at && selectedJob.updated_at !== selectedJob.created_at}
            <div class="mb-4">
              <div class="text-sm text-gray-600">마지막 업데이트</div>
              <div>{new Date(selectedJob.updated_at).toLocaleString()}</div>
            </div>
          {/if}
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" on:click={closeModal}>닫기</button>
          
          {#if selectedJob.status === 'processing'}
            <button 
              class="btn btn-secondary" 
              on:click={() => handlePauseJob(selectedJob.id)}
            >
              일시정지
            </button>
          {:else if selectedJob.status === 'paused'}
            <button 
              class="btn btn-secondary" 
              on:click={() => handleResumeJob(selectedJob.id)}
            >
              재개
            </button>
          {/if}
          
          {#if selectedJob.status === 'processing' || selectedJob.status === 'paused' || selectedJob.status === 'queued'}
            <button 
              class="btn btn-primary" 
              on:click={() => { handleCancelJob(selectedJob.id); closeModal(); }}
            >
              취소
            </button>
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .progress-bar {
    width: 100%;
    height: 6px;
    background-color: #e2e8f0;
    border-radius: 3px;
    overflow: hidden;
  }
  
  .progress-bar-fill {
    height: 100%;
    background-color: #3b82f6;
    transition: width 0.3s ease;
  }
  
  /* 모달 스타일 */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .modal-content {
    background-color: white;
    border-radius: 0.5rem;
    width: 90%;
    max-width: 32rem;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid #e2e8f0;
  }
  
  .modal-close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    color: #718096;
  }
  
  .dark .modal-content {
    background-color: #1a202c;
    color: #e2e8f0;
  }
  
  .dark .modal-header,
  .dark .modal-footer {
    border-color: #2d3748;
  }
  
  .dark .modal-close {
    color: #a0aec0;
  }
</style> 