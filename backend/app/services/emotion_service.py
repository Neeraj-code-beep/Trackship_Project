"""Speech-emotion inference over real waveform segments."""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from app.audio.preprocessing import PreprocessedAudio, preprocess_audio
from app.core.config import settings
from app.schemas.schemas import (
    DriverState,
    EmotionLabel,
    EmotionProbabilities,
    TranscriptSegment,
)
from app.services.model_registry import ModelUnavailableError, registry

logger = logging.getLogger(__name__)


class EmotionAnalysisError(RuntimeError):
    """A safe speech-emotion inference failure."""

    def __init__(
        self,
        message: str,
        error_code: str = "EMOTION_ANALYSIS_FAILED",
        status_code: int = 500,
    ) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class SegmentWindow:
    segment_id: str
    start_time: float
    end_time: float


EMOTION_LABEL_GROUPS: dict[EmotionLabel, frozenset[str]] = {
    EmotionLabel.STRESSED: frozenset(
        {"angry", "anger", "fearful", "fear", "disgust", "surprised", "surprise"}
    ),
    EmotionLabel.CALM: frozenset({"calm", "happy", "happiness", "joy"}),
    EmotionLabel.NEUTRAL: frozenset({"neutral", "sad", "sadness"}),
    EmotionLabel.TIRED: frozenset({"tired", "sleepy", "bored", "boredom"}),
}


async def analyze_emotions(
    data: bytes,
    ext: str,
    segments: list[TranscriptSegment] | None = None,
) -> list[DriverState]:
    """Decode audio and run real SER on transcript or fixed-duration windows."""
    try:
        audio = await asyncio.to_thread(preprocess_audio, data, ext)
    except Exception as exc:
        raise EmotionAnalysisError("Audio preprocessing failed before emotion analysis.") from exc
    return await analyze_preprocessed_emotions(audio, segments)


async def analyze_preprocessed_emotions(
    audio: PreprocessedAudio,
    segments: list[TranscriptSegment] | None = None,
) -> list[DriverState]:
    """Run SER over a prepared waveform without decoding it again."""
    if audio.is_silent:
        return []

    windows = _segment_windows(audio.duration_seconds, segments)
    prepared: list[tuple[SegmentWindow, np.ndarray]] = []
    for window in windows:
        start_sample = max(0, round(window.start_time * audio.model_sample_rate))
        end_sample = min(
            audio.model_waveform.size,
            round(window.end_time * audio.model_sample_rate),
        )
        if end_sample > start_sample:
            prepared.append((window, audio.model_waveform[start_sample:end_sample]))

    if not prepared:
        return []
    return await asyncio.to_thread(_run_emotion_model, prepared)


def _run_emotion_model(
    prepared: list[tuple[SegmentWindow, np.ndarray]],
) -> list[DriverState]:
    try:
        model = registry.get_emotion_model()
    except ModelUnavailableError as exc:
        raise EmotionAnalysisError(
            "The speech-emotion model is unavailable.",
            error_code="MODEL_UNAVAILABLE",
            status_code=503,
        ) from exc

    waveforms = [waveform for _, waveform in prepared]
    try:
        output = model(waveforms, top_k=None, batch_size=min(len(waveforms), 8))
    except Exception as exc:
        logger.exception("Speech-emotion inference failed.")
        raise EmotionAnalysisError("Speech-emotion inference failed.") from exc

    batches = _coerce_batches(output, expected=len(prepared))
    states: list[DriverState] = []
    for (window, _), batch in zip(prepared, batches, strict=True):
        raw_emotions = _raw_probabilities(batch)
        mapped, coverage = map_raw_emotions(raw_emotions)
        dominant = max(mapped, key=mapped.get)
        confidence = min(max(max(mapped.values()) * coverage, 0.0), 1.0)
        states.append(
            DriverState(
                segment_id=window.segment_id,
                timestamp=window.start_time,
                start_time=window.start_time,
                end_time=window.end_time,
                dominant_emotion=dominant,
                probabilities=EmotionProbabilities(
                    **{label.value: score for label, score in mapped.items()}
                ),
                raw_emotions=raw_emotions,
                confidence=round(confidence, 4),
            )
        )
    return states


def map_raw_emotions(
    raw_emotions: dict[str, float],
) -> tuple[dict[EmotionLabel, float], float]:
    """Map model-specific labels to application groups in one documented location."""
    mapped = {label: 0.0 for label in EmotionLabel}
    known_mass = 0.0

    for raw_label, score in raw_emotions.items():
        normalized = _normalize_label(raw_label)
        target = next(
            (
                application_label
                for application_label, model_labels in EMOTION_LABEL_GROUPS.items()
                if normalized in model_labels
            ),
            None,
        )
        if target is not None:
            mapped[target] += score
            known_mass += score

    if known_mass <= 0:
        raise EmotionAnalysisError(
            "The emotion model returned no recognized labels.",
            error_code="EMOTION_LABEL_MAPPING_FAILED",
        )

    normalized_scores = {label: score / known_mass for label, score in mapped.items()}
    return normalized_scores, min(known_mass, 1.0)


def _segment_windows(
    duration_seconds: float,
    segments: list[TranscriptSegment] | None,
) -> list[SegmentWindow]:
    if segments is not None:
        return [
            SegmentWindow(
                segment_id=segment.id,
                start_time=max(segment.start_time, 0.0),
                end_time=min(max(segment.end_time, segment.start_time), duration_seconds),
            )
            for segment in segments
        ]

    windows: list[SegmentWindow] = []
    start = 0.0
    index = 1
    while start < duration_seconds:
        end = min(start + settings.SER_SEGMENT_SECONDS, duration_seconds)
        windows.append(
            SegmentWindow(
                segment_id=f"ser_{index:03d}",
                start_time=round(start, 3),
                end_time=round(end, 3),
            )
        )
        start = end
        index += 1
    return windows


def _coerce_batches(output: Any, *, expected: int) -> list[list[dict[str, Any]]]:
    if not isinstance(output, list):
        raise EmotionAnalysisError("The emotion model returned an invalid result.")
    if expected == 1 and (not output or isinstance(output[0], dict)):
        batches = [output]
    else:
        batches = output
    if len(batches) != expected or any(not isinstance(batch, list) for batch in batches):
        raise EmotionAnalysisError("The emotion model returned an invalid batch result.")
    return batches


def _raw_probabilities(batch: list[dict[str, Any]]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for item in batch:
        if not isinstance(item, dict):
            raise EmotionAnalysisError("The emotion model returned an invalid label result.")
        label = str(item.get("label") or "").strip()
        try:
            score = float(item["score"])
        except (KeyError, TypeError, ValueError) as exc:
            raise EmotionAnalysisError("The emotion model returned an invalid score.") from exc
        if not label or not math.isfinite(score) or score < 0:
            raise EmotionAnalysisError("The emotion model returned an invalid probability.")
        scores[label] = scores.get(label, 0.0) + score

    total = sum(scores.values())
    if total <= 0 or not math.isfinite(total):
        raise EmotionAnalysisError("The emotion model returned no valid probabilities.")
    return {label: round(score / total, 6) for label, score in scores.items()}


def _normalize_label(label: str) -> str:
    return label.strip().lower().replace("-", "_").replace(" ", "_")
