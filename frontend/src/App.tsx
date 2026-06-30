import { useEffect, useState } from "react";
import {
  createApplication,
  deleteApplication,
  getCurrentUser,
  listApplications,
  loginUrl,
  logout,
  updateApplication,
} from "./api";
import type { Application, ApplicationCreate, User } from "./types";
import { ApplicationForm } from "./components/ApplicationForm";
import { ApplicationTable } from "./components/ApplicationTable";
import { GmailPanel } from "./components/GmailPanel";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [applications, setApplications] = useState<Application[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setApplications(await listApplications());
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

  useEffect(() => {
    if (user) {
      refresh();
    } else {
      setApplications([]);
      setLoading(false);
    }
  }, [user]);

  async function handleCreate(payload: ApplicationCreate) {
    await createApplication(payload);
    await refresh();
  }

  async function handleDelete(id: number) {
    await deleteApplication(id);
    await refresh();
  }

  async function handleStatusChange(id: number, status: string) {
    await updateApplication(id, { status });
    await refresh();
  }

  async function handleUpdate(id: number, changes: Partial<ApplicationCreate>) {
    await updateApplication(id, changes);
    await refresh();
  }

  async function handleLogout() {
    await logout();
    setUser(null);
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

      <ApplicationForm onCreate={handleCreate} />

      {loading ? (
        <p className="empty">Loading…</p>
      ) : (
        <ApplicationTable
          applications={applications}
          onDelete={handleDelete}
          onStatusChange={handleStatusChange}
          onUpdate={handleUpdate}
        />
      )}

      <GmailPanel />
    </div>
  );
}
