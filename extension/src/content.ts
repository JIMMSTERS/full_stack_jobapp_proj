// Content script: runs on career pages and scrapes job details on request.
import { extractJob } from "./scrape";
import type { ContentMessage, ScrapedJob } from "./types";

chrome.runtime.onMessage.addListener(
  (message: ContentMessage, _sender, sendResponse: (job: ScrapedJob) => void) => {
    if (message?.type === "SCRAPE") {
      sendResponse(extractJob(document, window.location));
    }
    // Synchronous response; no need to return true.
  }
);
