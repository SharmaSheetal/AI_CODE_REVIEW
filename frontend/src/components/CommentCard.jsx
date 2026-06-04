/**
 * CommentCard.jsx — Renders a single AI suggestion.
 *
 * Shows: type badge (color-coded), file + line attribution, confidence bar,
 * the suggestion message, and an expandable code block for the suggested fix.
 */

import { useState } from "react";

// Color scheme per suggestion type — maps to our SuggestionType enum
const TYPE_CONFIG = {
  bug:      { color: "#f38ba8", bg: "#3d1f2b", label: "BUG" },
  security: { color: "#fab387", bg: "#3d2a1a", label: "SECURITY" },
  test:     { color: "#89b4fa", bg: "#1a2a3d", label: "TEST" },
  review:   { color: "#a6e3a1", bg: "#1a3d1f", label: "REVIEW" },
};

export default function CommentCard({ suggestion }) {
  const [fixOpen, setFixOpen] = useState(false);

  const config = TYPE_CONFIG[suggestion.suggestion_type] || TYPE_CONFIG.review;
  const confidencePct = Math.round(suggestion.confidence * 100);

  return (
    <div style={{ ...styles.card, borderLeft: `4px solid ${config.color}` }}>

      {/* Header row: badge + file:line + confidence */}
      <div style={styles.header}>
        <span style={{ ...styles.badge, color: config.color, background: config.bg }}>
          {config.label}
        </span>

        <span style={styles.location}>
          {suggestion.file_path}:{suggestion.line_start}
          {suggestion.line_end !== suggestion.line_start && `–${suggestion.line_end}`}
        </span>

        <div style={styles.confidenceWrapper}>
          <span style={styles.confidenceLabel}>
            Confidence {confidencePct}%
          </span>
          <div style={styles.confidenceTrack}>
            <div
              style={{
                ...styles.confidenceFill,
                width: `${confidencePct}%`,
                background: config.color,
              }}
            />
          </div>
        </div>
      </div>

      {/* Suggestion message */}
      <p style={styles.message}>{suggestion.message}</p>

      {/* Suggested fix — expandable code block */}
      {suggestion.suggested_fix && (
        <div>
          <button
            style={styles.fixToggle}
            onClick={() => setFixOpen((o) => !o)}
          >
            {fixOpen ? "▾ Hide fix" : "▸ Show suggested fix"}
          </button>
          {fixOpen && (
            <pre style={styles.fixCode}>{suggestion.suggested_fix}</pre>
          )}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    background: "#1e1e2e",
    borderRadius: "8px",
    padding: "20px 24px",
    marginBottom: "16px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginBottom: "12px",
    flexWrap: "wrap",
  },
  badge: {
    fontSize: "11px",
    fontWeight: 800,
    padding: "3px 10px",
    borderRadius: "4px",
    letterSpacing: "0.08em",
  },
  location: {
    fontFamily: "monospace",
    fontSize: "13px",
    color: "#a6adc8",
  },
  confidenceWrapper: {
    marginLeft: "auto",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    gap: "4px",
  },
  confidenceLabel: {
    fontSize: "11px",
    color: "#6c7086",
  },
  confidenceTrack: {
    width: "80px",
    height: "4px",
    background: "#313244",
    borderRadius: "2px",
    overflow: "hidden",
  },
  confidenceFill: {
    height: "100%",
    borderRadius: "2px",
    transition: "width 0.3s ease",
  },
  message: {
    margin: "0 0 12px",
    color: "#cdd6f4",
    fontSize: "14px",
    lineHeight: 1.6,
  },
  fixToggle: {
    background: "none",
    border: "none",
    color: "#89b4fa",
    fontSize: "13px",
    cursor: "pointer",
    padding: 0,
    marginBottom: "8px",
  },
  fixCode: {
    background: "#181825",
    border: "1px solid #313244",
    borderRadius: "6px",
    padding: "12px 16px",
    fontSize: "12px",
    color: "#a6e3a1",
    overflowX: "auto",
    margin: 0,
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
  },
};
