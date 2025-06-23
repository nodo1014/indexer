/**
 * API 클라이언트
 * FastAPI 백엔드와 통신하기 위한 API 호출 함수들을 제공합니다.
 */

// API 기본 URL 설정
const API_BASE_URL = 'http://localhost:8000';

// 타입 정의
export interface DirectoryItem {
  name: string;
  path: string;
  is_directory: boolean;
  video_count: number;
  audio_count: number;
}

export interface MediaFile {
  name: string;
  path: string;
  type: 'video' | 'audio';
  size: number;
  has_subtitle: boolean;
  subtitle_files?: string[];
}

export interface SearchResult {
  files: MediaFile[];
  total_files: number;
  video_count: number;
  audio_count: number;
  with_subtitle_count: number;
  without_subtitle_count: number;
}

export interface WhisperJob {
  id: string;
  file_path: string;
  file_name: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'paused';
  progress: number;
  language: string;
  model: string;
  created_at: string;
  updated_at: string;
  error?: string;
  subtitle_path?: string;
}

export interface SyncCheckResult {
  media_path: string;
  subtitle_path: string;
  sync_status: 'good' | 'needs_adjustment' | 'bad';
  offset: number;
  confidence_score: number;
  segments: SyncSegment[];
  adjusted_subtitle_path?: string;
}

export interface SyncSegment {
  position: 'start' | 'middle' | 'end';
  time_position: number;
  similarity_score: number;
  subtitle_text: string;
  transcribed_text: string;
  offset: number;
}

export interface SystemSettings {
  nas_media_path: string;
  opensubtitles_api_key: string;
}

// API 호출 함수

/**
 * 오류 핸들링 함수
 */
const handleError = (error: any): never => {
  console.error('API 오류:', error);
  throw error;
};

/**
 * 디렉토리 목록 조회
 */
export const getDirectories = async (path: string = ''): Promise<DirectoryItem[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/browse?current_path=${encodeURIComponent(path)}`);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    const data = await response.json();
    return data.directories || [];
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 미디어 파일 검색
 */
export const searchMediaFiles = async (
  path: string, 
  withSubtitle: boolean = false
): Promise<SearchResult> => {
  try {
    // API 경로 수정: /api/files 사용
    const url = `${API_BASE_URL}/api/files?scan_path=${encodeURIComponent(path)}`;
    const response = await fetch(url);
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    
    const data = await response.json();
    
    // 클라이언트 측에서 withSubtitle 필터 처리
    if (!withSubtitle) {
      // 자막이 없는 파일만 필터링
      data.files = data.files.filter((file: MediaFile) => !file.has_subtitle);
    }
    
    return data;
  } catch (error) {
    return handleError(error);
  }
};

/**
 * Whisper 작업 실행
 */
export const runWhisper = async (
  files: string[], 
  language: string, 
  model: string
): Promise<WhisperJob[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/run-whisper`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ files, language, model_size: model, client_id: 'frontend' })
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 현재 작업 목록 조회
 */
export const getJobs = async (): Promise<WhisperJob[]> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/jobs`);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    const data = await response.json();
    return data.jobs || [];
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 작업 제어 (일시정지, 재개, 취소)
 */
export const controlJob = async (
  jobId: string, 
  action: 'pause' | 'resume' | 'stop' | 'delete'
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/job/${jobId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
  } catch (error) {
    handleError(error);
  }
};

/**
 * 자막 싱크 검증
 */
export const checkSubtitleSync = async (
  mediaPath: string,
  subtitlePath: string
): Promise<SyncCheckResult> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/check_sync`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ media_path: mediaPath, subtitle_path: subtitlePath })
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 자막 오프셋 조정
 */
export const adjustSubtitleOffset = async (
  subtitlePath: string,
  offset: number
): Promise<{adjusted_subtitle_path: string}> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/adjust_subtitle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ subtitle_path: subtitlePath, offset })
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 자막 다운로드 URL 생성
 */
export const getSubtitleDownloadUrl = (subtitlePath: string): string => {
  return `${API_BASE_URL}/download?path=${encodeURIComponent(subtitlePath)}`;
};

/**
 * 자막 다운로드 함수
 * OpenSubtitles API를 통해 자막을 검색하고 다운로드합니다.
 */
export async function downloadSubtitle(
  mediaPath: string,
  language: string = 'ko',
  useMultilingual: boolean = false,
  languages: string[] = ['ko', 'en']
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/download_subtitle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      media_path: mediaPath,
      language,
      use_multilingual: useMultilingual,
      languages: useMultilingual ? languages : [language]
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '자막 다운로드 실패');
  }

  return await response.json();
}

/**
 * 자막 자동 처리 통합 함수
 * 자막 다운로드, 싱크 확인, 필요시 오프셋 조정을 한 번에 처리합니다.
 */
export async function autoProcessSubtitle(
  mediaPath: string,
  language: string = 'ko',
  useMultilingual: boolean = false,
  languages: string[] = ['ko', 'en']
): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/auto_process_subtitle`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      media_path: mediaPath,
      language,
      use_multilingual: useMultilingual,
      languages: useMultilingual ? languages : [language]
    })
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || '자막 자동 처리 실패');
  }

  return await response.json();
}

/**
 * 시스템 설정 조회
 */
export const getSystemSettings = async (): Promise<SystemSettings> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/settings`);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 시스템 설정 업데이트
 */
export const updateSystemSettings = async (settings: Partial<SystemSettings>): Promise<SystemSettings> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

export default {
  getDirectories,
  searchMediaFiles,
  runWhisper,
  getJobs,
  controlJob,
  checkSubtitleSync,
  adjustSubtitleOffset,
  getSubtitleDownloadUrl,
  downloadSubtitle,
  autoProcessSubtitle,
  getSystemSettings,
  updateSystemSettings
}; 