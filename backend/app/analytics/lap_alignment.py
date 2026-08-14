"""Timestamp-to-lap alignment using explicit normalized lap boundaries."""

from __future__ import annotations

import math

from backend.app.analytics.lap_performance import compute_lap_baseline, lap_delta
from backend.app.schemas.schemas import (
    AlignedLapEmotion,
    DriverState,
    EmotionLabel,
    LapData,
    TranscriptSegment,
)
from backend.app.services.lap_service import normalize_laps

BOUNDARY_TOLERANCE_SECONDS = 1e-9


def compute_lap_boundaries(laps: list[LapData]) -> list[tuple[float, float]]:
    """Return validated start/end boundaries in the same order as the laps."""
    normalized = normalize_laps(laps)
    return [(float(lap.start_time), float(lap.end_time)) for lap in normalized]


def timestamp_to_lap(timestamp: float, laps: list[LapData]) -> LapData | None:
    """Map a race-clock timestamp using left-closed, right-open intervals."""
    if not math.isfinite(timestamp) or not laps:
        return None

    normalized = normalize_laps(laps)
    for index, lap in enumerate(normalized):
        start = float(lap.start_time)
        end = float(lap.end_time)
        if start <= timestamp < end:
            return lap
        is_final = index == len(normalized) - 1
        if is_final and math.isclose(
            timestamp,
            end,
            rel_tol=0.0,
            abs_tol=BOUNDARY_TOLERANCE_SECONDS,
        ):
            return lap
    return None


def align_segments_to_laps(
    segments: list[TranscriptSegment],
    laps: list[LapData],
) -> dict[int, list[TranscriptSegment]]:
    """Assign crossing transcript segments by midpoint."""
    aligned: dict[int, list[TranscriptSegment]] = {}
    for segment in segments:
        midpoint = (segment.start_time + segment.end_time) / 2.0
        lap = timestamp_to_lap(midpoint, laps)
        if lap is not None:
            aligned.setdefault(lap.lap_number, []).append(segment)
    return aligned


def align_emotions_to_laps(
    driver_states: list[DriverState],
    laps: list[LapData],
) -> dict[int, list[DriverState]]:
    """Assign driver states by their segment midpoint, or timestamp when unavailable."""
    aligned: dict[int, list[DriverState]] = {}
    for state in driver_states:
        start = state.start_time if state.start_time is not None else state.timestamp
        end = state.end_time if state.end_time is not None else start
        midpoint = (start + end) / 2.0
        lap = timestamp_to_lap(midpoint, laps)
        if lap is not None:
            aligned.setdefault(lap.lap_number, []).append(state)
    return aligned


def build_aligned_laps(
    laps: list[LapData],
    driver_states: list[DriverState],
) -> list[AlignedLapEmotion]:
    """Aggregate aligned state evidence for each normalized lap."""
    if not laps:
        return []
    normalized = normalize_laps(laps)
    lap_states = align_emotions_to_laps(driver_states, normalized)
    best_time = min(lap.lap_time_seconds for lap in normalized)
    baseline = compute_lap_baseline(normalized)
    outlier_laps = set(baseline.outlier_lap_numbers)

    aligned: list[AlignedLapEmotion] = []
    for lap in normalized:
        states = lap_states.get(lap.lap_number, [])
        stress_score = _average([state.stress_score for state in states])
        fatigue_score = _average([state.fatigue_score for state in states])
        calm_score = _average([state.calm_score for state in states])
        dominant = _dominant_state(states, stress_score, fatigue_score, calm_score)
        aligned.append(
            AlignedLapEmotion(
                lap_number=lap.lap_number,
                lap_time_seconds=lap.lap_time_seconds,
                start_time=float(lap.start_time),
                end_time=float(lap.end_time),
                baseline_lap_time=baseline.baseline_lap_time,
                lap_delta=lap_delta(
                    lap.lap_time_seconds,
                    baseline.baseline_lap_time,
                ),
                delta_to_best=round(lap.lap_time_seconds - best_time, 3),
                is_timing_outlier=lap.lap_number in outlier_laps,
                dominant_emotion=dominant,
                stress_level=round(stress_score / 100.0, 4),
                fatigue_level=round(fatigue_score / 100.0, 4),
                stress_score=stress_score,
                fatigue_score=fatigue_score,
                calm_score=calm_score,
                segment_ids=[state.segment_id for state in states if state.segment_id],
            )
        )
    return aligned


def _average(values: list[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return round(sum(finite) / len(finite), 1) if finite else 0.0


def _dominant_state(
    states: list[DriverState],
    stress_score: float,
    fatigue_score: float,
    calm_score: float,
) -> EmotionLabel:
    if not states:
        return EmotionLabel.NEUTRAL
    scores = {
        EmotionLabel.STRESSED: stress_score,
        EmotionLabel.TIRED: fatigue_score,
        EmotionLabel.CALM: calm_score,
    }
    best = max(scores, key=scores.get)
    return best if scores[best] >= 50.0 else EmotionLabel.NEUTRAL
