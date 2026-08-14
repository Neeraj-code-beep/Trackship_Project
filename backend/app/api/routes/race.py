"""
Race data API routes.
POST /api/v1/race/laps — ingest lap timing data
GET  /api/v1/race/{race_id} — retrieve race overview
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.app.schemas.schemas import (
    LapIngestionRequest,
    LapIngestionResponse,
    RaceOverview,
    ErrorResponse,
)
from backend.app.api.routes import _stores

router = APIRouter(prefix="/race", tags=["Race"])


@router.post(
    "/laps",
    response_model=LapIngestionResponse,
    summary="Ingest lap timing data",
    description="Submit lap times, sector splits, and telemetry for a race session.",
)
async def ingest_laps(request: LapIngestionRequest):
    """
    Ingest lap timing data for a race. Creates a new race entry or
    appends to an existing one.
    """
    race_id = request.race_id

    if race_id in _stores.race_store:
        # Append laps to existing race
        existing = _stores.race_store[race_id]
        existing_numbers = {l.lap_number for l in existing["laps"]}
        new_laps = [l for l in request.laps if l.lap_number not in existing_numbers]
        existing["laps"].extend(new_laps)
        laps_added = len(new_laps)
    else:
        # Create new race entry
        _stores.race_store[race_id] = {
            "race_id": race_id,
            "driver_name": request.driver_name,
            "laps": list(request.laps),
            "analyses": [],
            "created_at": datetime.utcnow(),
        }
        laps_added = len(request.laps)

    return LapIngestionResponse(
        race_id=race_id,
        driver_name=request.driver_name,
        laps_received=laps_added,
        message=f"Successfully ingested {laps_added} laps for race '{race_id}'.",
    )


@router.get(
    "/{race_id}",
    response_model=RaceOverview,
    responses={
        404: {"model": ErrorResponse, "description": "Race not found"},
    },
    summary="Get race overview",
    description="Retrieve full race data including laps, best/average times, and linked analyses.",
)
async def get_race(race_id: str):
    """Retrieve race overview by race_id."""
    if race_id not in _stores.race_store:
        raise HTTPException(
            status_code=404,
            detail=f"Race '{race_id}' not found.",
        )

    race = _stores.race_store[race_id]
    laps = race["laps"]

    best_time = min((l.lap_time_seconds for l in laps), default=None) if laps else None
    avg_time = (
        sum(l.lap_time_seconds for l in laps) / len(laps) if laps else None
    )

    return RaceOverview(
        race_id=race["race_id"],
        driver_name=race["driver_name"],
        total_laps=len(laps),
        best_lap_time=round(best_time, 3) if best_time else None,
        average_lap_time=round(avg_time, 3) if avg_time else None,
        laps=laps,
        analyses=race.get("analyses", []),
        created_at=race["created_at"],
    )
