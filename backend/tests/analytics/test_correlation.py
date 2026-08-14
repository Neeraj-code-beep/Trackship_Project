from __future__ import annotations

import math

from app.analytics.correlation import (
    compute_fatigue_pace_correlation,
    compute_stint_fatigue_trend,
    compute_stress_pace_correlation,
)
from app.schemas.schemas import AlignedLapEmotion, EmotionLabel


def _lap(
    number,
    delta,
    *,
    stress=0.0,
    fatigue=0.0,
    outlier=False,
    has_segment=True,
):
    return AlignedLapEmotion(
        lap_number=number,
        lap_time_seconds=90 + delta,
        lap_delta=delta,
        dominant_emotion=EmotionLabel.NEUTRAL,
        stress_score=stress,
        fatigue_score=fatigue,
        is_timing_outlier=outlier,
        segment_ids=[f"seg_{number:03d}"] if has_segment else [],
    )


def test_positive_stress_correlation():
    result = compute_stress_pace_correlation(
        [_lap(1, -1, stress=10), _lap(2, 0, stress=20), _lap(3, 1, stress=30)]
    )

    assert result.pearson_r == 1.0
    assert result.direction == "positive"
    assert result.strength == "strong"
    assert result.sample_size == 3


def test_negative_fatigue_correlation():
    result = compute_fatigue_pace_correlation(
        [_lap(1, -1, fatigue=30), _lap(2, 0, fatigue=20), _lap(3, 1, fatigue=10)]
    )

    assert result.pearson_r == -1.0
    assert result.direction == "negative"
    assert result.strength == "strong"


def test_near_zero_correlation_is_machine_readable():
    result = compute_stress_pace_correlation(
        [
            _lap(1, 1, stress=1),
            _lap(2, -1, stress=2),
            _lap(3, -1, stress=3),
            _lap(4, 1, stress=4),
        ]
    )

    assert result.pearson_r == 0.0
    assert result.direction == "none"
    assert result.strength == "negligible"


def test_insufficient_samples_return_null_not_zero():
    result = compute_stress_pace_correlation([_lap(1, 0, stress=10), _lap(2, 1, stress=20)])

    assert result.pearson_r is None
    assert result.reason == "insufficient_data"
    assert result.sample_size == 2


def test_constant_score_or_delta_returns_zero_variance_reason():
    constant_score = compute_stress_pace_correlation(
        [_lap(1, -1, stress=10), _lap(2, 0, stress=10), _lap(3, 1, stress=10)]
    )
    constant_delta = compute_stress_pace_correlation(
        [_lap(1, 1, stress=10), _lap(2, 1, stress=20), _lap(3, 1, stress=30)]
    )

    assert constant_score.pearson_r is None
    assert constant_score.reason == "zero_variance"
    assert constant_delta.pearson_r is None
    assert constant_delta.reason == "zero_variance"


def test_nan_and_timing_outliers_are_explicitly_excluded():
    invalid = AlignedLapEmotion.model_construct(
        lap_number=3,
        lap_time_seconds=90,
        lap_delta=float("nan"),
        dominant_emotion=EmotionLabel.NEUTRAL,
        stress_score=30,
        fatigue_score=20,
        segment_ids=["seg_003"],
        is_timing_outlier=False,
    )
    result = compute_stress_pace_correlation(
        [
            _lap(1, -1, stress=10),
            _lap(2, 0, stress=20),
            invalid,
            _lap(4, 100, stress=99, outlier=True),
        ]
    )

    assert result.pearson_r is None
    assert result.sample_size == 2
    assert result.excluded_lap_numbers == [3, 4]
    assert result.model_dump(mode="json")["pearson_r"] is None
    assert all(
        not isinstance(value, float) or math.isfinite(value)
        for value in result.model_dump(mode="json").values()
    )


def test_fatigue_trend_reports_early_to_late_change():
    trend = compute_stint_fatigue_trend(
        [
            _lap(1, 0, fatigue=10),
            _lap(2, 0, fatigue=20),
            _lap(3, 0, fatigue=50),
            _lap(4, 0, fatigue=60),
        ]
    )

    assert trend.trend == "rising"
    assert trend.change == 40.0
    assert trend.early_average == 15.0
    assert trend.late_average == 55.0


def test_fatigue_trend_requires_three_usable_laps():
    trend = compute_stint_fatigue_trend([_lap(1, 0, fatigue=10), _lap(2, 0, fatigue=20)])

    assert trend.trend == "insufficient_data"
    assert trend.change is None
    assert trend.reason == "insufficient_data"
