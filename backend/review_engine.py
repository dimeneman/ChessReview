"""
ChessReview Engine Module.
Performs game analysis, move classification, centipawn loss evaluation,
opening detection, and coach commentary generation using Stockfish.
"""

import base64
import io
import json
import os
from typing import Any, Dict, Generator, List, Optional

import chess
import chess.engine
import chess.pgn
import chess.polyglot
import matplotlib.pyplot as plt

from config import settings
from logger import logger

# ----------------- Configuration Defaults -----------------
ENGINE_PATH: str = settings.STOCKFISH_PATH
OPENINGS_JSON_PATH: str = settings.OPENINGS_JSON_PATH

MIN_OPENING_PLIES: int = settings.MIN_OPENING_PLIES
DEFAULT_DEPTH: int = settings.DEFAULT_DEPTH
DEFAULT_MULTIPV: int = settings.DEFAULT_MULTIPV
BRILLIANT_CP_GAP: int = settings.BRILLIANT_CP_GAP
CP_LOSS_CAP: int = settings.CP_LOSS_CAP

# ----------------- Load Openings JSON (Cached In-Memory) -----------------
_OPENINGS_DB: Dict[str, str] = {}
try:
    if os.path.exists(OPENINGS_JSON_PATH):
        with open(OPENINGS_JSON_PATH, "r", encoding="utf-8") as f:
            _OPENINGS_DB = json.load(f)
        logger.info(f"Successfully loaded {len(_OPENINGS_DB)} chess opening positions from {OPENINGS_JSON_PATH}")
    else:
        logger.warning(f"Openings file not found at {OPENINGS_JSON_PATH}. Opening detection will be disabled.")
except Exception as exc:
    logger.error(f"Failed to load openings from {OPENINGS_JSON_PATH}: {exc}")
    _OPENINGS_DB = {}


# ----------------- Analysis Helpers -----------------
def material_count(board: chess.Board) -> int:
    """Calculates piece material balance from White's perspective."""
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
    }
    score = 0
    for piece_type, value in values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def cp_loss_to_accuracy(cp_loss: int) -> float:
    """Maps centipawn loss to a smooth accuracy percentage [0.0 - 100.0]."""
    capped_loss = min(cp_loss, CP_LOSS_CAP)
    accuracy = 100.0 - (capped_loss / 5.0)
    return max(0.0, min(100.0, accuracy))


def average(lst: List[float]) -> float:
    """Computes arithmetic mean with a default fallback of 100.0 for empty lists."""
    return sum(lst) / len(lst) if lst else 100.0


def eval_to_bar(score: Optional[chess.engine.PovScore]) -> float:
    """
    Normalizes a chess.engine score into an evaluation bar float in [-1.0, +1.0].
    Positive indicates White advantage; negative indicates Black advantage.
    """
    if score is None:
        return 0.0
    if score.is_mate():
        # Mate score positive: White has forced mate; Mate score negative: Black has forced mate
        mate_moves = score.mate()
        if mate_moves is not None:
            return 1.0 if mate_moves >= 0 else -1.0
        return 1.0
    cp = score.score(mate_score=100000)
    if cp is None:
        return 0.0
    cp = max(-1000, min(1000, cp))
    return cp / 1000.0


