#!/usr/bin/env python3
"""
CLI utility to test Stockfish engine initialization and board evaluation.
"""

import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import chess
import chess.engine
import chess.pgn
from config import settings

sample_path = BACKEND_DIR / "games" / "sample.pgn"
if not sample_path.exists():
    print(f"Sample PGN not found at {sample_path}")
    sys.exit(1)

with open(sample_path) as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()

# Play first 6 plies (3 moves)
for i, move in enumerate(game.mainline_moves()):
    board.push(move)
    if i == 5:
        break

engine_path = settings.STOCKFISH_PATH
print(f"Starting Stockfish engine from: {engine_path}")
engine = chess.engine.SimpleEngine.popen_uci(engine_path)

info = engine.analyse(board, chess.engine.Limit(depth=14))
score = info["score"].white()

print("\nBoard position after 3 moves:")
print(board)
print("\nEvaluation:")
if score.is_mate():
    print(f"Mate in: {score.mate()}")
else:
    print(f"Centipawn Score: {score.score()}")

engine.quit()
print("Engine test completed successfully.")

