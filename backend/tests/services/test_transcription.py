from __future__ import annotations

import asyncio
import math

import numpy as np
import pytest
from app.audio.preprocessing import preprocess_audio
from app.services.model_registry import ModelUnavailableError, registry
from app.services.transcription_service import TranscriptionError, transcribe_audio


class FakeWhisperModel:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def transcribe(self, waveform, **options):
        self.calls.append((waveform, options))
        return self.result


def test_whisper_receives_real_waveform_and_preserves_timestamps(
    monkeypatch,
    wav_bytes_factory,
):
    model = FakeWhisperModel(
        {
            "language": "en",
            "segments": [
                {
                    "start": 0.1,
                    "end": 0.7,
                    "text": " Radio check. ",
                    "avg_logprob": math.log(0.8),
                },
                {"start": 0.7, "end": 1.0, "text": "Copy.", "avg_logprob": None},
            ],
        }
    )
    monkeypatch.setattr(registry, "get_whisper_model", lambda: model)
    monkeypatch.setattr(registry, "_device", "cpu")
    wav_data = wav_bytes_factory(duration_seconds=1.0)

    result = asyncio.run(transcribe_audio(wav_data, ".wav", "audio-1"))

    assert result.detected_speech is True
    assert result.full_text == "Radio check. Copy."
    assert result.language == "en"
    assert result.duration_seconds == 1.0
    assert [segment.id for segment in result.segments] == ["seg_001", "seg_002"]
    assert result.segments[0].start_time == 0.1
    assert result.segments[0].end_time == 0.7
    assert result.segments[0].confidence == 0.8
    assert result.segments[1].confidence is None
    waveform, options = model.calls[0]
    expected = preprocess_audio(wav_data, ".wav").model_waveform
    assert np.allclose(waveform, expected)
    assert options["fp16"] is False
    assert options["condition_on_previous_text"] is False


def test_empty_whisper_result_does_not_invent_speech(monkeypatch, wav_bytes_factory):
    model = FakeWhisperModel({"text": "", "segments": [], "language": "en"})
    monkeypatch.setattr(registry, "get_whisper_model", lambda: model)
    monkeypatch.setattr(registry, "_device", "cpu")

    result = asyncio.run(transcribe_audio(wav_bytes_factory(), ".wav", "audio-2"))

    assert result.detected_speech is False
    assert result.full_text == ""
    assert result.segments == []


def test_silence_skips_model_loading(monkeypatch, wav_bytes_factory):
    def unexpected_load():
        raise AssertionError("model must not load for silence")

    monkeypatch.setattr(registry, "get_whisper_model", unexpected_load)

    result = asyncio.run(
        transcribe_audio(
            wav_bytes_factory(duration_seconds=1.0, amplitude=0.0),
            ".wav",
            "silent-audio",
        )
    )

    assert result.detected_speech is False
    assert result.language is None
    assert result.duration_seconds == 1.0


def test_whisper_failure_returns_error_not_fallback(monkeypatch, wav_bytes_factory):
    class FailingModel:
        def transcribe(self, waveform, **options):
            raise RuntimeError("inference failure")

    monkeypatch.setattr(registry, "get_whisper_model", lambda: FailingModel())
    monkeypatch.setattr(registry, "_device", "cpu")

    with pytest.raises(TranscriptionError) as captured:
        asyncio.run(transcribe_audio(wav_bytes_factory(), ".wav", "audio-3"))

    assert captured.value.error_code == "TRANSCRIPTION_FAILED"
    assert "inference failure" not in str(captured.value)


def test_unavailable_model_returns_structured_error(monkeypatch, wav_bytes_factory):
    def unavailable():
        raise ModelUnavailableError("whisper", "private detail")

    monkeypatch.setattr(registry, "get_whisper_model", unavailable)

    with pytest.raises(TranscriptionError) as captured:
        asyncio.run(transcribe_audio(wav_bytes_factory(), ".wav", "audio-4"))

    assert captured.value.error_code == "MODEL_UNAVAILABLE"
    assert captured.value.status_code == 503
    assert "private detail" not in str(captured.value)


def test_invalid_confidence_and_timestamps_are_sanitized(monkeypatch, wav_bytes_factory):
    model = FakeWhisperModel(
        {
            "segments": [
                {
                    "start": float("nan"),
                    "end": float("inf"),
                    "text": "Message",
                    "avg_logprob": 1_000.0,
                }
            ]
        }
    )
    monkeypatch.setattr(registry, "get_whisper_model", lambda: model)
    monkeypatch.setattr(registry, "_device", "cpu")

    result = asyncio.run(transcribe_audio(wav_bytes_factory(), ".wav", "audio-5"))

    assert result.segments[0].start_time == 0.0
    assert result.segments[0].end_time == 0.0
    assert result.segments[0].confidence == 1.0
