import { useMemo, useState } from "react";
import type { Application } from "../types";
import { STATUSES } from "../types";
import { getFollowUp } from "../followUp";

interface Props {
  applications: Application[];
  highlightId?: number | null;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
  onOpenDetail: (application: Application) => void;
}

const SORTS: { key: string; label: string }[] = [
  { key: "newest", label: "Newest" },
  { key: "oldest", label: "Oldest" },
  { key: "company", label: "Company A–Z" },
  { key: "status", label: "Status" },
];

export function ApplicationTable({
  applications,
  highlightId,
  onDelete,
  onStatusChange,
  onOpenDetail,
}: Props) {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortKey, setSortKey] = useState("newest");

  const counts = useMemo(() => {
    const tally: Record<string, number> = {};
    for (const a of applications) {
      tally[a.status] = (tally[a.status] ?? 0) + 1;
    }
    return tally;
  }, [applications]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = applications.filter((a) => {
      const matchesQuery =
        !q || `${a.company} ${a.position}`.toLowerCase().includes(q);
      const matchesStatus = statusFilter === "all" || a.status === statusFilter;
      return matchesQuery && matchesStatus;
    });
    return [...filtered].sort((a, b) => {
      switch (sortKey) {
        case "oldest":
          return a.created_at.localeCompare(b.created_at);
        case "company":
          return a.company.localeCompare(b.company);
        case "status":
          return STATUSES.indexOf(a.status) - STATUSES.indexOf(b.status);
        case "newest":
        default:
          return b.created_at.localeCompare(a.created_at);
      }
    });
  }, [applications, query, statusFilter, sortKey]);

  if (applications.length === 0) {
    return <p className="empty">No applications yet. Add your first one above.</p>;
  }

  return (
    <div className="table-section">
      <div className="table-controls">
        <input
          className="table-search"
          placeholder="Search company or position…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search applications"
        />
        <select
          className="sort-select"
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value)}
          aria-label="Sort applications"
        >
          {SORTS.map((s) => (
            <option key={s.key} value={s.key}>
              Sort: {s.label}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-chips" role="group" aria-label="Filter by status">
        <button
          className={`chip${statusFilter === "all" ? " is-active" : ""}`}
          onClick={() => setStatusFilter("all")}
        >
          All <span className="chip-count">{applications.length}</span>
        </button>
        {STATUSES.map((s) => (
          <button
            key={s}
            className={`chip chip-${s}${statusFilter === s ? " is-active" : ""}`}
            onClick={() => setStatusFilter(s)}
          >
            {s} <span className="chip-count">{counts[s] ?? 0}</span>
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="empty">No applications match your search or filter.</p>
      ) : (
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
            {visible.map((a) => (
              <Row
                key={a.id}
                application={a}
                highlighted={a.id === highlightId}
                onDelete={onDelete}
                onStatusChange={onStatusChange}
                onOpenDetail={onOpenDetail}
              />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

interface RowProps {
  application: Application;
  highlighted: boolean;
  onDelete: (id: number) => void;
  onStatusChange: (id: number, status: string) => void;
  onOpenDetail: (application: Application) => void;
}

function Row({ application: a, highlighted, onDelete, onStatusChange, onOpenDetail }: RowProps) {
  const due = getFollowUp(a.follow_up_date, a.status);
  return (
    <tr id={`app-row-${a.id}`} className={highlighted ? "row-highlight" : undefined}>
      <td>
        <button className="link-cell" onClick={() => onOpenDetail(a)}>
          {a.company}
        </button>
        {a.source === "gmail" && (
          <span className="badge badge-source" title="Imported from Gmail">
            Gmail
          </span>
        )}
        {due && <span className={`due-pill due-${due.tone}`}>{due.label}</span>}
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
          <button className="link" onClick={() => onDelete(a.id)}>
            delete
          </button>
        </div>
      </td>
    </tr>
  );
}
