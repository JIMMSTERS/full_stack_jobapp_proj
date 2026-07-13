// Background service worker: the extension's single point of contact with the
// OfferFlow API. It reads the bearer token from storage and proxies requests so
// the token never lives in a content script or a scraped page.
import { DEFAULT_API_BASE, STORAGE_KEYS } from "./config";
import type { BackgroundMessage, BackgroundResponse } from "./types";

async function getSettings(): Promise<{ token: string; apiBase: string }> {
  const stored = await chrome.storage.local.get([
    STORAGE_KEYS.token,
    STORAGE_KEYS.apiBase,
  ]);
  return {
    token: stored[STORAGE_KEYS.token] ?? "",
    apiBase: stored[STORAGE_KEYS.apiBase] ?? DEFAULT_API_BASE,
  };
}

async function apiFetch(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const { token, apiBase } = await getSettings();
  if (!token) throw new NeedsAuthError();
  return fetch(`${apiBase.replace(/\/$/, "")}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
}

class NeedsAuthError extends Error {}

async function handle(
  message: BackgroundMessage
): Promise<BackgroundResponse> {
  try {
    if (message.type === "PING_AUTH") {
      const res = await apiFetch("/auth/me");
      if (res.status === 401) return { ok: false, error: "Not connected", needsAuth: true };
      if (!res.ok) return { ok: false, error: `API ${res.status}` };
      return { ok: true, data: await res.json() };
    }

    if (message.type === "SAVE") {
      const res = await apiFetch("/applications", {
        method: "POST",
        body: JSON.stringify(message.payload),
      });
      if (res.status === 401) return { ok: false, error: "Not connected", needsAuth: true };
      if (!res.ok) {
        const detail = await res.text();
        return { ok: false, error: `API ${res.status}: ${detail}` };
      }
      return { ok: true, data: await res.json() };
    }

    return { ok: false, error: "Unknown message" };
  } catch (err) {
    if (err instanceof NeedsAuthError) {
      return { ok: false, error: "Not connected", needsAuth: true };
    }
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Request failed",
    };
  }
}

chrome.runtime.onMessage.addListener((message: BackgroundMessage, _sender, sendResponse) => {
  handle(message).then(sendResponse);
  return true; // keep the message channel open for the async response
});
