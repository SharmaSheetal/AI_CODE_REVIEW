"""
test_llm_client.py — Tests for prompt construction and LLM routing in llm_client.py.

We never call the real Groq/Ollama API in unit tests — that would require secrets
and make tests slow and flaky. Instead we use unittest.mock to patch the API call
and verify that:
  1. The correct prompt is built from a FunctionContext
  2. The right provider is called based on settings
  3. The response is passed through unchanged
"""

from unittest.mock import patch, MagicMock
from backend.core.llm_client import get_review_response, get_test_response, call_llm
from backend.core.parser import FunctionContext


# A sample function context mimicking what the parser would produce
SAMPLE_FUNC = FunctionContext(
    name="calculate_discount",
    start_line=10,
    end_line=20,
    source="def calculate_discount(price, rate):\n    return price * rate",
    has_docstring=False,
    has_return=True,
    parameter_names=["price", "rate"],
)


def test_review_prompt_contains_function_name():
    """The prompt sent to the LLM must include the function name for attribution."""
    with patch("backend.core.llm_client._call_groq", return_value='{"issues":[]}') as mock:
        get_review_response("utils.py", SAMPLE_FUNC, "+ return price * rate")
        prompt = mock.call_args[0][0]
        assert "calculate_discount" in prompt


def test_review_prompt_contains_line_numbers():
    """Line numbers in the prompt allow the LLM to cite exact locations."""
    with patch("backend.core.llm_client._call_groq", return_value='{"issues":[]}') as mock:
        get_review_response("utils.py", SAMPLE_FUNC, "")
        prompt = mock.call_args[0][0]
        assert "10" in prompt
        assert "20" in prompt


def test_review_prompt_contains_parameter_names():
    """Parameter names give the LLM context about what the function expects."""
    with patch("backend.core.llm_client._call_groq", return_value='{"issues":[]}') as mock:
        get_review_response("utils.py", SAMPLE_FUNC, "")
        prompt = mock.call_args[0][0]
        assert "price" in prompt
        assert "rate" in prompt


def test_test_prompt_contains_function_source():
    """The test-generation prompt must include the actual function code."""
    with patch("backend.core.llm_client._call_groq", return_value='{"test_code":"","description":""}') as mock:
        get_test_response("utils.py", SAMPLE_FUNC)
        prompt = mock.call_args[0][0]
        assert "def calculate_discount" in prompt


def test_call_llm_routes_to_groq(monkeypatch):
    """When LLM_PROVIDER=groq, call_llm should call _call_groq."""
    monkeypatch.setattr("backend.core.llm_client.settings.llm_provider", "groq")
    with patch("backend.core.llm_client._call_groq", return_value="ok") as mock_groq:
        result = call_llm("test prompt")
        mock_groq.assert_called_once_with("test prompt")
        assert result == "ok"


def test_call_llm_routes_to_ollama(monkeypatch):
    """When LLM_PROVIDER=ollama, call_llm should call _call_ollama."""
    monkeypatch.setattr("backend.core.llm_client.settings.llm_provider", "ollama")
    with patch("backend.core.llm_client._call_ollama", return_value="ok") as mock_ollama:
        result = call_llm("test prompt")
        mock_ollama.assert_called_once_with("test prompt")
        assert result == "ok"
