"""
llm_client.py — Sends structured prompts to LLaMA-3 and returns raw text responses.

Supports two providers:
  - Groq: cloud API, fast inference, requires GROQ_API_KEY
  - Ollama: local inference, free, requires Ollama running on localhost

The prompt engineering here is key: we give the model structured context
(file, function name, line numbers) so its output can be attributed back
to exact locations in the diff.
"""

import time
import httpx
from groq import Groq, RateLimitError
from backend.config import settings

# Retry config for Groq rate limit errors (429)
_MAX_RETRIES = 4
_BASE_BACKOFF = 2  # seconds — doubles each retry: 2, 4, 8, 16
from backend.core.parser import FunctionContext


def _build_review_prompt(filename: str, func: FunctionContext, patch: str) -> str:
    """
    Builds the prompt for a general code review of one function.
    Enforcing JSON output format makes the response reliably parseable.
    """
    return f"""You are an expert code reviewer. Analyze the following Python function and provide feedback.

File: {filename}
Function: {func.name} (lines {func.start_line}–{func.end_line})
Has docstring: {func.has_docstring}
Parameters: {', '.join(func.parameter_names) or 'none'}

Diff context:
{patch}

Function source:
{func.source}

Respond with a JSON object in exactly this format:
{{
  "issues": [
    {{
      "type": "review" | "bug" | "security",
      "line": <line number within the file>,
      "message": "<concise description of the issue>",
      "fix": "<optional code snippet showing the fix, or null>"
    }}
  ]
}}
Only include real issues. Do not invent problems that do not exist."""


def _build_test_prompt(filename: str, func: FunctionContext) -> str:
    """Builds a prompt asking the LLM to generate pytest unit tests for a function."""
    return f"""You are a senior Python developer. Write pytest unit tests for the following function.

File: {filename}
Function: {func.name} (lines {func.start_line}–{func.end_line})
Parameters: {', '.join(func.parameter_names) or 'none'}

Function source:
{func.source}

Respond with a JSON object in exactly this format:
{{
  "test_code": "<complete pytest test function(s) as a string>",
  "description": "<one sentence explaining what the tests verify>"
}}"""


def _call_groq(prompt: str) -> str:
    """Calls LLaMA-3 via the Groq cloud API with exponential backoff on rate limits."""
    client = Groq(api_key=settings.groq_api_key)

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1024,
            )
            return response.choices[0].message.content

        except RateLimitError:
            if attempt == _MAX_RETRIES - 1:
                raise   # Exhausted all retries — let the error propagate
            wait = _BASE_BACKOFF ** attempt  # 1s, 2s, 4s, 8s
            print(f"Groq rate limit hit — retrying in {wait}s (attempt {attempt + 1}/{_MAX_RETRIES})")
            time.sleep(wait)


def _call_ollama(prompt: str) -> str:
    """Calls LLaMA-3 via local Ollama."""
    response = httpx.post(
        f"{settings.ollama_base_url}/api/generate",
        json={
            "model": settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=120.0,   # Local inference can be slow without a GPU
    )
    response.raise_for_status()
    return response.json()["response"]


def call_llm(prompt: str) -> str:
    """Routes the prompt to the configured LLM provider."""
    if settings.llm_provider == "groq":
        return _call_groq(prompt)
    elif settings.llm_provider == "ollama":
        return _call_ollama(prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


def get_review_response(filename: str, func: FunctionContext, patch: str) -> str:
    """Returns raw LLM JSON string for a code review of one function."""
    return call_llm(_build_review_prompt(filename, func, patch))


def get_test_response(filename: str, func: FunctionContext) -> str:
    """Returns raw LLM JSON string for test suggestions for one function."""
    return call_llm(_build_test_prompt(filename, func))
