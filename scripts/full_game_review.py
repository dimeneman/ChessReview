#!/usr/bin/env python3
"""
CLI utility to run a complete game review on sample.pgn and display evaluation metrics.
"""

import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from review_engine import review_game

sample_path = BACKEND_DIR / "games" / "sample.pgn"
if not sample_path.exists():
    print(f"Sample PGN not found at {sample_path}")
    sys.exit(1)

with open(sample_path) as f:
    pgn_text = f.read()

print("Running full game review on sample.pgn...")
results = review_game(pgn_text, depth=14)

if "error" in results:
    print(f"Error: {results['error']}")
    sys.exit(1)

print("\nMove | Side | Played | Best | CP Loss | Label | Evaluation")
print("-" * 72)
for m in results["moves"]:
    print(
        f"{m['move_no']:>4} | {m['side']} | {m['played_san']:<6} | {m['best_san']:<6} | "
        f"{m['cp_loss']:>7} | {m['label']:<10} | {m['eval']:+.2f}"
    )

print("\n=== Summary ===")
print(f"Opening:        {results.get('opening', 'Unknown')}")
print(f"White Accuracy: {results.get('white_accuracy')} %")
print(f"Black Accuracy: {results.get('black_accuracy')} %")

