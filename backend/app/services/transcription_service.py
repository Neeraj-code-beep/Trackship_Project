"""Real Whisper speech-to-text service with no implicit fake results."""

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
from typing import Any

from app.audio.preprocessing import PreprocessedAudio, preprocess_audio
from app.core.config import settings
from app.schemas.schemas import TranscriptionResult, TranscriptSegment
from app.services.model_registry import ModelUnavailableError, registry

logger = logging.getLogger(__name__)


class TranscriptionError(RuntimeError):
    """A safe transcription failure for the orchestration/API layers."""

    def __init__(
        self,
        message: str,
        error_code: str = "TRANSCRIPTION_FAILED",
        status_code: int = 500,
    ) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


async def transcribe_audio(
    data: bytes,
    ext: str,
    file_id: str,
    storage_path: Path | None = None,
) -> TranscriptionResult:
    """Decode and transcribe uploaded audio; ``storage_path`` is retained for compatibility."""
    del storage_path
    try:
        audio = await asyncio.to_thread(preprocess_audio, data, ext)
    except Exception as exc:
        raise TranscriptionError("Audio preprocessing failed before transcription.") from exc
    return await transcribe_preprocessed(audio, file_id)


async def transcribe_preprocessed(
    audio: PreprocessedAudio,
    file_id: str,
) -> TranscriptionResult:
    """Transcribe a prepared waveform without decoding it again."""
    if audio.is_silent:
        logger.info("No speech inference attempted for silent audio '%s'.", file_id)
        return TranscriptionResult(
            file_id=file_id,
            full_text="",
            segments=[],
            language=None,
            duration_seconds=audio.duration_seconds,
            detected_speech=False,
        )

    return await asyncio.to_thread(_run_whisper, audio, file_id)


def _run_whisper(audio: PreprocessedAudio, file_id: str) -> TranscriptionResult:
    try:
        model = registry.get_whisper_model()
    except ModelUnavailableError as exc:
        raise TranscriptionError(
            "The transcription model is unavailable.",
            error_code="MODEL_UNAVAILABLE",
            status_code=503,
        ) from exc

    options: dict[str, Any] = {
        "fp16": registry.device == "cuda",
        "verbose": False,
        "condition_on_previous_text": False,
    }
    if settings.ASR_LANGUAGE:
        options["language"] = settings.ASR_LANGUAGE

    logger.info("Running Whisper transcription for audio '%s'.", file_id)
    try:
        result = model.transcribe(audio.model_waveform, **options)
    except Exception as exc:
        logger.exception("Whisper inference failed for audio '%s'.", file_id)
        raise TranscriptionError("Whisper transcription failed.") from exc

    if not isinstance(result, dict):
        raise TranscriptionError("Whisper returned an invalid transcription result.")

    segments: list[TranscriptSegment] = []
    for source_index, raw_segment in enumerate(result.get("segments") or [], start=1):
        if not isinstance(raw_segment, dict):
            raise TranscriptionError("Whisper returned an invalid transcript segment.")
        text = str(raw_segment.get("text") or "").strip()
        if not text:
            continue

        start = _finite_timestamp(raw_segment.get("start"), default=0.0)
        end = _finite_timestamp(raw_segment.get("end"), default=start)
        start = min(max(start, 0.0), audio.duration_seconds)
        end = min(max(end, start), audio.duration_seconds)
        segments.append(
            TranscriptSegment(
                id=f"seg_{source_index:03d}",
                start_time=round(start, 3),
                end_time=round(end, 3),
                text=text,
                confidence=_segment_confidence(raw_segment),
                speaker="Driver",
            )
        )

    full_text = " ".join(segment.text for segment in segments)
    detected_speech = bool(segments)
    language = str(result.get("language") or settings.ASR_LANGUAGE or "").strip() or None
    logger.info(
        "Whisper produced %d speech segments for audio '%s'.",
        len(segments),
        file_id,
    )
    return TranscriptionResult(
        file_id=file_id,
        full_text=full_text,
        segments=segments,
        language=language,
        duration_seconds=audio.duration_seconds,
        detected_speech=detected_speech,
    )


def _finite_timestamp(value: Any, *, default: float) -> float:
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return default
    return timestamp if math.isfinite(timestamp) else default


def _segment_confidence(raw_segment: dict[str, Any]) -> float | None:
    """Convert Whisper average log probability to an uncalibrated probability estimate."""
    try:
        average_log_probability = float(raw_segment["avg_logprob"])
    except (KeyError, TypeError, ValueError):
        return None
    if not math.isfinite(average_log_probability):
        return None
    return round(math.exp(min(average_log_probability, 0.0)), 4)
