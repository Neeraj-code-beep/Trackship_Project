import type { AnalysisResponse, CorrelationResult } from '../../types';

export interface DriverStateView {
  stressScore: number | null;
  fatigueScore: number | null;
  calmScore: number | null;
  confidence: number | null;
}

export function getDriverStateView(analysis: AnalysisResponse | null): DriverStateView {
  if (!analysis || analysis.driver_states.length === 0) {
    return { stressScore: null, fatigueScore: null, calmScore: null, confidence: null };
  }

  const confidence = analysis.driver_states.reduce((sum, state) => sum + state.confidence, 0)
    / analysis.driver_states.length;

  return {
    stressScore: analysis.summary.average_stress_score,
    fatigueScore: analysis.summary.average_fatigue_score,
    calmScore: analysis.summary.average_calm_score,
    confidence,
  };
}

export function formatLapTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return '--:--.---';
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${secs.toFixed(3).padStart(6, '0')}`;
}

export function formatCorrelation(result?: CorrelationResult): string {
  if (!result || result.pearson_r === null) return 'Correlation unavailable';
  const signed = result.pearson_r >= 0 ? `+${result.pearson_r.toFixed(2)}` : result.pearson_r.toFixed(2);
  return `${signed} · ${result.direction} ${result.strength}`;
}

export function correlationReason(result?: CorrelationResult): string {
  return result?.reason ? result.reason.replaceAll('_', ' ') : 'insufficient aligned data';
}
