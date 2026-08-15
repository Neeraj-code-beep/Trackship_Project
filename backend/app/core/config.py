"""Application configuration loaded from environment variables."""

import json
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Silent Co-Driver"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = False

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    MODEL_DIR: Path = BASE_DIR / "models"

    MAX_UPLOAD_SIZE_MB: float = 50.0
    MIN_AUDIO_DURATION_SECONDS: float = 0.5
    MAX_AUDIO_DURATION_SECONDS: float = 600.0
    MAX_LAP_CSV_SIZE_MB: float = 2.0
    ALLOWED_EXTENSIONS: set[str] = {".wav", ".mp3", ".m4a", ".flac"}

    ASR_MODEL_NAME: str = "tiny"
    ASR_LANGUAGE: str | None = None
    EMOTION_MODEL_NAME: str = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    SER_SEGMENT_SECONDS: float = Field(default=5.0, gt=0.0, le=60.0)
    AI_DEVICE: str = "auto"
    ENABLE_AI_MOCKS: bool = False
    HF_TOKEN: SecretStr | None = None
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=True,
        extra="ignore",
        enable_decoding=False,
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        """Accept JSON lists or comma-separated strings from environment variables."""
        if value is None:
            return value
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return []
            if candidate.startswith("["):
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
                raise ValueError("CORS_ORIGINS JSON must decode to a list")
            return [item.strip() for item in candidate.split(",") if item.strip()]
        return value

    @property
    def max_upload_size_bytes(self) -> int:
        """Configured upload limit converted to bytes."""
        return int(self.MAX_UPLOAD_SIZE_MB * 1024 * 1024)

    @property
    def max_lap_csv_size_bytes(self) -> int:
        return int(self.MAX_LAP_CSV_SIZE_MB * 1024 * 1024)

    @model_validator(mode="after")
    def resolve_runtime_paths(self) -> "Settings":
        """Anchor relative runtime paths to the backend directory."""
        base_dir = self.BASE_DIR.resolve()
        for field_name in ("UPLOAD_DIR", "PROCESSED_DIR", "MODEL_DIR"):
            value = getattr(self, field_name)
            if not value.is_absolute():
                setattr(self, field_name, (base_dir / value).resolve())
        return self


settings = Settings()
