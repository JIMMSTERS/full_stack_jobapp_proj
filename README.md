# OfferFlow

**A full-stack job & internship application tracker that turns a chaotic job search into an organized, actionable pipeline.**

OfferFlow lets you capture applications, move them through a visual hiring pipeline, track every status change on a timeline, get colour-coded follow-up reminders, and even auto-import applications from your Gmail — all behind Google sign-in.

### 🔗 [Live demo → offerflow-frontend.onrender.com](https://offerflow-frontend.onrender.com)

Sign in with Google, or click **“Try the live demo”** to jump into a pre-seeded sandbox account — no account needed. _(Hosted on Render's free tier, so the first load may take ~30s to wake up.)_

[![CI](https://github.com/JIMMSTERS/full_stack_jobapp_proj/actions/workflows/ci.yml/badge.svg)](https://github.com/JIMMSTERS/full_stack_jobapp_proj/actions/workflows/ci.yml)
&nbsp;![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
&nbsp;![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
&nbsp;![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
&nbsp;![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
&nbsp;![Tests](https://img.shields.io/badge/tests-75%20passing-brightgreen)

---

## Demo

**▶️ Try it live: https://offerflow-frontend.onrender.com** — use **“Try the live demo”** for instant access, no sign-in required.

<!-- Record a ~60s screen capture (login -> add application -> drag across Kanban -> open detail drawer -> toggle dark theme) and save it as docs/demo.gif to embed it here. -->

_A short demo GIF lives here once recorded (`docs/demo.gif`)._

---

## Highlights

- **Google OAuth + server-side sessions** — sign in with Google; sessions are opaque, httpOnly-cookie backed, and stored server-side (no JWT-in-localStorage foot-guns).
- **One-click demo login** — a public “Try the live demo” button spins up a throwaway sandbox account seeded with realistic sample applications, so anyone can explore the full app without Google sign-in.
- **Two ways to view your pipeline** — a **drag-and-drop Kanban board** (powered by dnd-kit) and a **sortable, searchable, filterable table**, kept in sync.
- **Activity timeline** — every status change is recorded as an immutable event and rendered as a per-application history in a slide-out detail drawer.
- **Follow-up reminders** — set a next-action date and get colour-coded urgency pills (overdue / due soon / later) that automatically hide once an application is closed.
- **Gmail import** — reads your recent mail, classifies job-related messages, guesses the company/status, and imports them as applications (deduped by Gmail thread).
- **LLM classifier with an eval harness** — email classification runs through an LLM (Anthropic, structured tool-call output) with the deterministic keyword heuristic as an automatic fallback; a checked-in labeled dataset + `eval/` script measure accuracy so the two approaches can be compared quantitatively.
- **Browser extension** — a Manifest V3 extension that scrapes the company/position from LinkedIn, Greenhouse, Lever, Ashby, Workday and Indeed and saves the job in one click, authenticated with a revocable bearer pairing token.
- **Dashboard metrics** — live counts by status so you can see the shape of your funnel at a glance.
- **Command palette** — `Ctrl/Cmd-K` to jump around and act fast (cmdk).
- **Polished UX** — five selectable themes including dark modes, skeleton loading states, and toast notifications.
- **Engineered like production** — Alembic migrations, 75 automated tests, GitHub Actions CI, and env-driven config ready for split-domain deployment.

---

## Architecture

```mermaid
flowchart LR
    subgraph Client
        FE["React + TS SPA<br/>(Vite)"]
        EXT["Browser Extension<br/>(MV3, one-click save)"]
    end

    subgraph Server["FastAPI Backend"]
        AUTH["Auth<br/>Google OAuth + sessions"]
        APPS["Applications API<br/>CRUD - stats - timeline"]
        GMAIL["Gmail API<br/>read - classify - import"]
    end

    GOOG["Google OAuth<br/>+ Gmail API"]
    DB[("PostgreSQL")]

    FE -->|"REST (cookie auth)"| Server
    EXT -->|"REST (bearer token)"| Server
    AUTH <-->|OAuth 2.0| GOOG
    GMAIL -->|read messages| GOOG
    Server -->|SQLAlchemy 2.0| DB
```

**Request flow:** the SPA calls the API with `credentials: include`; a session middleware resolves the opaque cookie to a `User`, and every query is scoped to that user. Schema changes ship as Alembic migrations that run automatically on deploy.

---

## Tech Stack

| Layer          | Technology                                                                 |
| -------------- | -------------------------------------------------------------------------- |
| Frontend       | React 18, TypeScript, Vite 5, dnd-kit, cmdk, sonner                         |
| Backend        | Python 3.12, FastAPI, SQLAlchemy 2.0 (typed `Mapped` models), Pydantic v2   |
| Auth           | Authlib (Google OAuth 2.0), server-side sessions via httpOnly cookie        |
| Database       | PostgreSQL (production) - SQLite (local dev) - Alembic migrations           |
| Integrations   | Gmail API (google-api-python-client)                                        |
| AI             | Anthropic Messages API (structured tool-call classification) + eval harness |
| Extension      | Manifest V3 (Chrome/Edge), TypeScript, esbuild, bearer-token auth           |
| Testing        | pytest + httpx (backend) - Vitest + React Testing Library (frontend)        |
| CI / Infra     | GitHub Actions - Render Blueprint (`render.yaml`: API + Postgres + static frontend) |

---

## Data Model

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ APPLICATIONS : owns
    APPLICATIONS ||--o{ STATUS_EVENTS : logs

    USERS {
        int id PK
        string google_sub UK
        string email
        string name
        string google_refresh_token
    }
    SESSIONS {
        int id PK
        string token UK
        int user_id FK
        datetime expires_at
    }
    APPLICATIONS {
        int id PK
        int user_id FK
        string company
        string position
        string status
        date follow_up_date
        string source
        string gmail_thread_id
        datetime created_at
        datetime updated_at
    }
    STATUS_EVENTS {
        int id PK
        int application_id FK
        string from_status
        string to_status
        datetime created_at
    }
```

Every `Application` belongs to a `User` and carries an ordered list of `StatusEvent`s — one when it first appears (`from_status = NULL`) and one per subsequent status change — which powers the activity timeline. Cascades keep sessions, applications, and events tidy when a parent is deleted.

---

## API Reference

All application and Gmail routes require an authenticated session cookie and are scoped to the current user.

| Method   | Endpoint                          | Description                                        |
| -------- | --------------------------------- | -------------------------------------------------- |
| `GET`    | `/auth/login`                     | Begin the Google OAuth flow                         |
| `GET`    | `/auth/callback`                  | OAuth callback; sets the session cookie             |
| `POST`   | `/auth/logout`                    | End the session and clear the cookie                |
| `GET`    | `/auth/me`                        | Current authenticated user                          |
| `GET`    | `/applications`                   | List the user's applications                        |
| `POST`   | `/applications`                   | Create an application                                |
| `GET`    | `/applications/stats`             | Status counts for the dashboard                     |
| `GET`    | `/applications/{id}`              | Fetch a single application                          |
| `GET`    | `/applications/{id}/events`       | Activity timeline for an application                |
| `PATCH`  | `/applications/{id}`              | Update fields / status (records a timeline event)   |
| `DELETE` | `/applications/{id}`              | Delete an application                               |
| `GET`    | `/gmail/messages`                 | Recent Gmail messages with job-related classification |
| `POST`   | `/gmail/import`                   | Import classified messages as applications          |

Interactive OpenAPI docs are available at `/docs` when the server is running.

---

## AI Email Classification & Evaluation

Incoming emails are classified (job-related? which stage? which company?) by a
two-tier classifier:

1. **LLM tier** — calls Anthropic's Messages API with a forced **tool-call schema**, so the model returns strict, validated JSON instead of free text. Enabled via `LLM_CLASSIFIER_ENABLED` + `ANTHROPIC_API_KEY`.
2. **Heuristic fallback** — a deterministic keyword/sender-rule classifier that runs when the LLM is disabled, unconfigured, or errors, so the feature degrades gracefully and never hard-depends on an external service.

Rather than eyeball quality, the repo ships an **evaluation harness** ([`backend/eval/`](backend/eval)) with a hand-labeled dataset ([`dataset.jsonl`](backend/eval/dataset.jsonl), 36 examples) and a scorer:

```bash
python -m eval.evaluate            # heuristic baseline
python -m eval.evaluate --model llm --  # LLM (needs ANTHROPIC_API_KEY)
python -m eval.evaluate --model both    # side-by-side comparison
```

The heuristic baseline (measured, and guarded by a CI test so regressions fail the build):

| Metric | is_job_related | status |
| --- | --- | --- |
| Accuracy | 0.86 | 0.92 |
| Precision / Recall / F1 | 0.83 / 1.00 / 0.91 | — |

The heuristic has perfect recall but over-triggers on recruiting-marketing and job-alert emails (lower precision) — exactly the ambiguity the LLM tier is designed to resolve.

---

## Engineering Practices

- **Typed end to end** — SQLAlchemy 2.0 `Mapped[...]` models, Pydantic v2 schemas, and strict-mode TypeScript.
- **Migrations, not `create_all`** — every schema change is a reviewed Alembic revision; the production start command runs `alembic upgrade head` before serving.
- **Tested** — 58 backend tests (isolated in-memory SQLite per test with dependency-overridden auth), 13 frontend tests (pure logic + component behaviour), and 4 extension scraper tests.
- **CI on every push/PR** — GitHub Actions runs `pytest` and the frontend test + build in parallel.
- **Security-minded** — httpOnly, `SameSite`/`Secure`-configurable session cookies; per-user data scoping on every query; secrets kept out of source via env vars.
- **Deployment-ready** — env-driven CORS origins and cross-site cookie flags, proxy-aware startup, and a one-file Render blueprint.

---

## Local Development

### Prerequisites
- Python 3.12+
- Node.js 20+
- (Optional) PostgreSQL — or use SQLite locally with zero setup.

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   -   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env          # then fill in the values (see below)
alembic upgrade head          # create the schema
uvicorn app.main:app --reload --port 8000
```

For a zero-dependency local database, set `DATABASE_URL=sqlite:///./offerflow.db` in `.env`.

**Google OAuth setup:** create OAuth credentials in the Google Cloud Console, add
`http://127.0.0.1:8000/auth/callback` as an authorized redirect URI, and put the client
ID/secret in `.env`. Then browse to the app via `http://127.0.0.1:5173` (not `localhost`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                   # http://127.0.0.1:5173
```

The frontend reads the API base URL from `VITE_API_URL` (defaults to `http://127.0.0.1:8000`).

---

## Testing

```bash
# Backend
cd backend && pytest -q

# Frontend
cd frontend && npm test
```

---

## Deployment

The repo is wired for a split-domain deploy (frontend and API on different hosts), all in **one Render Blueprint** ([`render.yaml`](render.yaml)):

- **Backend + Postgres:** provisions a managed Postgres database and a Python web service, runs Alembic migrations on deploy, and serves the API behind TLS with proxy headers.
- **Frontend:** builds `frontend/` as a Render static site with a SPA rewrite; set `VITE_API_URL` to the API URL.
- **Cross-site auth:** in production set `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, and `ALLOWED_ORIGINS` to the deployed frontend URL so the session cookie flows across domains.

After the first deploy, fill each service's URL into the other's env vars (`VITE_API_URL`, `FRONTEND_URL`, `ALLOWED_ORIGINS`) and register `<API_URL>/auth/callback` as an authorized redirect URI in Google Cloud.

> Note: sign-in requests only non-sensitive identity scopes (`openid email profile`), so once the OAuth app is published to production **any Google user can sign in** without verification. Gmail import is a separate, opt-in authorization that requests the sensitive `gmail.readonly` scope via incremental consent — that step stays limited to Google test users until the app passes verification. To keep a shareable link friction-free, the app also ships a **“Try the live demo” login** (`DEMO_MODE_ENABLED`) that drops visitors into a throwaway sandbox account pre-seeded with sample applications — no Google sign-in required.

---

## Roadmap

**Shipped**
- Google OAuth + server-side sessions
- Application CRUD, dashboard stats, and status-scoped filtering
- Kanban board (drag-and-drop) and sortable/searchable table
- Activity timeline of status changes
- Follow-up reminder dates with urgency pills
- Gmail import with heuristic classification
- Multi-theme dark mode, skeleton loaders, command palette
- Alembic migrations, automated tests, and CI

**Planned**
- Empty-state onboarding for first-time users
- Bulk actions (multi-select move/delete)
- `framer-motion` micro-interactions and a full mobile/responsive pass
- Tags/labels and CSV export
- Analytics: response rates and time-in-stage funnel
- Browser extension to capture postings in one click
- Public demo via a seeded demo-login mode

---

## Project Structure

```
jimmy_fullstack_proj/
├── backend/            # FastAPI service
│   ├── app/
│   │   ├── routes/     # auth, applications, gmail
│   │   ├── models.py   # SQLAlchemy 2.0 ORM models
│   │   ├── schemas.py  # Pydantic v2 schemas
│   │   ├── crud.py     # data-access layer
│   │   └── main.py     # app factory + middleware
│   ├── alembic/        # database migrations
│   └── tests/          # pytest suite
├── frontend/           # React + TypeScript SPA
│   └── src/
│       ├── components/ # Kanban, Table, DetailDrawer, Dashboard, ...
│       ├── api.ts      # typed API client
│       └── followUp.ts # follow-up urgency logic
├── extension/          # browser extension (planned)
├── docs/               # architecture notes
├── render.yaml         # Render deployment blueprint
└── .github/workflows/  # CI
```
