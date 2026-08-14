from __future__ import annotations

from backend.app.api.routes import _stores
from backend.app.main import app
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
