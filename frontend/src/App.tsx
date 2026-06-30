import { useEffect, useState } from "react";
import { Toaster, toast } from "sonner";
import {
  createApplication,
  deleteApplication,
  getApplicationStats,
  getCurrentUser,
  listApplications,
  loginUrl,
  logout,
  updateApplication,
} from "./api";
import type { Application, ApplicationCreate, ApplicationStats, User } from "./types";
import { ApplicationForm } from "./components/ApplicationForm";
import { ApplicationTable } from "./components/ApplicationTable";
import { CommandPalette } from "./components/CommandPalette";
import { Dashboard } from "./components/Dashboard";
import { GmailPanel } from "./components/GmailPanel";
import { KanbanBoard } from "./components/KanbanBoard";

type View = "table" | "board";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [highlightId, setHighlightId] = useState<number | null>(null);
  const [view, setView] = useState<View>("table");

  async function refresh() {
    try {
      const [apps, nextStats] = await Promise.all([
        listApplications(),
        getApplicationStats(),
      ]);
      setApplications(apps);
      setStats(nextStats);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getCurrentUser()
      .then((u) => setUser(u))
      .catch(() => setUser(null))
      .finally(() => setAuthChecked(true));
  }, []);

  // Global Cmd/Ctrl+K toggles the command palette.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (user) {
      refresh();
    } else {
      setApplications([]);
      setStats(null);
      setLoading(false);
    }
  }, [user]);

  async function handleCreate(payload: ApplicationCreate) {
    await createApplication(payload);
    await refresh();
    toast.success(`Added ${payload.company}`);
  }

  async function handleDelete(id: number) {
    const removed = applications.find((a) => a.id === id);
    await deleteApplication(id);
    await refresh();
    toast.success(`Deleted ${removed?.company ?? "application"}`);
  }

  async function handleStatusChange(id: number, status: string) {
    const previous = applications;
    // Optimistically move the card/row so table and board feel instant.
    setApplications((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status } : a))
    );
    try {
      await updateApplication(id, { status });
      toast.success(`Moved to ${status}`);
      await refresh();
    } catch {
      setApplications(previous);
      toast.error("Couldn't update status");
    }
  }

  async function handleUpdate(id: number, changes: Partial<ApplicationCreate>) {
    await updateApplication(id, changes);
    await refresh();
    toast.success("Saved changes");
  }

  async function handleLogout() {
    await logout();
    setUser(null);
  }

  function focusAddForm() {
    const input = document.getElementById(
      "app-company-input"
    ) as HTMLInputElement | null;
    input?.scrollIntoView({ behavior: "smooth", block: "center" });
    input?.focus();
  }

  function scrollToGmail() {
    document
      .querySelector(".gmail-panel")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function handleJumpTo(id: number) {
    setView("table");
    setHighlightId(id);
    requestAnimationFrame(() => {
      document
        .getElementById(`app-row-${id}`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
    window.setTimeout(
      () => setHighlightId((cur) => (cur === id ? null : cur)),
      2200
    );
  }

  if (!authChecked) {
    return (
      <div className="app">
        <p className="empty">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="app">
        <header>
          <h1>OfferFlow</h1>
          <p>Track your job applications in one place.</p>
        </header>
        <div className="login">
          <a className="login-button" href={loginUrl}>
            Sign in with Google
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header>
        <div className="header-row">
          <div>
            <h1>OfferFlow</h1>
            <p>Track your job applications in one place.</p>
          </div>
          <div className="user-box">
            <button
              className="cmdk-trigger"
              onClick={() => setPaletteOpen(true)}
              title="Open command palette"
            >
              <span className="cmdk-trigger-text">Search…</span>
              <kbd>⌘K</kbd>
            </button>
            {user.picture && (
              <img className="avatar" src={user.picture} alt="" />
            )}
            <span className="user-name">{user.name ?? user.email}</span>
            <button className="logout-button" onClick={handleLogout}>
              Sign out
            </button>
          </div>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      <Dashboard stats={stats} />

      <ApplicationForm onCreate={handleCreate} />

      <div className="view-toggle" role="tablist" aria-label="View mode">
        <button
          role="tab"
          aria-selected={view === "table"}
          className={`view-tab${view === "table" ? " is-active" : ""}`}
          onClick={() => setView("table")}
        >
          Table
        </button>
        <button
          role="tab"
          aria-selected={view === "board"}
          className={`view-tab${view === "board" ? " is-active" : ""}`}
          onClick={() => setView("board")}
        >
          Board
        </button>
      </div>

      {loading ? (
        <p className="empty">Loading…</p>
      ) : view === "table" ? (
        <ApplicationTable
          applications={applications}
          highlightId={highlightId}
          onDelete={handleDelete}
          onStatusChange={handleStatusChange}
          onUpdate={handleUpdate}
        />
      ) : (
        <KanbanBoard
          applications={applications}
          onStatusChange={handleStatusChange}
        />
      )}

      <GmailPanel onImported={refresh} />

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        applications={applications}
        onAddApplication={focusAddForm}
        onGoToGmail={scrollToGmail}
        onJumpTo={handleJumpTo}
        onSignOut={handleLogout}
      />

      <Toaster position="bottom-right" richColors closeButton />
    </div>
  );
}