# ----------------- Move Classification -----------------
def classify_move(
    move: chess.Move,
    best_move: Optional[chess.Move],
    score_before: Optional[chess.engine.PovScore],
    score_after: Optional[chess.engine.PovScore],
    cp_loss: int,
    material_before: int,
    material_after: int,
    best_score: Optional[chess.engine.PovScore] = None,
    second_score: Optional[chess.engine.PovScore] = None,
    brilliant_cp_gap: int = BRILLIANT_CP_GAP,
) -> str:
    """
    Classifies a played move into standard Chess.com-style taxonomic tiers:
    Brilliant, Great, Best, Excellent, Good, Inaccuracy, Mistake, Blunder, Missed Win, Missed Mate.
    """

    def score_to_cp(s: Optional[chess.engine.PovScore]) -> Optional[int]:
        if s is None:
            return None
        try:
            if s.is_mate():
                m = s.mate()
                return 100000 if (m is not None and m > 0) else -100000
            return s.score(mate_score=100000)
        except Exception:
            return None

    best_cp = score_to_cp(best_score)
    second_cp = score_to_cp(second_score)

    # 1. Missed Mate
    if score_before is not None and score_before.is_mate():
        if score_after is None or not score_after.is_mate():
            return "Missed Mate"

    # 2. Missed Win
    if score_before is not None and score_after is not None:
        sb_cp = score_to_cp(score_before)
        sa_cp = score_to_cp(score_after)
        if sb_cp is not None and sa_cp is not None:
            if sb_cp > 500 and sa_cp < 200:
                return "Missed Win"

    # 3. Brilliant: MultiPV gap (only winning move by significant margin)
    if (
        best_move is not None
        and move == best_move
        and best_cp is not None
        and second_cp is not None
        and (best_cp - second_cp) >= brilliant_cp_gap
    ):
        return "Brilliant"

    # 4. Brilliant: Piece sacrifice with positive positional evaluation
    if (
        best_move is not None
        and move == best_move
        and material_after < material_before
        and score_after is not None
        and score_before is not None
    ):
        try:
            before_cp = score_to_cp(score_before)
            after_cp = score_to_cp(score_after)
            if before_cp is not None and after_cp is not None:
                delta = after_cp - before_cp
                if (delta >= 300 and after_cp > 200) or (delta <= -300 and after_cp < -200):
                    return "Brilliant"
        except Exception:
            pass

    # 5. Great Move
    if (
        best_move is not None
        and move == best_move
        and score_before is not None
    ):
        sb_val = score_to_cp(score_before)
        if sb_val is not None and abs(sb_val) > 200:
            return "Great"

    # 6. Best Move
    if best_move is not None and move == best_move:
        return "Best"

    # 7. Standard Centipawn Loss Thresholds
    if cp_loss <= 20:
        return "Excellent"
    if cp_loss <= 50:
        return "Good"
    if cp_loss <= 100:
        return "Inaccuracy"
    if cp_loss <= 300:
        return "Mistake"
    return "Blunder"


def get_coach_comment(
    label: str,
    played_san: str,
    best_san: str,
    cp_loss: int,
    side: str,
) -> str:
    """Generates tailored virtual coach commentary for the played move."""
    comments = {
        "Brilliant": "You saw your chance for a brilliant move and you took it! Incredible vision.",
        "Great": "That was a great move! You are playing with high precision.",
        "Best": f"{played_san} is the best move in this position. Keep it up!",
        "Excellent": "An excellent move. You're maintaining a strong position.",
        "Good": "A good solid move.",
        "Inaccuracy": f"This is an inaccuracy. {best_san} was better.",
        "Mistake": f"That move was a mistake. You gave up some advantage. {best_san} was the best move.",
        "Blunder": f"You blundered. This move loses significant material or advantage. You should have played {best_san}.",
        "Missed Mate": f"You missed a forced checkmate! {best_san} would have led to mate.",
        "Missed Win": f"You missed a chance to win cleanly. {best_san} was the winning continuation.",
        "Theory": "Book move following opening theory.",
    }
    return comments.get(label, "Interesting move.")


