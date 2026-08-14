# Silent Co-Driver Backend API Contract

Version: `0.2.0`  
Base path: `/api/v1`

The backend is independently usable through JSON/HTTP and Swagger at `/docs`. AI results are
derived from uploaded audio. Model or inference failures return errors; they do not produce demo
transcripts, randomized emotions, or fabricated scores.

Driver-state scores are prototype estimates from speech emotion, acoustic features, and a documented
heuristic fusion engine. The estimated fatigue score is not a medical assessment. Correlation is an
association and does not establish causation.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/health` | Lightweight service/model-registry status; never loads models |
| POST | `/api/v1/audio/upload` | Validate, decode, and safely persist audio |
| POST | `/api/v1/race/laps` | Ingest lap timing as JSON |
| POST | `/api/v1/race/laps/csv` | Ingest lap timing as CSV |
| GET | `/api/v1/race/{race_id}` | Retrieve normalized race/lap data |
| POST | `/api/v1/analysis` | Run the complete driver-intelligence pipeline |

`GET /health` remains as a compatibility alias and is omitted from Swagger.

## Structured errors

All known failures include the nested contract below. The top-level `detail` and `error_code` fields
are retained for compatibility.

```json
{
  "detail": "The requested audio file was not found.",
  "error_code": "AUDIO_NOT_FOUND",
  "error": {
    "code": "AUDIO_NOT_FOUND",
    "message": "The requested audio file was not found.",
    "request_id": "2e374bb0-e34c-441b-97f4-b9fe12fa03f7"
  }
}
```

Validation failures may add `error.details` containing only field location, message, and type. Raw
request values, tracebacks, model paths, and secrets are not returned. Every response includes an
`x-request-id` header.

Implemented error codes include:

- `INVALID_AUDIO`, `UNSUPPORTED_AUDIO_FORMAT`, `AUDIO_TOO_LARGE`, `AUDIO_TOO_SHORT`,
  `AUDIO_TOO_LONG`, `AUDIO_DECODER_UNAVAILABLE`
- `INVALID_LAP_DATA`, `RACE_NOT_FOUND`, `AUDIO_NOT_FOUND`
- `MODEL_UNAVAILABLE`, `TRANSCRIPTION_FAILED`, `EMOTION_ANALYSIS_FAILED`,
  `EMOTION_LABEL_MAPPING_FAILED`, `ANALYSIS_FAILED`
- `REQUEST_VALIDATION_ERROR`, `INTERNAL_SERVER_ERROR`

## Audio upload

### `POST /api/v1/audio/upload`

Send `multipart/form-data` with one `file` field. Supported extensions are `.wav`, `.mp3`, `.m4a`,
and `.flac`. The default limit is 50 MB and decoded duration must be between 0.5 and 600 seconds.
Extension, reliable MIME type, container type, decodability, decoded frames, size, and duration are
validated.

```json
{
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "filename": "radio.wav",
  "file_size_bytes": 32044,
  "duration_seconds": 1.0,
  "sample_rate": 16000,
  "format": "wav",
  "upload_timestamp": "2026-08-14T12:00:00Z",
  "storage_path": "data/uploads/c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e.wav",
  "message": "Audio file uploaded successfully"
}
```

The storage path is a logical relative path. The original filename is never used as a server path.

## Lap ingestion

### `POST /api/v1/race/laps`

```json
{
  "race_id": "race-001",
  "driver_name": "Demo Driver",
  "laps": [
    {"lap_number": 1, "lap_time_seconds": 89.42, "start_time": 0.0},
    {"lap_number": 2, "lap_time_seconds": 89.71, "start_time": 89.42}
  ]
}
```

`start_time` and `end_time` may be omitted for sequential JSON laps. The backend derives complete
boundaries. The legacy `timestamp` field is retained as the lap end timestamp.

### `POST /api/v1/race/laps/csv`

Send `multipart/form-data` fields `race_id`, `driver_name`, and `file`.

```csv
lap,lap_time,start_time
1,89.420,0.000
2,89.710,89.420
3,90.180,179.130
```

An optional `end_time` column is accepted and checked against `start_time + lap_time`. CSV input is
bounded to 2 MB/10,000 rows. Empty input, missing columns, invalid or non-finite values, nonpositive or
implausibly long lap times, duplicate/unordered laps, overlapping time ranges, and inconsistent end
times are rejected.

Lap intervals use `start_time <= timestamp < end_time`. Segment midpoint determines assignment when a
radio segment crosses a boundary. An exact final-lap end timestamp remains assigned to the final lap.

## Analysis

### `POST /api/v1/analysis`

```json
{
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "race_id": "race-001"
}
```

`race_id` is optional. If supplied, it must exist. Processing is:

1. decode once and retain original-amplitude plus normalized 16 kHz waveforms;
2. run lazy-loaded Whisper ASR;
3. run lazy-loaded speech-emotion recognition on transcript segments;
4. extract acoustic features and session-relative deviations;
5. fuse stress, estimated fatigue, calm, and neutral state scores;
6. align segment midpoints to lap intervals;
7. calculate median baseline, signed lap deltas, safe correlations, and insights.

Top-level response fields:

```json
{
  "analysis_id": "analysis_3d90d3e9-cf10-4ee8-a70c-fc66509966ec",
  "audio_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "file_id": "c9b2e1f4-8a3d-4c7a-9b1e-2f3a4b5c6d7e",
  "race_id": "race-001",
  "summary": {
    "dominant_state": "stressed",
    "average_stress_score": 63.4,
    "average_fatigue_score": 31.8,
    "average_calm_score": 22.1,
    "segments_analyzed": 3
  },
  "transcription": {},
  "acoustic_analysis": {},
  "driver_states": [],
  "aligned_laps": [],
  "correlations": {},
  "fatigue_trend": {},
  "insights": [],
  "overall_stress": 0.634,
  "overall_fatigue": 0.318,
  "processing_time_ms": 145.2
}
```

`overall_stress` and `overall_fatigue` remain 0–1 compatibility fields. Summary and per-segment fused
scores use 0–100.

Transcript segments include stable IDs, real Whisper start/end timestamps, nullable confidence, and
detected-speech state. Confidence is `null` when Whisper does not supply a finite average log
probability. Empty/silent audio produces no transcript segments; it never produces placeholder text.

Driver states include raw SER labels, centralized mapped probabilities, acoustic features, fused
scores, normalized signals, supporting explanations, and an evidence-reliability confidence value.

Lap analysis uses the median of all valid lap times. `lap_delta > 0` means slower than the median and
`lap_delta < 0` means faster. Robust timing anomalies are flagged, not deleted. Correlations exclude
laps without radio evidence and flagged timing anomalies. They return `pearson_r: null` with
`insufficient_data` or `zero_variance` when a coefficient is not defensible.

Insights have deterministic IDs, `low`/`medium`/`high` priority, a rule `type`, title, cautious message,
and the exact `evidence` that triggered the rule. The legacy `severity`, `category`, and `data` fields
remain available.
