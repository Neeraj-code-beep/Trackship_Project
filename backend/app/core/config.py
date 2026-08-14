import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Silent Co-Driver"
    API_V1_STR: str = "/api/v1"
    
    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    
    # Audio Validation Settings
    MAX_AUDIO_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: set = {".wav", ".mp3", ".m4a", ".flac"}
    ALLOWED_MIME_TYPES: set = {
        "audio/wav", "audio/x-wav", 
        "audio/mpeg", "audio/mp3", 
        "audio/m4a", "audio/x-m4a", "audio/mp4",
        "audio/flac", "audio/x-flac"
    }
    MIN_DURATION_SECONDS: float = 0.5
    MAX_DURATION_SECONDS: float = 600.0  # 10 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure uploads directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
