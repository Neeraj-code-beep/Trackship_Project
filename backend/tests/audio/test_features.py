from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest
from backend.app.audio.features import analyze_acoustics, extract_acoustic_features
from backend.app.audio.preprocessing import preprocess_audio
from backend.app.schemas.schemas import TranscriptSegment


def _sine(frequency: float, duration: float = 1.0, sample_rate: int = 16_000, amplitude=0.2):
    time = np.arange(round(duration * sample_rate), dtype=np.float64) / sample_rate
    return (amplitude * np.sin(2 * np.pi * frequency * time)).astype(np.float32)


def test_sine_features_are_real_and_interpretable():
    features = extract_acoustic_features(
        _sine(200.0, amplitude=0.2),
        16_000,
        text="three spoken words",
    )

    assert features.rms_energy == pytest.approx(0.2 / math.sqrt(2), abs=0.005)
    assert features.pitch_mean_hz == pytest.approx(200.0, abs=5.0)
    assert features.pitch_std_hz is not None
    assert features.zero_crossing_rate == pytest.approx(400 / 16_000, abs=0.005)
    assert features.spectral_centroid_hz == pytest.approx(200.0, abs=20.0)
    assert features.duration_seconds == 1.0
    assert features.pause_ratio == 0.0
    assert features.speech_rate_wpm == 180.0
    assert features.voiced_ratio > 0.9
    assert features.energy_variability >= 0.0


def test_silence_has_no_pitch_and_no_nan():
    features = extract_acoustic_features(np.zeros(16_000, dtype=np.float32), 16_000, text="")

    assert features.rms_energy == 0.0
    assert features.pitch_mean_hz is None
    assert features.pitch_std_hz is None
    assert features.spectral_centroid_hz == 0.0
    assert features.pause_ratio == 1.0
    assert features.voiced_ratio == 0.0
    assert all(
        math.isfinite(value) for value in features.model_dump().values() if isinstance(value, float)
    )


def test_short_segment_is_handled_without_nan():
    features = extract_acoustic_features(_sine(200.0, duration=0.005), 16_000)

    assert features.duration_seconds == pytest.approx(0.005)
    assert features.pitch_mean_hz is None
    assert math.isfinite(features.rms_energy)


def test_session_baselines_and_relative_deviations_use_same_audio(
    wav_bytes_factory,
):
    first = wav_bytes_factory(duration_seconds=0.5, amplitude=0.1)
    second = wav_bytes_factory(duration_seconds=0.5, amplitude=0.3)
    first_audio = preprocess_audio(first, ".wav").raw_waveform
    second_audio = preprocess_audio(second, ".wav").raw_waveform
    combined = np.concatenate([first_audio, second_audio])
    combined_audio = preprocess_audio(
        wav_bytes_factory(duration_seconds=1.0, amplitude=0.1),
        ".wav",
    )
    combined_audio = replace(combined_audio, raw_waveform=combined)
    segments = [
        TranscriptSegment(id="seg_001", start_time=0, end_time=0.5, text="slow words"),
        TranscriptSegment(id="seg_002", start_time=0.5, end_time=1.0, text="many fast words now"),
    ]

    analysis = analyze_acoustics(combined_audio, segments)

    assert len(analysis.segments) == 2
    assert analysis.session_baselines["rms_energy"] > 0
    assert analysis.segments[0].session_deviations["rms_energy"] < 0
    assert analysis.segments[1].session_deviations["rms_energy"] > 0
    assert analysis.segments[0].session_deviations["speech_rate_wpm"] < 0
    assert analysis.segments[1].session_deviations["speech_rate_wpm"] > 0


def test_identical_segments_have_zero_relative_deviation(wav_bytes_factory):
    audio = preprocess_audio(wav_bytes_factory(duration_seconds=1.0), ".wav")
    segments = [
        TranscriptSegment(id="seg_001", start_time=0, end_time=0.5, text="same"),
        TranscriptSegment(id="seg_002", start_time=0.5, end_time=1.0, text="same"),
    ]

    analysis = analyze_acoustics(audio, segments)

    assert analysis.segments[0].session_deviations["rms_energy"] == pytest.approx(0.0, abs=1e-3)
    assert analysis.segments[1].session_deviations["rms_energy"] == pytest.approx(0.0, abs=1e-3)
