"""
review.py — POST /review endpoint.

Receives a GitHub PR URL, runs the full review pipeline (fetch diff → parse
→ LLM → score), and returns structured suggestions. This file only handles
HTTP concerns; the actual logic lives in core/reviewer.py.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import ReviewRequest, ReviewResponse, Suggestion, SuggestionType
from backend.core.reviewer import run_review
import time
import traceback

router = APIRouter()


def _dry_run_response(pr_url: str) -> ReviewResponse:
    """
    Returns hard-coded sample data so the full API shape can be tested
    without a GitHub token or Groq key. Used for local demos and CI checks.
    """
    return ReviewResponse(
        pr_url=pr_url,
        repo="owner/sample-repo",
        pr_number=42,
        total_suggestions=2,
        suggestions=[
            Suggestion(
                suggestion_type=SuggestionType.bug,
                file_path="src/utils/math.py",
                line_start=14,
                line_end=14,
                message="Division by zero is possible when `denominator` is 0. Add a guard before dividing.",
                confidence=0.85,
                suggested_fix="if denominator == 0:\n    raise ValueError('denominator cannot be zero')",
            ),
            Suggestion(
                suggestion_type=SuggestionType.test,
                file_path="src/utils/math.py",
                line_start=10,
                line_end=18,
                message="Function `divide` has no unit tests. Suggested pytest cases below.",
                confidence=0.80,
                suggested_fix="def test_divide_normal():\n    assert divide(10, 2) == 5\n\ndef test_divide_by_zero():\n    with pytest.raises(ValueError):\n        divide(10, 0)",
            ),
        ],
        processing_time_seconds=0.01,
    )


@router.post("/review", response_model=ReviewResponse)
async def review_pull_request(request: ReviewRequest):
    """
    Main endpoint. Accepts a PR URL and returns AI-generated suggestions.

    Pass dry_run=true to get sample data without any API calls — useful for
    testing the frontend or demoing the project without credentials.
    """
    if request.dry_run:
        return _dry_run_response(request.pr_url)

    start = time.time()

    try:
        result = await run_review(
            pr_url=request.pr_url,
            include_tests=request.include_tests,
            include_bug_detection=request.include_bug_detection,
        )
    except ValueError as e:
        # Raised by github_client when the URL is invalid or PR not found
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()   # Print full stack trace to server logs
        raise HTTPException(status_code=500, detail=f"Review failed: {repr(e)}")

    result.processing_time_seconds = round(time.time() - start, 2)
    return result
