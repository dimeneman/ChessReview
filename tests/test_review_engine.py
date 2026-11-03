"""
Unit Tests for ChessReview Analytical Engine, Move Classification,
Centipawn Evaluation, and Coach Commentary.
"""

import chess
from review_engine import (
    average,
    classify_move,
    cp_loss_to_accuracy,
    eval_to_bar,
    get_coach_comment,
    material_count,
)


def test_material_count_initial_position():
    """Starting chess position must have an equal material count of 0."""
    board = chess.Board()
    assert material_count(board) == 0


def test_material_count_advantage():
    """Board where White captures Black's queen must reflect +9 material advantage."""
    board = chess.Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")  # Black queen removed
    assert material_count(board) == 9


def test_cp_loss_to_accuracy_mapping():
    """Verify conversion of centipawn loss into standard accuracy percentages."""
    # Zero loss = 100% precision
    assert cp_loss_to_accuracy(0) == 100.0

    # 100 cp loss = 100 - (100 / 5) = 80% accuracy
    assert cp_loss_to_accuracy(100) == 80.0

    # 500 cp loss = 100 - (500 / 5) = 0% accuracy
    assert cp_loss_to_accuracy(500) == 0.0

    # Massive blunders (>1000) are capped to 1000 cp loss and return 0.0
    assert cp_loss_to_accuracy(2500) == 0.0


def test_average_function():
    """Tests arithmetic mean calculation with fallback for empty lists."""
    assert average([100.0, 80.0, 60.0]) == 80.0
    assert average([]) == 100.0


def test_eval_to_bar_none():
    """None score must produce a neutral 0.0 evaluation bar."""
    assert eval_to_bar(None) == 0.0


def test_classify_move_thresholds():
    """Verify move taxonomy tiers based on centipawn loss and move choices."""
    dummy_move = chess.Move.from_uci("e2e4")
    best_move = chess.Move.from_uci("e2e4")
    suboptimal_move = chess.Move.from_uci("a2a3")

    # Played move matches engine's best choice
    assert classify_move(
        move=dummy_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=0,
        material_before=0,
        material_after=0,
    ) == "Best"

    # Played move deviates from best move: evaluate centipawn loss
    assert classify_move(
        move=suboptimal_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=15,
        material_before=0,
        material_after=0,
    ) == "Excellent"

    assert classify_move(
        move=suboptimal_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=45,
        material_before=0,
        material_after=0,
    ) == "Good"

    assert classify_move(
        move=suboptimal_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=90,
        material_before=0,
        material_after=0,
    ) == "Inaccuracy"

    assert classify_move(
        move=suboptimal_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=220,
        material_before=0,
        material_after=0,
    ) == "Mistake"

    assert classify_move(
        move=suboptimal_move,
        best_move=best_move,
        score_before=None,
        score_after=None,
        cp_loss=450,
        material_before=0,
        material_after=0,
    ) == "Blunder"


def test_coach_comments():
    """Verify coach feedback strings are non-empty and tailored to classification."""
    for label in ["Brilliant", "Great", "Best", "Excellent", "Good", "Inaccuracy", "Mistake", "Blunder", "Missed Win", "Missed Mate", "Theory"]:
        comment = get_coach_comment(label, "e4", "e4", 0, "W")
        assert isinstance(comment, str)
        assert len(comment) > 5

