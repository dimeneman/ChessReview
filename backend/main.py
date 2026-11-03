"""
Main FastAPI application entry point for ChessReview API.
Provides high-performance chess game analysis, live evaluation,
streamed progress updates, and Chess.com game fetching.
"""

import os
import shutil
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict

import requests
from fastapi import Body, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from config import settings
from live_analysis import analyze_position
from logger import logger
from review_engine import review_game, review_game_stream

# Application launch timestamp for uptime tracking
START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handler for startup and shutdown procedures."""
    logger.info("Starting ChessReview API service...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Configured Stockfish Path: {settings.STOCKFISH_PATH}")

    # Verify Stockfish availability
    engine_exists = os.path.exists(settings.STOCKFISH_PATH) or (shutil.which(settings.STOCKFISH_PATH) is not None)
    if engine_exists:
        logger.info("Stockfish engine located successfully.")
    else:
        logger.warning(
            f"Stockfish binary not detected at '{settings.STOCKFISH_PATH}'. "
            "Please configure STOCKFISH_PATH or ensure Stockfish is installed on system PATH."
        )

    yield

    logger.info("Shutting down ChessReview API service...")


app = FastAPI(
    title="Chess Review API",
    description="Production-grade Chess.com-style game review and position analysis powered by Stockfish.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ----------------- Middleware -----------------
# Request execution time logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={duration_ms}ms"
    )
    return response


# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Request / Response Models -----------------
class PGNRequest(BaseModel):
    """Request payload containing a full PGN string."""
    pgn: str = Field(..., description="Portable Game Notation (PGN) text string of the chess game.")


class AnalyzeRequest(BaseModel):
    """Request payload containing a FEN position string."""
    fen: str = Field(..., description="Forsyth-Edwards Notation (FEN) string representing board position.")


class FetchGamesRequest(BaseModel):
    """Request payload for querying Chess.com public archives."""
    username: str = Field(..., min_length=1, max_length=50, description="Chess.com username")
    year: int = Field(..., ge=2000, le=2100, description="Archive year (e.g., 2026)")
    month: int = Field(..., ge=1, le=12, description="Archive month (1-12)")


# ----------------- Root & Health Check Endpoints -----------------
@app.get(
    "/",
    tags=["General"],
    summary="Root Service Status",
    description="Returns basic service information and documentation links.",
)
def root() -> Dict[str, Any]:
    return {
        "service": "ChessReview API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get(
    "/health",
    tags=["Monitoring"],
    summary="Health Check Endpoint",
    description="Reports service operational status, uptime, version, and engine binary availability for Docker and Kubernetes probes.",
)
def health_check() -> Dict[str, Any]:
    engine_available = os.path.exists(settings.STOCKFISH_PATH) or (shutil.which(settings.STOCKFISH_PATH) is not None)
    uptime_seconds = round(time.time() - START_TIME, 2)

    status_str = "healthy" if engine_available else "degraded"

    return {
        "status": status_str,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime_seconds,
        "engine_available": engine_available,
        "engine_path": settings.STOCKFISH_PATH,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ----------------- Game Review Endpoints -----------------
@app.post(
    "/review",
    tags=["Analysis"],
    summary="Full Game Review (JSON Body)",
    description="Analyzes an entire PGN game and returns move classifications, accuracy scores, and evaluation graph.",
)
def review(req: PGNRequest) -> Dict[str, Any]:
    if not req.pgn.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PGN text cannot be empty.",
        )
    return review_game(req.pgn)


@app.post(
    "/review-raw",
    tags=["Analysis"],
    summary="Full Game Review (Raw Text Body)",
    description="Accepts raw PGN plain text. Supports optional query parameter `depth` (5-25).",
)
def review_raw(
    pgn: str = Body(..., media_type="text/plain"),
    depth: int = 18,
) -> Dict[str, Any]:
    if not pgn.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PGN text cannot be empty.",
        )
    depth = max(settings.MIN_DEPTH, min(depth, settings.MAX_DEPTH))
    return review_game(pgn, depth=depth)


@app.post(
    "/review-stream",
    tags=["Analysis"],
    summary="Streaming Game Review (NDJSON)",
    description="Streams real-time analysis progress using Newline-Delimited JSON (NDJSON) events.",
)
def review_stream(
    pgn: str = Body(..., media_type="text/plain"),
    depth: int = 18,
) -> StreamingResponse:
    if not pgn.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PGN text cannot be empty.",
        )
    depth = max(settings.MIN_DEPTH, min(depth, settings.MAX_DEPTH))
    return StreamingResponse(
        review_game_stream(pgn, depth=depth),
        media_type="application/x-ndjson",
    )


# ----------------- Live Position Analysis -----------------
@app.post(
    "/analyze",
    tags=["Analysis"],
    summary="Live FEN Position Evaluation",
    description="Analyzes a single FEN position and returns best move, evaluation, and game state.",
)
def analyze(req: AnalyzeRequest) -> Dict[str, Any]:
    if not req.fen.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FEN string cannot be empty.",
        )
    return analyze_position(req.fen)


# ----------------- Third-Party Chess.com Integration -----------------
@app.post(
    "/fetch-games",
    tags=["Integration"],
    summary="Fetch Monthly Chess.com Games",
    description="Queries the public Chess.com Archives API for a player's games in a given year/month.",
)
def fetch_games(req: FetchGamesRequest) -> Dict[str, Any]:
    url = f"https://api.chess.com/pub/player/{req.username}/games/{req.year}/{req.month:02d}"
    headers = {
        "User-Agent": "ChessReviewApp/1.0 (https://github.com/ChessReview; contact@example.com)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as exc:
        logger.warning(f"Chess.com API HTTP error for user '{req.username}': {exc}")
        return JSONResponse(
            status_code=response.status_code,
            content={"error": f"Chess.com API error: {response.text}"},
        )
    except requests.exceptions.RequestException as exc:
        logger.error(f"Network error querying Chess.com: {exc}")
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={"error": f"Failed to connect to Chess.com API: {str(exc)}"},
        )
