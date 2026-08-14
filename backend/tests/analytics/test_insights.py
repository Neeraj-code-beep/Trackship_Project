from __future__ import annotations

from backend.app.analytics.insights import generate_insights
from backend.app.schemas.schemas import (
    AlignedLapEmotion,
    EmotionLabel,
    InsightPriority,
)


def _lap(
    number,
    *,
    delta=0.0,
    stress=0.0,
    fatigue=0.0,
    calm=0.0,
    state=EmotionLabel.NEUTRAL,
    has_segment=True,
):
    return AlignedLapEmotion(
        lap_number=number,
        lap_time_seconds=90 + delta,
        baseline_lap_time=90,
        lap_delta=delta,
        dominant_emotion=state,
        stress_score=stress,
        fatigue_score=fatigue,
        calm_score=calm,
        segment_ids=[f"seg_{number:03d}"] if has_segment else [],
    )


def test_stress_pace_association_contains_exact_evidence():
    insights = generate_insights(
        [
            _lap(1, delta=-1, stress=20),
            _lap(2, delta=0, stress=50),
            _lap(3, delta=1, stress=80),
        ]
    )

    association = next(item for item in insights if item.type == "stress_pace_association")
    assert association.priority is InsightPriority.HIGH
    assert association.evidence == {
        "pearson_r": 1.0,
        "sample_size": 3,
        "strength": "strong",
    }
    assert "does not establish causation" in association.message


def test_rising_fatigue_signal_is_cautious_and_evidence_backed():
    insights = generate_insights(
        [
            _lap(1, fatigue=10),
            _lap(2, fatigue=20),
            _lap(3, fatigue=50),
            _lap(4, fatigue=60),
        ]
    )

    trend = next(item for item in insights if item.type == "rising_fatigue_signal")
    assert trend.priority is InsightPriority.MEDIUM
    assert trend.evidence["fatigue_change"] == 40.0
    assert "not a medical assessment" in trend.message


def test_calm_best_lap_rule():
    insights = generate_insights(
        [
            _lap(
                1,
                delta=-1,
                stress=10,
                calm=70,
                state=EmotionLabel.CALM,
            ),
            _lap(2, delta=0, stress=30, calm=20),
            _lap(3, delta=1, stress=40, calm=10),
        ]
    )

    calm = next(item for item in insights if item.type == "calm_best_lap")
    assert calm.priority is InsightPriority.LOW
    assert calm.lap_number == 1
    assert calm.evidence["calm_score"] == 70
    assert calm.evidence["session_median_stress_score"] == 30


def test_no_meaningful_signal_returns_low_priority_evidence_state():
    insights = generate_insights([_lap(1), _lap(2), _lap(3)])

    assert len(insights) == 1
    assert insights[0].type == "insufficient_evidence"
    assert insights[0].priority is InsightPriority.LOW
    assert insights[0].evidence["stress_correlation_reason"] == "zero_variance"


def test_priority_order_and_ids_are_deterministic():
    laps = [
        _lap(1, delta=-1, stress=20, fatigue=10),
        _lap(2, delta=0, stress=50, fatigue=20),
        _lap(3, delta=1, stress=80, fatigue=50),
        _lap(4, delta=2, stress=90, fatigue=70),
    ]

    first = generate_insights(laps)
    second = generate_insights(laps)

    priorities = [item.priority for item in first]
    assert priorities == sorted(
        priorities,
        key={
            InsightPriority.HIGH: 0,
            InsightPriority.MEDIUM: 1,
            InsightPriority.LOW: 2,
        }.get,
    )
    assert [item.id for item in first] == [
        f"insight_{index:03d}" for index in range(1, len(first) + 1)
    ]
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]
    assert all("pit now" not in item.message.lower() for item in first)


def test_no_lap_data_is_explicit():
    insights = generate_insights([])

    assert insights[0].type == "no_lap_data"
    assert insights[0].evidence == {"usable_laps": 0}
