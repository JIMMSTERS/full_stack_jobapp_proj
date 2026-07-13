// Job-posting scraper. Pure functions of a document + location so they can be
// unit-tested without a real browser (see tests/scrape.test.ts).

import type { ScrapedJob } from "./types";

/** Minimal DOM surface the scraper relies on (satisfied by the real DOM). */
export interface ElementLike {
  textContent: string | null;
  getAttribute(name: string): string | null;
}

export interface DomLike {
  title: string;
  querySelector(selectors: string): ElementLike | null;
}

export interface LocationLike {
  hostname: string;
  href: string;
}

/** Collapse whitespace and trim. */
function clean(text: string | null | undefined): string {
  return (text ?? "").replace(/\s+/g, " ").trim();
}

/** First non-empty text content among the given selectors. */
function pickText(doc: DomLike, selectors: string[]): string {
  for (const selector of selectors) {
    const text = clean(doc.querySelector(selector)?.textContent);
    if (text) return text;
  }
  return "";
}

/** Read a `<meta>` tag's content by property or name. */
function meta(doc: DomLike, key: string): string {
  const el =
    doc.querySelector(`meta[property="${key}"]`) ??
    doc.querySelector(`meta[name="${key}"]`);
  return clean(el?.getAttribute("content"));
}

/** Turn a hostname into a readable company guess (e.g. "acme.com" -> "Acme"). */
function companyFromHost(hostname: string): string {
  const parts = hostname.replace(/^www\./, "").split(".");
  const core = parts.length > 1 ? parts[parts.length - 2] : parts[0];
  return core ? core.charAt(0).toUpperCase() + core.slice(1) : "";
}

/** First path segment of a URL (used by Lever/Greenhouse to name the company). */
function firstPathSegment(href: string): string {
  try {
    const segments = new URL(href).pathname.split("/").filter(Boolean);
    return segments[0] ?? "";
  } catch {
    return "";
  }
}

/** Split a page title like "Software Engineer - Acme" into position + company. */
export function splitTitle(title: string): { position: string; company: string } {
  const cleaned = clean(title);
  const match = cleaned.match(/^(.*?)\s+(?:-|–|—|\||at|@|·)\s+(.*)$/i);
  if (match) {
    return { position: clean(match[1]), company: clean(match[2]) };
  }
  return { position: cleaned, company: "" };
}

/** Drop tracking query params so saved URLs are canonical. */
function canonicalUrl(href: string): string {
  try {
    const url = new URL(href);
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return href;
  }
}

/**
 * Extract a job's company / position / url from a career page.
 *
 * Uses site-specific selectors for the major job boards and falls back to
 * Open Graph / `<title>` parsing for everything else.
 */
export function extractJob(doc: DomLike, loc: LocationLike): ScrapedJob {
  const host = loc.hostname.replace(/^www\./, "");
  let position = "";
  let company = "";

  if (host.includes("linkedin.com")) {
    position = pickText(doc, [
      ".job-details-jobs-unified-top-card__job-title",
      ".topcard__title",
      "h1.top-card-layout__title",
      "h1",
    ]);
    company = pickText(doc, [
      ".job-details-jobs-unified-top-card__company-name a",
      ".job-details-jobs-unified-top-card__company-name",
      ".topcard__org-name-link",
      "a.topcard__org-name-link",
    ]);
  } else if (host.includes("greenhouse.io")) {
    position = pickText(doc, [".app-title", ".job__title h1", "h1.section-header"]);
    company = pickText(doc, [".company-name", "span.company-name"]);
  } else if (host.includes("lever.co")) {
    position = pickText(doc, [".posting-headline h2", "h2"]);
    company =
      clean(doc.querySelector(".main-header-logo img")?.getAttribute("alt")) ||
      companyFromHost(firstPathSegment(loc.href) + ".com");
  } else if (host.includes("ashbyhq.com")) {
    position = pickText(doc, ["h1", ".ashby-job-posting-heading"]);
  } else if (host.includes("myworkdayjobs.com")) {
    position = pickText(doc, [
      '[data-automation-id="jobPostingHeader"]',
      "h1",
    ]);
    company = companyFromHost(host);
  } else if (host.includes("indeed.com")) {
    position = pickText(doc, ["h1.jobsearch-JobInfoHeader-title", "h1"]);
    company = pickText(doc, [
      '[data-testid="inlineHeader-companyName"]',
      ".jobsearch-InlineCompanyRating div",
    ]);
  }

  // Open Graph fallbacks for anything still missing.
  const ogTitle = meta(doc, "og:title");
  if (!position) {
    position = ogTitle ? splitTitle(ogTitle).position : "";
  }
  if (!company) {
    company =
      meta(doc, "og:site_name") ||
      (ogTitle ? splitTitle(ogTitle).company : "");
  }

  // Final fallbacks from the document title / hostname.
  if (!position || !company) {
    const fromTitle = splitTitle(doc.title);
    if (!position) position = fromTitle.position;
    if (!company) company = fromTitle.company;
  }
  if (!company) company = companyFromHost(host);

  return { company, position, url: canonicalUrl(loc.href) };
}
