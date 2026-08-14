/**
 * Axios API client for Silent Co-Driver.
 * Configured to communicate exclusively through /api/v1/* endpoints.
 */

import axios, { AxiosProgressEvent } from 'axios';
import { ENDPOINTS } from './endpoints';
import type {
  AudioUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  LapIngestionRequest,
  LapIngestionResponse,
  RaceOverview,
} from '../types';

const apiClient = axios.create({
  timeout: 120_000, // 2 minutes for large audio processing
  headers: {
    'Accept': 'application/json',
  },
});

// ─── Audio API ───────────────────────────────────────────────────────────────

export async function uploadAudio(
  file: File,
  onProgress?: (progress: number) => void
): Promise<AudioUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post<AudioUploadResponse>(
    ENDPOINTS.AUDIO_UPLOAD,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event: AxiosProgressEvent) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    }
  );

  return response.data;
}

// ─── Analysis API ────────────────────────────────────────────────────────────

export async function runAnalysis(
  request: AnalysisRequest
): Promise<AnalysisResponse> {
  const response = await apiClient.post<AnalysisResponse>(
    ENDPOINTS.ANALYSIS,
    request
  );
  return response.data;
}

// ─── Race API ────────────────────────────────────────────────────────────────

export async function ingestLaps(
  request: LapIngestionRequest
): Promise<LapIngestionResponse> {
  const response = await apiClient.post<LapIngestionResponse>(
    ENDPOINTS.RACE_LAPS,
    request
  );
  return response.data;
}

export async function getRace(raceId: string): Promise<RaceOverview> {
  const response = await apiClient.get<RaceOverview>(
    ENDPOINTS.RACE_DETAIL(raceId)
  );
  return response.data;
}

// ─── Health ──────────────────────────────────────────────────────────────────

export async function healthCheck(): Promise<Record<string, unknown>> {
  const response = await apiClient.get(ENDPOINTS.HEALTH);
  return response.data;
}

export default apiClient;
