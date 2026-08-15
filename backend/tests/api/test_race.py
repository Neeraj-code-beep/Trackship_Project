from __future__ import annotations

from app.api.routes import _stores
from app.main import app
from fastapi.testclient import TestClient


def setup_function():
    _stores.race_store.clear()


def teardown_function():
    _stores.race_store.clear()


def test_json_lap_ingestion_and_retrieval():
    client = TestClient(app)
    response = client.post(
        "/api/v1/race/laps",
        json={
            "race_id": "race-json",
            "driver_name": "Demo Driver",
            "laps": [
                {"lap_number": 1, "lap_time_seconds": 90.0},
                {"lap_number": 2, "lap_time_seconds": 91.0},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["laps_received"] == 2
    overview = client.get("/api/v1/race/race-json")
    assert overview.status_code == 200
    assert overview.json()["laps"][1]["start_time"] == 90.0
    assert overview.json()["laps"][1]["end_time"] == 181.0
    assert overview.json()["baseline_lap_time"] == 90.5


def test_csv_lap_ingestion():
    client = TestClient(app)
    response = client.post(
        "/api/v1/race/laps/csv",
        data={"race_id": "race-csv", "driver_name": "Demo Driver"},
        files={
            "file": (
                "laps.csv",
                b"lap,lap_time,start_time\n1,89.4,0\n2,89.8,89.4\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["laps_received"] == 2
    assert len(_stores.race_store["race-csv"]["laps"]) == 2


def test_duplicate_json_lap_returns_structured_validation_error():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/race/laps",
        json={
            "race_id": "race-duplicate",
            "driver_name": "Demo Driver",
            "laps": [
                {"lap_number": 1, "lap_time_seconds": 90},
                {"lap_number": 1, "lap_time_seconds": 91},
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_LAP_DATA"


def test_retrying_an_already_ingested_lap_is_rejected_without_mutating_race():
    client = TestClient(app, raise_server_exceptions=False)
    payload = {
        "race_id": "race-retry",
        "driver_name": "Test Driver",
        "laps": [{"lap_number": 1, "lap_time_seconds": 90}],
    }

    first = client.post("/api/v1/race/laps", json=payload)
    retry = client.post("/api/v1/race/laps", json=payload)

    assert first.status_code == 200
    assert retry.status_code == 400
    assert retry.json()["detail"] == "Duplicate lap number 1."

    overview = client.get("/api/v1/race/race-retry")
    assert overview.status_code == 200
    assert overview.json()["total_laps"] == 1
