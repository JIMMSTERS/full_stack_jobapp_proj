"""Authentication: Google OAuth client, session helpers, and dependencies."""

import secrets
from datetime import datetime, timedelta, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app import config, models
from app.database import get_db

# OAuth scopes we request. gmail.readonly lets us read (not modify) the inbox.
GOOGLE_SCOPES = "openid email profile https://www.googleapis.com/auth/gmail.readonly"

# Authlib OAuth registry. Google's discovery document supplies all endpoints.
oauth = OAuth()
oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": GOOGLE_SCOPES},
)


def save_google_tokens(db: Session, user: models.User, token: dict) -> None:
    """Persist the Google access/refresh tokens from an OAuth token response."""
    user.google_access_token = token.get("access_token")
    # Google only returns a refresh_token on the first consent; keep the old one
    # if this response doesn't include a new one.
    if token.get("refresh_token"):
        user.google_refresh_token = token["refresh_token"]
    expires_at = token.get("expires_at")
    if expires_at:
        user.google_token_expiry = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    db.commit()


def upsert_user(db: Session, claims: dict) -> models.User:
    """Create or update a user from Google ID-token claims."""
    google_sub = claims["sub"]
    user = (
        db.query(models.User)
        .filter(models.User.google_sub == google_sub)
        .one_or_none()
    )
    if user is None:
        user = models.User(google_sub=google_sub)
        db.add(user)
    user.email = claims.get("email", "")
    user.name = claims.get("name")
    user.picture = claims.get("picture")
    db.commit()
    db.refresh(user)
    return user


def create_session(db: Session, user: models.User) -> models.Session:
    """Create a new server-side session row with an opaque token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=config.SESSION_TTL_DAYS)
    session = models.Session(token=token, user_id=user.id, expires_at=expires_at)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def delete_session(db: Session, token: str) -> None:
    """Delete a session row by its token, if it exists."""
    session = (
        db.query(models.Session)
        .filter(models.Session.token == token)
        .one_or_none()
    )
    if session is not None:
        db.delete(session)
        db.commit()


def _bearer_token(authorization: str | None) -> str | None:
    """Extract the token from an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def get_current_user(
    db: Session = Depends(get_db),
    offerflow_session: str | None = Cookie(default=None),
    authorization: str | None = Header(default=None),
) -> models.User:
    """Resolve the logged-in user from the session token, or 401.

    The token comes from the ``offerflow_session`` cookie (web app) or an
    ``Authorization: Bearer <token>`` header (browser extension / API clients).
    Both resolve against the same server-side ``Session`` table.
    """
    token = offerflow_session or _bearer_token(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    session = (
        db.query(models.Session)
        .filter(models.Session.token == token)
        .one_or_none()
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )
    return session.user
