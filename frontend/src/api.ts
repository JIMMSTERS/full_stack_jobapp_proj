import type { Application, ApplicationCreate } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function listApplications(): Promise<Application[]> {
  return handle(await fetch(`${BASE_URL}/applications`));
}

export async function createApplication(
  payload: ApplicationCreate
): Promise<Application> {
  return handle(
    await fetch(`${BASE_URL}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function updateApplication(
  id: number,
  changes: Partial<ApplicationCreate>
): Promise<Application> {
  return handle(
    await fetch(`${BASE_URL}/applications/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes),
    })
  );
}

export async function deleteApplication(id: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/applications/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
}
