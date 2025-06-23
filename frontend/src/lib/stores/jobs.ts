/**
 * 작업 관리 스토어
 * Whisper 및 기타 백그라운드 작업의 상태를 관리합니다.
 */

import { writable, derived } from 'svelte/store';
import { getJobs, controlJob } from '$lib/api';
import type { WhisperJob } from '$lib/api';
import { socketMessages } from '$lib/api/websocket';

// 스토어 정의
export const jobs = writable<WhisperJob[]>([]);
export const isLoading = writable(false);
export const loadError = writable<string | null>(null);

// 이전 스토어와의 호환성을 위한 별칭
export const isLoadingJobs = isLoading;
export const jobsError = loadError;

// 자동 새로고침 설정
const AUTO_REFRESH_INTERVAL = 30000; // 30초
let refreshTimer: number | null = null;

/**
 * 작업 목록 로드
 */
export async function loadJobs() {
  isLoading.set(true);
  loadError.set(null);
  
  try {
    const jobsList = await getJobs();
    jobs.set(jobsList);
  } catch (error) {
    console.error('작업 목록 로드 오류:', error);
    loadError.set(error.message || '작업 목록을 불러오는 데 실패했습니다.');
  } finally {
    isLoading.set(false);
  }
}

/**
 * 작업 데이터 필터링된 파생 스토어
 */
export const queuedJobs = derived(jobs, $jobs => 
  $jobs.filter(job => job.status === 'queued')
);

export const activeJobs = derived(jobs, $jobs => 
  $jobs.filter(job => ['queued', 'processing', 'paused'].includes(job.status))
);

export const completedJobs = derived(jobs, $jobs => 
  $jobs.filter(job => ['completed', 'failed'].includes(job.status))
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
);

export const failedJobs = derived(jobs, $jobs => 
  $jobs.filter(job => job.status === 'failed')
);

/**
 * 작업 일시정지
 */
export async function pauseJob(jobId: string): Promise<void> {
  try {
    await controlJob(jobId, 'pause');
    // 로컬 상태 업데이트
    jobs.update($jobs => {
      const index = $jobs.findIndex(job => job.id === jobId);
      if (index !== -1) {
        $jobs[index] = { ...$jobs[index], status: 'paused' };
      }
      return $jobs;
    });
  } catch (error) {
    console.error('작업 일시정지 오류:', error);
    throw error;
  }
}

/**
 * 작업 재개
 */
export async function resumeJob(jobId: string): Promise<void> {
  try {
    await controlJob(jobId, 'resume');
    // 로컬 상태 업데이트
    jobs.update($jobs => {
      const index = $jobs.findIndex(job => job.id === jobId);
      if (index !== -1) {
        $jobs[index] = { ...$jobs[index], status: 'processing' };
      }
      return $jobs;
    });
  } catch (error) {
    console.error('작업 재개 오류:', error);
    throw error;
  }
}

/**
 * 작업 취소
 */
export async function cancelJob(jobId: string): Promise<void> {
  try {
    await controlJob(jobId, 'stop');
    // 로컬 상태 업데이트
    jobs.update($jobs => {
      const index = $jobs.findIndex(job => job.id === jobId);
      if (index !== -1) {
        $jobs[index] = { ...$jobs[index], status: 'failed', progress: 0 };
      }
      return $jobs;
    });
  } catch (error) {
    console.error('작업 취소 오류:', error);
    throw error;
  }
}

/**
 * WebSocket 메시지 처리를 통한 작업 업데이트
 */
socketMessages.subscribe(messages => {
  if (messages.length === 0) return;
  
  // 가장 최근 메시지 가져오기
  const latestMessage = messages[messages.length - 1];
  
  if (latestMessage.type === 'progress_update' || latestMessage.type === 'job_update') {
    // 작업 상태 업데이트
    jobs.update($jobs => {
      const jobIndex = $jobs.findIndex(job => job.id === latestMessage.job_id);
      
      if (jobIndex !== -1) {
        $jobs[jobIndex] = {
          ...$jobs[jobIndex],
          progress: latestMessage.progress || $jobs[jobIndex].progress,
          status: latestMessage.status || $jobs[jobIndex].status,
          error: latestMessage.error || $jobs[jobIndex].error,
        };
      }
      
      return $jobs;
    });
  } else if (latestMessage.type === 'job_complete') {
    // 작업 완료 시 목록 새로고침
    loadJobs();
  }
});

/**
 * 자동 새로고침 시작
 */
export function startAutoRefresh() {
  if (refreshTimer !== null) return;
  
  refreshTimer = window.setInterval(() => {
    loadJobs();
  }, AUTO_REFRESH_INTERVAL);
}

/**
 * 자동 새로고침 중지
 */
export function stopAutoRefresh() {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

// 작업 초기 로드 및 자동 새로고침 시작
loadJobs().then(() => {
  startAutoRefresh();
});

// 페이지 언로드 시 자동 새로고침 중지
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
  });
}

export default {
  jobs,
  isLoading,
  loadError,
  isLoadingJobs,
  jobsError,
  queuedJobs,
  activeJobs,
  completedJobs,
  failedJobs,
  loadJobs,
  pauseJob,
  resumeJob,
  cancelJob,
  startAutoRefresh,
  stopAutoRefresh
}; 