# ----------------- Core Batch Review Function -----------------
def review_game(
    pgn_text: str,
    engine_path: str = ENGINE_PATH,
    depth: int = DEFAULT_DEPTH,
    return_eval_graph_image: bool = False,
    multipv: int = DEFAULT_MULTIPV,
) -> Dict[str, Any]:
    """
    Parses a PGN string and evaluates every move using Stockfish.
    Returns complete analysis results including accuracies, classifications, and eval graph.
    """
    pgn_io = io.StringIO(pgn_text)
    try:
        game = chess.pgn.read_game(pgn_io)
    except Exception as exc:
        logger.error(f"Failed to parse PGN: {exc}")
        return {"error": f"Could not parse PGN: {exc}"}

    if game is None:
        return {"error": "No game found in PGN text."}

    board = game.board()

    # Launch engine process
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as exc:
        logger.error(f"Could not initialize Stockfish engine at '{engine_path}': {exc}")
        return {"error": f"Could not start engine at '{engine_path}': {exc}"}

    results: Dict[str, Any] = {
        "moves": [],
        "opening": None,
        "white_accuracy": None,
        "black_accuracy": None,
        "eval_graph": [],
    }

    move_no = 1
    ply_count = 0
    played_moves_san: List[str] = []
    current_opening: Optional[str] = None

    white_accuracies: List[float] = []
    black_accuracies: List[float] = []
    eval_graph: List[float] = []

    try:
        for move in game.mainline_moves():
            side = "W" if board.turn == chess.WHITE else "B"
            material_before = material_count(board)
            san_played_raw = board.san(move)
            played_moves_san.append(san_played_raw)

            cp_loss = 0
            san_best = "-"
            label = "Unknown"
            best_move = None
            best_score = None
            second_score = None

            # MultiPV analysis for top lines
            try:
                infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
            except Exception:
                infos = None

            if isinstance(infos, list) and len(infos) > 0:
                top_info = infos[0]
                pv = top_info.get("pv")
                if pv and len(pv) > 0:
                    best_move = pv[0]
                else:
                    try:
                        best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
                    except Exception:
                        best_move = None

                try:
                    score_obj = top_info.get("score")
                    best_score = score_obj.white() if score_obj is not None else None
                except Exception:
                    best_score = None

                try:
                    if len(infos) > 1 and infos[1].get("score") is not None:
                        second_score = infos[1].get("score").white()
                except Exception:
                    second_score = None
            else:
                try:
                    best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
                except Exception:
                    best_move = None

            try:
                san_best = board.san(best_move) if best_move else "-"
            except Exception:
                san_best = "-"

            # Analyze before move
            info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_before = info_before.get("score")
            if score_before is not None:
                score_before = score_before.white()

            # Execute move on internal board
            board.push(move)
            material_after = material_count(board)

            # Analyze after move
            info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_after = info_after.get("score")
            if score_after is not None:
                score_after = score_after.white()

            # Calculate evaluation bar
            eval_bar = eval_to_bar(score_after)
            eval_graph.append(eval_bar)

            # Calculate centipawn loss
            cp_before = None
            cp_after = None
            try:
                cp_before = score_before.score(mate_score=100000) if score_before is not None else None
            except Exception:
                cp_before = None
            try:
                cp_after = score_after.score(mate_score=100000) if score_after is not None else None
            except Exception:
                cp_after = None

            if cp_before is not None and cp_after is not None:
                cp_loss_val = cp_before - cp_after
                if side == "B":
                    cp_loss_val = -cp_loss_val
                cp_loss = abs(int(cp_loss_val))
            else:
                cp_loss = 0

            cp_loss = min(cp_loss, CP_LOSS_CAP)

            label = classify_move(
                move,
                best_move,
                score_before,
                score_after,
                cp_loss,
                material_before,
                material_after,
                best_score=best_score,
                second_score=second_score,
                brilliant_cp_gap=brilliant_cp_gap,
            )

            # Opening theory matching via FEN
            current_fen_key = board.board_fen()
            if current_fen_key in _OPENINGS_DB:
                current_opening = _OPENINGS_DB[current_fen_key]
                label = "Theory"
                cp_loss = 0

            # Accuracy accumulation
            if label != "Theory":
                move_acc = cp_loss_to_accuracy(cp_loss)
                if side == "W":
                    white_accuracies.append(move_acc)
                else:
                    black_accuracies.append(move_acc)

            entry = {
                "ply": ply_count + 1,
                "move_no": move_no,
                "side": side,
                "played_san": san_played_raw,
                "best_san": san_best,
                "is_book_move": label == "Theory",
                "cp_loss": cp_loss,
                "label": label,
                "coach_comment": get_coach_comment(label, san_played_raw, san_best, cp_loss, side),
                "eval": eval_graph[-1] if eval_graph else 0.0,
                "opening": current_opening,
            }
            results["moves"].append(entry)

            if side == "B":
                move_no += 1
            ply_count += 1

        # Final aggregate calculations
        results["opening"] = current_opening
        results["white_accuracy"] = round(average(white_accuracies), 2)
        results["black_accuracy"] = round(average(black_accuracies), 2)
        results["eval_graph"] = eval_graph

        # Optional server-side plot rendering
        if return_eval_graph_image:
            try:
                fig, ax = plt.subplots(figsize=(10, 4))
                moves_x = list(range(1, len(eval_graph) + 1))
                ax.plot(moves_x, eval_graph, linewidth=2)
                ax.axhline(0, linestyle="--", linewidth=1)
                ax.set_xlabel("Move (ply)")
                ax.set_ylabel("Evaluation (White + / Black -)")
                ax.set_title("Game Evaluation Over Time")
                ax.set_ylim(-1.05, 1.05)
                plt.tight_layout()
                buf = io.BytesIO()
                plt.savefig(buf, format="png")
                plt.close(fig)
                buf.seek(0)
                results["eval_graph_image_base64"] = base64.b64encode(buf.read()).decode("ascii")
            except Exception as plot_err:
                logger.warning(f"Failed to generate eval graph plot: {plot_err}")
                results["eval_graph_image_base64"] = None

    except Exception as exc:
        logger.error(f"Error analyzing game: {exc}", exc_info=True)
        try:
            engine.quit()
        except Exception:
            pass
        return {"error": f"Error analyzing game: {exc}"}

    finally:
        try:
            engine.quit()
        except Exception:
            pass

    return results


