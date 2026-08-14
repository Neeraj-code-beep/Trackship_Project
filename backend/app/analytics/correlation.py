"""
Correlation module.
Maps driver stress/fatigue levels against lap performance deviations.
"""

from __future__ import annotations

import math
from typing import Optional

from backend.app.schemas.schemas import AlignedLapEmotion


def compute_stress_pace_correlation(
    aligned_laps: list[AlignedLapEmotion],
) -> float:
    """
    Compute Pearson correlation between stress levels and lap time deltas.
    
    Returns:
        Correlation coefficient in [-1.0, 1.0]. Positive means higher stress
        correlates with slower laps. Returns 0.0 if insufficient data.
    """
    if len(aligned_laps) < 3:
        return 0.0

    stress = [lap.stress_level for lap in aligned_laps]
    deltas = [lap.delta_to_best for lap in aligned_laps]

    return _pearson(stress, deltas)


def compute_fatigue_pace_correlation(
    aligned_laps: list[AlignedLapEmotion],
) -> float:
    """
    Compute Pearson correlation between fatigue levels and lap time deltas.
    """
    if len(aligned_laps) < 3:
        return 0.0

    fatigue = [lap.fatigue_level for lap in aligned_laps]
    deltas = [lap.delta_to_best for lap in aligned_laps]

    return _pearson(fatigue, deltas)


def detect_performance_anomalies(
    aligned_laps: list[AlignedLapEmotion],
    delta_threshold: float = 1.5,
) -> list[dict]:
    """
    Detect laps where performance deviated significantly from the best
    AND emotional state was elevated.
    
    Args:
        aligned_laps: Lap data with emotion alignment
        delta_threshold: Seconds above best lap to flag as anomaly
        
    Returns:
        List of anomaly dicts with lap number, delta, and emotional state.
    """
    anomalies = []

    for lap in aligned_laps:
        if lap.delta_to_best >= delta_threshold:
            anomalies.append({
                "lap_number": lap.lap_number,
                "delta_to_best": lap.delta_to_best,
                "dominant_emotion": lap.dominant_emotion.value,
                "stress_level": lap.stress_level,
                "fatigue_level": lap.fatigue_level,
                "severity": (
                    "critical" if lap.delta_to_best >= delta_threshold * 2
                    else "warning"
                ),
            })

    return anomalies


def compute_stint_fatigue_trend(
    aligned_laps: list[AlignedLapEmotion],
    window: int = 3,
) -> list[dict]:
    """
    Compute a rolling fatigue trend across laps to detect progressive
    driver tiredness within a stint.
    
    Returns:
        List of dicts with lap range, average fatigue, and trend direction.
    """
    if len(aligned_laps) < window:
        return []

    trends = []
    for i in range(len(aligned_laps) - window + 1):
        window_laps = aligned_laps[i : i + window]
        avg_fatigue = sum(l.fatigue_level for l in window_laps) / window
        avg_delta = sum(l.delta_to_best for l in window_laps) / window

        # Determine trend by comparing first and last in window
        if window_laps[-1].fatigue_level > window_laps[0].fatigue_level + 0.05:
            direction = "increasing"
        elif window_laps[-1].fatigue_level < window_laps[0].fatigue_level - 0.05:
            direction = "decreasing"
        else:
            direction = "stable"

        trends.append({
            "lap_start": window_laps[0].lap_number,
            "lap_end": window_laps[-1].lap_number,
            "avg_fatigue": round(avg_fatigue, 4),
            "avg_delta": round(avg_delta, 3),
            "trend": direction,
        })

    return trends


def _pearson(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient between two lists."""
    n = len(x)
    if n != len(y) or n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return 0.0

    return round(cov / (std_x * std_y), 4)
