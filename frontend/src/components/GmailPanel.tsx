import { useState } from "react";
import { toast } from "sonner";
import { fetchGmailMessages, importFromGmail } from "../api";
import type { GmailMessage, ImportSummary } from "../types";

function formatDate(raw: string): string {
  if (!raw) return "";
  const d = new Date(raw);
  if (isNaN(d.getTime())) return raw;
  const now = new Date();
  const sameYear = d.getFullYear() === now.getFullYear();
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
    hour: "numeric",
    minute: "2-digit",
  });
}

export function GmailPanel({ onImported }: { onImported?: () => void }) {
  const [messages, setMessages] = useState<GmailMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [jobsOnly, setJobsOnly] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportSummary | null>(null);
  const [count, setCount] = useState(50);

  async function handleFetch() {
    setLoading(true);
    setError(null);
    try {
      setMessages(await fetchGmailMessages(count));
      setLoaded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch Gmail");
    } finally {
      setLoading(false);
    }
  }

  async function handleImport() {
    setImporting(true);
    setError(null);
    setImportResult(null);
    try {
      const result = await importFromGmail(count);
      setImportResult(result);
      onImported?.();
      toast.success(
        `Import complete · ${result.created} added, ${result.updated} updated`
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to import from Gmail");
      toast.error("Gmail import failed");
    } finally {
      setImporting(false);
    }
  }

  const jobCount = messages.filter((m) => m.classification.is_job_related).length;
  const visible = jobsOnly
    ? messages.filter((m) => m.classification.is_job_related)
    : messages;

  return (
    <section className="gmail-panel">
      <div className="gmail-header">
        <h2>Inbox preview</h2>
        <div className="gmail-controls">
          <label className="gmail-count-select">
            Show
            <select
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              disabled={loading || importing}
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <button onClick={handleFetch} disabled={loading}>
            {loading ? "Fetching…" : "Fetch recent emails"}
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {loaded && messages.length > 0 && (
        <div className="gmail-toolbar">
          <span className="gmail-count">
            {jobCount} of {messages.length} look job-related
          </span>
          <label className="gmail-filter">
            <input
              type="checkbox"
              checked={jobsOnly}
              onChange={(e) => setJobsOnly(e.target.checked)}
            />
            Job-related only
          </label>
        </div>
      )}

      {loaded && messages.length > 0 && (
        <div className="gmail-import">
          <button onClick={handleImport} disabled={importing}>
            {importing ? "Importing…" : "Import job emails into tracker"}
          </button>
          {importResult && (
            <span className="gmail-import-result">
              Added {importResult.created} · Updated {importResult.updated} ·
              Unchanged {importResult.unchanged}
            </span>
          )}
        </div>
      )}

      {loaded && messages.length === 0 && !error && (
        <p className="empty">No messages found.</p>
      )}

      {visible.length > 0 && (
        <ul className="gmail-list">
          {visible.map((m) => {
            const c = m.classification;
            return (
              <li
                key={m.id}
                className={`gmail-item${c.is_job_related ? " is-job" : ""}`}
              >
                <a
                  className="gmail-link"
                  href={`https://mail.google.com/mail/u/0/#all/${m.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Open in Gmail"
                >
                  <div className="gmail-subject">
                    {m.subject || "(no subject)"}
                    {c.is_job_related && (
                      <span className="badge badge-job">job</span>
                    )}
                    {c.detected_status && (
                      <span
                        className={`badge badge-status status-${c.detected_status}`}
                      >
                        {c.detected_status}
                      </span>
                    )}
                  </div>
                  <div className="gmail-meta">
                    {m.from}
                    {c.company_guess && (
                      <span className="gmail-company"> · {c.company_guess}</span>
                    )}
                    {m.date && (
                      <span className="gmail-date"> · {formatDate(m.date)}</span>
                    )}
                  </div>
                  <div className="gmail-snippet">{m.snippet}</div>
                </a>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
