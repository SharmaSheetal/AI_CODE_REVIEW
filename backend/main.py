"""
main.py — FastAPI application entry point.

Creates the app instance, registers route groups (routers), and configures
CORS so the React frontend (running on a different port) can call the API.

Run with:  uvicorn backend.main:app --reload
Docs at:   http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import review, health
from backend.config import settings

app = FastAPI(
    title="AI Code Review Assistant",
    description=(
        "Fetches GitHub PR diffs, parses code with Tree-sitter, "
        "and generates LLaMA-3 review comments with confidence scoring."
    ),
    version="1.0.0",
)

# CORS — allows the React dev server (localhost:5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route groups
app.include_router(health.router, tags=["Health"])
app.include_router(review.router, prefix="/api/v1", tags=["Review"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
