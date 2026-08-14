from __future__ import annotations

from backend.app.analytics.lap_alignment import build_aligned_laps
from backend.app.analytics.lap_performance import compute_lap_baseline, lap_delta
from backend.app.schemas.schemas import LapData
from backend.app.services.lap_service import normalize_laps


def _laps(times):
    return normalize_laps(
        [
            LapData(lap_number=index, lap_time_seconds=value)
            for index, value in enumerate(times, start=1)
        ]
    )


def test_median_baseline_for_odd_and_even_lap_counts():
    assert compute_lap_baseline(_laps([90, 91, 100])).baseline_lap_time == 91
    assert compute_lap_baseline(_laps([89, 90, 91, 92])).baseline_lap_time == 90.5


def test_lap_delta_sign_is_unambiguous():
    assert lap_delta(91.2, 90.0) == 1.2
    assert lap_delta(89.5, 90.0) == -0.5


def test_extreme_timing_anomaly_is_flagged_but_not_discarded():
    laps = _laps([90, 90, 90, 130])
    baseline = compute_lap_baseline(laps)
    aligned = build_aligned_laps(laps, [])

    assert baseline.baseline_lap_time == 90
    assert baseline.outlier_lap_numbers == [4]
    assert len(aligned) == 4
    assert aligned[3].is_timing_outlier is True
    assert aligned[3].lap_delta == 40


def test_aligned_laps_expose_baseline_and_both_delta_contracts():
    aligned = build_aligned_laps(_laps([89, 90, 92]), [])

    assert [lap.baseline_lap_time for lap in aligned] == [90, 90, 90]
    assert [lap.lap_delta for lap in aligned] == [-1, 0, 2]
    assert [lap.delta_to_best for lap in aligned] == [0, 1, 3]
