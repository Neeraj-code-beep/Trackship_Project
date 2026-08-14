"""
Lazy-loaded model registry for AI/ML pipelines.
Prevents slow server startups by deferring model initialization until first use.
Provides graceful fallbacks when models are unavailable.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Singleton registry that lazily loads AI/ML models on first access.
    All models are initialized once and cached for subsequent calls.
    """

    _instance: Optional[ModelRegistry] = None
    _models: dict[str, Any] = {}
    _load_errors: dict[str, str] = {}

    def __new__(cls) -> ModelRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
            cls._instance._load_errors = {}
        return cls._instance

    def get_whisper_model(self) -> Optional[Any]:
        """
        Lazily load OpenAI Whisper model (tiny for dev, base for production).
        Returns None if whisper is not installed.
        """
        key = "whisper"
        if key in self._models:
            return self._models[key]
        if key in self._load_errors:
            return None

        try:
            import whisper

            logger.info("Loading Whisper model (tiny)...")
            model = whisper.load_model("tiny")
            self._models[key] = model
            logger.info("Whisper model loaded successfully.")
            return model
        except ImportError:
            self._load_errors[key] = "whisper package not installed"
            logger.warning(
                "Whisper not available. Using rule-based transcription fallback."
            )
            return None
        except Exception as e:
            self._load_errors[key] = str(e)
            logger.warning(f"Failed to load Whisper model: {e}. Using fallback.")
            return None

    def get_emotion_model(self) -> Optional[Any]:
        """
        Lazily load a HuggingFace Speech Emotion Recognition model.
        Returns None if transformers is not installed.
        """
        key = "emotion_ser"
        if key in self._models:
            return self._models[key]
        if key in self._load_errors:
            return None

        try:
            from transformers import pipeline

            logger.info("Loading Speech Emotion Recognition pipeline...")
            model = pipeline(
                "audio-classification",
                model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                top_k=4,
            )
            self._models[key] = model
            logger.info("SER model loaded successfully.")
            return model
        except ImportError:
            self._load_errors[key] = "transformers package not installed"
            logger.warning(
                "HuggingFace transformers not available. "
                "Using acoustic-feature-based emotion fallback."
            )
            return None
        except Exception as e:
            self._load_errors[key] = str(e)
            logger.warning(f"Failed to load SER model: {e}. Using fallback.")
            return None

    def is_model_available(self, key: str) -> bool:
        """Check if a model is loaded or can be loaded."""
        return key in self._models and key not in self._load_errors

    def get_status(self) -> dict:
        """Return the status of all model slots."""
        return {
            "loaded": list(self._models.keys()),
            "errors": dict(self._load_errors),
        }


# Module-level singleton accessor
registry = ModelRegistry()
