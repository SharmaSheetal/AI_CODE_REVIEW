"""
test_reviewer.py — Unit tests for the LLM response parsers in reviewer.py.

We test _parse_llm_review and _parse_llm_test with pre-canned JSON strings
so no LLM call is needed. This lets CI verify the parsing logic without secrets.
"""

from backend.core.reviewer import _parse_llm_review, _parse_llm_test
from backend.models.schemas import SuggestionType


VALID_REVIEW_JSON = '''
{
  "issues": [
    {
      "type": "bug",
      "line": 10,
      "message": "Division by zero is possible when denominator is 0.",
      "fix": "if denominator == 0: raise ValueError('denominator cannot be zero')"
    }
  ]
}
'''

VALID_TEST_JSON = '''
{
  "test_code": "def test_add():\\n    assert add(2, 3) == 5",
  "description": "Verifies that add returns the correct sum."
}
'''


def test_parse_review_extracts_suggestion():
    suggestions = _parse_llm_review(VALID_REVIEW_JSON, "math.py", "")
    assert len(suggestions) == 1
    assert suggestions[0].suggestion_type == SuggestionType.bug
    assert suggestions[0].line_start == 10


def test_parse_review_handles_malformed_json():
    # Must return empty list, not raise — keeps the pipeline alive on bad LLM output
    suggestions = _parse_llm_review("not json at all", "math.py", "")
    assert suggestions == []


def test_parse_test_extracts_suggestion():
    suggestions = _parse_llm_test(VALID_TEST_JSON, "math.py", 1, 5)
    assert len(suggestions) == 1
    assert suggestions[0].suggestion_type == SuggestionType.test
    assert "def test_add" in suggestions[0].suggested_fix


def test_parse_test_handles_empty_test_code():
    empty = '{"test_code": "", "description": "nothing"}'
    suggestions = _parse_llm_test(empty, "math.py", 1, 5)
    assert suggestions == []
