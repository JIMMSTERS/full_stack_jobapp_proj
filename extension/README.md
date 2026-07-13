# OfferFlow Browser Extension

A Manifest V3 browser extension (Chrome/Edge) that captures job postings from
career sites and saves them straight into your OfferFlow account with one click.

## What it does

- Detects the company, position and canonical URL on the page you're viewing.
- Site-aware scraping for **LinkedIn, Greenhouse, Lever, Ashby, Workday and
  Indeed**, with an Open Graph / `<title>` fallback for other sites.
- Talks to the OfferFlow API using a **bearer pairing token** (a dedicated
  server-side session) — no cookies, no passwords stored in the extension.
- All network calls go through the background service worker, so the token
  never touches page content or content scripts.

## Structure

```
extension/
├── src/
│   ├── manifest.json     # MV3 manifest
│   ├── background.ts     # service worker: API proxy (holds the token)
│   ├── content.ts        # scrapes the active page on request
│   ├── scrape.ts         # pure extraction logic (unit-tested)
│   ├── popup.html/.css/.ts  # connect + save UI
│   ├── config.ts         # API base, storage keys, statuses
│   └── types.ts          # shared message/response types
├── tests/scrape.test.ts  # node:test unit tests for the scraper
├── build.mjs             # esbuild bundler → dist/
└── dist/                 # build output (load this as an unpacked extension)
```

## Build

```bash
cd extension
npm install
npm run build      # bundles src/ → dist/
npm test           # scraper unit tests
npm run typecheck  # tsc --noEmit
```

Use `npm run watch` for incremental rebuilds while developing.

## Load it in Chrome / Edge

1. Run `npm run build` to produce `dist/`.
2. Open `chrome://extensions` (or `edge://extensions`).
3. Enable **Developer mode**.
4. Click **Load unpacked** and select the `extension/dist` folder.

## Connect it to your account

1. Start the backend (`http://127.0.0.1:8000`) and sign in to the web app.
2. In the web app, scroll to **Browser extension** and click
   **Generate extension token**, then copy the token.
3. Click the OfferFlow extension icon, paste the token, and hit **Connect**.
4. Navigate to a job posting, open the popup, review the pre-filled fields, and
   click **Save to OfferFlow**.

> **Deploying?** The extension only has host permissions for `localhost:8000`
> and `127.0.0.1:8000` by default. Add your production API origin to
> `host_permissions` in `src/manifest.json`, then set the API base URL from the
> extension's settings (⚙) panel.
