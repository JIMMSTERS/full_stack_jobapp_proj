"""OfferFlow FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app import config
from app.routes import applications, auth, gmail

# CORS origins allowed to call this API (React dev server).
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan. Schema is managed by Alembic migrations."""
    yield


app = FastAPI(title="OfferFlow API", version="0.1.0", lifespan=lifespan)

# Signs the short-lived cookie Authlib uses to hold the OAuth "state" value.
app.add_middleware(SessionMiddleware, secret_key=config.SECRET_KEY, same_site="lax")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(applications.router)
app.include_router(gmail.router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Basic liveness/info endpoint."""
    return {"service": "offerflow-api", "status": "ok"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
