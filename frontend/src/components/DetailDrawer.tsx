import { useEffect, useRef, useState } from "react";
import { getApplicationEvents } from "../api";
import { getFollowUp } from "../followUp";
import type { Application, ApplicationCreate, StatusEvent } from "../types";
import { STATUSES } from "../types";

interface Props {
  application: Application | null;
  onClose: () => void;
  onUpdate: (id: number, changes: Partial<ApplicationCreate>) => Promise<void>;
  onStatusChange: (id: number, status: string) => void;
  onDelete: (id: number) => void;
}

const STATUS_META: Record<string, { label: string; color: string }> = {
  applied: { label: "Applied", color: "#2563eb" },
  screening: { label: "Screening", color: "#0891b2" },
  interview: { label: "Interview", color: "#7c3aed" },
  offer: { label: "Offer", color: "#16a34a" },
  rejected: { label: "Rejected", color: "#dc2626" },
};

function statusLabel(status: string): string {
  return STATUS_META[status]?.label ?? status;
}

function statusColor(status: string): string {
  return STATUS_META[status]?.color ?? "#64748b";
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.round(days / 30);
  return `${months}mo ago`;
}

export function DetailDrawer({
  application,
  onClose,
  onUpdate,
  onStatusChange,
  onDelete,
}: Props) {
  const [company, setCompany] = useState("");
  const [position, setPosition] = useState("");
  const [url, setUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [followUp, setFollowUp] = useState("");
  const [saving, setSaving] = useState(false);
  const [events, setEvents] = useState<StatusEvent[]>([]);
  const [loadingEvents, setLoadingEvents] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const id = application?.id ?? null;
  const updatedAt = application?.updated_at ?? null;

  // Reset the editable draft whenever a different application is opened.
  useEffect(() => {
    if (!application) return;
    setCompany(application.company);
    setPosition(application.position);
    setUrl(application.url ?? "");
    setNotes(application.notes ?? "");
    setFollowUp(application.follow_up_date ?? "");
  }, [application?.id]);

  // Load the activity timeline; refetch when the application changes or is updated
  // (a status change bumps updated_at, so a new event will have been recorded).
  useEffect(() => {
    if (id == null) return;
    let active = true;
    setLoadingEvents(true);
    getApplicationEvents(id)
      .then((data) => {
        if (active) setEvents(data);
      })
      .catch(() => {
        if (active) setEvents([]);
      })
      .finally(() => {
        if (active) setLoadingEvents(false);
      });
    return () => {
      active = false;
    };
  }, [id, updatedAt]);

  // Close on Escape and focus the panel when opened.
  useEffect(() => {
    if (id == null) return;
    panelRef.current?.focus();
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [id, onClose]);

  if (!application) return null;

  const dirty =
    company.trim() !== application.company ||
    position.trim() !== application.position ||
    (url.trim() || "") !== (application.url ?? "") ||
    (notes.trim() || "") !== (application.notes ?? "") ||
    (followUp || "") !== (application.follow_up_date ?? "");

  async function save() {
    if (!application) return;
    setSaving(true);
    try {
      await onUpdate(application.id, {
        company: company.trim(),
        position: position.trim(),
        url: url.trim() || null,
        notes: notes.trim() || null,
        follow_up_date: followUp || null,
      });
    } finally {
      setSaving(false);
    }
  }

  // Timeline rendered newest-first so the latest activity is at the top.
  const timeline = [...events].reverse();

  const due = getFollowUp(application.follow_up_date, application.status);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-label={`${application.company} — ${application.position}`}
        ref={panelRef}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="drawer-header">
          <div>
            <span
              className="drawer-status-dot"
              style={{ background: statusColor(application.status) }}
            />
            <h2>{application.company}</h2>
            <p>{application.position}</p>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </header>

        <div className="drawer-body">
          <label className="drawer-field">
            <span>Status</span>
            <select
              value={application.status}
              onChange={(e) => onStatusChange(application.id, e.target.value)}
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {statusLabel(s)}
                </option>
              ))}
            </select>
          </label>

          <label className="drawer-field">
            <span>Company</span>
            <input value={company} onChange={(e) => setCompany(e.target.value)} />
          </label>

          <label className="drawer-field">
            <span>Position</span>
            <input
              value={position}
              onChange={(e) => setPosition(e.target.value)}
            />
          </label>

          <label className="drawer-field">
            <span>Job URL</span>
            <input
              placeholder="https://…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </label>

          <label className="drawer-field">
            <span>
              Follow-up date
              {due && (
                <span className={`due-pill due-${due.tone}`}>{due.label}</span>
              )}
            </span>
            <input
              type="date"
              value={followUp}
              onChange={(e) => setFollowUp(e.target.value)}
            />
          </label>

          <label className="drawer-field">
            <span>Notes</span>
            <textarea
              rows={4}
              placeholder="Recruiter name, next steps, prep notes…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </label>

          <div className="drawer-actions">
            <button onClick={save} disabled={!dirty || saving}>
              {saving ? "Saving…" : "Save changes"}
            </button>
            <button
              className="link"
              onClick={() => onDelete(application.id)}
            >
              Delete
            </button>
          </div>

          <section className="timeline">
            <h3>Activity</h3>
            {loadingEvents ? (
              <p className="timeline-empty">Loading…</p>
            ) : timeline.length === 0 ? (
              <p className="timeline-empty">No activity yet.</p>
            ) : (
              <ol className="timeline-list">
                {timeline.map((ev) => (
                  <li key={ev.id} className="timeline-item">
                    <span
                      className="timeline-dot"
                      style={{ background: statusColor(ev.to_status) }}
                    />
                    <div className="timeline-content">
                      <div className="timeline-label">
                        {ev.from_status ? (
                          <>
                            {statusLabel(ev.from_status)}
                            <span className="timeline-arrow">→</span>
                            {statusLabel(ev.to_status)}
                          </>
                        ) : (
                          <>Created as {statusLabel(ev.to_status)}</>
                        )}
                      </div>
                      <div
                        className="timeline-time"
                        title={formatDateTime(ev.created_at)}
                      >
                        {timeAgo(ev.created_at)}
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}
