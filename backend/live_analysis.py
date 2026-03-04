import chess
import chess.engine
import os

ENGINE_PATH = os.environ.get("STOCKFISH_PATH", "engine/stockfish")

def analyze_position(fen: str, depth: int = 15):
    """
    Analyzes a single position and returns eval, best move, and metadata.
    """
    board = chess.Board(fen)

    # Count legal moves to detect forced moves
    legal_moves = list(board.legal_moves)
    num_legal = len(legal_moves)

    # Handle game-over positions (checkmate, stalemate)
    if board.is_game_over():
        outcome = board.outcome()
        if board.is_checkmate():
            # The side that just MOVED (not the side to move) delivered checkmate
            # board.turn is the side that is now in checkmate
            eval_val = -100.0 if board.turn == chess.WHITE else 100.0
        else:
            eval_val = 0.0  # stalemate / draw
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
    except Exception as e:
        return {"error": str(e)}

    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move_result = engine.play(board, chess.engine.Limit(depth=depth))
        best_move = best_move_result.move

        pov_score = info.get("score")
        eval_val = 0.0
        if pov_score:
            # Get Score from White's perspective
            white_score = pov_score.white()
            if white_score.is_mate():
                eval_val = 100.0 if white_score.mate() > 0 else -100.0
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
    except Exception as e:
        return {"error": str(e)}
    finally:
        engine.quit()

