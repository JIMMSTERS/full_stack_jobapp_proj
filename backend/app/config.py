"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    """Read a truthy/falsy environment variable."""
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


# Google OAuth credentials (from Google Cloud Console).
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# Secret key used to sign the temporary OAuth state cookie (SessionMiddleware).
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-change-me")

# Where to send the user after a successful login (the React app).
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# How long a login session stays valid.
SESSION_TTL_DAYS = int(os.getenv("SESSION_TTL_DAYS", "30"))

# Name of the httpOnly cookie that holds the opaque session token.
SESSION_COOKIE_NAME = "offerflow_session"

# Browser origins allowed to call this API (comma-separated). Defaults to the
# local Vite dev server; set to the deployed frontend URL in production.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

# Cookie flags. When the frontend and API live on different domains (e.g. Vercel
# + Render), the session cookie must be SameSite=None and Secure to be sent on
# cross-site requests. Locally over http these stay lax/insecure.
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()
COOKIE_SECURE = _bool("COOKIE_SECURE", False)

