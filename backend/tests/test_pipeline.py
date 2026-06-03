"""
test_pipeline.py — End-to-end pipeline test with all external calls mocked.

This test exercises the full path:
  GitHub API mock → parser (real) → LLM mock → scorer (real) → ReviewResponse

It proves the pieces fit together without needing a GitHub token or Groq key.
This is the test you'd run in CI on every pull request.
"""

import pytest
from unittest.mock import patch, MagicMock
from backend.core.reviewer import run_review


# Fake GitHub data that fetch_pr_data would normally return
FAKE_PR_DATA = MagicMock()
FAKE_PR_DATA.repo_name = "testowner/testrepo"
FAKE_PR_DATA.pr_number = 7
FAKE_PR_DATA.title = "Add discount calculation"
FAKE_PR_DATA.changed_files = [
    MagicMock(
        filename="src/pricing.py",
        patch="+ def calculate_discount(price, rate):\n+     return price * rate",
        raw_content="""
def calculate_discount(price, rate):
    return price * rate

def apply_tax(price, tax_rate):
    return price + (price * tax_rate)
""",
    )
]

# Fake LLM response: one bug suggestion
FAKE_LLM_REVIEW = '''{
  "issues": [
    {
      "type": "bug",
      "line": 2,
      "message": "No validation for negative price or rate values, which could return incorrect discounts.",
      "fix": "if price < 0 or rate < 0:\\n    raise ValueError('price and rate must be non-negative')"
    }
  ]
}'''

# Fake LLM test suggestion
FAKE_LLM_TEST = '''{
  "test_code": "def test_calculate_discount():\\n    assert calculate_discount(100, 0.1) == 10.0",
  "description": "Verifies discount is calculated as price multiplied by rate."
}'''


@pytest.mark.asyncio
async def test_full_pipeline_returns_review_response():
    with patch("backend.core.reviewer.fetch_pr_data", return_value=FAKE_PR_DATA), \
         patch("backend.core.reviewer.get_review_response", return_value=FAKE_LLM_REVIEW), \
         patch("backend.core.reviewer.get_test_response", return_value=FAKE_LLM_TEST):

        result = await run_review(
            pr_url="https://github.com/testowner/testrepo/pull/7",
            include_tests=True,
        )

    assert result.repo == "testowner/testrepo"
    assert result.pr_number == 7
    assert result.total_suggestions > 0


@pytest.mark.asyncio
async def test_pipeline_includes_bug_suggestion():
    with patch("backend.core.reviewer.fetch_pr_data", return_value=FAKE_PR_DATA), \
         patch("backend.core.reviewer.get_review_response", return_value=FAKE_LLM_REVIEW), \
         patch("backend.core.reviewer.get_test_response", return_value=FAKE_LLM_TEST):

        result = await run_review(
            pr_url="https://github.com/testowner/testrepo/pull/7",
        )

    bug_suggestions = [s for s in result.suggestions if s.suggestion_type == "bug"]
    assert len(bug_suggestions) >= 1
    assert "negative" in bug_suggestions[0].message.lower()


@pytest.mark.asyncio
async def test_pipeline_filters_by_confidence():
    """All returned suggestions must meet the minimum confidence threshold."""
    from backend.config import settings

    with patch("backend.core.reviewer.fetch_pr_data", return_value=FAKE_PR_DATA), \
         patch("backend.core.reviewer.get_review_response", return_value=FAKE_LLM_REVIEW), \
         patch("backend.core.reviewer.get_test_response", return_value=FAKE_LLM_TEST):

        result = await run_review(
            pr_url="https://github.com/testowner/testrepo/pull/7",
        )

    for s in result.suggestions:
        assert s.confidence >= settings.min_confidence


@pytest.mark.asyncio
async def test_pipeline_handles_bad_llm_response_gracefully():
    """If the LLM returns garbage JSON, the pipeline should return 0 suggestions, not crash."""
    with patch("backend.core.reviewer.fetch_pr_data", return_value=FAKE_PR_DATA), \
         patch("backend.core.reviewer.get_review_response", return_value="sorry, I cannot help"), \
         patch("backend.core.reviewer.get_test_response", return_value="also garbage"):

        result = await run_review(
            pr_url="https://github.com/testowner/testrepo/pull/7",
        )

    assert result.suggestions == []
    assert result.total_suggestions == 0
