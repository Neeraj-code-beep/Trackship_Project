"""Robust lap-time baseline, deltas, and explicit outlier flags."""

from __future__ import annotations

import math
from statistics import median

from app.schemas.schemas import LapData, LapPerformanceBaseline

MODIFIED_Z_THRESHOLD = 3.5
MAD_SCALE = 0.6745


def compute_lap_baseline(laps: list[LapData]) -> LapPerformanceBaseline:
    """Use the median of all valid laps and flag, rather than hide, anomalies."""
    if not laps:
        raise ValueError("At least one lap is required to calculate a baseline.")
    times = [float(lap.lap_time_seconds) for lap in laps]
    if any(not math.isfinite(value) or value <= 0 for value in times):
        raise ValueError("Lap baseline received an invalid lap time.")

    baseline = float(median(times))
    absolute_deviations = [abs(value - baseline) for value in times]
    mad = float(median(absolute_deviations))
    outlier_laps: list[int] = []

    for lap, lap_time in zip(laps, times, strict=True):
        if mad > 0:
            modified_z = MAD_SCALE * (lap_time - baseline) / mad
            is_outlier = abs(modified_z) > MODIFIED_Z_THRESHOLD
        else:
            fallback_threshold = max(baseline * 0.1, 5.0)
            is_outlier = abs(lap_time - baseline) > fallback_threshold
        if is_outlier:
            outlier_laps.append(lap.lap_number)

    return LapPerformanceBaseline(
        baseline_lap_time=round(baseline, 6),
        method="median_all_valid_laps",
        sample_size=len(times),
        outlier_lap_numbers=outlier_laps,
    )


def lap_delta(lap_time_seconds: float, baseline_lap_time: float) -> float:
    """Positive is slower than baseline; negative is faster."""
    delta = float(lap_time_seconds) - float(baseline_lap_time)
    return round(delta, 6) if math.isfinite(delta) else 0.0
