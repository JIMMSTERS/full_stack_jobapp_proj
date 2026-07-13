// Popup UI controller: connect flow, scraping the active tab, and saving.
import { DEFAULT_API_BASE, STATUSES, STORAGE_KEYS } from "./config";
import type {
  BackgroundMessage,
  BackgroundResponse,
  ScrapedJob,
} from "./types";

/** Typed helper for grabbing required elements. */
function el<T extends HTMLElement>(id: string): T {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing element #${id}`);
  return node as T;
}

const views = {
  save: el<HTMLElement>("save-view"),
  connect: el<HTMLElement>("connect-view"),
  settings: el<HTMLElement>("settings-view"),
};

function show(view: keyof typeof views): void {
  for (const [name, node] of Object.entries(views)) {
    node.hidden = name !== view;
  }
}

function setNote(node: HTMLElement, message: string, kind?: "error" | "ok"): void {
  node.textContent = message;
  node.classList.toggle("is-error", kind === "error");
  node.classList.toggle("is-ok", kind === "ok");
}

function sendToBackground<T = unknown>(
  message: BackgroundMessage
): Promise<BackgroundResponse<T>> {
  return chrome.runtime.sendMessage(message) as Promise<BackgroundResponse<T>>;
}

async function getActiveTab(): Promise<chrome.tabs.Tab | undefined> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

/** Ask the content script to scrape, falling back to the tab's own metadata. */
async function scrapeActiveTab(): Promise<ScrapedJob> {
  const tab = await getActiveTab();
  const fallback: ScrapedJob = {
    company: "",
    position: tab?.title ?? "",
    url: tab?.url ?? "",
  };
  if (!tab?.id) return fallback;
  try {
    const job = (await chrome.tabs.sendMessage(tab.id, {
      type: "SCRAPE",
    })) as ScrapedJob | undefined;
    return job ?? fallback;
  } catch {
    // No content script on this page (unsupported site) — use the fallback.
    return fallback;
  }
}

function populateStatuses(): void {
  const select = el<HTMLSelectElement>("status");
  for (const status of STATUSES) {
    const option = document.createElement("option");
    option.value = status;
    option.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    select.append(option);
  }
}

async function enterSaveView(): Promise<void> {
  show("save");
  const job = await scrapeActiveTab();
  el<HTMLInputElement>("company").value = job.company;
  el<HTMLInputElement>("position").value = job.position;
  el<HTMLInputElement>("url").value = job.url;
}

async function refresh(): Promise<void> {
  const stored = await chrome.storage.local.get(STORAGE_KEYS.token);
  if (!stored[STORAGE_KEYS.token]) {
    show("connect");
    return;
  }
  const res = await sendToBackground({ type: "PING_AUTH" });
  if (res.ok) {
    await enterSaveView();
  } else {
    show("connect");
    if (!res.needsAuth) {
      setNote(el("connect-status"), res.error, "error");
    }
  }
}

function wireSaveView(): void {
  const button = el<HTMLButtonElement>("save-btn");
  button.addEventListener("click", async () => {
    const company = el<HTMLInputElement>("company").value.trim();
    const position = el<HTMLInputElement>("position").value.trim();
    const note = el("save-status");
    if (!company || !position) {
      setNote(note, "Company and position are required.", "error");
      return;
    }
    button.disabled = true;
    setNote(note, "Saving…");
    const res = await sendToBackground({
      type: "SAVE",
      payload: {
        company,
        position,
        status: el<HTMLSelectElement>("status").value as never,
        url: el<HTMLInputElement>("url").value.trim(),
      },
    });
    button.disabled = false;
    if (res.ok) {
      setNote(note, "Saved ✓", "ok");
      setTimeout(() => window.close(), 800);
    } else if (res.needsAuth) {
      show("connect");
    } else {
      setNote(note, res.error, "error");
    }
  });
}

function wireConnectView(): void {
  el<HTMLButtonElement>("connect-btn").addEventListener("click", async () => {
    const token = el<HTMLInputElement>("token-input").value.trim();
    const note = el("connect-status");
    if (!token) {
      setNote(note, "Paste a token first.", "error");
      return;
    }
    await chrome.storage.local.set({ [STORAGE_KEYS.token]: token });
    setNote(note, "Connecting…");
    const res = await sendToBackground({ type: "PING_AUTH" });
    if (res.ok) {
      await enterSaveView();
    } else {
      setNote(note, "That token didn't work. Generate a fresh one.", "error");
    }
  });
}

function wireSettingsView(): void {
  el<HTMLButtonElement>("settings-toggle").addEventListener("click", async () => {
    const stored = await chrome.storage.local.get([
      STORAGE_KEYS.token,
      STORAGE_KEYS.apiBase,
    ]);
    el<HTMLInputElement>("api-base").value =
      stored[STORAGE_KEYS.apiBase] ?? DEFAULT_API_BASE;
    el<HTMLInputElement>("settings-token").value =
      stored[STORAGE_KEYS.token] ?? "";
    show("settings");
  });

  el<HTMLButtonElement>("settings-save").addEventListener("click", async () => {
    await chrome.storage.local.set({
      [STORAGE_KEYS.apiBase]:
        el<HTMLInputElement>("api-base").value.trim() || DEFAULT_API_BASE,
      [STORAGE_KEYS.token]: el<HTMLInputElement>("settings-token").value.trim(),
    });
    setNote(el("settings-status"), "Saved. Reopening…", "ok");
    setTimeout(refresh, 400);
  });

  el<HTMLButtonElement>("disconnect-btn").addEventListener("click", async () => {
    await chrome.storage.local.remove(STORAGE_KEYS.token);
    show("connect");
  });
}

populateStatuses();
wireSaveView();
wireConnectView();
wireSettingsView();
void refresh();
