"""Orchestration for the complete driver-intelligence analysis pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from backend.app.analytics.correlation import (
    compute_fatigue_pace_correlation,
    compute_stint_fatigue_trend,
    compute_stress_pace_correlation,
)
from backend.app.analytics.insights import generate_insights
from backend.app.analytics.lap_alignment import build_aligned_laps
from backend.app.audio.features import analyze_acoustics
from backend.app.audio.preprocessing import preprocess_audio, save_processed_audio
from backend.app.core.config import settings
from backend.app.schemas.schemas import (
    AcousticAnalysis,
    AnalysisResponse,
    AnalysisSummary,
    CorrelationSummary,
    DriverState,
    EmotionLabel,
)
from backend.app.services.driver_state_service import fuse_driver_states
from backend.app.services.emotion_service import analyze_preprocessed_emotions
from backend.app.services.transcription_service import transcribe_preprocessed

logger = logging.getLogger(__name__)


class AnalysisPipelineError(RuntimeError):
    """A safe orchestration or resource failure."""

    def __init__(
        self,
        message: str,
        error_code: str = "ANALYSIS_FAILED",
        status_code: int = 500,
    ) -> None:
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(message)


async def run_full_analysis(
    *,
    file_id: str,
    race_id: str | None,
    race_store: dict[str, dict[str, Any]],
) -> AnalysisResponse:
    """Run real audio intelligence and optional race analytics end to end."""
    started = time.perf_counter()
    analysis_id = f"analysis_{uuid.uuid4()}"
    canonical_file_id = _canonical_uuid(file_id)
    if race_id is not None and race_id not in race_store:
        raise AnalysisPipelineError(
            f"Race '{race_id}' was not found.",
            error_code="RACE_NOT_FOUND",
            status_code=404,
        )

    upload_path = _find_upload(canonical_file_id)
    try:
        data = await asyncio.to_thread(upload_path.read_bytes)
        audio = await asyncio.to_thread(preprocess_audio, data, upload_path.suffix.lower())
        await asyncio.to_thread(save_processed_audio, canonical_file_id, audio)
    except AnalysisPipelineError:
        raise
    except Exception as exc:
        logger.exception("Audio preparation failed for analysis '%s'.", analysis_id)
        raise AnalysisPipelineError(
            "The stored audio could not be prepared for analysis.",
            error_code="INVALID_AUDIO",
            status_code=400,
        ) from exc

    transcription = await transcribe_preprocessed(audio, canonical_file_id)
    if transcription.detected_speech:
        emotion_task = analyze_preprocessed_emotions(audio, transcription.segments)
        acoustic_task = asyncio.to_thread(
            analyze_acoustics,
            audio,
            transcription.segments,
        )
        emotion_states, acoustics = await asyncio.gather(emotion_task, acoustic_task)
        driver_states = fuse_driver_states(
            emotion_states,
            acoustics,
            transcription.segments,
        )
    else:
        acoustics = AcousticAnalysis()
        driver_states = []

    laps = race_store[race_id]["laps"] if race_id is not None else []
    aligned_laps = build_aligned_laps(laps, driver_states) if laps else []
    stress_correlation = compute_stress_pace_correlation(aligned_laps)
    fatigue_correlation = compute_fatigue_pace_correlation(aligned_laps)
    fatigue_trend = compute_stint_fatigue_trend(aligned_laps)
    insights = generate_insights(aligned_laps)
    summary = _summary(driver_states)

    if race_id is not None:
        race_store[race_id]["analyses"].append(analysis_id)

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    logger.info(
        "Analysis '%s' completed: segments=%d laps=%d duration_ms=%.1f",
        analysis_id,
        len(transcription.segments),
        len(aligned_laps),
        elapsed_ms,
    )
    return AnalysisResponse(
        analysis_id=analysis_id,
        audio_id=canonical_file_id,
        file_id=canonical_file_id,
        race_id=race_id,
        summary=summary,
        transcription=transcription,
        acoustic_analysis=acoustics,
        driver_states=driver_states,
        aligned_laps=aligned_laps,
        correlations=CorrelationSummary(
            stress_vs_lap_delta=stress_correlation,
            fatigue_vs_lap_delta=fatigue_correlation,
        ),
        fatigue_trend=fatigue_trend,
        insights=insights,
        overall_stress=round(summary.average_stress_score / 100.0, 4),
        overall_fatigue=round(summary.average_fatigue_score / 100.0, 4),
        processing_time_ms=round(elapsed_ms, 2),
    )


def _canonical_uuid(file_id: str) -> str:
    try:
        return str(uuid.UUID(file_id))
    except (ValueError, AttributeError) as exc:
        raise AnalysisPipelineError(
            "The audio file ID is invalid.",
            error_code="AUDIO_NOT_FOUND",
            status_code=404,
        ) from exc


def _find_upload(file_id: str) -> Path:
    matches = [
        settings.UPLOAD_DIR / f"{file_id}{extension}"
        for extension in sorted(settings.ALLOWED_EXTENSIONS)
        if (settings.UPLOAD_DIR / f"{file_id}{extension}").is_file()
    ]
    if len(matches) != 1:
        raise AnalysisPipelineError(
            "The requested audio file was not found.",
            error_code="AUDIO_NOT_FOUND",
            status_code=404,
        )
    return matches[0]


def _summary(states: list[DriverState]) -> AnalysisSummary:
    if not states:
        return AnalysisSummary(
            dominant_state=EmotionLabel.NEUTRAL,
            average_stress_score=0.0,
            average_fatigue_score=0.0,
            average_calm_score=0.0,
            segments_analyzed=0,
        )
    counts = Counter(state.dominant_emotion for state in states)
    dominant = max(
        EmotionLabel,
        key=lambda state: (counts[state], -list(EmotionLabel).index(state)),
    )
    count = len(states)
    return AnalysisSummary(
        dominant_state=dominant,
        average_stress_score=round(sum(state.stress_score for state in states) / count, 1),
        average_fatigue_score=round(sum(state.fatigue_score for state in states) / count, 1),
        average_calm_score=round(sum(state.calm_score for state in states) / count, 1),
        segments_analyzed=count,
    )
