import { useState } from "react";
import { fetchGmailMessages } from "../api";
import type { GmailMessage } from "../types";

export function GmailPanel() {
  const [messages, setMessages] = useState<GmailMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  async function handleFetch() {
    setLoading(true);
    setError(null);
    try {
      setMessages(await fetchGmailMessages(20));
      setLoaded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch Gmail");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="gmail-panel">
      <div className="gmail-header">
        <h2>Inbox preview</h2>
        <button onClick={handleFetch} disabled={loading}>
          {loading ? "Fetching…" : "Fetch recent emails"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {loaded && messages.length === 0 && !error && (
        <p className="empty">No messages found.</p>
      )}

      {messages.length > 0 && (
        <ul className="gmail-list">
          {messages.map((m) => (
            <li key={m.id} className="gmail-item">
              <div className="gmail-subject">{m.subject || "(no subject)"}</div>
              <div className="gmail-meta">{m.from}</div>
              <div className="gmail-snippet">{m.snippet}</div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
