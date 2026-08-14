"""
Silent Co-Driver — FastAPI Application Entry Point.
Registers all routers, CORS middleware, and exception handlers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.api.routes.audio import router as audio_router
from backend.app.api.routes.analysis import router as analysis_router
from backend.app.api.routes.race import router as race_router
from backend.app.audio.validation import AudioValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"🏎️  {settings.PROJECT_NAME} starting up...")
    logger.info(f"📂  Upload directory: {settings.UPLOAD_DIR}")
    yield
    logger.info(f"🏁  {settings.PROJECT_NAME} shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "AI-powered race engineering system that analyzes driver radio "
        "communications to detect stress, fatigue, and emotional states, "
        "correlating them with lap performance data."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ────────────────────────────────────────────────────────
app.include_router(audio_router, prefix=settings.API_V1_STR)
app.include_router(analysis_router, prefix=settings.API_V1_STR)
app.include_router(race_router, prefix=settings.API_V1_STR)


# ─── Exception Handlers ──────────────────────────────────────────────────────

@app.exception_handler(AudioValidationError)
async def audio_validation_handler(request: Request, exc: AudioValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.message, "error_code": exc.error_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Basic health check endpoint."""
    from backend.app.services.model_registry import registry
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "models": registry.get_status(),
    }
