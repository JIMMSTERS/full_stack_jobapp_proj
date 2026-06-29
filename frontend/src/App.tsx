import { useEffect, useState } from "react";
import {
  createApplication,
  deleteApplication,
  listApplications,
  updateApplication,
} from "./api";
import type { Application, ApplicationCreate } from "./types";
import { ApplicationForm } from "./components/ApplicationForm";
import { ApplicationTable } from "./components/ApplicationTable";

export default function App() {
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
    refresh();
  }, []);

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

  return (
    <div className="app">
      <header>
        <h1>OfferFlow</h1>
        <p>Track your job applications in one place.</p>
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
    </div>
  );
}
