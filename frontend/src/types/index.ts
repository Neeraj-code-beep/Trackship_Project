/**
 * TypeScript type definitions for Silent Co-Driver.
 * Mirrors the backend Pydantic schemas for strict type safety.
 */

// ─── Enums ───────────────────────────────────────────────────────────────────

export type EmotionLabel = 'calm' | 'stressed' | 'neutral' | 'tired';
export type InsightSeverity = 'info' | 'warning' | 'critical';

// ─── Audio ───────────────────────────────────────────────────────────────────

export interface AudioUploadResponse {
  file_id: string;
  filename: string;
  file_size_bytes: number;
  duration_seconds: number | null;
  sample_rate: number | null;
  format: string;
  upload_timestamp: string;
  storage_path: string;
  message: string;
}

// ─── Emotion / Driver State ──────────────────────────────────────────────────

export interface EmotionProbabilities {
  calm: number;
  stressed: number;
  neutral: number;
  tired: number;
}

export interface DriverState {
  timestamp: number;
  dominant_emotion: EmotionLabel;
  probabilities: EmotionProbabilities;
  confidence: number;
  rms_energy: number | null;
  speech_rate_wpm: number | null;
}

// ─── Transcription ───────────────────────────────────────────────────────────

export interface TranscriptSegment {
  start_time: number;
  end_time: number;
  text: string;
  confidence: number | null;
  speaker: string | null;
}

export interface TranscriptionResult {
  file_id: string;
  full_text: string;
  segments: TranscriptSegment[];
  language: string | null;
  duration_seconds: number;
  detected_speech: boolean;
}

// ─── Lap / Race ──────────────────────────────────────────────────────────────

export interface LapData {
  lap_number: number;
  lap_time_seconds: number;
  sector_1: number | null;
  sector_2: number | null;
  sector_3: number | null;
  timestamp: number | null;
  tyre_compound: string | null;
  fuel_load_kg: number | null;
}

export interface LapIngestionRequest {
  race_id: string;
  driver_name: string;
  laps: LapData[];
}

export interface LapIngestionResponse {
  race_id: string;
  driver_name: string;
  laps_received: number;
  message: string;
}

// ─── Analysis ────────────────────────────────────────────────────────────────

export interface AnalysisRequest {
  file_id: string;
  race_id?: string;
}

export interface AlignedLapEmotion {
  lap_number: number;
  lap_time_seconds: number;
  delta_to_best: number;
  dominant_emotion: EmotionLabel;
  stress_level: number;
  fatigue_level: number;
}

export interface InsightItem {
  id: string;
  severity: InsightSeverity;
  category: string;
  message: string;
  lap_number: number | null;
  timestamp: number | null;
  data: Record<string, unknown> | null;
}

export interface AnalysisResponse {
  file_id: string;
  race_id: string | null;
  transcription: TranscriptionResult | null;
  driver_states: DriverState[];
  aligned_laps: AlignedLapEmotion[];
  insights: InsightItem[];
  overall_stress: number;
  overall_fatigue: number;
  processing_time_ms: number;
}

// ─── Race Overview ───────────────────────────────────────────────────────────

export interface RaceOverview {
  race_id: string;
  driver_name: string;
  total_laps: number;
  best_lap_time: number | null;
  average_lap_time: number | null;
  laps: LapData[];
  analyses: string[];
  created_at: string;
}

// ─── UI State ────────────────────────────────────────────────────────────────

export interface UploadProgress {
  status: 'idle' | 'uploading' | 'processing' | 'complete' | 'error';
  progress: number;
  message: string;
}
