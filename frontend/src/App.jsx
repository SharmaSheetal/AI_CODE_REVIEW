/**
 * App.jsx — Root component. Owns all shared state and orchestrates the flow:
 *   idle → loading → results (or error)
 *
 * State lives here (not in child components) because both ReviewForm and
 * ReviewResults need to know about the API response. This is called
 * "lifting state up" — a core React pattern.
 */

import { useState } from "react";
import ReviewForm from "./components/ReviewForm";
import ReviewResults from "./components/ReviewResults";
import { reviewPullRequest } from "./api/reviewApi";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(prUrl, dryRun, includeTests) {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await reviewPullRequest(prUrl, dryRun, includeTests);
      setResult(data);
    } catch (err) {
      // axios wraps HTTP errors; extract the backend's detail message if present
      const msg = err.response?.data?.detail || err.message || "Unknown error";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <ReviewForm onSubmit={handleSubmit} loading={loading} />

        {loading && (
          <div style={styles.status}>
            <div style={styles.spinner} />
            <span style={styles.statusText}>
              Fetching diff → parsing code → calling LLaMA-3…
            </span>
          </div>
        )}

        {error && (
          <div style={styles.errorBox}>
            <strong style={{ color: "#f38ba8" }}>Error: </strong>
            <span style={{ color: "#cdd6f4" }}>{error}</span>
          </div>
        )}

        {result && <ReviewResults result={result} />}
      </div>

      {/* Spinner keyframe — inline style blocks don't support @keyframes so we inject it */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        * { box-sizing: border-box; }
        body { margin: 0; }
        input:focus { outline: 2px solid #89b4fa; }
      `}</style>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#11111b",
    padding: "40px 16px",
    fontFamily: "'Inter', system-ui, sans-serif",
  },
  container: {
    maxWidth: "860px",
    margin: "0 auto",
  },
  status: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "20px 24px",
    background: "#1e1e2e",
    borderRadius: "8px",
    marginBottom: "16px",
  },
  spinner: {
    width: "20px",
    height: "20px",
    border: "3px solid #313244",
    borderTop: "3px solid #89b4fa",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    flexShrink: 0,
  },
  statusText: {
    color: "#a6adc8",
    fontSize: "14px",
  },
  errorBox: {
    background: "#3d1f2b",
    border: "1px solid #f38ba8",
    borderRadius: "8px",
    padding: "16px 20px",
    marginBottom: "16px",
    fontSize: "14px",
  },
};
