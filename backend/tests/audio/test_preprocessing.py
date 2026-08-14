from __future__ import annotations

import math
import uuid
import wave

import numpy as np
import pytest
from backend.app.audio.preprocessing import (
    compute_rms_energy,
    extract_audio_segments,
    preprocess_audio,
    save_processed_audio,
    save_upload,
)
from backend.app.audio.validation import AudioValidationError
from backend.app.core.config import settings


def test_preprocessing_preserves_raw_intensity_and_normalizes_model_copy(wav_bytes_factory):
    audio = preprocess_audio(
        wav_bytes_factory(sample_rate=8_000, amplitude=0.2, channels=2),
        ".wav",
    )

    assert audio.raw_sample_rate == 8_000
    assert audio.model_sample_rate == 16_000
    assert audio.raw_waveform.size == 8_000
    assert audio.model_waveform.size == pytest.approx(16_000, abs=2)
    assert np.max(np.abs(audio.raw_waveform)) == pytest.approx(0.2, abs=0.01)
    assert np.max(np.abs(audio.model_waveform)) == pytest.approx(0.95, abs=0.01)
    assert audio.normalization_gain > 1.0
    assert not audio.is_silent


def test_silence_is_finite_and_not_amplified(wav_bytes_factory):
    audio = preprocess_audio(wav_bytes_factory(amplitude=0.0), ".wav")

    assert audio.is_silent
    assert audio.normalization_gain == 1.0
    assert np.all(np.isfinite(audio.raw_waveform))
    assert np.all(audio.model_waveform == 0.0)


def test_segments_use_real_duration_and_energy(wav_bytes_factory):
    segments = extract_audio_segments(
        wav_bytes_factory(duration_seconds=1.2, amplitude=0.25),
        ".wav",
        segment_duration_seconds=0.5,
    )

    assert len(segments) == 3
    assert segments[-1]["end_time"] == 1.2
    assert all(segment["rms_energy"] > 0 for segment in segments)
    assert compute_rms_energy(wav_bytes_factory(amplitude=0.25), ".wav") == pytest.approx(
        0.25 / math.sqrt(2),
        abs=0.01,
    )


def test_upload_path_ignores_untrusted_filename(tmp_path, monkeypatch, wav_bytes_factory):
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "UPLOAD_DIR", upload_dir)

    file_id, path = save_upload(wav_bytes_factory(), "../../driver-radio.wav")

    assert uuid.UUID(file_id)
    assert path.parent == upload_dir.resolve()
    assert path.name == f"{file_id}.wav"
    assert "driver-radio" not in path.name


def test_direct_persistence_rejects_unsupported_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)
    with pytest.raises(AudioValidationError):
        save_upload(b"payload", "../../payload.exe")


def test_processed_audio_uses_separate_directory(tmp_path, monkeypatch, wav_bytes_factory):
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr(settings, "PROCESSED_DIR", processed_dir)
    audio = preprocess_audio(wav_bytes_factory(), ".wav")
    file_id = str(uuid.uuid4())

    output = save_processed_audio(file_id, audio)

    assert output.parent == processed_dir.resolve()
    assert output.name == f"{file_id}.wav"
    with wave.open(str(output), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 16_000
