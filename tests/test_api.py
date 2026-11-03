"""
API Integration & Contract Tests for ChessReview FastAPI Backend.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test that GET / returns 200 OK and valid service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "ChessReview API"
    assert data["status"] == "online"
    assert "version" in data
    assert "docs_url" in data
    assert "health_url" in data


def test_health_check_endpoint(client: TestClient):
    """Test that GET /health returns required health check fields for orchestrators."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "uptime_seconds" in data
    assert "engine_available" in data
    assert "timestamp" in data
    assert "environment" in data


def test_review_endpoint_empty_body(client: TestClient):
    """Test that POST /review rejects empty PGN strings with 400 Bad Request."""
    response = client.post("/review", json={"pgn": "   "})
    assert response.status_code == 400
    assert "PGN text cannot be empty" in response.json()["detail"]


def test_review_raw_endpoint_empty_body(client: TestClient):
    """Test that POST /review-raw rejects empty body with 400 Bad Request."""
    response = client.post(
        "/review-raw",
        content="",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 400


def test_review_stream_empty_body(client: TestClient):
    """Test that POST /review-stream rejects empty body with 400 Bad Request."""
    response = client.post(
        "/review-stream",
        content="",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 400


def test_analyze_endpoint_empty_fen(client: TestClient):
    """Test that POST /analyze rejects empty FEN with 400 Bad Request."""
    response = client.post("/analyze", json={"fen": "  "})
    assert response.status_code == 400


def test_analyze_endpoint_checkmate_detection(client: TestClient, sample_fen_checkmate: str):
    """
    Test that POST /analyze correctly identifies game-over / checkmate state
    without requiring external engine analysis.
    """
    response = client.post("/analyze", json={"fen": sample_fen_checkmate})
    assert response.status_code == 200
    data = response.json()
    assert data["is_game_over"] is True
    assert data["evaluation"] == -100.0  # White is checkmated
    assert data["turn"] == "white"


def test_analyze_endpoint_stalemate_detection(client: TestClient, sample_fen_stalemate: str):
    """
    Test that POST /analyze correctly identifies stalemate as 0.0 evaluation.
    """
    response = client.post("/analyze", json={"fen": sample_fen_stalemate})
    assert response.status_code == 200
    data = response.json()
    assert data["is_game_over"] is True
    assert data["evaluation"] == 0.0  # Stalemate evaluation is 0.0
    assert data["turn"] == "black"


def test_fetch_games_validation(client: TestClient):
    """Test that POST /fetch-games enforces request validation constraints."""
    # Invalid month > 12
    response = client.post("/fetch-games", json={"username": "hikaru", "year": 2026, "month": 13})
    assert response.status_code == 422

    # Invalid year < 2000
    response = client.post("/fetch-games", json={"username": "hikaru", "year": 1999, "month": 5})
    assert response.status_code == 422

