/**
 * 네비게이션 스토어
 * 애플리케이션 내 경로, 페이지 이동 등 네비게이션 상태를 관리합니다.
 */

import { writable } from 'svelte/store';

// 현재 상대 경로 저장 (NAS_BASE_PATH 기준)
export const currentPath = writable<string>('');

// 경로 이동 히스토리
export const pathHistory = writable<string[]>([]);

/**
 * 히스토리에 경로 추가
 */
export function addToHistory(path: string) {
  pathHistory.update(history => {
    // 중복 방지
    if (history.length > 0 && history[history.length - 1] === path) {
      return history;
    }
    
    // 최대 20개만 유지
    const newHistory = [...history, path];
    if (newHistory.length > 20) {
      return newHistory.slice(newHistory.length - 20);
    }
    
    return newHistory;
  });
}

/**
 * 경로 변경 처리
 */
export function navigateTo(path: string) {
  currentPath.set(path);
  addToHistory(path);
}

/**
 * 상위 디렉토리로 이동
 */
export function navigateUp() {
  currentPath.update(path => {
    if (!path) return '';
    
    const parts = path.split('/').filter(Boolean);
    if (parts.length === 0) return '';
    
    const newPath = parts.slice(0, -1).join('/');
    addToHistory(newPath);
    return newPath;
  });
} 