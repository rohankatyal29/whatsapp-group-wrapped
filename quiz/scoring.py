"""Scoring logic for the quiz game."""

import math


def calculate_score(is_correct: bool, time_elapsed: float, time_constant: float = 15.0) -> int:
    """
    Calculate points for an answer.

    Args:
        is_correct: Whether the answer was correct
        time_elapsed: Seconds taken to answer
        time_constant: Decay rate for time bonus (lower = faster early drop)

    Returns:
        Points earned (0 if incorrect, 100-200 if correct based on speed)

    Scoring:
        - Incorrect answer: 0 points
        - Correct answer: base 100 points + time bonus (0-100)
        - Time bonus drops quickly early, then tapers off (exponential decay)
        - Formula: 100 + 100 * exp(-time_elapsed / time_constant)
    """
    if not is_correct:
        return 0

    base_points = 100

    # Fast early drop, then taper off.
    time_bonus = int(100 * math.exp(-max(time_elapsed, 0.0) / time_constant))

    return base_points + time_bonus
