from __future__ import annotations

from backend.app.analytics.lap_alignment import (
    align_emotions_to_laps,
    align_segments_to_laps,
    build_aligned_laps,
    timestamp_to_lap,
)
from backend.app.schemas.schemas import (
    DriverState,
    EmotionLabel,
    EmotionProbabilities,
    LapData,
    TranscriptSegment,
)
from backend.app.services.lap_service import normalize_laps


def _laps():
    return normalize_laps(
        [
            LapData(lap_number=10, lap_time_seconds=90, start_time=0),
            LapData(lap_number=11, lap_time_seconds=91, start_time=90),
        ]
    )


def _state(start, end, *, stress=60.0, segment_id="seg_001"):
    return DriverState(
        segment_id=segment_id,
        timestamp=start,
        start_time=start,
        end_time=end,
        dominant_emotion=EmotionLabel.STRESSED,
        probabilities=EmotionProbabilities(stressed=0.8, neutral=0.2),
        confidence=0.8,
        stress_score=stress,
        fatigue_score=20,
        calm_score=10,
    )


def test_timestamp_in_each_lap_and_outside_range():
    laps = _laps()

    assert timestamp_to_lap(20, laps).lap_number == 10
    assert timestamp_to_lap(120, laps).lap_number == 11
    assert timestamp_to_lap(-1, laps) is None
    assert timestamp_to_lap(182, laps) is None


def test_exact_internal_boundary_belongs_to_next_lap():
    assert timestamp_to_lap(90.0, _laps()).lap_number == 11


def test_exact_final_boundary_belongs_to_final_lap():
    assert timestamp_to_lap(181.0, _laps()).lap_number == 11


def test_crossing_segment_uses_midpoint_and_actual_lap_number():
    segment = TranscriptSegment(
        id="seg_001",
        start_time=89,
        end_time=91,
        text="Crossing boundary",
    )

    aligned = align_segments_to_laps([segment], _laps())

    assert list(aligned) == [11]
    assert aligned[11] == [segment]


def test_driver_state_crossing_boundary_uses_midpoint():
    state = _state(89, 91)

    aligned = align_emotions_to_laps([state], _laps())

    assert list(aligned) == [11]


def test_out_of_range_state_is_not_assigned():
    assert align_emotions_to_laps([_state(200, 201)], _laps()) == {}


def test_build_aligned_laps_aggregates_fused_scores():
    aligned = build_aligned_laps(
        _laps(),
        [
            _state(10, 20, stress=70, segment_id="seg_001"),
            _state(30, 40, stress=50, segment_id="seg_002"),
        ],
    )

    assert [lap.lap_number for lap in aligned] == [10, 11]
    assert aligned[0].stress_score == 60.0
    assert aligned[0].segment_ids == ["seg_001", "seg_002"]
    assert aligned[0].dominant_emotion is EmotionLabel.STRESSED
    assert aligned[1].dominant_emotion is EmotionLabel.NEUTRAL
