"""
Pytest fixtures and configuration for ChessReview test suite.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure backend directory is in Python path for direct imports
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Provides a TestClient instance for API endpoint testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pgn() -> str:
    """Returns a short, valid 4-move PGN (Scholar's Mate)."""
    return (
        '[Event "Casual Game"]\n'
        '[Site "ChessReview"]\n'
        '[Date "2026.01.01"]\n'
        '[White "Player1"]\n'
        '[Black "Player2"]\n'
        '[Result "1-0"]\n\n'
        '1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0\n'
    )


@pytest.fixture
def sample_fen_startpos() -> str:
    """Returns the starting board position FEN."""
    return "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


@pytest.fixture
def sample_fen_checkmate() -> str:
    """Returns a checkmate position FEN (Fool's mate)."""
    return "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"


@pytest.fixture
def sample_fen_stalemate() -> str:
    """Returns a classic stalemate position FEN."""
    return "k7/8/1Q6/8/8/8/8/7K b - - 0 1"

