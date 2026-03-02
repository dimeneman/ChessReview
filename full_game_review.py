import os
import chess
import chess.pgn
import chess.engine
import chess.polyglot
import matplotlib.pyplot as plt

from backend.opening_books.eco_loader import load_eco_openings, detect_opening

ENGINE_PATH = "backend/engine/stockfish"
BOOK_PATH = "backend/opening_books/books/bin/gm2001.bin"
ECO_PATH = "backend/opening_books/eco/openings.pgn"
MIN_OPENING_PLIES = 6



# ------------------ Load ECO openings ------------------

eco_openings = load_eco_openings(ECO_PATH)


# ------------------ Helper functions ------------------

def material_count(board):
    values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9
    }

    score = 0
    for piece_type, value in values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    return score


def classify_move(
    move,
    best_move,
    score_before,
    score_after,
    cp_loss,
    material_before,
    material_after
):
    # 1) Missed Mate
    if score_before is not None and score_before.is_mate():
        if score_after is None or not score_after.is_mate():
            return "Missed Mate"

    # 2) Missed Win
    if score_before is not None and score_after is not None:
        if (
            score_before.score(mate_score=100000) > 500
            and score_after.score(mate_score=100000) < 200
        ):
            return "Missed Win"

    # 3) Brilliant
    if (
        best_move is not None
        and move == best_move
        and material_after < material_before
        and score_after is not None
        and score_before is not None
        and score_after.score(mate_score=100000)
            >= score_before.score(mate_score=100000)
        and score_after.score(mate_score=100000) > 200
    ):
        return "Brilliant"

    # 4) Great
    if (
        best_move is not None
        and move == best_move
        and score_before is not None
        and abs(score_before.score(mate_score=100000)) > 200
    ):
        return "Great"

    # 5) Best
    if best_move is not None and move == best_move and cp_loss <= 5:
        return "Best"

    # 6) Excellent
    if cp_loss <= 20:
        return "Excellent"

    # 7) Good
    if cp_loss <= 50:
        return "Good"

    # 8) Inaccuracy
    if cp_loss <= 100:
        return "Inaccuracy"

    # 9) Mistake
    if cp_loss <= 300:
        return "Mistake"

    # 10) Blunder
    return "Blunder"


# For calculating accuracy
def cp_loss_to_accuracy(cp_loss):
    cp_loss = min(cp_loss , 1000)
    accuracy = 100 - (cp_loss / 5)
    return max(0 , min(100 , accuracy))

def average(lst):
    return sum(lst) / len(lst) if lst else 100.0


# For calculating eval bar
def eval_to_bar(score):
    """
    Converts a python-chess score to a normalized eval bar value.
    Returns float in range [-1.0, +1.0]
    """
    if score is None:
        return 0.0
    
    # Mate handeling 
    if score.is_mate():
        return 1.0 if score.mate() > 0 else -1.0

    cp = score.score(mate_score=100000)

    # Clamp
    cp = max(-1000, min(1000, cp))

    return cp / 1000.0


# For drawing the graph of the game 
def plot_eval_graph(eval_graph):
    moves = list(range(1, len(eval_graph) + 1))

    plt.figure(figsize=(10, 4))
    plt.plot(moves, eval_graph, linewidth=2)

    # Zero line (equal position)
    plt.axhline(0, linestyle="--", linewidth=1)

    # Labels
    plt.xlabel("Move (ply)")
    plt.ylabel("Evaluation (White + / Black -)")
    plt.title("Game Evaluation Over Time")

    # Clamp view like chess.com
    plt.ylim(-1.05, 1.05)

    plt.tight_layout()
    plt.show()



# ------------------ Main logic ------------------

with open("backend/games/sample.pgn") as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()
engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

# Opening book
book = None
if os.path.exists(BOOK_PATH):
    book = chess.polyglot.open_reader(BOOK_PATH)
else:
    print("No opening book found at", BOOK_PATH)

print("Move | Side | Played | Best | CP Loss | Label")
print("-" * 72)

move_no = 1

# Opening detection state
played_moves_san = []
current_opening = None
opening_printed = False
ply_count = 0

# For tracking accuracy
white_accuracies = []
black_accuracies = []

# For tracking eval bar
eval_bar = 0.0
eval_graph = []


for move in game.mainline_moves():

    material_before = material_count(board)

    # -------- Determine SAN of played move --------
    san_played = board.san(move)

    # -------- Opening detection (ALL moves) --------
    played_moves_san.append(san_played)

    # Detect opening ONLY after enough plies
    if ply_count  >= MIN_OPENING_PLIES:
        eco, name = detect_opening(played_moves_san, eco_openings)
        if name:
            current_opening = f"{eco} — {name}"

            if not opening_printed:
                print(f"\nOpening detected: {current_opening}\n")
                opening_printed = True


    # -------- Book move check --------
    is_book_move = False
    book_moves = []

    if book is not None:
        try:
            entries = list(book.find_all(board))
            book_moves = [e.move for e in entries]
            if move in book_moves:
                is_book_move = True
        except Exception:
            is_book_move = False

    if is_book_move:
        # THEORY move
        label = "Theory"
        cp_loss = 0

        best_move = book_moves[0] if book_moves else None
        try:
            san_best = board.san(best_move) if best_move else "-"
        except Exception:
            san_best = "-"

        score_before = None
        score_after = None
        material_after = material_before

        board.push(move)

    else:
        # -------- Engine analysis --------
        info_before = engine.analyse(board, chess.engine.Limit(depth=14))
        score_before = info_before["score"].white()

        best_move = engine.play(board, chess.engine.Limit(depth=14)).move
        try:
            san_best = board.san(best_move)
        except Exception:
            san_best = "-"

        board.push(move)

        material_after = material_count(board)

        info_after = engine.analyse(board, chess.engine.Limit(depth=14))
        score_after = info_after["score"].white()

        # For eval bar
        eval_bar = eval_to_bar(score_after)
        eval_graph.append(eval_bar)


        cp_loss = (
            score_before.score(mate_score=100000)
            - score_after.score(mate_score=100000)
        )

        if board.turn == chess.BLACK:
            cp_loss = -cp_loss

        cp_loss = abs(cp_loss)

        label = classify_move(
            move,
            best_move,
            score_before,
            score_after,
            cp_loss,
            material_before,
            material_after
        )

        # For accuracy
        if label != "Theory":
            move_accuracy = cp_loss_to_accuracy(cp_loss)

            if side == 'W':
                white_accuracies.append(move_accuracy)
            else:
                 black_accuracies.append(move_accuracy)
    

    side = "W" if board.turn == chess.BLACK else "B"

    print(
    f"{move_no:>4} | {side} | {san_played:<6} | {san_best:<6} | "
    f"{cp_loss:>6} | {label:<10} | Eval: {eval_bar:+.2f}"
)


    if side == "B":
        move_no += 1
    
    ply_count += 1

white_accuracy = average(white_accuracies)
black_accuracy = average(black_accuracies)

print("\n=== Accuracy ===")
print(f"White accuracy: {white_accuracy:.1f}%")
print(f"Black accuracy: {black_accuracy:.1f}%")

# Drawing the graph of the game 
plot_eval_graph(eval_graph)


# Cleanup
if book is not None:
    book.close()
engine.quit()
