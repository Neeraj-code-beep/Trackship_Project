"""Thread-safe lazy registry for the backend's AI models."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    """Raised when a required AI model cannot be loaded."""

    error_code = "MODEL_UNAVAILABLE"

    def __init__(self, model_key: str, message: str) -> None:
        self.model_key = model_key
        super().__init__(message)


class ModelRegistry:
    """Load each configured model on first use and reuse it thereafter."""

    def __init__(self) -> None:
        self._models: dict[str, Any] = {}
        self._load_errors: dict[str, str] = {}
        self._lock = threading.RLock()
        self._device: str | None = None

    def get_whisper_model(self) -> Any:
        """Return the cached Whisper model, loading it once when necessary."""
        return self._get_or_load("whisper", self._load_whisper)

    def get_emotion_model(self) -> Any:
        """Return the cached speech-emotion pipeline, loading it once when necessary."""
        return self._get_or_load("emotion_ser", self._load_emotion)

    def _get_or_load(self, key: str, loader: Callable[[], Any]) -> Any:
        if key in self._models:
            return self._models[key]

        with self._lock:
            if key in self._models:
                return self._models[key]
            if key in self._load_errors:
                raise ModelUnavailableError(
                    key,
                    f"The required '{key}' model is unavailable.",
                )

            logger.info("Loading AI model '%s'.", key)
            try:
                model = loader()
                if model is None:
                    raise RuntimeError("model loader returned no instance")
            except Exception as exc:
                safe_error = f"{type(exc).__name__}: model load failed"
                self._load_errors[key] = safe_error
                logger.exception("Failed to load AI model '%s'.", key)
                raise ModelUnavailableError(
                    key,
                    f"The required '{key}' model could not be loaded.",
                ) from exc

            self._models[key] = model
            logger.info("AI model '%s' loaded successfully.", key)
            return model

    def _load_whisper(self) -> Any:
        import whisper

        model_dir = self._model_directory("whisper")
        return whisper.load_model(
            settings.ASR_MODEL_NAME,
            device=self.device,
            download_root=str(model_dir),
        )

    def _load_emotion(self) -> Any:
        from transformers import pipeline

        token = settings.HF_TOKEN.get_secret_value() if settings.HF_TOKEN else None
        pipeline_device = 0 if self.device == "cuda" else -1
        return pipeline(
            "audio-classification",
            model=settings.EMOTION_MODEL_NAME,
            device=pipeline_device,
            token=token,
        )

    @property
    def device(self) -> str:
        """Resolve and cache the compute device without assuming CUDA."""
        if self._device is not None:
            return self._device

        with self._lock:
            if self._device is not None:
                return self._device

            requested = settings.AI_DEVICE.strip().lower()
            if requested == "auto":
                selected = "cuda" if self._cuda_available() else "cpu"
            elif requested == "cuda":
                if not self._cuda_available():
                    raise RuntimeError("AI_DEVICE=cuda was requested but CUDA is unavailable")
                selected = "cuda"
            elif requested == "cpu":
                selected = "cpu"
            else:
                raise RuntimeError("AI_DEVICE must be one of: auto, cpu, cuda")

            self._device = selected
            logger.info("Selected AI compute device: %s", selected)
            return selected

    @staticmethod
    def _cuda_available() -> bool:
        try:
            import torch
        except ImportError:
            return False
        return bool(torch.cuda.is_available())

    @staticmethod
    def _model_directory(name: str) -> Path:
        directory = (settings.MODEL_DIR / name).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def get_status(self) -> dict[str, Any]:
        """Report registry state without importing or loading model libraries."""
        keys = ("whisper", "emotion_ser")
        states = {
            key: (
                "loaded"
                if key in self._models
                else "unavailable"
                if key in self._load_errors
                else "not_loaded"
            )
            for key in keys
        }
        return {
            "loaded": sorted(self._models),
            "errors": dict(self._load_errors),
            "states": states,
            "configured_device": settings.AI_DEVICE,
            "selected_device": self._device,
        }

    def reset(self) -> None:
        """Clear registry state; intended for isolated tests only."""
        with self._lock:
            self._models.clear()
            self._load_errors.clear()
            self._device = None


registry = ModelRegistry()
