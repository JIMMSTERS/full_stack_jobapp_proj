import assert from "node:assert/strict";
import { test } from "node:test";

import { extractJob, splitTitle } from "../src/scrape";
import type { DomLike, LocationLike } from "../src/scrape";

function fakeDoc(opts: {
  title?: string;
  nodes?: Record<string, { text?: string; attrs?: Record<string, string> }>;
}): DomLike {
  const nodes = opts.nodes ?? {};
  return {
    title: opts.title ?? "",
    querySelector(selector: string) {
      const node = nodes[selector];
      if (!node) return null;
      return {
        textContent: node.text ?? null,
        getAttribute: (name: string) => node.attrs?.[name] ?? null,
      };
    },
  };
}

function loc(hostname: string, href: string): LocationLike {
  return { hostname, href };
}

test("splitTitle separates position and company across separators", () => {
  assert.deepEqual(splitTitle("Software Engineer - Acme"), {
    position: "Software Engineer",
    company: "Acme",
  });
  assert.deepEqual(splitTitle("Data Scientist at Globex"), {
    position: "Data Scientist",
    company: "Globex",
  });
  assert.deepEqual(splitTitle("Product Manager | Initech"), {
    position: "Product Manager",
    company: "Initech",
  });
  assert.deepEqual(splitTitle("Just A Title"), {
    position: "Just A Title",
    company: "",
  });
});

test("extractJob uses Open Graph tags for generic sites", () => {
  const doc = fakeDoc({
    nodes: {
      'meta[property="og:title"]': {
        attrs: { content: "Backend Engineer - Example Inc" },
      },
      'meta[property="og:site_name"]': { attrs: { content: "Example Inc" } },
    },
  });
  const job = extractJob(
    doc,
    loc("jobs.example.com", "https://jobs.example.com/role/123?utm=abc")
  );
  assert.equal(job.company, "Example Inc");
  assert.equal(job.position, "Backend Engineer");
  assert.equal(job.url, "https://jobs.example.com/role/123");
});

test("extractJob reads LinkedIn-specific selectors", () => {
  const doc = fakeDoc({
    nodes: {
      ".job-details-jobs-unified-top-card__job-title": { text: "Senior SWE" },
      ".job-details-jobs-unified-top-card__company-name a": {
        text: "Acme Corp",
      },
    },
  });
  const job = extractJob(
    doc,
    loc("www.linkedin.com", "https://www.linkedin.com/jobs/view/42/")
  );
  assert.equal(job.position, "Senior SWE");
  assert.equal(job.company, "Acme Corp");
});

test("extractJob falls back to the hostname for company", () => {
  const doc = fakeDoc({ title: "" });
  const job = extractJob(
    doc,
    loc("careers.bigco.com", "https://careers.bigco.com/job/9#section")
  );
  assert.equal(job.company, "Bigco");
  assert.equal(job.url, "https://careers.bigco.com/job/9");
});
