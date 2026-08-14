"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field, SecretStr, model_validator
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
    ALLOWED_EXTENSIONS: set[str] = {".wav", ".mp3", ".m4a", ".flac"}

    ASR_MODEL_NAME: str = "tiny"
    ASR_LANGUAGE: str | None = None
    EMOTION_MODEL_NAME: str = "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition"
    SER_SEGMENT_SECONDS: float = Field(default=5.0, gt=0.0, le=60.0)
    AI_DEVICE: str = "auto"
    ENABLE_AI_MOCKS: bool = False
    HF_TOKEN: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Configured upload limit converted to bytes."""
        return int(self.MAX_UPLOAD_SIZE_MB * 1024 * 1024)

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
