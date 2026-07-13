# OfferFlow Frontend

React 18 + TypeScript single-page application built with Vite. Renders the dashboard,
Kanban board, application table, detail drawer with activity timeline, command palette,
and multi-theme dark mode. Talks to the FastAPI backend over a cookie-authenticated REST API.

See the [root README](../README.md) for the full feature list and architecture.

## Prerequisites

- Node.js 20+ and npm

## Setup

```powershell
# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app is served at http://127.0.0.1:5173. Use `127.0.0.1` (not `localhost`) so the
session cookie from the OAuth flow is shared correctly.

## Environment

The API base URL is read from `VITE_API_URL` and defaults to `http://127.0.0.1:8000`.
For a deployed frontend, set `VITE_API_URL` to your API URL (e.g. in the Render
static-site env vars, or any host's build settings). Use no trailing slash.

## Scripts

| Command             | Description                                  |
| ------------------- | -------------------------------------------- |
| `npm run dev`       | Start the Vite dev server.                   |
| `npm run build`     | Type-check (`tsc -b`) and build for production. |
| `npm run preview`   | Preview the production build locally.        |
| `npm test`          | Run the Vitest suite once.                   |
| `npm run test:watch`| Run Vitest in watch mode.                    |

## Testing

Tests use Vitest + React Testing Library (jsdom). Component tests render with Testing
Library and assert on accessible roles/labels; pure logic (e.g. follow-up urgency) is
unit tested directly.

```powershell
npm test
```

## Structure

```
frontend/src/
├── App.tsx            # top-level state, layout, theme + auth handling
├── main.tsx           # React entry point
├── api.ts             # typed API client (fetch + credentials)
├── types.ts           # shared TypeScript types
├── followUp.ts        # follow-up urgency logic (unit tested)
├── index.css          # design tokens + component styles (themeable)
├── components/        # Dashboard, KanbanBoard, ApplicationTable,
│                      #   DetailDrawer, CommandPalette, GmailPanel,
│                      #   ApplicationForm, Skeleton
└── test/setup.ts      # Vitest + jest-dom setup
```
