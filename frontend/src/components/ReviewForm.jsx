/**
 * ReviewForm.jsx — PR URL input form.
 *
 * Controlled component: the input value lives in React state, not the DOM.
 * When the user submits, it calls onSubmit(url, dryRun) — the parent (App)
 * owns the actual API call so this component stays pure UI.
 */

import { useState } from "react";

export default function ReviewForm({ onSubmit, loading }) {
  const [url, setUrl] = useState("");
  const [dryRun, setDryRun] = useState(false);
  const [includeTests, setIncludeTests] = useState(true);

  const DRY_RUN_PLACEHOLDER = "https://github.com/owner/repo/pull/1";

  // In dry run mode the backend ignores the URL — use a placeholder so the
  // user doesn't have to type anything real.
  const effectiveUrl = dryRun ? DRY_RUN_PLACEHOLDER : url;

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit(effectiveUrl, dryRun, includeTests);
  }

  function handleDryRunToggle(e) {
    setDryRun(e.target.checked);
    // Clear the real URL when switching to dry run so it doesn't linger
    if (e.target.checked) setUrl("");
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h1 style={styles.title}>AI Code Review Assistant</h1>
      <p style={styles.subtitle}>
        Paste a GitHub Pull Request URL to get AI-powered review comments,
        bug detection, and unit test suggestions.
      </p>

      <div style={styles.inputRow}>
        <input
          type="url"
          placeholder={dryRun ? DRY_RUN_PLACEHOLDER : "https://github.com/owner/repo/pull/42"}
          value={dryRun ? DRY_RUN_PLACEHOLDER : url}
          onChange={(e) => setUrl(e.target.value)}
          style={{
            ...styles.input,
            ...(dryRun ? styles.inputDisabled : {}),
          }}
          disabled={loading || dryRun}
          required={!dryRun}
        />
        <button type="submit" style={styles.button} disabled={loading}>
          {loading ? "Reviewing…" : "Review PR"}
        </button>
      </div>

      <div style={styles.options}>
        <label style={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={includeTests}
            onChange={(e) => setIncludeTests(e.target.checked)}
            disabled={loading}
          />
          &nbsp;Suggest missing tests
        </label>
        <label style={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={dryRun}
            onChange={handleDryRunToggle}
            disabled={loading}
          />
          &nbsp;Dry run <span style={styles.hint}>(no PR URL needed)</span>
        </label>
      </div>
    </form>
  );
}

const styles = {
  form: {
    background: "#1e1e2e",
    borderRadius: "12px",
    padding: "32px",
    marginBottom: "32px",
    boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
  },
  title: {
    margin: "0 0 8px",
    fontSize: "24px",
    color: "#cdd6f4",
    fontWeight: 700,
  },
  subtitle: {
    margin: "0 0 24px",
    color: "#a6adc8",
    fontSize: "14px",
    lineHeight: 1.6,
  },
  inputRow: {
    display: "flex",
    gap: "12px",
  },
  input: {
    flex: 1,
    padding: "12px 16px",
    borderRadius: "8px",
    border: "1px solid #313244",
    background: "#181825",
    color: "#cdd6f4",
    fontSize: "14px",
    outline: "none",
  },
  button: {
    padding: "12px 28px",
    borderRadius: "8px",
    border: "none",
    background: "#89b4fa",
    color: "#1e1e2e",
    fontWeight: 700,
    fontSize: "14px",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },
  options: {
    display: "flex",
    gap: "24px",
    marginTop: "16px",
  },
  checkboxLabel: {
    color: "#a6adc8",
    fontSize: "13px",
    display: "flex",
    alignItems: "center",
    cursor: "pointer",
  },
  inputDisabled: {
    opacity: 0.4,
    cursor: "not-allowed",
  },
  hint: {
    color: "#6c7086",
    fontSize: "12px",
    marginLeft: "4px",
  },
};
