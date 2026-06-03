"""
health.py — GET /health endpoint.

A simple liveness check used by GitHub Actions and deployment tools to verify
the backend is running before sending a review request. Returns the LLM
provider in use so you can confirm the right config is loaded.
"""

from fastapi import APIRouter
from backend.config import settings

router = APIRouter()


@router.get("/health")
def health_check():
    """Returns 200 OK with basic service info. Used for uptime monitoring."""
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.groq_model if settings.llm_provider == "groq" else settings.ollama_model,
    }
