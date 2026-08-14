/**
 * API endpoint definitions for Silent Co-Driver.
 * All backend route paths defined centrally.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_V1 = `${API_BASE}/api/v1`;

export const ENDPOINTS = {
  // Audio
  AUDIO_UPLOAD: `${API_V1}/audio/upload`,

  // Analysis
  ANALYSIS: `${API_V1}/analysis`,

  // Race
  RACE_LAPS: `${API_V1}/race/laps`,
  RACE_DETAIL: (raceId: string) => `${API_V1}/race/${raceId}`,

  // System
  HEALTH: `${API_BASE}/health`,
} as const;
