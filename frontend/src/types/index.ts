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
  segment_id: string | null;
  timestamp: number;
  start_time: number | null;
  end_time: number | null;
  dominant_emotion: EmotionLabel;
  probabilities: EmotionProbabilities;
  raw_emotions: Record<string, number>;
  confidence: number;
  stress_score: number;
  fatigue_score: number;
  calm_score: number;
  signals: Record<string, number>;
  drivers: string[];
  rms_energy: number | null;
  speech_rate_wpm: number | null;
  acoustic_features: AcousticFeatures | null;
}

// ─── Transcription ───────────────────────────────────────────────────────────

export interface TranscriptSegment {
  id: string;
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

export interface AcousticFeatures {
  rms_energy: number;
  pitch_mean_hz: number | null;
  pitch_std_hz: number | null;
  zero_crossing_rate: number;
  spectral_centroid_hz: number;
  duration_seconds: number;
  pause_ratio: number;
  speech_rate_wpm: number | null;
  voiced_ratio: number;
  energy_variability: number;
}

export interface SegmentAcousticFeatures {
  segment_id: string;
  start_time: number;
  end_time: number;
  features: AcousticFeatures;
  session_deviations: Record<string, number>;
}

export interface AcousticAnalysis {
  session_baselines: Record<string, number>;
  segments: SegmentAcousticFeatures[];
}

// ─── Lap / Race ──────────────────────────────────────────────────────────────

export interface LapData {
  lap_number: number;
  lap_time_seconds: number;
  start_time: number | null;
  end_time: number | null;
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
  start_time: number;
  end_time: number;
  baseline_lap_time: number;
  lap_delta: number;
  delta_to_best: number;
  is_timing_outlier: boolean;
  dominant_emotion: EmotionLabel;
  stress_level: number;
  fatigue_level: number;
  stress_score: number;
  fatigue_score: number;
  calm_score: number;
  segment_ids: string[];
}

export interface AnalysisSummary {
  dominant_state: EmotionLabel;
  average_stress_score: number;
  average_fatigue_score: number;
  average_calm_score: number;
  segments_analyzed: number;
}

export interface CorrelationResult {
  metric: string;
  pearson_r: number | null;
  sample_size: number;
  direction: string;
  strength: string;
  reason: string | null;
  excluded_lap_numbers: number[];
}

export interface CorrelationSummary {
  stress_vs_lap_delta: CorrelationResult;
  fatigue_vs_lap_delta: CorrelationResult;
}

export interface FatigueTrend {
  trend: string;
  change: number | null;
  early_average: number | null;
  late_average: number | null;
  sample_size: number;
  reason: string | null;
}

export interface InsightItem {
  id: string;
  severity: InsightSeverity;
  priority: 'low' | 'medium' | 'high';
  type: string;
  title: string;
  category: string;
  message: string;
  evidence: Record<string, unknown>;
  lap_number: number | null;
  timestamp: number | null;
  data: Record<string, unknown> | null;
}

export interface AnalysisResponse {
  analysis_id: string;
  audio_id: string;
  file_id: string;
  race_id: string | null;
  summary: AnalysisSummary;
  transcription: TranscriptionResult | null;
  acoustic_analysis: AcousticAnalysis;
  driver_states: DriverState[];
  aligned_laps: AlignedLapEmotion[];
  correlations: CorrelationSummary;
  fatigue_trend: FatigueTrend;
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
  baseline_lap_time: number | null;
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
