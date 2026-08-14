"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Silent Co-Driver"
    API_V1_STR: str = "/api/v1"

    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"

    MAX_UPLOAD_SIZE_MB: float = 50.0
    MIN_AUDIO_DURATION_SECONDS: float = 0.5
    MAX_AUDIO_DURATION_SECONDS: float = 600.0
    ALLOWED_EXTENSIONS: set[str] = {".wav", ".mp3", ".m4a", ".flac"}

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Configured upload limit converted to bytes."""
        return int(self.MAX_UPLOAD_SIZE_MB * 1024 * 1024)


settings = Settings()
