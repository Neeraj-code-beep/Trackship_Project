"""Thin API route for the full backend analysis pipeline."""

from __future__ import annotations

from backend.app.api.routes import _stores
from backend.app.schemas.schemas import AnalysisRequest, AnalysisResponse, ErrorResponse
from backend.app.services.analysis_service import run_full_analysis
from fastapi import APIRouter

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post(
    "",
    response_model=AnalysisResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Audio or race not found"},
        503: {"model": ErrorResponse, "description": "Required AI model unavailable"},
    },
    summary="Run full driver-intelligence analysis",
    description=(
        "Runs real transcription, speech emotion inference, acoustic feature extraction, "
        "driver-state fusion, lap alignment, correlations, and evidence-backed insights."
    ),
)
async def run_analysis(request: AnalysisRequest):
    return await run_full_analysis(
        file_id=request.file_id,
        race_id=request.race_id,
        race_store=_stores.race_store,
    )
