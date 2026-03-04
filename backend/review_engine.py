# review_engine.py
import os
import io
import base64
from typing import List, Tuple, Optional, Dict, Any

import chess
import chess.pgn
import chess.engine
import chess.polyglot
import matplotlib.pyplot as plt
import json

# ----------------- Config -----------------
ENGINE_PATH = os.environ.get("STOCKFISH_PATH", os.path.join(os.path.dirname(__file__), "engine/stockfish"))
OPENINGS_JSON_PATH = os.environ.get("OPENINGS_JSON_PATH", os.path.join(os.path.dirname(__file__), "opening_books/openings.json"))

MIN_OPENING_PLIES = 6         # set to 0 to detect from first ply
DEFAULT_DEPTH = 14
DEFAULT_MULTIPV = 3

BRILLIANT_CP_GAP = 300        # cp gap between best and 2nd best for "Brilliant"
CP_LOSS_CAP = 1000            # cap to avoid mate explosions


# ----------------- Load Openings JSON (once) -----------------
try:
    with open(OPENINGS_JSON_PATH, "r", encoding="utf-8") as f:
        _OPENINGS_DB = json.load(f)
except Exception as e:
    print(f"ERROR: Failed to load openings from {OPENINGS_JSON_PATH}: {e}")
    _OPENINGS_DB = {}


# ----------------- Analysis helpers -----------------
def material_count(board: chess.Board) -> int:
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
    cp_loss = min(cp_loss, CP_LOSS_CAP)
    accuracy = 100 - (cp_loss / 5)
    return max(0.0, min(100.0, accuracy))


def average(lst: List[float]) -> float:
    return sum(lst) / len(lst) if lst else 100.0


def eval_to_bar(score) -> float:
    if score is None:
        return 0.0
    if score.is_mate():
        # score.mate() > 0  → white has a forced mate (white winning)
        # score.mate() == 0 → checkmate just delivered, winner is white (Mate(0) from white's POV)
        # score.mate() < 0  → black has a forced mate (black winning)
        return 1.0 if score.mate() >= 0 else -1.0
    cp = score.score(mate_score=100000)
    cp = max(-1000, min(1000, cp))
    return cp / 1000.0


# ----------------- Improved classify_move (Brilliant detection) -----------------
def classify_move(
    move,
    best_move,
    score_before,
    score_after,
    cp_loss,
    material_before,
    material_after,
    best_score=None,
    second_score=None,
    brilliant_cp_gap: int = BRILLIANT_CP_GAP,
):
    def score_to_cp(s):
        if s is None:
            return None
        try:
            if s.is_mate():
                return 100000 if s.mate() > 0 else -100000
            return s.score(mate_score=100000)
        except Exception:
            return None

    best_cp = score_to_cp(best_score)
    second_cp = score_to_cp(second_score)

    # Missed Mate
    if score_before is not None and score_before.is_mate():
        if score_after is None or not score_after.is_mate():
            return "Missed Mate"

    # Missed Win
    if score_before is not None and score_after is not None:
        if score_before.score(mate_score=100000) > 500 and score_after.score(mate_score=100000) < 200:
            return "Missed Win"

    # Brilliant: multipv gap
    if (
        best_move is not None
        and move == best_move
        and best_cp is not None
        and second_cp is not None
        and (best_cp - second_cp) >= brilliant_cp_gap
    ):
        return "Brilliant"

    # Brilliant: sacrifice + strong eval improvement
    if (
        best_move is not None
        and move == best_move
        and material_after < material_before
        and score_after is not None
        and score_before is not None
    ):
        try:
            before_cp = (
                100000 if score_before.is_mate() and score_before.mate() > 0
                else -100000 if score_before.is_mate()
                else score_before.score(mate_score=100000)
            )
            after_cp = (
                100000 if score_after.is_mate() and score_after.mate() > 0
                else -100000 if score_after.is_mate()
                else score_after.score(mate_score=100000)
            )
            if before_cp is not None and after_cp is not None:
                delta = after_cp - before_cp
                if (delta >= 300 and after_cp > 200) or (delta <= -300 and after_cp < -200):
                    return "Brilliant"
        except Exception:
            pass

    # Great
    if (
        best_move is not None
        and move == best_move
        and score_before is not None
        and abs(score_before.score(mate_score=100000)) > 200
    ):
        return "Great"

    # Best
    if best_move is not None and move == best_move:
        return "Best"

    # Excellent / Good / Inaccuracy / Mistake / Blunder
    if cp_loss <= 20:
        return "Excellent"
    if cp_loss <= 50:
        return "Good"
    if cp_loss <= 100:
        return "Inaccuracy"
    if cp_loss <= 300:
        return "Mistake"
    return "Blunder"


