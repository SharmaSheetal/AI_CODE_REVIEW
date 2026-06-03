"""
review.py — POST /review endpoint.

Receives a GitHub PR URL, runs the full review pipeline (fetch diff → parse
→ LLM → score), and returns structured suggestions. This file only handles
HTTP concerns; the actual logic lives in core/reviewer.py.
"""

from fastapi import APIRouter, HTTPException
from backend.models.schemas import ReviewRequest, ReviewResponse
from backend.core.reviewer import run_review
import time

router = APIRouter()


@router.post("/review", response_model=ReviewResponse)
async def review_pull_request(request: ReviewRequest):
    """
    Main endpoint. Accepts a PR URL and returns AI-generated suggestions.

    The async keyword lets FastAPI handle multiple requests concurrently
    while waiting on GitHub API or LLM responses.
    """
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
        # Catch-all for unexpected failures (LLM timeout, parse error, etc.)
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")

    result.processing_time_seconds = round(time.time() - start, 2)
    return result
