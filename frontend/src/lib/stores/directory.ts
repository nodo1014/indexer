/**
 * 디렉토리 상태 관리 스토어
 * 디렉토리 탐색 및 현재 경로 상태를 관리합니다.
 */

import { writable, derived, type Writable, type Readable } from 'svelte/store';
import type { DirectoryItem } from '$lib/api';
import { getDirectories } from '$lib/api';

// 상태 정의
export const currentPath: Writable<string> = writable('');
export const directoryItems: Writable<DirectoryItem[]> = writable([]);
export const isLoading: Writable<boolean> = writable(false);
export const errorMessage: Writable<string | null> = writable(null);

// 파생 스토어: 현재 경로의 상위 경로(들)
export const parentPaths: Readable<{ path: string; name: string }[]> = derived(
  currentPath,
  $currentPath => {
    if (!$currentPath) return [];
    
    const parts = $currentPath.split('/').filter(Boolean);
    let accumPath = '';
    
    return parts.map((part, index) => {
      accumPath = index === 0 ? part : `${accumPath}/${part}`;
      return {
        path: accumPath,
        name: part
      };
    });
  }
);

/**
 * 디렉토리 불러오기
 */
export const loadDirectory = async (path: string = '') => {
  isLoading.set(true);
  errorMessage.set(null);
  
  try {
    const items = await getDirectories(path);
    directoryItems.set(items);
    currentPath.set(path);
  } catch (error) {
    console.error('디렉토리 로드 오류:', error);
    errorMessage.set('디렉토리를 불러오는 중 오류가 발생했습니다.');
    directoryItems.set([]);
  } finally {
    isLoading.set(false);
  }
};

/**
 * 상위 디렉토리로 이동
 */
export const navigateUp = () => {
  currentPath.update($currentPath => {
    const parts = $currentPath.split('/').filter(Boolean);
    parts.pop();
    const newPath = parts.join('/');
    loadDirectory(newPath);
    return newPath;
  });
};

/**
 * 디렉토리 탐색 초기화
 */
export const initializeDirectoryBrowser = () => {
  loadDirectory('');
};

export default {
  currentPath,
  directoryItems,
  parentPaths,
  isLoading,
  errorMessage,
  loadDirectory,
  navigateUp,
  initializeDirectoryBrowser
}; 