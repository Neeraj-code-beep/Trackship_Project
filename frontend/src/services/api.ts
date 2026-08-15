/**
 * Axios API client for Silent Co-Driver.
 * Configured to communicate exclusively through /api/v1/* endpoints.
 */

import axios from 'axios';
import type { AxiosProgressEvent } from 'axios';
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

export async function uploadLapTelemetryCsv(
  request: {
    raceId: string;
    driverName: string;
    file: File;
  }
): Promise<LapIngestionResponse> {
  const formData = new FormData();
  formData.append('race_id', request.raceId);
  formData.append('driver_name', request.driverName);
  formData.append('file', request.file);

  const response = await apiClient.post<LapIngestionResponse>(
    ENDPOINTS.RACE_LAPS_CSV,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
    }
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

export function normalizeError(err: unknown): string {
  if (!err) return 'An unknown error occurred.';

  if (axios.isAxiosError(err)) {
    if (!err.response) {
      return 'Unable to connect to the backend.';
    }

    const status = err.response.status;
    const data = err.response.data as any;

    if (status === 422) {
      if (data && data.error && Array.isArray(data.error.details)) {
        try {
          const messages = data.error.details.map((d: any) => {
            const field = Array.isArray(d.location) ? d.location.slice(1).join('.') : '';
            return field ? `${field}: ${d.message}` : d.message;
          });
          return `Validation failed: ${messages.join(', ')}`;
        } catch {
          return 'Some submitted data is invalid.';
        }
      }
      if (data && Array.isArray(data.detail)) {
        try {
          const messages = data.detail.map((d: any) => {
            const field = Array.isArray(d.loc) ? d.loc.slice(1).join('.') : '';
            return field ? `${field}: ${d.msg}` : d.msg;
          });
          return `Validation failed: ${messages.join(', ')}`;
        } catch {
          return 'Some submitted data is invalid.';
        }
      }
      return 'Some submitted data is invalid.';
    }

    if (status === 400) {
      return data && typeof data.detail === 'string' ? data.detail : 'Invalid request.';
    }
    if (status === 404) {
      return data && typeof data.detail === 'string' ? data.detail : 'Resource not found.';
    }
    if (status === 413) {
      return 'Audio file is too large.';
    }
    if (status === 500) {
      return 'Server error. Please try again.';
    }
    if (status === 503) {
      return 'Required AI model service is currently unavailable.';
    }

    if (data && typeof data.detail === 'string') {
      return data.detail;
    }
  }

  const errorObj = err as Error;
  return errorObj.message || 'An unexpected error occurred.';
}

export default apiClient;
