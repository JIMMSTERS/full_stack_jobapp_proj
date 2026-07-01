# OfferFlow Backend

Python + FastAPI service backing OfferFlow. Provides Google OAuth authentication,
per-user application CRUD, an activity timeline, follow-up reminders, and Gmail import.
Uses SQLAlchemy 2.0 with Alembic migrations; PostgreSQL in production and SQLite for
zero-setup local development.

See the [root README](../README.md) for the full feature list, architecture, and API reference.

## Prerequisites

- Python 3.12+
- (Optional) PostgreSQL 14+ — or use SQLite locally with no extra setup.

## Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate

# 2. Install runtime + dev (test) dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 3. Configure environment
Copy-Item .env.example .env          # then fill in values

# 4. Create the schema, then run the dev server
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The API is served at http://127.0.0.1:8000 with interactive docs at http://127.0.0.1:8000/docs.

For a zero-dependency local database, set `DATABASE_URL=sqlite:///./offerflow.db` in `.env`.

## Environment variables

See [.env.example](.env.example) for the full list. Key ones:

| Variable                         | Purpose                                                        |
| -------------------------------- | -------------------------------------------------------------- |
| `DATABASE_URL`                   | SQLAlchemy connection string (`postgres://` URLs are auto-normalized to the psycopg driver). |
| `GOOGLE_CLIENT_ID` / `_SECRET`   | Google OAuth credentials.                                      |
| `SECRET_KEY`                     | Signs the OAuth state cookie.                                  |
| `FRONTEND_URL`                   | Where to redirect after login.                                 |
| `ALLOWED_ORIGINS`                | Comma-separated CORS origins.                                  |
| `COOKIE_SAMESITE` / `COOKIE_SECURE` | Session-cookie flags (`none` / `true` for cross-site prod). |

**Google OAuth:** add `http://127.0.0.1:8000/auth/callback` as an authorized redirect URI,
and browse to the app via `http://127.0.0.1:5173` (not `localhost`).

## Testing

```powershell
pytest -q
```

Tests use an isolated in-memory SQLite database per test with authentication overridden,
so no external services or secrets are required.

## Database migrations

Schema is managed by Alembic (never `create_all` at runtime). After changing a model:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Structure

```
backend/
├── app/
│   ├── main.py         # FastAPI app factory + middleware
│   ├── config.py       # environment-driven settings
│   ├── database.py     # engine, session, Base
│   ├── models.py       # SQLAlchemy 2.0 ORM models
│   ├── schemas.py      # Pydantic v2 schemas
│   ├── crud.py         # data-access layer
│   ├── auth.py         # OAuth client, sessions, current-user dependency
│   └── routes/         # auth, applications, gmail routers
├── alembic/            # migration environment + versions
├── tests/              # pytest suite
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```
