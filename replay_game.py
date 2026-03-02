import chess.pgn 

# Load the PGN
with open("games/sample.pgn") as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board() # creating the board

print("=== Game Replay ===")

move_no = 1

for move in game.mainline_moves():
    san = board.san(move)
    board.push(move)

    if board.turn == chess.BLACK:
        print(f"{move_no}. White: {san}")
    else:
        print(f"{move_no}. Black: {san}")
        move_no += 1
