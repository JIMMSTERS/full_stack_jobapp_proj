import { useState } from "react";
import type { Application, ApplicationCreate } from "../types";
import { STATUSES } from "../types";

interface Props {
  applications: Application[];
  highlightId?: number | null;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
  onUpdate: (id: number, changes: Partial<ApplicationCreate>) => Promise<void>;
}

export function ApplicationTable({
  applications,
  highlightId,
  onDelete,
  onStatusChange,
  onUpdate,
}: Props) {
  if (applications.length === 0) {
    return <p className="empty">No applications yet. Add your first one above.</p>;
  }

  return (
    <table className="card table">
      <thead>
        <tr>
          <th>Company</th>
          <th>Position</th>
          <th>Status</th>
          <th>Link</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {applications.map((a) => (
          <Row
            key={a.id}
            application={a}
            highlighted={a.id === highlightId}
            onDelete={onDelete}
            onStatusChange={onStatusChange}
            onUpdate={onUpdate}
          />
        ))}
      </tbody>
    </table>
  );
}

interface RowProps {
  application: Application;
  highlighted: boolean;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
  onUpdate: (id: number, changes: Partial<ApplicationCreate>) => Promise<void>;
}

function Row({ application: a, highlighted, onDelete, onStatusChange, onUpdate }: RowProps) {
  const [editing, setEditing] = useState(false);
  const [company, setCompany] = useState(a.company);
  const [position, setPosition] = useState(a.position);
  const [url, setUrl] = useState(a.url ?? "");
  const [saving, setSaving] = useState(false);

  function startEdit() {
    setCompany(a.company);
    setPosition(a.position);
    setUrl(a.url ?? "");
    setEditing(true);
  }

  async function save() {
    setSaving(true);
    try {
      await onUpdate(a.id, {
        company: company.trim(),
        position: position.trim(),
        url: url.trim() || null,
      });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (editing) {
    return (
      <tr id={`app-row-${a.id}`} className={highlighted ? "row-highlight" : undefined}>
        <td>
          <input value={company} onChange={(e) => setCompany(e.target.value)} />
        </td>
        <td>
          <input value={position} onChange={(e) => setPosition(e.target.value)} />
        </td>
        <td>
          <span className={`badge badge-${a.status}`}>{a.status}</span>
        </td>
        <td>
          <input
            placeholder="Job URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </td>
        <td>
          <div className="actions">
            <button onClick={save} disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </button>
            <button className="link" onClick={() => setEditing(false)}>
              cancel
            </button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr id={`app-row-${a.id}`} className={highlighted ? "row-highlight" : undefined}>
      <td>
        {a.company}
        {a.source === "gmail" && (
          <span className="badge badge-source" title="Imported from Gmail">
            Gmail
          </span>
        )}
      </td>
      <td>{a.position}</td>
      <td>
        <select
          className={`badge badge-${a.status}`}
          value={a.status}
          onChange={(e) => onStatusChange(a.id, e.target.value)}
        >
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </td>
      <td>
        {a.url ? (
          <a href={a.url} target="_blank" rel="noreferrer">
            view
          </a>
        ) : (
          "—"
        )}
      </td>
      <td>
        <div className="actions">
          <button className="link" onClick={startEdit}>
            edit
          </button>
          <button className="link" onClick={() => onDelete(a.id)}>
            delete
          </button>
        </div>
      </td>
    </tr>
  );
}
