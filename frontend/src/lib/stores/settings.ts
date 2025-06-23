/**
 * 사용자 환경설정 스토어
 * Whisper 설정, UI 설정 등 각종 사용자 설정을 로컬 스토리지에 저장합니다.
 */

import { writable, derived, get, type Writable } from 'svelte/store';
import { browser } from '$app/environment';

// 기본 설정값
const DEFAULT_SETTINGS = {
  whisper: {
    language: 'ko',
    model: 'small', 
    autoStart: false
  },
  ui: {
    darkMode: false,
    tableRowsPerPage: 10,
    showHiddenFiles: false
  },
  filters: {
    showWithSubtitle: false,
    videoOnly: false,
    audioOnly: false
  },
  system: {
    nasMediaPath: '',
    openSubtitlesApiKey: ''
  }
};

// 타입 정의
export type WhisperSettings = typeof DEFAULT_SETTINGS.whisper;
export type UISettings = typeof DEFAULT_SETTINGS.ui;
export type FilterSettings = typeof DEFAULT_SETTINGS.filters;
export type SystemSettings = typeof DEFAULT_SETTINGS.system;
export type Settings = typeof DEFAULT_SETTINGS;

// 로컬 스토리지에서 설정 불러오기
const loadSettings = (): Settings => {
  if (!browser) return DEFAULT_SETTINGS;
  
  try {
    const savedSettings = localStorage.getItem('whisper_app_settings');
    if (savedSettings) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(savedSettings) };
    }
  } catch (error) {
    console.error('설정 불러오기 오류:', error);
  }
  
  return DEFAULT_SETTINGS;
};

// 로컬 스토리지에 설정 저장
const saveSettings = (settings: Settings) => {
  if (!browser) return;
  
  try {
    localStorage.setItem('whisper_app_settings', JSON.stringify(settings));
  } catch (error) {
    console.error('설정 저장 오류:', error);
  }
};

// 설정 스토어 생성
export const settings: Writable<Settings> = writable(loadSettings());

// 설정 변경 시 자동 저장
settings.subscribe(value => {
  saveSettings(value);
});

// 개별 설정 접근을 위한 파생 스토어
export const whisperSettings = derived(
  settings,
  $settings => $settings.whisper
);

export const uiSettings = derived(
  settings,
  $settings => $settings.ui
);

export const filterSettings = derived(
  settings,
  $settings => $settings.filters
);

export const systemSettings = derived(
  settings,
  $settings => $settings.system
);

// 설정 업데이트 함수들
export const updateWhisperSettings = (newSettings: Partial<WhisperSettings>) => {
  settings.update(s => ({
    ...s,
    whisper: { ...s.whisper, ...newSettings }
  }));
};

export const updateUISettings = (newSettings: Partial<UISettings>) => {
  settings.update(s => ({
    ...s,
    ui: { ...s.ui, ...newSettings }
  }));
};

export const updateFilterSettings = (newSettings: Partial<FilterSettings>) => {
  settings.update(s => ({
    ...s,
    filters: { ...s.filters, ...newSettings }
  }));
};

export const updateSystemSettings = (newSettings: Partial<SystemSettings>) => {
  settings.update(s => ({
    ...s,
    system: { ...s.system, ...newSettings }
  }));
};

export default {
  settings,
  whisperSettings,
  uiSettings,
  filterSettings,
  systemSettings,
  updateWhisperSettings,
  updateUISettings,
  updateFilterSettings,
  updateSystemSettings
}; 