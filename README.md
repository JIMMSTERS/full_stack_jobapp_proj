# OfferFlow

OfferFlow is a full-stack automated job application tracker for CS students. It helps you
capture, organize, and track the status of job and internship applications in one place.

> **Status:** Early scaffolding. Gmail, Calendar, and AI features are intentionally **not**
> built yet. This repo currently contains the base monorepo structure only.

## Tech Stack

| Layer      | Technology                       |
| ---------- | -------------------------------- |
| Frontend   | React + TypeScript (Vite)        |
| Backend    | Python + FastAPI                 |
| Database   | PostgreSQL                       |
| Extension  | Browser extension (TypeScript)   |

## Repository Structure

```
offerflow/
├── frontend/     # React + TypeScript single-page app
├── backend/      # FastAPI service + PostgreSQL data layer
├── extension/    # Browser extension to capture job postings
├── docs/         # Architecture notes and design docs
├── README.md
└── .gitignore
```

## Getting Started

Each package has its own README with setup steps:

- [frontend/README.md](frontend/README.md)
- [backend/README.md](backend/README.md)
- [extension/README.md](extension/README.md)

## Roadmap (high level)

1. ✅ Monorepo scaffolding
2. ⬜ Core application CRUD (create / list / update applications)
3. ⬜ Persistence with PostgreSQL
4. ⬜ Browser extension capture flow
5. ⬜ Gmail integration (later)
6. ⬜ Calendar integration (later)
7. ⬜ AI features (later)
```
