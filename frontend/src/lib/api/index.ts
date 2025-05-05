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
    const response = await fetch(`${API_BASE_URL}/browse?path=${encodeURIComponent(path)}`);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
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
    const url = `${API_BASE_URL}/search?path=${encodeURIComponent(path)}&with_subtitle=${withSubtitle}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
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
      body: JSON.stringify({ files, language, model })
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
    const response = await fetch(`${API_BASE_URL}/jobs`);
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
    return await response.json();
  } catch (error) {
    return handleError(error);
  }
};

/**
 * 작업 제어 (일시정지, 재개, 취소)
 */
export const controlJob = async (
  jobId: string, 
  action: 'pause' | 'resume' | 'cancel'
): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/job/${jobId}/${action}`, {
      method: 'POST'
    });
    
    if (!response.ok) throw new Error(`서버 오류: ${response.status}`);
  } catch (error) {
    handleError(error);
  }
};

/**
 * 자막 다운로드 URL 생성
 */
export const getSubtitleDownloadUrl = (subtitlePath: string): string => {
  return `${API_BASE_URL}/download?path=${encodeURIComponent(subtitlePath)}`;
};

export default {
  getDirectories,
  searchMediaFiles,
  runWhisper,
  getJobs,
  controlJob,
  getSubtitleDownloadUrl
}; 