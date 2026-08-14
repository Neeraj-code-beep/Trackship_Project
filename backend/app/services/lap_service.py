"""Lap timing parsing, validation, normalization, and in-memory ingestion."""

from __future__ import annotations

import csv
import io
import math
from datetime import datetime, timezone
from typing import Any

from app.schemas.schemas import LapData, LapIngestionResponse

REQUIRED_CSV_COLUMNS = frozenset({"lap", "lap_time", "start_time"})
TIMING_TOLERANCE_SECONDS = 0.01
MAX_LAP_ROWS = 10_000


class LapDataValidationError(ValueError):
    """A readable lap-data validation failure."""

    error_code = "INVALID_LAP_DATA"
    status_code = 400


def parse_lap_csv(data: bytes) -> list[LapData]:
    """Parse the documented ``lap,lap_time,start_time`` CSV format."""
    if not data:
        raise LapDataValidationError("The lap CSV file is empty.")
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise LapDataValidationError("The lap CSV must be UTF-8 encoded.") from exc

    try:
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise LapDataValidationError("The lap CSV has no header row.")
        normalized_headers = [header.strip().lower() for header in reader.fieldnames]
        if len(normalized_headers) != len(set(normalized_headers)):
            raise LapDataValidationError("The lap CSV contains duplicate columns.")
        missing = REQUIRED_CSV_COLUMNS.difference(normalized_headers)
        if missing:
            raise LapDataValidationError(
                f"The lap CSV is missing required columns: {', '.join(sorted(missing))}."
            )

        rows: list[LapData] = []
        for row_number, raw_row in enumerate(reader, start=2):
            if row_number > MAX_LAP_ROWS + 1:
                raise LapDataValidationError(f"The lap CSV exceeds the {MAX_LAP_ROWS} row limit.")
            if None in raw_row:
                raise LapDataValidationError(
                    f"CSV row {row_number} contains more values than the header."
                )
            row = {
                key.strip().lower(): (value.strip() if value is not None else "")
                for key, value in raw_row.items()
                if key is not None
            }
            if not any(row.values()):
                continue
            rows.append(_parse_csv_row(row, row_number))
    except csv.Error as exc:
        raise LapDataValidationError("The lap CSV could not be parsed.") from exc

    if not rows:
        raise LapDataValidationError("The lap CSV contains no lap rows.")
    return normalize_laps(rows)


def normalize_laps(laps: list[LapData]) -> list[LapData]:
    """Return complete, ordered lap boundaries or raise a readable error."""
    if not laps:
        raise LapDataValidationError("At least one lap is required.")

    normalized: list[LapData] = []
    seen_laps: set[int] = set()
    previous_lap_number = 0
    previous_end = 0.0

    for index, lap in enumerate(laps, start=1):
        if lap.lap_number in seen_laps:
            raise LapDataValidationError(f"Duplicate lap number {lap.lap_number}.")
        if lap.lap_number <= previous_lap_number:
            raise LapDataValidationError("Lap numbers must be strictly increasing.")

        if lap.start_time is not None:
            start = lap.start_time
        elif lap.timestamp is not None:
            start = lap.timestamp - lap.lap_time_seconds
        else:
            start = previous_end
        if not math.isfinite(start) or start < 0:
            raise LapDataValidationError(f"Lap {lap.lap_number} has an invalid start_time.")

        derived_end = start + lap.lap_time_seconds
        explicit_end = lap.end_time if lap.end_time is not None else lap.timestamp
        if explicit_end is not None:
            if not math.isfinite(explicit_end) or explicit_end <= start:
                raise LapDataValidationError(f"Lap {lap.lap_number} has an invalid end_time.")
            if abs(explicit_end - derived_end) > TIMING_TOLERANCE_SECONDS:
                raise LapDataValidationError(
                    f"Lap {lap.lap_number} timing is inconsistent with lap_time."
                )
            end = explicit_end
        else:
            end = derived_end

        if index > 1 and start + TIMING_TOLERANCE_SECONDS < previous_end:
            raise LapDataValidationError(f"Lap {lap.lap_number} overlaps the preceding lap.")

        normalized.append(
            lap.model_copy(
                update={
                    "start_time": round(start, 6),
                    "end_time": round(end, 6),
                    "timestamp": round(end, 6),
                }
            )
        )
        seen_laps.add(lap.lap_number)
        previous_lap_number = lap.lap_number
        previous_end = end
    return normalized


def ingest_laps(
    race_store: dict[str, dict[str, Any]],
    *,
    race_id: str,
    driver_name: str,
    laps: list[LapData],
) -> LapIngestionResponse:
    """Validate and store laps while rejecting silent duplicate suppression."""
    if race_id in race_store:
        existing = race_store[race_id]
        if existing["driver_name"] != driver_name:
            raise LapDataValidationError(f"Race '{race_id}' already belongs to a different driver.")
        normalized = normalize_laps([*existing["laps"], *laps])
        laps_added = len(laps)
        existing["laps"] = normalized
    else:
        normalized = normalize_laps(laps)
        laps_added = len(normalized)
        race_store[race_id] = {
            "race_id": race_id,
            "driver_name": driver_name,
            "laps": normalized,
            "analyses": [],
            "created_at": datetime.now(timezone.utc),
        }

    return LapIngestionResponse(
        race_id=race_id,
        driver_name=driver_name,
        laps_received=laps_added,
        message=f"Successfully ingested {laps_added} laps for race '{race_id}'.",
    )


def _parse_csv_row(row: dict[str, str], row_number: int) -> LapData:
    lap_number = _parse_lap_number(row.get("lap", ""), row_number)
    lap_time = _parse_finite_float(row.get("lap_time", ""), "lap_time", row_number)
    start_time = _parse_finite_float(row.get("start_time", ""), "start_time", row_number)
    end_text = row.get("end_time", "")
    end_time = _parse_finite_float(end_text, "end_time", row_number) if end_text else None
    try:
        return LapData(
            lap_number=lap_number,
            lap_time_seconds=lap_time,
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        raise LapDataValidationError(f"Invalid values on CSV row {row_number}.") from exc


def _parse_lap_number(value: str, row_number: int) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise LapDataValidationError(f"CSV row {row_number} has a non-integer lap number.") from exc
    if str(parsed) != value.strip() or parsed <= 0:
        raise LapDataValidationError(f"CSV row {row_number} has an invalid lap number.")
    return parsed


def _parse_finite_float(value: str, column: str, row_number: int) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise LapDataValidationError(f"CSV row {row_number} has a non-numeric {column}.") from exc
    if not math.isfinite(parsed):
        raise LapDataValidationError(f"CSV row {row_number} has a non-finite {column}.")
    return parsed
