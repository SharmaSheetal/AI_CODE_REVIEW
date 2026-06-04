# AI Code Review and Debug Assistant

An end-to-end AI tool that automatically reviews GitHub Pull Requests using LLaMA-3, Tree-sitter AST parsing, and FastAPI. It detects bugs, security vulnerabilities, and missing tests — then posts results as PR comments via GitHub Actions.

## What it does

- Fetches PR diffs from GitHub via the REST API
- Parses Python code with Tree-sitter to extract function-level structure (not raw text)
- Sends structured context to LLaMA-3 (via Groq cloud or local Ollama) per function
- Detects bugs, security issues, and code quality problems with suggested fixes
- Suggests unit tests for functions that lack them
- Scores each suggestion with a confidence level (0.0 – 1.0) and filters out noise
- Attributes every finding to a specific file and line number
- Displays results in a React dashboard
- Posts results as PR comments automatically via GitHub Actions

## Architecture

```
Pull Request opened on GitHub
         |
         v
GitHub Actions workflow fires
         |
         v
post_review.py (standalone pipeline script)
         |
         |-- github_client.py  -->  Fetch PR diff + file contents
         |-- parser.py         -->  Tree-sitter AST: extract functions, params, docstrings
         |-- llm_client.py     -->  Build prompt per function, call LLaMA-3 via Groq
         |-- scorer.py         -->  Assign confidence score to each suggestion
         |-- reviewer.py       -->  Orchestrate all of the above
         |
         v
Post comment on GitHub PR  (or display in React dashboard)
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python 3.13, FastAPI | Async API, auto-generated docs, typed schemas |
| LLM | LLaMA-3 via Groq API | Fast cloud inference; swap to Ollama for local |
| Code parsing | Tree-sitter | AST-level understanding vs raw text search |
| GitHub integration | PyGitHub | Typed wrapper around GitHub REST API |
| Frontend | React + Vite | Fast dev server, component-based UI |
| CI/CD | GitHub Actions | Triggers on PR events, no server needed |
| Dependency management | uv | Fast Python package manager |

## Project Structure

```
AI_Code_Review/
├── .github/workflows/
│   └── code_review.yml        # GitHub Actions trigger
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # All env vars in one place
│   ├── api/routes/
│   │   ├── review.py          # POST /api/v1/review
│   │   └── health.py          # GET /health
│   ├── core/
│   │   ├── github_client.py   # Fetch PR diffs from GitHub
│   │   ├── parser.py          # Tree-sitter AST parsing
│   │   ├── llm_client.py      # LLaMA-3 via Groq or Ollama
│   │   ├── reviewer.py        # Orchestrates the full pipeline
│   │   └── scorer.py          # Confidence scoring per suggestion
│   ├── models/schemas.py      # Pydantic request/response models
│   ├── scripts/
│   │   └── post_review.py     # Standalone script used by GitHub Actions
│   └── tests/                 # 35 unit tests (all offline, no API keys needed)
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── ReviewForm.jsx
│       │   ├── ReviewResults.jsx
│       │   └── CommentCard.jsx
│       └── api/reviewApi.js
├── .env.example               # Secret template — copy to .env
└── pyproject.toml             # Python dependencies
```

## Local Setup

### Prerequisites
- Python 3.13
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) — `pip install uv`
- Groq API key (free at [console.groq.com](https://console.groq.com)) OR Ollama running locally

### 1. Clone and configure

```bash
git clone https://github.com/SharmaSheetal/AI_CODE_REVIEW.git
cd AI_CODE_REVIEW

cp .env.example .env
# Edit .env and fill in:
#   GITHUB_TOKEN   — GitHub PAT (no scopes needed for public repos)
#   GROQ_API_KEY   — from console.groq.com
```

### 2. Start the backend

```bash
uv sync
uv run uvicorn backend.main:app --reload
# API running at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:5173
```

### 4. Run tests

```bash
uv run pytest backend/tests/ -v
# 35 tests — all run offline, no API keys required
```

## API Reference

### `GET /health`
Returns service status and active LLM model.

```json
{ "status": "ok", "llm_provider": "groq", "model": "llama-3.1-8b-instant" }
```

### `POST /api/v1/review`

**Request:**
```json
{
  "pr_url": "https://github.com/owner/repo/pull/42",
  "include_tests": true,
  "include_bug_detection": true,
  "dry_run": false
}
```

Set `dry_run: true` to get sample data without any API calls — useful for demos.

**Response:**
```json
{
  "repo": "owner/repo",
  "pr_number": 42,
  "total_suggestions": 5,
  "processing_time_seconds": 9.2,
  "suggestions": [
    {
      "suggestion_type": "security",
      "file_path": "src/auth.py",
      "line_start": 12,
      "line_end": 12,
      "message": "SQL injection risk — user input passed directly into query string.",
      "confidence": 0.80,
      "suggested_fix": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
    }
  ]
}
```

## Integrating with Another Repository

### Option A — Copy the workflow (recommended)

1. Copy `.github/workflows/code_review.yml` into the target repo
2. Add `GROQ_API_KEY` as a repository secret (Settings → Secrets → Actions)
3. Push — the workflow will run on every new PR automatically

The `GITHUB_TOKEN` is provided automatically by GitHub. No extra setup needed.

### Option B — Run manually via API

Point the React dashboard or a direct `curl` call at any public PR:

```bash
curl -X POST http://localhost:8000/api/v1/review \
  -H "Content-Type: application/json" \
  -d '{"pr_url": "https://github.com/any-owner/any-repo/pull/123"}'
```

### Option C — Run the script directly

```bash
PR_URL=https://github.com/owner/repo/pull/42 \
  uv run python backend/scripts/post_review.py
```

Prints the review as Markdown to stdout (no GitHub token needed in this mode).

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub PAT — no scopes for public repos |
| `GROQ_API_KEY` | Yes (if using Groq) | From console.groq.com |
| `LLM_PROVIDER` | No | `groq` (default) or `ollama` |
| `GROQ_MODEL` | No | Default: `llama-3.1-8b-instant` |
| `OLLAMA_BASE_URL` | No | Default: `http://localhost:11434` |
| `MIN_CONFIDENCE` | No | Filter threshold, default `0.5` |
| `API_PORT` | No | Default: `8000` |
