"""Silent Co-Driver FastAPI application."""

from __future__ import annotations

import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from backend.app.api.routes.analysis import router as analysis_router
from backend.app.api.routes.audio import router as audio_router
from backend.app.api.routes.race import router as race_router
from backend.app.audio.validation import AudioValidationError
from backend.app.core.config import settings
from backend.app.core.errors import AppError
from backend.app.services.analysis_service import AnalysisPipelineError
from backend.app.services.emotion_service import EmotionAnalysisError
from backend.app.services.lap_service import LapDataValidationError
from backend.app.services.transcription_service import TranscriptionError
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting; models remain lazy.", settings.PROJECT_NAME)
    yield
    logger.info("%s shutting down.", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AI-assisted race-engineering analysis of driver radio audio and lap timing. "
        "Driver-state and fatigue-related outputs are estimates, not medical assessments."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audio_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(race_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = _request_id(request.headers.get("x-request-id"))
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (time.perf_counter() - started) * 1000.0,
    )
    return response


@app.exception_handler(AudioValidationError)
async def audio_validation_handler(request: Request, exc: AudioValidationError):
    return _error_response(request, exc.status_code, exc.error_code, exc.message)


@app.exception_handler(LapDataValidationError)
async def lap_validation_handler(request: Request, exc: LapDataValidationError):
    return _error_response(request, exc.status_code, exc.error_code, str(exc))


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return _error_response(request, exc.status_code, exc.error_code, str(exc))


@app.exception_handler(AnalysisPipelineError)
async def analysis_error_handler(request: Request, exc: AnalysisPipelineError):
    return _error_response(request, exc.status_code, exc.error_code, str(exc))


@app.exception_handler(TranscriptionError)
async def transcription_error_handler(request: Request, exc: TranscriptionError):
    return _error_response(request, exc.status_code, exc.error_code, str(exc))


@app.exception_handler(EmotionAnalysisError)
async def emotion_error_handler(request: Request, exc: EmotionAnalysisError):
    return _error_response(request, exc.status_code, exc.error_code, str(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    details = [
        {
            "location": [str(part) for part in error["loc"]],
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _error_response(
        request,
        422,
        "REQUEST_VALIDATION_ERROR",
        "Request validation failed.",
        details=details,
    )


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
    code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
    return _error_response(request, exc.status_code, code, message)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception for request_id=%s",
        getattr(request.state, "request_id", "unknown"),
    )
    return _error_response(
        request,
        500,
        "INTERNAL_SERVER_ERROR",
        "Internal server error.",
    )


@app.get(f"{settings.API_V1_STR}/health", tags=["System"])
@app.get("/health", tags=["System"], include_in_schema=False)
async def health_check():
    """Fast health/status response that never loads an AI model."""
    from backend.app.services.model_registry import registry

    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": app.version,
        "models": registry.get_status(),
    }


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    nested: dict[str, Any] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if details is not None:
        nested["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message,
            "error_code": code,
            "error": nested,
        },
    )


def _request_id(candidate: str | None) -> str:
    if candidate and len(candidate) <= 100 and re.fullmatch(r"[A-Za-z0-9._-]+", candidate):
        return candidate
    return str(uuid.uuid4())
