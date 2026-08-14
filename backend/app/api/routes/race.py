"""Race lap ingestion and retrieval routes."""

from __future__ import annotations

from typing import Annotated

from backend.app.analytics.lap_performance import compute_lap_baseline
from backend.app.api.routes import _stores
from backend.app.core.config import settings
from backend.app.schemas.schemas import (
    ErrorResponse,
    LapIngestionRequest,
    LapIngestionResponse,
    RaceOverview,
)
from backend.app.services.lap_service import (
    LapDataValidationError,
    parse_lap_csv,
)
from backend.app.services.lap_service import (
    ingest_laps as ingest_laps_service,
)
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/race", tags=["Race"])


@router.post(
    "/laps",
    response_model=LapIngestionResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid lap data"}},
    summary="Ingest JSON lap timing data",
)
async def ingest_laps(request: LapIngestionRequest):
    """Validate and store JSON lap timing data."""
    return ingest_laps_service(
        _stores.race_store,
        race_id=request.race_id,
        driver_name=request.driver_name,
        laps=request.laps,
    )


@router.post(
    "/laps/csv",
    response_model=LapIngestionResponse,
    responses={400: {"model": ErrorResponse, "description": "Invalid lap CSV"}},
    summary="Ingest lap timing CSV",
    description="Accepts UTF-8 CSV with lap, lap_time, and start_time columns.",
)
async def ingest_laps_csv(
    race_id: Annotated[str, Form(min_length=1, max_length=100)],
    driver_name: Annotated[str, Form(min_length=1, max_length=100)],
    file: Annotated[UploadFile, File(...)],
):
    """Validate a bounded CSV upload and store its normalized laps."""
    if not file.filename:
        raise LapDataValidationError("No lap CSV filename was provided.")
    data = await file.read(settings.max_lap_csv_size_bytes + 1)
    if len(data) > settings.max_lap_csv_size_bytes:
        raise LapDataValidationError(
            f"Lap CSV exceeds the {settings.MAX_LAP_CSV_SIZE_MB:g} MB limit."
        )
    laps = parse_lap_csv(data)
    return ingest_laps_service(
        _stores.race_store,
        race_id=race_id,
        driver_name=driver_name,
        laps=laps,
    )


@router.get(
    "/{race_id}",
    response_model=RaceOverview,
    responses={404: {"model": ErrorResponse, "description": "Race not found"}},
    summary="Get race overview",
)
async def get_race(race_id: str):
    """Retrieve a race overview by stable race ID."""
    if race_id not in _stores.race_store:
        raise HTTPException(status_code=404, detail=f"Race '{race_id}' not found.")

    race = _stores.race_store[race_id]
    laps = race["laps"]
    best_time = min((lap.lap_time_seconds for lap in laps), default=None)
    average_time = sum(lap.lap_time_seconds for lap in laps) / len(laps) if laps else None
    baseline = compute_lap_baseline(laps) if laps else None
    return RaceOverview(
        race_id=race["race_id"],
        driver_name=race["driver_name"],
        total_laps=len(laps),
        best_lap_time=round(best_time, 3) if best_time is not None else None,
        average_lap_time=round(average_time, 3) if average_time is not None else None,
        baseline_lap_time=baseline.baseline_lap_time if baseline else None,
        laps=laps,
        analyses=race.get("analyses", []),
        created_at=race["created_at"],
    )
