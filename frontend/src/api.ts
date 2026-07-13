import type {
  Application,
  ApplicationCreate,
  ApplicationStats,
  GmailMessage,
  ImportSummary,
  StatusEvent,
  User,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// Send the session cookie with every request so the API can identify the user.
const withCredentials: RequestInit = { credentials: "include" };

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const loginUrl = `${BASE_URL}/auth/login`;

export async function getCurrentUser(): Promise<User | null> {
  const res = await fetch(`${BASE_URL}/auth/me`, withCredentials);
  if (res.status === 401) return null;
  return handle<User>(res);
}

export async function startDemo(): Promise<User> {
  return handle(
    await fetch(`${BASE_URL}/auth/demo`, {
      method: "POST",
      ...withCredentials,
    })
  );
}

export async function logout(): Promise<void> {
  await fetch(`${BASE_URL}/auth/logout`, {
    method: "POST",
    ...withCredentials,
  });
}

export async function createExtensionToken(): Promise<{
  token: string;
  expires_at: string;
}> {
  return handle(
    await fetch(`${BASE_URL}/auth/extension-token`, {
      method: "POST",
      ...withCredentials,
    })
  );
}

export async function listApplications(): Promise<Application[]> {
  return handle(await fetch(`${BASE_URL}/applications`, withCredentials));
}

export async function getApplicationStats(): Promise<ApplicationStats> {
  return handle(
    await fetch(`${BASE_URL}/applications/stats`, withCredentials)
  );
}

export async function getApplicationEvents(
  id: number
): Promise<StatusEvent[]> {
  return handle(
    await fetch(`${BASE_URL}/applications/${id}/events`, withCredentials)
  );
}

export async function createApplication(
  payload: ApplicationCreate
): Promise<Application> {
  return handle(
    await fetch(`${BASE_URL}/applications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      ...withCredentials,
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
      ...withCredentials,
    })
  );
}

export async function deleteApplication(id: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/applications/${id}`, {
    method: "DELETE",
    ...withCredentials,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
}

export async function fetchGmailMessages(limit = 20): Promise<GmailMessage[]> {
  return handle(
    await fetch(`${BASE_URL}/gmail/messages?limit=${limit}`, withCredentials)
  );
}

export async function importFromGmail(limit = 25): Promise<ImportSummary> {
  return handle(
    await fetch(`${BASE_URL}/gmail/import?limit=${limit}`, {
      method: "POST",
      ...withCredentials,
    })
  );
}
