"""Safe association metrics between driver-state scores and lap deltas."""

from __future__ import annotations

import math

from app.schemas.schemas import (
    AlignedLapEmotion,
    CorrelationResult,
    FatigueTrend,
)

MIN_CORRELATION_SAMPLES = 3
FATIGUE_TREND_THRESHOLD = 10.0


def compute_stress_pace_correlation(
    aligned_laps: list[AlignedLapEmotion],
) -> CorrelationResult:
    """Associate stress score with signed median-baseline lap delta."""
    return _correlation_result(
        "stress_vs_lap_delta",
        aligned_laps,
        score_attribute="stress_score",
    )


def compute_fatigue_pace_correlation(
    aligned_laps: list[AlignedLapEmotion],
) -> CorrelationResult:
    """Associate estimated fatigue score with signed median-baseline lap delta."""
    return _correlation_result(
        "fatigue_vs_lap_delta",
        aligned_laps,
        score_attribute="fatigue_score",
    )


def compute_stint_fatigue_trend(
    aligned_laps: list[AlignedLapEmotion],
) -> FatigueTrend:
    """Compare early and late usable laps without physiological claims."""
    usable = [lap for lap in aligned_laps if _is_usable(lap, "fatigue_score")]
    if len(usable) < MIN_CORRELATION_SAMPLES:
        return FatigueTrend(
            trend="insufficient_data",
            sample_size=len(usable),
            reason="insufficient_data",
        )

    half = max(1, len(usable) // 2)
    early = usable[:half]
    late = usable[-half:]
    early_average = sum(lap.fatigue_score for lap in early) / len(early)
    late_average = sum(lap.fatigue_score for lap in late) / len(late)
    change = late_average - early_average
    if change >= FATIGUE_TREND_THRESHOLD:
        trend = "rising"
    elif change <= -FATIGUE_TREND_THRESHOLD:
        trend = "falling"
    else:
        trend = "stable"
    return FatigueTrend(
        trend=trend,
        change=round(change, 1),
        early_average=round(early_average, 1),
        late_average=round(late_average, 1),
        sample_size=len(usable),
    )


def detect_performance_anomalies(
    aligned_laps: list[AlignedLapEmotion],
    delta_threshold: float = 1.5,
) -> list[dict]:
    """Retain a compatibility helper using median-baseline pace loss."""
    anomalies = []
    for lap in aligned_laps:
        if lap.lap_delta >= delta_threshold and not lap.is_timing_outlier:
            anomalies.append(
                {
                    "lap_number": lap.lap_number,
                    "lap_delta": lap.lap_delta,
                    "delta_to_best": lap.delta_to_best,
                    "dominant_emotion": lap.dominant_emotion.value,
                    "stress_score": lap.stress_score,
                    "fatigue_score": lap.fatigue_score,
                    "stress_level": lap.stress_level,
                    "fatigue_level": lap.fatigue_level,
                    "severity": "critical" if lap.lap_delta >= delta_threshold * 2 else "warning",
                }
            )
    return anomalies


def _correlation_result(
    metric: str,
    aligned_laps: list[AlignedLapEmotion],
    *,
    score_attribute: str,
) -> CorrelationResult:
    usable = [lap for lap in aligned_laps if _is_usable(lap, score_attribute)]
    usable_ids = {id(lap) for lap in usable}
    excluded = [lap.lap_number for lap in aligned_laps if id(lap) not in usable_ids]
    if len(usable) < MIN_CORRELATION_SAMPLES:
        return CorrelationResult(
            metric=metric,
            pearson_r=None,
            sample_size=len(usable),
            direction="none",
            strength="unknown",
            reason="insufficient_data",
            excluded_lap_numbers=excluded,
        )

    scores = [float(getattr(lap, score_attribute)) for lap in usable]
    deltas = [float(lap.lap_delta) for lap in usable]
    coefficient = _pearson(scores, deltas)
    if coefficient is None:
        return CorrelationResult(
            metric=metric,
            pearson_r=None,
            sample_size=len(usable),
            direction="none",
            strength="unknown",
            reason="zero_variance",
            excluded_lap_numbers=excluded,
        )

    direction, strength = interpret_correlation(coefficient)
    return CorrelationResult(
        metric=metric,
        pearson_r=coefficient,
        sample_size=len(usable),
        direction=direction,
        strength=strength,
        excluded_lap_numbers=excluded,
    )


def interpret_correlation(coefficient: float) -> tuple[str, str]:
    """Return machine-readable direction and documented magnitude band."""
    absolute = abs(coefficient)
    direction = "none" if absolute < 1e-12 else "positive" if coefficient > 0 else "negative"
    if absolute < 0.2:
        strength = "negligible"
    elif absolute < 0.4:
        strength = "weak"
    elif absolute < 0.7:
        strength = "moderate"
    else:
        strength = "strong"
    return direction, strength


def _is_usable(lap: AlignedLapEmotion, score_attribute: str) -> bool:
    score = float(getattr(lap, score_attribute))
    return (
        bool(lap.segment_ids)
        and not lap.is_timing_outlier
        and math.isfinite(score)
        and math.isfinite(float(lap.lap_delta))
    )


def _pearson(x: list[float], y: list[float]) -> float | None:
    if len(x) != len(y) or len(x) < MIN_CORRELATION_SAMPLES:
        return None
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    centered_x = [value - mean_x for value in x]
    centered_y = [value - mean_y for value in y]
    sum_sq_x = sum(value * value for value in centered_x)
    sum_sq_y = sum(value * value for value in centered_y)
    if sum_sq_x <= 0 or sum_sq_y <= 0:
        return None
    covariance = sum(a * b for a, b in zip(centered_x, centered_y, strict=True))
    coefficient = covariance / math.sqrt(sum_sq_x * sum_sq_y)
    if not math.isfinite(coefficient):
        return None
    return round(min(max(coefficient, -1.0), 1.0), 4)
