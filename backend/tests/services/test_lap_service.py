from __future__ import annotations

import pytest
from app.schemas.schemas import LapData
from app.services.lap_service import (
    LapDataValidationError,
    ingest_laps,
    normalize_laps,
    parse_lap_csv,
)

VALID_CSV = b"""lap,lap_time,start_time
1,89.420,0.000
2,89.710,89.420
3,90.180,179.130
"""


def test_valid_csv_derives_complete_lap_boundaries():
    laps = parse_lap_csv(VALID_CSV)

    assert [lap.lap_number for lap in laps] == [1, 2, 3]
    assert laps[0].start_time == 0.0
    assert laps[0].end_time == 89.42
    assert laps[1].start_time == 89.42
    assert laps[1].end_time == 179.13
    assert laps[2].timestamp == 269.31


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"", "empty"),
        (b"lap,lap_time\n1,90\n", "missing required columns"),
        (b"lap,lap_time,start_time\n", "no lap rows"),
        (b"lap,lap_time,start_time\n1,fast,0\n", "non-numeric lap_time"),
        (b"lap,lap_time,start_time\none,90,0\n", "non-integer lap number"),
        (b"lap,lap_time,start_time\n1,nan,0\n", "non-finite lap_time"),
        (b"lap,lap_time,start_time\n1,90,inf\n", "non-finite start_time"),
    ],
)
def test_invalid_csv_returns_readable_error(payload, message):
    with pytest.raises(LapDataValidationError, match=message):
        parse_lap_csv(payload)


def test_negative_and_impossible_lap_times_are_rejected():
    with pytest.raises(LapDataValidationError, match="Invalid values"):
        parse_lap_csv(b"lap,lap_time,start_time\n1,-1,0\n")
    with pytest.raises(LapDataValidationError, match="Invalid values"):
        parse_lap_csv(b"lap,lap_time,start_time\n1,4000,0\n")


def test_duplicate_laps_are_rejected():
    payload = b"lap,lap_time,start_time\n1,90,0\n1,91,90\n"

    with pytest.raises(LapDataValidationError, match="Duplicate lap"):
        parse_lap_csv(payload)


def test_unordered_or_overlapping_start_times_are_rejected():
    payload = b"lap,lap_time,start_time\n1,90,0\n2,91,50\n"

    with pytest.raises(LapDataValidationError, match="overlaps"):
        parse_lap_csv(payload)


def test_explicit_end_time_must_match_lap_time():
    payload = b"lap,lap_time,start_time,end_time\n1,90,0,95\n"

    with pytest.raises(LapDataValidationError, match="inconsistent"):
        parse_lap_csv(payload)


def test_json_laps_without_timestamps_are_normalized_sequentially():
    laps = normalize_laps(
        [
            LapData(lap_number=1, lap_time_seconds=90),
            LapData(lap_number=2, lap_time_seconds=91),
        ]
    )

    assert laps[0].start_time == 0
    assert laps[0].end_time == 90
    assert laps[1].start_time == 90
    assert laps[1].end_time == 181


def test_ingestion_does_not_silently_ignore_existing_duplicate():
    store = {}
    ingest_laps(
        store,
        race_id="race-1",
        driver_name="Driver",
        laps=[LapData(lap_number=1, lap_time_seconds=90)],
    )

    with pytest.raises(LapDataValidationError, match="Duplicate lap"):
        ingest_laps(
            store,
            race_id="race-1",
            driver_name="Driver",
            laps=[LapData(lap_number=1, lap_time_seconds=89)],
        )
