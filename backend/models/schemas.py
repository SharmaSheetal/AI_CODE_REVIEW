"""
schemas.py — Pydantic models defining the request and response shapes for the API.

Pydantic validates incoming JSON automatically and serializes outgoing data.
These models are the contract between the frontend and backend — if either
side sends the wrong shape, it fails loudly with a clear error.
"""

from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from enum import Enum


class SuggestionType(str, Enum):
    """Category of AI suggestion — used to colour-code cards in the frontend."""
    review = "review"          # General code quality comment
    bug = "bug"                # Identified bug or error-prone pattern
    test = "test"              # Missing unit test suggestion
    security = "security"      # Potential security issue


class Suggestion(BaseModel):
    """A single AI-generated suggestion attached to a specific location in the diff."""
    suggestion_type: SuggestionType
    file_path: str             # e.g. "src/utils/helpers.py"
    line_start: int            # First line in the original file this applies to
    line_end: int              # Last line (same as line_start for single-line comments)
    message: str               # The human-readable AI suggestion
    confidence: float          # 0.0 – 1.0; how confident the model is
    suggested_fix: Optional[str] = None  # Optional code snippet showing the fix


class ReviewRequest(BaseModel):
    """Payload the frontend (or GitHub Actions) sends to POST /review."""
    pr_url: str                # Full GitHub PR URL, e.g. https://github.com/owner/repo/pull/42
    include_tests: bool = True           # Whether to generate missing test suggestions
    include_bug_detection: bool = True   # Whether to run bug pattern detection
    dry_run: bool = False                # If True, skip all API calls and return sample data


class ReviewResponse(BaseModel):
    """What the backend returns after processing a PR."""
    pr_url: str
    repo: str                  # e.g. "owner/repo"
    pr_number: int
    total_suggestions: int
    suggestions: List[Suggestion]
    processing_time_seconds: float
