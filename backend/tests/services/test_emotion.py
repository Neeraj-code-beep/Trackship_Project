from __future__ import annotations

import asyncio

import pytest
from app.schemas.schemas import EmotionLabel, TranscriptSegment
from app.services.emotion_service import (
    EmotionAnalysisError,
    analyze_emotions,
    map_raw_emotions,
)
from app.services.model_registry import ModelUnavailableError, registry


class FakeEmotionModel:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def __call__(self, waveforms, **options):
        self.calls.append((waveforms, options))
        if isinstance(self.output, Exception):
            raise self.output
        return self.output


def _segments():
    return [
        TranscriptSegment(id="seg_001", start_time=0.0, end_time=0.4, text="One"),
        TranscriptSegment(id="seg_002", start_time=0.4, end_time=1.0, text="Two"),
    ]


def test_ser_analyzes_actual_transcript_windows_and_preserves_raw_labels(
    monkeypatch,
    wav_bytes_factory,
):
    model = FakeEmotionModel(
        [
            [{"label": "angry", "score": 0.7}, {"label": "neutral", "score": 0.3}],
            [{"label": "sad", "score": 0.6}, {"label": "calm", "score": 0.4}],
        ]
    )
    monkeypatch.setattr(registry, "get_emotion_model", lambda: model)

    states = asyncio.run(analyze_emotions(wav_bytes_factory(), ".wav", _segments()))

    assert len(states) == 2
    assert states[0].segment_id == "seg_001"
    assert states[0].raw_emotions == {"angry": 0.7, "neutral": 0.3}
    assert states[0].dominant_emotion is EmotionLabel.STRESSED
    assert states[0].probabilities.stressed == 0.7
    assert states[1].raw_emotions == {"sad": 0.6, "calm": 0.4}
    assert states[1].dominant_emotion is EmotionLabel.NEUTRAL
    assert states[1].probabilities.tired == 0.0
    waveforms, options = model.calls[0]
    assert len(waveforms[0]) == 6_400
    assert len(waveforms[1]) == 9_600
    assert options["top_k"] is None


def test_sadness_is_not_mapped_to_tired():
    mapped, coverage = map_raw_emotions({"sad": 1.0})

    assert mapped[EmotionLabel.NEUTRAL] == 1.0
    assert mapped[EmotionLabel.TIRED] == 0.0
    assert coverage == 1.0


def test_only_explicit_fatigue_labels_map_to_tired():
    mapped, _ = map_raw_emotions({"sleepy": 0.75, "neutral": 0.25})

    assert mapped[EmotionLabel.TIRED] == 0.75
    assert mapped[EmotionLabel.NEUTRAL] == 0.25


def test_unknown_labels_are_preserved_and_reduce_confidence(monkeypatch, wav_bytes_factory):
    model = FakeEmotionModel(
        [[{"label": "angry", "score": 0.5}, {"label": "unknown_label", "score": 0.5}]]
    )
    monkeypatch.setattr(registry, "get_emotion_model", lambda: model)
    segment = [TranscriptSegment(id="seg_001", start_time=0, end_time=1, text="Message")]

    state = asyncio.run(analyze_emotions(wav_bytes_factory(), ".wav", segment))[0]

    assert state.raw_emotions["unknown_label"] == 0.5
    assert state.probabilities.stressed == 1.0
    assert state.confidence == 0.5


def test_all_unknown_labels_fail_mapping(monkeypatch, wav_bytes_factory):
    model = FakeEmotionModel([[{"label": "LABEL_0", "score": 1.0}]])
    monkeypatch.setattr(registry, "get_emotion_model", lambda: model)
    segment = [TranscriptSegment(id="seg_001", start_time=0, end_time=1, text="Message")]

    with pytest.raises(EmotionAnalysisError) as captured:
        asyncio.run(analyze_emotions(wav_bytes_factory(), ".wav", segment))

    assert captured.value.error_code == "EMOTION_LABEL_MAPPING_FAILED"


def test_model_failure_returns_error_not_fallback(monkeypatch, wav_bytes_factory):
    model = FakeEmotionModel(RuntimeError("private inference failure"))
    monkeypatch.setattr(registry, "get_emotion_model", lambda: model)

    with pytest.raises(EmotionAnalysisError) as captured:
        asyncio.run(analyze_emotions(wav_bytes_factory(), ".wav"))

    assert captured.value.error_code == "EMOTION_ANALYSIS_FAILED"
    assert "private inference failure" not in str(captured.value)


def test_unavailable_model_returns_structured_error(monkeypatch, wav_bytes_factory):
    def unavailable():
        raise ModelUnavailableError("emotion_ser", "private model error")

    monkeypatch.setattr(registry, "get_emotion_model", unavailable)

    with pytest.raises(EmotionAnalysisError) as captured:
        asyncio.run(analyze_emotions(wav_bytes_factory(), ".wav"))

    assert captured.value.error_code == "MODEL_UNAVAILABLE"
    assert captured.value.status_code == 503


def test_silence_skips_emotion_model(monkeypatch, wav_bytes_factory):
    def unexpected_load():
        raise AssertionError("SER model must not load for silence")

    monkeypatch.setattr(registry, "get_emotion_model", unexpected_load)

    states = asyncio.run(analyze_emotions(wav_bytes_factory(amplitude=0.0), ".wav"))

    assert states == []
