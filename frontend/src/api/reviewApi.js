/**
 * reviewApi.js — All HTTP calls to the FastAPI backend live here.
 *
 * Keeping API logic in one file means if the backend URL ever changes,
 * there's exactly one place to update — not scattered across components.
 */

import axios from "axios";

const BASE_URL = "http://localhost:8000";

/**
 * Submits a PR URL to the backend and returns the full ReviewResponse.
 * @param {string} prUrl  - Full GitHub PR URL
 * @param {boolean} dryRun - If true, backend returns sample data (no API calls)
 * @param {boolean} includeTests - Whether to request test suggestions
 */
export async function reviewPullRequest(prUrl, dryRun = false, includeTests = true) {
  const response = await axios.post(`${BASE_URL}/api/v1/review`, {
    pr_url: prUrl,
    dry_run: dryRun,
    include_tests: includeTests,
    include_bug_detection: true,
  });
  return response.data;
}
