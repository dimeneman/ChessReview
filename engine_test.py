import chess
import chess.pgn
import chess.engine

# Load PGN
with open("games/sample.pgn") as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()

# Play the first 6 piles (3 moves)
for i , move in enumerate(game.mainline_moves()):
    board.push(move)
    if i == 5:
        break


# Start stockfish 
engine = chess.engine.SimpleEngine.popen_uci("engine/stockfish")

# Analyze position 
info = engine.analyse(
    board, 
    chess.engine.Limit(depth=14)
)

score = info["score"].white()

print("Board position:")
print(board)
print("\nEvaluation:")


if score.is_mate():
    print("Mate in: " , score.mate())
else:
    print("Centipawn Score: " , score.score())

engine.quit()
