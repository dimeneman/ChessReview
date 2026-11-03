"""
Live position analysis module for ChessReview Backend.
Evaluates individual chess board positions (FEN) using Stockfish.
"""

from typing import Any, Dict

import chess
import chess.engine

from config import settings
from logger import logger

ENGINE_PATH: str = settings.STOCKFISH_PATH


def analyze_position(fen: str, depth: int = 15) -> Dict[str, Any]:
    """
    Analyzes a single FEN chess position.
    Returns the evaluation score, best move, best SAN, side to move,
    and game-over or forced move status.
    """
    try:
        board = chess.Board(fen)
    except Exception as exc:
        logger.warning(f"Invalid FEN string provided '{fen}': {exc}")
        return {"error": f"Invalid FEN: {exc}"}

    # Count legal moves to detect forced moves
    num_legal = len(list(board.legal_moves))

    # Handle game-over positions (checkmate, stalemate, insufficient material)
    if board.is_game_over():
        if board.is_checkmate():
            eval_val = -100.0 if board.turn == chess.WHITE else 100.0
        else:
            eval_val = 0.0  # Stalemate / Draw
        return {
            "best_move": None,
            "best_san": "-",
            "evaluation": eval_val,
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_forced": False,
            "is_game_over": True,
        }

    is_forced = num_legal == 1

    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    except Exception as exc:
        logger.error(f"Could not launch Stockfish engine at '{ENGINE_PATH}': {exc}")
        return {"error": f"Could not launch Stockfish engine: {exc}"}

    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move_result = engine.play(board, chess.engine.Limit(depth=depth))
        best_move = best_move_result.move

        pov_score = info.get("score")
        eval_val = 0.0
        if pov_score:
            white_score = pov_score.white()
            if white_score.is_mate():
                mate_val = white_score.mate()
                eval_val = 100.0 if (mate_val is not None and mate_val > 0) else -100.0
            else:
                cp = white_score.score(mate_score=10000)
                eval_val = (cp or 0) / 100.0

        return {
            "best_move": best_move.uci() if best_move else None,
            "best_san": board.san(best_move) if best_move else "-",
            "evaluation": eval_val,
            "turn": "white" if board.turn == chess.WHITE else "black",
            "is_forced": is_forced,
            "is_game_over": False,
        }
    except Exception as exc:
        logger.error(f"Error during position evaluation: {exc}")
        return {"error": str(exc)}
    finally:
        try:
            engine.quit()
        except Exception:
            pass
