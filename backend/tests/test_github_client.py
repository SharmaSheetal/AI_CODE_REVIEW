"""
test_github_client.py — Unit tests for the GitHub URL parser.

We test parse_pr_url in isolation because it is pure logic (no API call needed).
The actual GitHub API call (fetch_pr_data) is covered by integration tests
run manually or in CI with secrets injected via GitHub Actions.
"""

import pytest
from backend.core.github_client import parse_pr_url


def test_parse_valid_pr_url():
    repo, number = parse_pr_url("https://github.com/owner/repo/pull/42")
    assert repo == "owner/repo"
    assert number == 42


def test_parse_pr_url_rejects_repo_url():
    with pytest.raises(ValueError, match="Invalid GitHub PR URL"):
        parse_pr_url("https://github.com/owner/repo")


def test_parse_pr_url_rejects_non_github_url():
    with pytest.raises(ValueError):
        parse_pr_url("https://gitlab.com/owner/repo/merge_requests/1")
