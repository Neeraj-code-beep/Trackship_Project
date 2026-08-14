from __future__ import annotations

import math

from backend.app.schemas.schemas import (
    AcousticAnalysis,
    AcousticFeatures,
    DriverState,
    EmotionLabel,
    EmotionProbabilities,
    SegmentAcousticFeatures,
    TranscriptSegment,
)
from backend.app.services.driver_state_service import fuse_driver_states


def _emotion(
    *,
    stressed=0.0,
    tired=0.0,
    calm=0.0,
    neutral=0.0,
    confidence=0.8,
):
    return DriverState(
        segment_id="seg_001",
        timestamp=0.0,
        start_time=0.0,
        end_time=1.0,
        dominant_emotion=max(
            {
                EmotionLabel.STRESSED: stressed,
                EmotionLabel.TIRED: tired,
                EmotionLabel.CALM: calm,
                EmotionLabel.NEUTRAL: neutral,
            },
            key=lambda label: {
                EmotionLabel.STRESSED: stressed,
                EmotionLabel.TIRED: tired,
                EmotionLabel.CALM: calm,
                EmotionLabel.NEUTRAL: neutral,
            }[label],
        ),
        probabilities=EmotionProbabilities(
            stressed=stressed,
            tired=tired,
            calm=calm,
            neutral=neutral,
        ),
        confidence=confidence,
    )


def _acoustics(deviations, *, pause=0.1, voiced=0.9, pitch=20.0, speech_rate=120.0):
    features = AcousticFeatures(
        rms_energy=0.1,
        pitch_mean_hz=180.0,
        pitch_std_hz=pitch,
        zero_crossing_rate=0.05,
        spectral_centroid_hz=1_500.0,
        duration_seconds=1.0,
        pause_ratio=pause,
        speech_rate_wpm=speech_rate,
        voiced_ratio=voiced,
        energy_variability=0.02,
    )
    return AcousticAnalysis(
        segments=[
            SegmentAcousticFeatures(
                segment_id="seg_001",
                start_time=0,
                end_time=1,
                features=features,
                session_deviations=deviations,
            )
        ]
    )


def _transcript(text="routine message"):
    return [TranscriptSegment(id="seg_001", start_time=0, end_time=1, text=text)]


def test_stress_heavy_evidence_produces_explainable_stressed_state():
    result = fuse_driver_states(
        [_emotion(stressed=0.8, neutral=0.2)],
        _acoustics({"rms_energy": 0.8, "pitch_std_hz": 0.8, "speech_rate_wpm": 0.8}),
        _transcript("Box! Brake problem, losing power!"),
    )[0]

    assert result.dominant_emotion is EmotionLabel.STRESSED
    assert result.stress_score == 83.0
    assert 0 <= result.fatigue_score <= 100
    assert 0 <= result.calm_score <= 100
    assert result.confidence != result.stress_score
    assert "elevated speech-emotion stress probability" in result.drivers
    assert "urgent language in the radio transcript" in result.drivers


def test_fatigue_heavy_evidence_requires_acoustic_support():
    result = fuse_driver_states(
        [_emotion(tired=0.2, neutral=0.8)],
        _acoustics(
            {"rms_energy": -0.8, "pitch_std_hz": -0.8, "speech_rate_wpm": -0.8},
            pause=0.8,
            voiced=0.2,
        ),
        _transcript(),
    )[0]

    assert result.dominant_emotion is EmotionLabel.TIRED
    assert result.fatigue_score == 71.0
    assert "lower-than-session-median vocal energy" in result.drivers
    assert all("medical" not in driver for driver in result.drivers)


def test_calm_evidence_produces_calm_state():
    result = fuse_driver_states(
        [_emotion(calm=0.8, neutral=0.2)],
        _acoustics({"rms_energy": 0.0, "pitch_std_hz": 0.0, "speech_rate_wpm": 0.0}),
        _transcript("Okay, copy"),
    )[0]

    assert result.dominant_emotion is EmotionLabel.CALM
    assert result.calm_score == 89.0
    assert "elevated calm speech-emotion probability" in result.drivers


def test_ambiguous_evidence_remains_neutral():
    result = fuse_driver_states(
        [_emotion(neutral=1.0, confidence=1.0)],
        AcousticAnalysis(),
        _transcript("copy"),
    )[0]

    assert result.dominant_emotion is EmotionLabel.NEUTRAL
    assert result.stress_score == 0.0
    assert result.fatigue_score == 0.0
    assert "decision threshold" in result.drivers[0]


def test_missing_pitch_is_handled_gracefully():
    result = fuse_driver_states(
        [_emotion(stressed=0.6, neutral=0.4)],
        _acoustics({"rms_energy": 0.5, "speech_rate_wpm": 0.4}, pitch=None),
        _transcript("problem"),
    )[0]

    assert result.acoustic_features is not None
    assert result.acoustic_features.pitch_std_hz is None
    assert all(math.isfinite(value) for value in result.signals.values())


def test_nan_inputs_are_sanitized_and_bounded():
    probabilities = EmotionProbabilities.model_construct(
        calm=float("nan"),
        stressed=float("inf"),
        neutral=0.0,
        tired=-1.0,
    )
    emotion = DriverState.model_construct(
        segment_id="seg_001",
        timestamp=0.0,
        start_time=0.0,
        end_time=1.0,
        dominant_emotion=EmotionLabel.NEUTRAL,
        probabilities=probabilities,
        raw_emotions={"bad": float("nan")},
        confidence=float("nan"),
    )

    result = fuse_driver_states([emotion], AcousticAnalysis(), _transcript())[0]

    assert result.dominant_emotion is EmotionLabel.NEUTRAL
    assert result.probabilities.neutral == 1.0
    assert result.raw_emotions["bad"] == 0.0
    assert all(
        math.isfinite(value)
        for value in (result.stress_score, result.fatigue_score, result.calm_score)
    )


def test_fusion_is_deterministic():
    arguments = (
        [_emotion(stressed=0.7, neutral=0.3)],
        _acoustics({"rms_energy": 0.4, "pitch_std_hz": 0.2, "speech_rate_wpm": 0.3}),
        _transcript("brake problem"),
    )

    first = fuse_driver_states(*arguments)[0]
    second = fuse_driver_states(*arguments)[0]

    assert first.model_dump() == second.model_dump()
