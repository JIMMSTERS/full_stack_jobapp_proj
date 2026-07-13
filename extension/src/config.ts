// Shared configuration and constants for the OfferFlow extension.

/** Default OfferFlow API base URL (local dev). Editable in the popup settings. */
export const DEFAULT_API_BASE = "http://127.0.0.1:8000";

/** chrome.storage.local keys. */
export const STORAGE_KEYS = {
  token: "offerflow_token",
  apiBase: "offerflow_api_base",
} as const;

/** Application statuses, mirroring the backend/web app. */
export const STATUSES = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
] as const;

export type Status = (typeof STATUSES)[number];
