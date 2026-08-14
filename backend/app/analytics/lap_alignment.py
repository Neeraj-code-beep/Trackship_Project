"""
Lap alignment module.
Aligns audio transcript timestamps and emotion data with race lap timing data.
"""

from __future__ import annotations

from typing import Optional
from backend.app.schemas.schemas import (
    LapData,
    TranscriptSegment,
    DriverState,
    AlignedLapEmotion,
    EmotionLabel,
)


def compute_lap_boundaries(laps: list[LapData]) -> list[tuple[float, float]]:
    """
    Compute the start/end timestamps for each lap based on cumulative lap times.
    
    Returns:
        List of (start_time, end_time) tuples aligned to race clock.
    """
    boundaries: list[tuple[float, float]] = []
    cursor = 0.0

    for lap in laps:
        # If the lap has an explicit timestamp, use it as end
        if lap.timestamp is not None:
            end = lap.timestamp
            start = end - lap.lap_time_seconds
        else:
            start = cursor
            end = cursor + lap.lap_time_seconds
        boundaries.append((start, end))
        cursor = end

    return boundaries


def align_segments_to_laps(
    segments: list[TranscriptSegment],
    boundaries: list[tuple[float, float]],
) -> dict[int, list[TranscriptSegment]]:
    """
    Map transcript segments to the lap they fall within.
    
    Returns:
        Dict mapping lap_number (1-indexed) to list of transcript segments.
    """
    lap_segments: dict[int, list[TranscriptSegment]] = {}

    for seg in segments:
        seg_mid = (seg.start_time + seg.end_time) / 2.0
        for i, (start, end) in enumerate(boundaries):
            if start <= seg_mid < end:
                lap_num = i + 1
                lap_segments.setdefault(lap_num, []).append(seg)
                break

    return lap_segments


def align_emotions_to_laps(
    driver_states: list[DriverState],
    boundaries: list[tuple[float, float]],
) -> dict[int, list[DriverState]]:
    """
    Map driver emotion states to the lap they fall within.
    
    Returns:
        Dict mapping lap_number (1-indexed) to list of DriverState entries.
    """
    lap_emotions: dict[int, list[DriverState]] = {}

    for state in driver_states:
        for i, (start, end) in enumerate(boundaries):
            if start <= state.timestamp < end:
                lap_num = i + 1
                lap_emotions.setdefault(lap_num, []).append(state)
                break

    return lap_emotions


def aggregate_lap_emotions(
    states: list[DriverState],
) -> tuple[EmotionLabel, float, float]:
    """
    Aggregate emotion states for a single lap into dominant emotion, 
    average stress, and average fatigue.
    """
    if not states:
        return EmotionLabel.NEUTRAL, 0.0, 0.0

    stress_sum = sum(s.probabilities.stressed for s in states)
    fatigue_sum = sum(s.probabilities.tired for s in states)
    n = len(states)

    avg_stress = stress_sum / n
    avg_fatigue = fatigue_sum / n

    # Count dominant emotions
    emotion_counts: dict[EmotionLabel, int] = {}
    for s in states:
        emotion_counts[s.dominant_emotion] = emotion_counts.get(s.dominant_emotion, 0) + 1

    dominant = max(emotion_counts, key=emotion_counts.get)  # type: ignore

    return dominant, round(avg_stress, 4), round(avg_fatigue, 4)


def build_aligned_laps(
    laps: list[LapData],
    driver_states: list[DriverState],
) -> list[AlignedLapEmotion]:
    """
    Full alignment pipeline: builds AlignedLapEmotion entries by mapping
    emotion data onto lap boundaries and computing deltas.
    """
    if not laps:
        return []

    boundaries = compute_lap_boundaries(laps)
    lap_emotions = align_emotions_to_laps(driver_states, boundaries)

    # Find best lap time for delta computation
    best_time = min(lap.lap_time_seconds for lap in laps)

    aligned: list[AlignedLapEmotion] = []
    for lap in laps:
        states = lap_emotions.get(lap.lap_number, [])
        dominant, stress, fatigue = aggregate_lap_emotions(states)

        aligned.append(
            AlignedLapEmotion(
                lap_number=lap.lap_number,
                lap_time_seconds=lap.lap_time_seconds,
                delta_to_best=round(lap.lap_time_seconds - best_time, 3),
                dominant_emotion=dominant,
                stress_level=stress,
                fatigue_level=fatigue,
            )
        )

    return aligned
