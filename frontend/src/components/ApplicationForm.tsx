import { useState } from "react";
import type { ApplicationCreate } from "../types";
import { STATUSES } from "../types";

interface Props {
  onCreate: (payload: ApplicationCreate) => Promise<void>;
}

export function ApplicationForm({ onCreate }: Props) {
  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [status, setStatus] = useState("applied");
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!company.trim() || !position.trim()) return;
    setSubmitting(true);
    try {
      await onCreate({
        company: company.trim(),
        position: position.trim(),
        status,
        url: url.trim() || null,
      });
      setCompany("");
      setPosition("");
      setStatus("applied");
      setUrl("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>Add application</h2>
      <div className="row">
        <input
          id="app-company-input"
          placeholder="Company"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          required
        />
        <input
          placeholder="Position"
          value={position}
          onChange={(e) => setPosition(e.target.value)}
          required
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <input
        placeholder="Job URL (optional)"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <button type="submit" disabled={submitting}>
        {submitting ? "Adding…" : "Add"}
      </button>
    </form>
  );
}