# ----------------- Streaming Review Generator -----------------
def review_game_stream(
    pgn_text: str,
    engine_path: str = ENGINE_PATH,
    depth: int = DEFAULT_DEPTH,
    multipv: int = DEFAULT_MULTIPV,
) -> Generator[str, None, None]:
    """
    Generator that yields JSON lines for real-time progress:
    {"type": "init", "total_ply": N, "players": {...}}
    {"type": "progress", "ply": i, "cur_move": "e4", "percent": 5.5}
    {"type": "complete", "data": {...}}
    """
    pgn_io = io.StringIO(pgn_text)
    try:
        game = chess.pgn.read_game(pgn_io)
    except Exception as exc:
        logger.error(f"Stream PGN parse error: {exc}")
        yield json.dumps({"error": f"Could not parse PGN: {exc}"}) + "\n"
        return

    if game is None:
        yield json.dumps({"error": "No game found in PGN text."}) + "\n"
        return

    board = game.board()

    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as exc:
        logger.error(f"Could not start Stockfish stream engine: {exc}")
        yield json.dumps({"error": f"Could not start engine: {exc}"}) + "\n"
        return

    # Count total plies
    total_ply = sum(1 for _ in game.mainline_moves())
    headers = game.headers
    white_name = headers.get("White", "White")
    black_name = headers.get("Black", "Black")

    yield json.dumps({
        "type": "init",
        "total_ply": total_ply,
        "players": {"white": white_name, "black": black_name},
    }) + "\n"

    results: Dict[str, Any] = {
        "moves": [],
        "opening": None,
        "white_accuracy": None,
        "black_accuracy": None,
        "eval_graph": [],
        "players": {"white": white_name, "black": black_name},
    }

    move_no = 1
    ply_count = 0
    played_moves_san: List[str] = []
    current_opening: Optional[str] = None

    white_accuracies: List[float] = []
    black_accuracies: List[float] = []
    eval_graph: List[float] = []

    try:
        for move in game.mainline_moves():
            side = "W" if board.turn == chess.WHITE else "B"
            material_before = material_count(board)
            san_played_raw = board.san(move)
            played_moves_san.append(san_played_raw)

            # Emit incremental progress event
            pct = round(((ply_count) / max(total_ply, 1)) * 100, 1)
            yield json.dumps({
                "type": "progress",
                "ply": ply_count + 1,
                "cur_move": san_played_raw,
                "percent": pct,
            }) + "\n"

            cp_loss = 0
            san_best = "-"
            label = "Unknown"
            best_move = None
            best_score = None
            second_score = None

            try:
                infos = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
            except Exception:
                infos = None

            if isinstance(infos, list) and len(infos) > 0:
                top_info = infos[0]
                pv = top_info.get("pv")
                if pv and len(pv) > 0:
                    best_move = pv[0]
                else:
                    try:
                        best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
                    except Exception:
                        best_move = None

                try:
                    score_obj = top_info.get("score")
                    best_score = score_obj.white() if score_obj is not None else None
                except Exception:
                    best_score = None

                try:
                    if len(infos) > 1 and infos[1].get("score") is not None:
                        second_score = infos[1].get("score").white()
                except Exception:
                    second_score = None
            else:
                try:
                    best_move = engine.play(board, chess.engine.Limit(depth=depth)).move
                except Exception:
                    best_move = None

            try:
                san_best = board.san(best_move) if best_move else "-"
            except Exception:
                san_best = "-"

            # Analyze position before move
            info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_before = info_before.get("score")
            if score_before is not None:
                score_before = score_before.white()

            # Push move
            board.push(move)
            material_after = material_count(board)

            # Analyze position after move
            info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_after = info_after.get("score")
            if score_after is not None:
                score_after = score_after.white()

            # Evaluation bar calculation
            eval_bar = eval_to_bar(score_after)
            eval_graph.append(eval_bar)

            # Centipawn loss calculation
            cp_before = None
            cp_after = None
            try:
                cp_before = score_before.score(mate_score=100000) if score_before is not None else None
            except Exception:
                cp_before = None
            try:
                cp_after = score_after.score(mate_score=100000) if score_after is not None else None
            except Exception:
                cp_after = None

            if cp_before is not None and cp_after is not None:
                cp_loss_val = cp_before - cp_after
                if side == "B":
                    cp_loss_val = -cp_loss_val
                cp_loss = abs(int(cp_loss_val))
            else:
                cp_loss = 0

            cp_loss = min(cp_loss, CP_LOSS_CAP)

            label = classify_move(
                move,
                best_move,
                score_before,
                score_after,
                cp_loss,
                material_before,
                material_after,
                best_score=best_score,
                second_score=second_score,
                brilliant_cp_gap=BRILLIANT_CP_GAP,
            )

            # Opening theory matching via FEN
            current_fen_key = board.board_fen()
            if current_fen_key in _OPENINGS_DB:
                current_opening = _OPENINGS_DB[current_fen_key]
                label = "Theory"
                cp_loss = 0

            if label != "Theory":
                move_acc = cp_loss_to_accuracy(cp_loss)
                if side == "W":
                    white_accuracies.append(move_acc)
                else:
                    black_accuracies.append(move_acc)

            entry = {
                "ply": ply_count + 1,
                "move_no": move_no,
                "side": side,
                "played_san": san_played_raw,
                "best_san": san_best,
                "is_book_move": label == "Theory",
                "cp_loss": cp_loss,
                "label": label,
                "coach_comment": get_coach_comment(label, san_played_raw, san_best, cp_loss, side),
                "eval": eval_graph[-1] if eval_graph else 0.0,
                "opening": current_opening,
            }
            results["moves"].append(entry)

            if side == "B":
                move_no += 1
            ply_count += 1

        # Finalize results
        results["opening"] = current_opening
        results["white_accuracy"] = round(average(white_accuracies), 2)
        results["black_accuracy"] = round(average(black_accuracies), 2)
        results["eval_graph"] = eval_graph

        yield json.dumps({"type": "complete", "data": results}) + "\n"

    except Exception as exc:
        logger.error(f"Error in stream analysis loop: {exc}", exc_info=True)
        yield json.dumps({"error": f"Error in analysis loop: {exc}"}) + "\n"

    finally:
        try:
            engine.quit()
        except Exception:
            pass
