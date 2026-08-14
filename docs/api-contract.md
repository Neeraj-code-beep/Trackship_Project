# Silent Co-Driver - API Contract Specification

Version: `v1`  
Base URL: `/api/v1`

---

## 1. Audio Endpoint

### `POST /api/v1/audio/upload`

Upload a driver radio audio file for validation and storage.

- **Content-Type**: `multipart/form-data`
- **Supported Formats**: `.wav`, `.mp3`, `.m4a`, `.flac`
- **Max File Size**: 50 MB

#### Request Body
Form parameter:
- `file`: `UploadFile` (binary audio data)

#### Response `200 OK`
```json
{
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "filename": "radio_stint1_lap4.wav",
  "file_size_bytes": 1048576,
  "duration_seconds": 24.5,
  "sample_rate": 44100,
  "format": "wav",
  "upload_timestamp": "2026-08-14T12:00:00Z",
  "storage_path": "data/uploads/c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e.wav",
  "message": "Audio file uploaded successfully"
}
```

#### Error Responses
- `400 Bad Request`: Format unsupported, file empty, or duration out of bounds.
- `413 Payload Too Large`: File exceeds 50MB limit.

---

## 2. Analysis Endpoint

### `POST /api/v1/analysis`

Trigger full audio analysis: transcription, emotion recognition, lap timestamp alignment, and race-engineer insights.

- **Content-Type**: `application/json`

#### Request Body
```json
{
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "race_id": "demo-race-001"
}
```

#### Response `200 OK`
```json
{
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "race_id": "demo-race-001",
  "transcription": {
    "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
    "full_text": "Box box box, tyres are gone.",
    "segments": [
      {
        "start_time": 0.0,
        "end_time": 5.0,
        "text": "Box box box, tyres are gone.",
        "confidence": 0.92,
        "speaker": "Driver"
      }
    ],
    "language": "en",
    "duration_seconds": 24.5
  },
  "driver_states": [
    {
      "timestamp": 0.0,
      "dominant_emotion": "stressed",
      "probabilities": {
        "calm": 0.05,
        "stressed": 0.65,
        "neutral": 0.15,
        "tired": 0.15
      },
      "confidence": 0.65,
      "rms_energy": 0.35,
      "speech_rate_wpm": 160.0
    }
  ],
  "aligned_laps": [
    {
      "lap_number": 4,
      "lap_time_seconds": 91.234,
      "delta_to_best": 1.358,
      "dominant_emotion": "stressed",
      "stress_level": 0.65,
      "fatigue_level": 0.15
    }
  ],
  "insights": [
    {
      "id": "e4b1a2c3-d4e5-4f6a-7b8c-9d0e1f2a3b4c",
      "severity": "warning",
      "category": "Stress-Performance",
      "message": "Strong positive correlation between driver stress and lap time degradation.",
      "lap_number": 4,
      "timestamp": null,
      "data": { "correlation": 0.62 }
    }
  ],
  "overall_stress": 0.65,
  "overall_fatigue": 0.15,
  "processing_time_ms": 145.2
}
```

---

## 3. Race Endpoints

### `POST /api/v1/race/laps`

Ingest lap timing telemetry for alignment with driver state audio.

- **Content-Type**: `application/json`

#### Request Body
```json
{
  "race_id": "demo-race-001",
  "driver_name": "Demo Driver",
  "laps": [
    {
      "lap_number": 1,
      "lap_time_seconds": 92.456,
      "sector_1": 28.3,
      "sector_2": 34.1,
      "sector_3": 30.056,
      "tyre_compound": "soft",
      "fuel_load_kg": 105.0
    }
  ]
}
```

#### Response `200 OK`
```json
{
  "race_id": "demo-race-001",
  "driver_name": "Demo Driver",
  "laps_received": 1,
  "message": "Successfully ingested 1 laps for race 'demo-race-001'."
}
```

---

### `GET /api/v1/race/{race_id}`

Retrieve overview for a race session.

#### Response `200 OK`
```json
{
  "race_id": "demo-race-001",
  "driver_name": "Demo Driver",
  "total_laps": 8,
  "best_lap_time": 89.876,
  "average_lap_time": 91.202,
  "laps": [...],
  "analyses": [],
  "created_at": "2026-08-14T12:00:00Z"
}
```

---

## 4. System Endpoint

### `GET /health`

Health check and AI model registry status.

#### Response `200 OK`
```json
{
  "status": "healthy",
  "service": "Silent Co-Driver",
  "models": {
    "loaded": [],
    "errors": {}
  }
}
```
