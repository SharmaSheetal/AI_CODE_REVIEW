"""
test_scorer.py — Tests for the confidence scoring heuristics.

Each test isolates one heuristic so the logic is easy to understand
and explain: "this test proves that a fix boosts confidence by 0.10."
"""

import pytest
from backend.core.scorer import score_suggestion, filter_by_confidence
from backend.models.schemas import Suggestion, SuggestionType


def make_suggestion(
    s_type=SuggestionType.review,
    message="This function lacks input validation for edge cases.",
    line_start=10,
    line_end=10,
    suggested_fix=None,
) -> Suggestion:
    """Helper that builds a Suggestion with sensible defaults."""
    return Suggestion(
        suggestion_type=s_type,
        file_path="src/utils.py",
        line_start=line_start,
        line_end=line_end,
        message=message,
        confidence=0.0,          # Will be set by score_suggestion
        suggested_fix=suggested_fix,
    )


# --- Base score by type ---

def test_test_suggestion_has_higher_base_than_bug():
    """Test suggestions start higher because missing tests are objectively verifiable."""
    test_score = score_suggestion(make_suggestion(s_type=SuggestionType.test))
    bug_score = score_suggestion(make_suggestion(s_type=SuggestionType.bug))
    assert test_score > bug_score


def test_security_suggestion_base_is_above_minimum():
    score = score_suggestion(make_suggestion(s_type=SuggestionType.security))
    assert score >= 0.5


# --- Fix bonus ---

def test_fix_increases_confidence():
    """A suggested_fix makes the finding actionable, boosting confidence by 0.10."""
    without_fix = score_suggestion(make_suggestion())
    with_fix = score_suggestion(make_suggestion(suggested_fix="x = max(0, x)"))
    assert with_fix == pytest.approx(without_fix + 0.10, abs=0.01)


# --- Single-line precision bonus ---

def test_single_line_increases_confidence():
    """Pointing to one exact line is more precise than a range."""
    single = score_suggestion(make_suggestion(line_start=5, line_end=5))
    multi = score_suggestion(make_suggestion(line_start=5, line_end=15))
    assert single > multi


# --- Message length penalties ---

def test_very_short_message_penalised():
    """Under 10 words is too vague to be actionable."""
    short = make_suggestion(message="Bad code here.")   # 3 words — penalised
    # 12 words — above threshold, no penalty
    normal = make_suggestion(message="This function lacks input validation and could return incorrect results for negative values.")
    assert score_suggestion(short) < score_suggestion(normal)


def test_very_long_message_penalised():
    """Over 80 words is likely hallucinated filler."""
    long_msg = " ".join(["word"] * 90)   # 90 words
    normal_msg = "This function lacks input validation for edge cases."
    assert score_suggestion(make_suggestion(message=long_msg)) < \
           score_suggestion(make_suggestion(message=normal_msg))


# --- Score clamping ---

def test_score_never_exceeds_one():
    """Even with all bonuses applied, score must be capped at 1.0."""
    s = make_suggestion(
        s_type=SuggestionType.test,
        suggested_fix="def test_foo(): pass",
        line_start=1,
        line_end=1,
    )
    assert score_suggestion(s) <= 1.0


def test_score_never_below_zero():
    """Even with all penalties, score must floor at 0.0."""
    s = make_suggestion(
        s_type=SuggestionType.bug,
        message="Bad.",              # Very short — penalty
        line_start=1,
        line_end=100,               # Wide range — no bonus
    )
    assert score_suggestion(s) >= 0.0


# --- Filtering ---

def test_filter_removes_low_confidence():
    suggestions = [
        make_suggestion(),   # score will be computed outside
    ]
    # Manually set confidence values
    suggestions[0].confidence = 0.3

    result = filter_by_confidence(suggestions, min_confidence=0.5)
    assert result == []


def test_filter_keeps_high_confidence():
    s = make_suggestion()
    s.confidence = 0.85
    result = filter_by_confidence([s], min_confidence=0.5)
    assert len(result) == 1


def test_filter_respects_exact_threshold():
    """A suggestion exactly at the threshold should be kept (>=, not >)."""
    s = make_suggestion()
    s.confidence = 0.5
    result = filter_by_confidence([s], min_confidence=0.5)
    assert len(result) == 1
