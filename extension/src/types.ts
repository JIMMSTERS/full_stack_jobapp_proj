import type { Status } from "./config";

/** Job details scraped from a career page. */
export interface ScrapedJob {
  company: string;
  position: string;
  url: string;
}

/** Messages sent from the popup to the content script. */
export type ContentMessage = { type: "SCRAPE" };

/** Messages sent from the popup to the background service worker. */
export type BackgroundMessage =
  | { type: "PING_AUTH" }
  | {
      type: "SAVE";
      payload: { company: string; position: string; url: string; status: Status };
    };

/** Response shape from the background service worker. */
export type BackgroundResponse<T = unknown> =
  | { ok: true; data: T }
  | { ok: false; error: string; needsAuth?: boolean };
