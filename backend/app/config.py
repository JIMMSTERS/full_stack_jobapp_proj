"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()

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
