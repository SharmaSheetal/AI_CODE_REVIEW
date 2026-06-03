"""
reviewer.py — Orchestrates the full review pipeline.

This is the only module that imports from all the others. Its job is to:
  1. Fetch the PR diff from GitHub
  2. Parse each changed Python file with Tree-sitter
  3. Call the LLM for each function (review + optionally tests)
  4. Parse and score each LLM suggestion
  5. Return a ReviewResponse ready for the API to return

Think of this as the controller in an MVC pattern — it coordinates, not implements.
"""

import json
from backend.core.github_client import fetch_pr_data
from backend.core.parser import parse_python_file
from backend.core.llm_client import get_review_response, get_test_response
from backend.core.scorer import score_suggestion, filter_by_confidence
from backend.models.schemas import Suggestion, SuggestionType, ReviewResponse
from backend.config import settings


def _parse_llm_review(raw: str, filename: str, patch: str) -> list[Suggestion]:
    """
    Parses the raw JSON string from the LLM into Suggestion objects.
    Handles malformed JSON gracefully — the LLM sometimes returns extra prose.
    """
    suggestions = []
    try:
        # Strip any prose the model added before/after the JSON block
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])

        for issue in data.get("issues", []):
            s_type = SuggestionType(issue.get("type", "review"))
            suggestions.append(Suggestion(
                suggestion_type=s_type,
                file_path=filename,
                line_start=int(issue.get("line", 1)),
                line_end=int(issue.get("line", 1)),
                message=issue.get("message", ""),
                confidence=0.0,   # Set by scorer after this
                suggested_fix=issue.get("fix"),
            ))
    except (json.JSONDecodeError, KeyError, ValueError):
        # If the LLM returned garbage, skip silently — don't crash the whole review
        pass
    return suggestions


def _parse_llm_test(
    raw: str, filename: str, func_start: int, func_end: int
) -> list[Suggestion]:
    """Parses the LLM's test suggestion response into a Suggestion object."""
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])

        test_code = data.get("test_code", "")
        description = data.get("description", "Missing unit tests detected")

        if not test_code:
            return []

        return [Suggestion(
            suggestion_type=SuggestionType.test,
            file_path=filename,
            line_start=func_start,
            line_end=func_end,
            message=description,
            confidence=0.0,
            suggested_fix=test_code,
        )]
    except (json.JSONDecodeError, KeyError):
        return []


async def run_review(
    pr_url: str,
    include_tests: bool = True,
    include_bug_detection: bool = True,
) -> ReviewResponse:
    """
    Full pipeline entry point. Called by the /review route handler.
    Returns a ReviewResponse with all scored and filtered suggestions.
    """
    # Step 1: Fetch diff from GitHub
    pr_data = fetch_pr_data(pr_url)

    all_suggestions: list[Suggestion] = []

    for changed_file in pr_data.changed_files:
        if not changed_file.raw_content:
            continue

        # Step 2: Parse with Tree-sitter
        parsed = parse_python_file(changed_file.filename, changed_file.raw_content)
        if parsed.parse_error or not parsed.functions:
            continue

        for func in parsed.functions:
            # Step 3a: Code review for every function in the diff
            raw_review = get_review_response(
                filename=changed_file.filename,
                func=func,
                patch=changed_file.patch,
            )
            review_suggestions = _parse_llm_review(
                raw=raw_review,
                filename=changed_file.filename,
                patch=changed_file.patch,
            )
            all_suggestions.extend(review_suggestions)

            # Step 3b: Test suggestions for functions without a docstring
            # (missing docstring is a proxy for potentially missing test coverage)
            if include_tests and not func.has_docstring:
                raw_test = get_test_response(
                    filename=changed_file.filename,
                    func=func,
                )
                test_suggestions = _parse_llm_test(
                    raw=raw_test,
                    filename=changed_file.filename,
                    func_start=func.start_line,
                    func_end=func.end_line,
                )
                all_suggestions.extend(test_suggestions)

    # Step 4: Score every suggestion
    for s in all_suggestions:
        s.confidence = score_suggestion(s)

    # Step 5: Filter out low-confidence noise
    filtered = filter_by_confidence(all_suggestions, settings.min_confidence)

    return ReviewResponse(
        pr_url=pr_url,
        repo=pr_data.repo_name,
        pr_number=pr_data.pr_number,
        total_suggestions=len(filtered),
        suggestions=filtered,
        processing_time_seconds=0.0,   # Filled in by the route handler
    )
