"""
scorer.py — Assigns a confidence score (0.0–1.0) to each LLM suggestion.

The LLM doesn't natively output confidence levels, so we infer them from
heuristics: how specific the line reference is, whether a fix is provided,
and whether the message length suggests a precise vs vague comment.

This is a key interview talking point: confidence scoring prevents the UI
from surfacing low-quality noise alongside high-signal findings.
"""

from backend.models.schemas import Suggestion, SuggestionType


# Base confidence by suggestion type.
# Test suggestions are high-confidence because missing tests are objectively detectable.
# Security issues are held to a slightly higher bar to reduce false-positive alarm.
BASE_CONFIDENCE = {
    SuggestionType.bug: 0.60,
    SuggestionType.security: 0.65,
    SuggestionType.review: 0.70,
    SuggestionType.test: 0.80,
}


def score_suggestion(suggestion: Suggestion) -> float:
    """
    Returns a confidence score for one suggestion.
    Starts from a type-based baseline and adjusts based on specificity signals.
    """
    score = BASE_CONFIDENCE.get(suggestion.suggestion_type, 0.60)

    # A code fix makes the finding concrete and actionable
    if suggestion.suggested_fix:
        score += 0.10

    # Single-line reference means the model was precise about the location
    if suggestion.line_start == suggestion.line_end:
        score += 0.05

    # Message length heuristic: too short = vague, too long = hallucination
    word_count = len(suggestion.message.split())
    if word_count < 10:
        score -= 0.05
    elif word_count > 80:
        score -= 0.10

    return round(min(max(score, 0.0), 1.0), 2)


def filter_by_confidence(
    suggestions: list[Suggestion], min_confidence: float
) -> list[Suggestion]:
    """Removes suggestions below the configured minimum confidence threshold."""
    return [s for s in suggestions if s.confidence >= min_confidence]
