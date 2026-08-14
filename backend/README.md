# Silent Co-Driver Backend

FastAPI backend for real driver-radio transcription, speech-emotion inference, acoustic analysis,
driver-state fusion, lap alignment, correlation, and evidence-backed race-engineering insights.

## Windows setup

From the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements-dev.txt
```

Python 3.10 or newer is supported. PyTorch installation may vary for CUDA systems; the default
requirements work on CPU and the registry automatically uses CUDA when PyTorch reports it available.

Copy the environment template only when overrides are needed:

```powershell
Copy-Item backend\.env.example backend\.env
```

Important defaults:

- audio: `.wav`, `.mp3`, `.m4a`, `.flac`; 50 MB; 0.5–600 seconds;
- ASR: OpenAI Whisper `tiny`;
- SER: `ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition`;
- compute device: `auto` (CUDA when available, otherwise CPU);
- uploads/processed/model files remain untracked runtime artifacts;
- `ENABLE_AI_MOCKS=false`; the runtime pipeline contains no built-in fabricated fallback results.

`HF_TOKEN` is optional for public models. Never commit a token. Model weights are loaded and cached on
the first analysis request that needs them; API startup and health checks do not download models.

## Run

From the backend directory:

```powershell
cd backend
uvicorn app.main:app --reload
```

Open [Swagger](http://127.0.0.1:8000/docs) or call
`http://127.0.0.1:8000/api/v1/health`.

## Test and lint

Ordinary tests mock AI inference and do not download model weights:

```powershell
python -m pytest backend\tests -q
python -m ruff check backend\app backend\tests
```

## Lap CSV

```csv
lap,lap_time,start_time
1,89.420,0.000
2,89.710,89.420
3,90.180,179.130
```

Submit it to `POST /api/v1/race/laps/csv` with form fields `race_id`, `driver_name`, and `file`.

## API and model behavior

See [`docs/api-contract.md`](../docs/api-contract.md) for the complete stable contract. Main paths are:

- `GET /api/v1/health`
- `POST /api/v1/audio/upload`
- `POST /api/v1/race/laps`
- `POST /api/v1/race/laps/csv`
- `GET /api/v1/race/{race_id}`
- `POST /api/v1/analysis`

Whisper and SER failures return structured `MODEL_UNAVAILABLE`, `TRANSCRIPTION_FAILED`, or
`EMOTION_ANALYSIS_FAILED` responses. Silence returns an empty no-speech transcription. Estimated
fatigue is a transparent vocal heuristic, not a medical diagnosis, and correlations do not establish
causation.

Race sessions are stored in process memory for this hackathon build. Restarting the backend clears
race data; uploaded audio remains on local disk until managed externally.