def get_coach_comment(label, played_san, best_san, cp_loss, side):
    """
    Generates a 'Coach' style comment based on the move classification.
    """
    if label == "Brilliant":
        return "You saw your chance for a brilliant move and you took it! Incredible vision."
    if label == "Great":
        return "That was a great move! You are playing with high precision."
    if label == "Best":
        return f"{played_san} is the best move in this position. Keep it up!"
    if label == "Excellent":
        return "An excellent move. You're maintaining a strong position."
    if label == "Good":
        return "A good solid move."
    if label == "Inaccuracy":
        return f"This is an inaccuracy. {best_san} was better."
    if label == "Mistake":
        return f"That move was a mistake. You gave up some advantage. {best_san} was the best move."
    if label == "Blunder":
        return f"You blundered. This move loses significant material or advantage. You should have played {best_san}."
    if label == "Missed Mate":
        return f"You missed a forced checkmate! {best_san} would have led to mate."
    if label == "Missed Win":
        return f"You missed a chace to win cleanly. {best_san} was the winning continuation."
    
    return "Interesting move."



# ----------------- Core function -----------------
def review_game(
    pgn_text: str,
    engine_path: str = ENGINE_PATH,
    depth: int = DEFAULT_DEPTH,
    return_eval_graph_image: bool = False,
    multipv: int = DEFAULT_MULTIPV,
) -> Dict[str, Any]:
    # parse PGN
    pgn_io = io.StringIO(pgn_text)
    try:
        game = chess.pgn.read_game(pgn_io)
    except Exception as e:
        return {"error": f"Could not parse PGN: {e}"}
    if game is None:
        return {"error": "No game found in PGN text."}

    # print(f"DEBUG: Parsed game moves: {list(game.mainline_moves())}")
    board = game.board()

    # start engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        return {"error": f"Could not start engine at '{engine_path}': {e}"}

    results: Dict[str, Any] = {"moves": [], "opening": None, "white_accuracy": None, "black_accuracy": None, "eval_graph": []}

    move_no = 1
    ply_count = 0

    played_moves_san: List[str] = []
    current_opening: Optional[str] = None
    opening_match_len: int = 0   # track best matched prefix length so far
    opening_printed: bool = False

    white_accuracies: List[float] = []
    black_accuracies: List[float] = []
    eval_graph: List[float] = []

    eval_graph: List[float] = []

    try:
        for move in game.mainline_moves():
            side = "W" if board.turn == chess.WHITE else "B"

            material_before = material_count(board)

            san_played_raw = board.san(move)
            # san_played_norm = normalize_san(san_played_raw)  # ECO norm logic commented out
            played_moves_san.append(san_played_raw) # Storing raw SAN just for history references if needed

            # ----------------- OLD ECO LOGIC COMMENTED OUT -----------------

            # Detect opening every move once we have enough plies; update only if match is longer
            # if len(played_moves_san) >= MIN_OPENING_PLIES:
            #     eco_code, eco_name, match_len = simple_detect_opening_with_length(played_moves_san)
            #     if eco_name and match_len > opening_match_len:
            #         current_opening = f"{eco_code} — {eco_name}"
            #         opening_match_len = match_len
            #         # print only when first detected
            #         if not opening_printed:
            #             print(f"\nOpening detected: {current_opening}\n")
            #             opening_printed = True
            # ----------------------------------------------------------------

            cp_loss = 0
            san_best = "-"
            label = "Unknown"
            best_move = None
            best_score = None
            second_score = None

            # multipv analysis
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
                    best_score = top_info.get("score").white() if top_info.get("score") is not None else None
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

            # analyze before
            info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_before = info_before.get("score")
            if score_before is not None:
                score_before = score_before.white()

            # push move
            board.push(move)
            
            material_after = material_count(board)

            # analyze after
            info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_after = info_after.get("score")
            if score_after is not None:
                score_after = score_after.white()

            # eval graph
            eval_bar = eval_to_bar(score_after)
            eval_graph.append(eval_bar)

            # cp loss
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

            # Cap cp_loss to avoid mate explosions
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

            # Detect opening via FEN (openings.json) - Runs for both Book and Engine moves
            current_fen_key = board.board_fen()
            if current_fen_key in _OPENINGS_DB:
                current_opening = _OPENINGS_DB[current_fen_key]
                label = "Theory"
                cp_loss = 0

            # accuracy
            if label != "Theory":
                move_accuracy = cp_loss_to_accuracy(cp_loss)
                if side == "W":
                    white_accuracies.append(move_accuracy)
                else:
                    black_accuracies.append(move_accuracy)

            # record move
            entry = {
                "ply": ply_count + 1,
                "move_no": move_no,
                "side": side,
                "played_san": san_played_raw,
                "best_san": san_best,
                "is_book_move": False,
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

        # finalize
        results["opening"] = current_opening
        results["white_accuracy"] = round(average(white_accuracies), 2)
        results["black_accuracy"] = round(average(black_accuracies), 2)
        results["eval_graph"] = eval_graph

        # optional image
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
            except Exception:
                results["eval_graph_image_base64"] = None

    except Exception as e:
        try:
            engine.quit()
        except Exception:
            pass
        return {"error": f"Error analyzing game: {e}"}

    # cleanup
    try:
        engine.quit()
    except Exception:
        pass

    return results


def review_game_stream(
    pgn_text: str,
    engine_path: str = ENGINE_PATH,
    depth: int = DEFAULT_DEPTH,
    multipv: int = DEFAULT_MULTIPV,
):
    """
    Generator that yields JSON lines:
    {"type": "init", "total_ply": N}
    {"type": "progress", "ply": i, "cur_move": "e4", "percent": 5.5}
    {"type": "complete", "data": {...}}
    """
    import json
    
    # parse PGN
    pgn_io = io.StringIO(pgn_text)
    try:
        game = chess.pgn.read_game(pgn_io)
    except Exception as e:
        yield json.dumps({"error": f"Could not parse PGN: {e}"}) + "\n"
        return
        
    if game is None:
        yield json.dumps({"error": "No game found in PGN text."}) + "\n"
        return

    board = game.board()

    # start engine
    try:
        engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    except Exception as e:
        yield json.dumps({"error": f"Could not start engine: {e}"}) + "\n"
        return

    # Count total plies for progress
    temp_board = game.board()
    total_ply = 0
    for _ in game.mainline_moves():
        total_ply += 1
    
    headers = game.headers
    white_name = headers.get("White", "White")
    black_name = headers.get("Black", "Black")

    yield json.dumps({
        "type": "init", 
        "total_ply": total_ply,
        "players": {"white": white_name, "black": black_name}
    }) + "\n"

    results: Dict[str, Any] = {
        "moves": [], 
        "opening": None, 
        "white_accuracy": None, 
        "black_accuracy": None, 
        "eval_graph": [],
        "players": {"white": white_name, "black": black_name}
    }
    
    # Analysis State
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

            # Report progress START of move
            yield json.dumps({
                "type": "progress",
                "ply": ply_count + 1,
                "cur_move": san_played_raw,
                "percent": round(((ply_count) / total_ply) * 100, 1)
            }) + "\n"

            cp_loss = 0
            san_best = "-"
            label = "Unknown"
            best_move = None
            best_score = None
            second_score = None

            # Engine Analysis
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
                    best_score = top_info.get("score").white() if top_info.get("score") is not None else None
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

            try:
                san_best = board.san(best_move) if best_move else "-"
            except Exception:
                san_best = "-"

            # analyze before
            info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_before = info_before.get("score")
            if score_before is not None:
                score_before = score_before.white()

            # push move
            board.push(move)
            material_after = material_count(board)

            # analyze after
            info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_after = info_after.get("score")
            if score_after is not None:
                score_after = score_after.white()

            # eval graph
            eval_bar = eval_to_bar(score_after)
            eval_graph.append(eval_bar)

            # cp loss
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

            # Detect opening via FEN (openings.json) - Runs for both Book and Engine moves
            current_fen_key = board.board_fen()
            if current_fen_key in _OPENINGS_DB:
                current_opening = _OPENINGS_DB[current_fen_key]
                label = "Theory"
                cp_loss = 0

            if label != "Theory":
                move_accuracy = cp_loss_to_accuracy(cp_loss)
                if side == "W":
                    white_accuracies.append(move_accuracy)
                else:
                    black_accuracies.append(move_accuracy)

            # record move
            entry = {
                "ply": ply_count + 1,
                "move_no": move_no,
                "side": side,
                "played_san": san_played_raw,
                "best_san": san_best,
                "is_book_move": False,
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
        
        # finalize
        results["opening"] = current_opening
        results["white_accuracy"] = round(average(white_accuracies), 2)
        results["black_accuracy"] = round(average(black_accuracies), 2)
        results["eval_graph"] = eval_graph
        
        yield json.dumps({"type": "complete", "data": results}) + "\n"

    except Exception as e:
        yield json.dumps({"error": f"Error in analysis loop: {e}"}) + "\n"
    
    finally:
        try: engine.quit()
        except: pass
