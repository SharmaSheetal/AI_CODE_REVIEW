"""
github_client.py — Fetches pull request metadata and file diffs from GitHub.

Uses the PyGitHub library (wraps GitHub REST API). Given a PR URL it returns:
  - repo name and PR number
  - list of changed files with their patch (the actual diff text)

The patch text is what we later feed into Tree-sitter and the LLM.
"""

from github import Github, GithubException
from backend.config import settings
from dataclasses import dataclass
from typing import List
import re


@dataclass
class ChangedFile:
    """Represents one file changed in the PR diff."""
    filename: str       # Relative path, e.g. "src/utils/helpers.py"
    patch: str          # Unified diff text (the +/- lines)
    raw_content: str    # Full file content (needed for Tree-sitter to build the AST)


@dataclass
class PRData:
    """All data we need from GitHub before parsing begins."""
    repo_name: str       # "owner/repo"
    pr_number: int
    title: str
    changed_files: List[ChangedFile]


def parse_pr_url(pr_url: str) -> tuple[str, int]:
    """
    Extracts owner/repo and PR number from a GitHub PR URL.
    Raises ValueError if the URL doesn't match the expected pattern.
    """
    pattern = r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)"
    match = re.match(pattern, pr_url)
    if not match:
        raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
    return match.group(1), int(match.group(2))


def fetch_pr_data(pr_url: str) -> PRData:
    """
    Main entry point. Takes a PR URL, returns a PRData object with all
    changed files and their diffs. Only fetches Python files for now
    (Tree-sitter grammar is loaded for Python in parser.py).
    """
    repo_name, pr_number = parse_pr_url(pr_url)

    client = Github(settings.github_token)

    try:
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
    except GithubException as e:
        raise ValueError(f"GitHub API error: {e.data.get('message', str(e))}")

    changed_files = []
    for file in pr.get_files():
        # Skip non-Python files for now; extend this list later for JS, TS, etc.
        if not file.filename.endswith(".py"):
            continue

        # patch is None for binary files or files too large for the API
        if file.patch is None:
            continue

        # Fetch the full file content so Tree-sitter can build a complete AST
        try:
            content_file = repo.get_contents(file.filename, ref=pr.head.sha)
            raw_content = content_file.decoded_content.decode("utf-8")
        except Exception:
            raw_content = ""  # Fall back to diff-only if full file is unavailable

        changed_files.append(ChangedFile(
            filename=file.filename,
            patch=file.patch,
            raw_content=raw_content,
        ))

    return PRData(
        repo_name=repo_name,
        pr_number=pr_number,
        title=pr.title,
        changed_files=changed_files,
    )
