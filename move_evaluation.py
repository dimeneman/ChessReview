import chess
import chess.pgn
import chess.engine

ENGINE_PATH = "backend/engine/stockfish"

# Load game
with open("backend/games/sample.pgn") as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

print("Move | Played | Best | CP Loss")

print("-" * 40)

move_no = 1

for move in game.mainline_moves():

    # Evaluate Before move
    info_before = engine.analyse(
        board, 
        chess.engine.Limit(depth=14)
    )

    score_before = info_before["score"].white().score(mate_score= 100000)

    best_move = engine.play(
        board,
        chess.engine.Limit(depth=14)
    ).move

    san_played = board.san(move)
    san_best = board.san(best_move)


    # Play the actual move 
    board.push(move)

    # Evaluate After move
    info_after = engine.analyse(
        board,
        chess.engine.Limit(depth= 14)
    )

    score_after = info_after["score"].white().score(mate_score=100000)

    # Adjust for side to move
    cp_loss = score_before - score_after
    if board.turn == chess.BLACK:
        cp_loss = - cp_loss
    
    side = 'W' if board.turn == chess.BLACK else "B"

    print(f"{move_no:>4} | {side} {san_played:<5} | {san_best:<5} | {cp_loss}")

    if side == "B":
        move_no += 1
    

engine.quit()

