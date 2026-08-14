"""
Analysis API route.
POST /api/v1/analysis — triggers full audio processing pipeline and returns driver state insights.
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.app.schemas.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    ErrorResponse,
)
from backend.app.core.config import settings
from backend.app.services.transcription_service import transcribe_audio
from backend.app.services.emotion_service import analyze_emotions
from backend.app.analytics.lap_alignment import build_aligned_laps
from backend.app.analytics.insights import generate_insights

# In-memory stores (shared with race.py via module-level imports)
from backend.app.api.routes import _stores

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "File not found"},
    },
    summary="Run full analysis on uploaded audio",
    description="Processes an uploaded audio file through transcription, "
    "emotion analysis, lap alignment, and insight generation.",
)
async def run_analysis(request: AnalysisRequest):
    """
    Full analysis pipeline:
    1. Load uploaded audio by file_id
    2. Run transcription (Whisper or fallback)
    3. Run emotion analysis (SER or acoustic fallback)
    4. If race data exists, align with laps and generate insights
    """
    start_time = time.time()

    # Find the uploaded file
    upload_dir = settings.UPLOAD_DIR
    matching = list(upload_dir.glob(f"{request.file_id}.*"))
    if not matching:
        raise HTTPException(
            status_code=404,
            detail=f"Audio file with ID '{request.file_id}' not found.",
        )

    file_path = matching[0]
    ext = file_path.suffix.lower()
    data = file_path.read_bytes()

    # 1. Transcription
    transcription = await transcribe_audio(
        data=data,
        ext=ext,
        file_id=request.file_id,
        storage_path=file_path,
    )

    # 2. Emotion analysis
    driver_states = await analyze_emotions(data=data, ext=ext)

    # 3. Lap alignment & insights (if race data available)
    aligned_laps = []
    insights = []
    race_id = request.race_id

    if race_id and race_id in _stores.race_store:
        race_data = _stores.race_store[race_id]
        aligned_laps = build_aligned_laps(race_data["laps"], driver_states)
        insights = generate_insights(aligned_laps)
    else:
        # Generate basic insights from emotion data alone
        from backend.app.schemas.schemas import InsightItem, InsightSeverity

        if driver_states:
            avg_stress = sum(s.probabilities.stressed for s in driver_states) / len(driver_states)
            avg_fatigue = sum(s.probabilities.tired for s in driver_states) / len(driver_states)

            if avg_stress > 0.4:
                insights.append(InsightItem(
                    severity=InsightSeverity.WARNING,
                    category="Emotional State",
                    message=f"Elevated average stress ({avg_stress:.0%}) detected in audio. "
                            f"Driver may be under pressure.",
                ))
            if avg_fatigue > 0.25:
                insights.append(InsightItem(
                    severity=InsightSeverity.WARNING,
                    category="Fatigue",
                    message=f"Moderate fatigue signals ({avg_fatigue:.0%}) detected. "
                            f"Consider monitoring driver alertness.",
                ))
            insights.append(InsightItem(
                severity=InsightSeverity.INFO,
                category="Transcript",
                message=f"Transcription complete: {len(transcription.segments)} "
                        f"segments over {transcription.duration_seconds:.1f}s.",
            ))

    # Compute overall metrics
    overall_stress = (
        sum(s.probabilities.stressed for s in driver_states) / len(driver_states)
        if driver_states else 0.0
    )
    overall_fatigue = (
        sum(s.probabilities.tired for s in driver_states) / len(driver_states)
        if driver_states else 0.0
    )

    elapsed = (time.time() - start_time) * 1000

    return AnalysisResponse(
        file_id=request.file_id,
        race_id=race_id,
        transcription=transcription,
        driver_states=driver_states,
        aligned_laps=aligned_laps,
        insights=insights,
        overall_stress=round(overall_stress, 4),
        overall_fatigue=round(overall_fatigue, 4),
        processing_time_ms=round(elapsed, 2),
    )
