import chess
import chess.engine
import os

ENGINE_PATH = os.environ.get("STOCKFISH_PATH", "engine/stockfish")

def analyze_position(fen: str, depth: int = 15):
    """
    Analyzes a single position and returns eval and best move.
    """
    board = chess.Board(fen)
    
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    except Exception as e:
        return {"error": str(e)}

    try:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
        
        score = info.get("score")
        eval_val = 0.0
        if score:
            if score.is_mate():
                eval_val = 100.0 if score.mate() > 0 else -100.0
            else:
                eval_val = score.white().score(mate_score=10000) / 100.0

        return {
            "best_move": best_move.uci(),
            "best_san": board.san(best_move) if best_move else "-",
            "evaluation": eval_val,
            "turn": "white" if board.turn == chess.WHITE else "black"
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        engine.quit()
