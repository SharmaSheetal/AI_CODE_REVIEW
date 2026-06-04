/**
 * ReviewResults.jsx — Displays the full review response.
 *
 * Shows a summary bar (total count, processing time, PR info) then
 * renders a CommentCard for each suggestion. Filters by type so the
 * user can focus on bugs or security issues first.
 */

import { useState } from "react";
import CommentCard from "./CommentCard";

const FILTER_OPTIONS = ["all", "bug", "security", "test", "review"];

const TYPE_COUNTS_LABEL = {
  bug: "Bugs",
  security: "Security",
  test: "Tests",
  review: "Review",
};

export default function ReviewResults({ result }) {
  const [activeFilter, setActiveFilter] = useState("all");

  const filtered = activeFilter === "all"
    ? result.suggestions
    : result.suggestions.filter((s) => s.suggestion_type === activeFilter);

  // Count per type for the filter buttons
  const counts = result.suggestions.reduce((acc, s) => {
    acc[s.suggestion_type] = (acc[s.suggestion_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      {/* Summary bar */}
      <div style={styles.summary}>
        <div>
          <span style={styles.repoLabel}>{result.repo}</span>
          <span style={styles.prLabel}>PR #{result.pr_number}</span>
        </div>
        <div style={styles.meta}>
          <span>{result.total_suggestions} suggestions</span>
          <span style={styles.dot}>·</span>
          <span>{result.processing_time_seconds}s</span>
        </div>
      </div>

      {/* Filter tabs */}
      <div style={styles.filters}>
        {FILTER_OPTIONS.map((f) => {
          const count = f === "all" ? result.suggestions.length : (counts[f] || 0);
          const isActive = activeFilter === f;
          return (
            <button
              key={f}
              style={{
                ...styles.filterBtn,
                ...(isActive ? styles.filterBtnActive : {}),
              }}
              onClick={() => setActiveFilter(f)}
            >
              {f === "all" ? "All" : TYPE_COUNTS_LABEL[f]}
              {count > 0 && (
                <span style={styles.filterCount}>{count}</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Suggestion cards */}
      {filtered.length === 0 ? (
        <p style={styles.empty}>No {activeFilter} suggestions found.</p>
      ) : (
        filtered.map((suggestion, idx) => (
          <CommentCard key={idx} suggestion={suggestion} />
        ))
      )}
    </div>
  );
}

const styles = {
  summary: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    background: "#1e1e2e",
    borderRadius: "8px",
    padding: "16px 24px",
    marginBottom: "16px",
  },
  repoLabel: {
    color: "#cdd6f4",
    fontWeight: 600,
    marginRight: "12px",
    fontFamily: "monospace",
  },
  prLabel: {
    color: "#89b4fa",
    fontFamily: "monospace",
    fontSize: "14px",
  },
  meta: {
    color: "#6c7086",
    fontSize: "13px",
    display: "flex",
    gap: "8px",
  },
  dot: {
    color: "#313244",
  },
  filters: {
    display: "flex",
    gap: "8px",
    marginBottom: "20px",
    flexWrap: "wrap",
  },
  filterBtn: {
    padding: "6px 16px",
    borderRadius: "20px",
    border: "1px solid #313244",
    background: "#1e1e2e",
    color: "#a6adc8",
    fontSize: "13px",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  filterBtnActive: {
    background: "#89b4fa",
    color: "#1e1e2e",
    borderColor: "#89b4fa",
    fontWeight: 600,
  },
  filterCount: {
    background: "#313244",
    borderRadius: "10px",
    padding: "1px 7px",
    fontSize: "11px",
  },
  empty: {
    color: "#6c7086",
    textAlign: "center",
    padding: "40px",
  },
};
