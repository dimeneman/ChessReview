"""
Configuration module for ChessReview Backend.
Centralizes environment variables and runtime settings with production defaults.
"""

import os
import shutil
from pathlib import Path
from typing import List


class Settings:
    """Application runtime settings and environment variables."""

    # Project directories
    BASE_DIR: Path = Path(__file__).resolve().parent

    # Service configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # CORS configuration
    # Comma-separated list of origins or wildcard
    CORS_ORIGINS_RAW: str = os.getenv("CORS_ORIGINS", "*")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        if self.CORS_ORIGINS_RAW.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS_RAW.split(",") if origin.strip()]

    # Engine analysis parameters
    DEFAULT_DEPTH: int = int(os.getenv("DEFAULT_DEPTH", "18"))
    DEFAULT_MULTIPV: int = int(os.getenv("DEFAULT_MULTIPV", "3"))
    MIN_DEPTH: int = int(os.getenv("MIN_DEPTH", "5"))
    MAX_DEPTH: int = int(os.getenv("MAX_DEPTH", "25"))
    BRILLIANT_CP_GAP: int = int(os.getenv("BRILLIANT_CP_GAP", "300"))
    CP_LOSS_CAP: int = int(os.getenv("CP_LOSS_CAP", "1000"))
    MIN_OPENING_PLIES: int = int(os.getenv("MIN_OPENING_PLIES", "6"))

    # File paths
    @property
    def OPENINGS_JSON_PATH(self) -> str:
        env_path = os.getenv("OPENINGS_JSON_PATH")
        if env_path:
            p = Path(env_path)
            if p.is_absolute():
                return str(p)
            # Check relative to base dir or current working dir
            if (self.BASE_DIR / p).exists():
                return str(self.BASE_DIR / p)
            return str(p)
        return str(self.BASE_DIR / "opening_books" / "openings.json")

    @property
    def STOCKFISH_PATH(self) -> str:
        """
        Locates the Stockfish binary with prioritized fallbacks:
        1. Explicit STOCKFISH_PATH environment variable
        2. System PATH (e.g. `which stockfish` / `/usr/games/stockfish` in Debian/Ubuntu)
        3. Local engine directory inside backend/engine/stockfish
        """
        env_path = os.getenv("STOCKFISH_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # Check system PATH
        system_bin = shutil.which("stockfish")
        if system_bin and os.path.exists(system_bin):
            return system_bin

        # Common Linux/Debian package installation paths
        common_paths = [
            "/usr/games/stockfish",
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "/opt/homebrew/bin/stockfish",
        ]
        for cp in common_paths:
            if os.path.exists(cp):
                return cp

        # Local workspace directory fallback
        local_bin = self.BASE_DIR / "engine" / "stockfish"
        if local_bin.exists():
            return str(local_bin)

        # Windows executable fallback
        local_exe = self.BASE_DIR / "engine" / "stockfish.exe"
        if local_exe.exists():
            return str(local_exe)

        return env_path or "/usr/games/stockfish"


settings = Settings()

