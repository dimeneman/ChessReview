#!/usr/bin/env python3
"""
CLI utility to replay a PGN game move-by-move in terminal.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sample_path = BACKEND_DIR / "games" / "sample.pgn"

try:
    import chess
    import chess.pgn
except ImportError:
    print("python-chess is required. Install via pip install chess")
    sys.exit(1)

if not sample_path.exists():
    print(f"Sample PGN not found at {sample_path}")
    sys.exit(1)

with open(sample_path) as pgn:
    game = chess.pgn.read_game(pgn)

board = game.board()
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

