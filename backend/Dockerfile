# ==============================================================================
# ChessReview - Backend Production Dockerfile
# ==============================================================================
# Multi-stage build:
#   Stage 1: Python dependency compilation
#   Stage 2: Slim production runtime with native Stockfish engine
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependency Builder
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools required for compiled wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install production Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Production Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Runtime labels following Open Containers Initiative (OCI) standards
LABEL maintainer="ChessReview Team" \
      description="Production backend container for ChessReview API with Stockfish" \
      version="1.0.0"

WORKDIR /app

# Install native Stockfish chess engine and curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    stockfish \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/games/stockfish /usr/local/bin/stockfish

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Security: Create and switch to non-root execution user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STOCKFISH_PATH=/usr/games/stockfish \
    OPENINGS_JSON_PATH=/app/opening_books/openings.json \
    ENVIRONMENT=production \
    PORT=8000 \
    HOST=0.0.0.0

# Copy application source code
COPY backend/ /app/

# Ensure proper permissions for non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose backend port
EXPOSE 8000

# Container health probe checking /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production startup command using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

