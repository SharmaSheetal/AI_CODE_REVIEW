# AI Code Review and Debug Assistant

An end-to-end AI tool that automatically reviews GitHub Pull Requests using LLaMA-3, Tree-sitter code parsing, and FastAPI.

## What it does

- Fetches PR diffs from GitHub via the GitHub REST API
- Parses Python code with Tree-sitter to extract function-level context (not just raw text)
- Sends structured context to LLaMA-3 (via Groq cloud or local Ollama) for review
- Generates unit test suggestions for functions lacking coverage
- Detects bug patterns and explains fixes
- Returns results with **source attribution** (file + line) and **confidence scoring** per suggestion
- Displays results in a React dashboard
- Triggers automatically on new PRs via GitHub Actions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, Uvicorn |
| LLM | LLaMA-3 via Groq API or Ollama (local) |
| Code parsing | Tree-sitter (Python bindings) |
| GitHub integration | PyGitHub |
| Frontend | React + Vite |
| CI/CD | GitHub Actions |

## Project Structure

```
backend/
  config.py          — Environment settings
  main.py            — FastAPI app entry point
  api/routes/        — HTTP endpoints
  core/              — Business logic (GitHub, parser, LLM, scorer, orchestrator)
  models/schemas.py  — Pydantic request/response models
  tests/             — Unit tests

frontend/
  src/components/    — React UI components
  src/api/           — API client for backend calls

.github/workflows/   — GitHub Actions CI trigger
```

## Setup

```bash
# 1. Copy secrets template
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and GROQ_API_KEY

# 2. Install Python dependencies (using uv)
uv sync

# 3. Run the backend
uvicorn backend.main:app --reload

# 4. Run the frontend (in a separate terminal)
cd frontend && npm install && npm run dev
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| POST | `/api/v1/review` | Submit a PR URL for review |

Interactive docs: `http://localhost:8000/docs`
