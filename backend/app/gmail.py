"""Gmail access: build credentials from stored tokens and read messages."""

from datetime import timezone

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app import auth, config, models

TOKEN_URI = "https://oauth2.googleapis.com/token"


class GmailNotConnected(Exception):
    """Raised when the user has no stored Google tokens."""


class GmailError(Exception):
    """Raised when the Gmail API call fails for a known reason."""


def _credentials_for(db: Session, user: models.User) -> Credentials:
    """Build google-auth Credentials, refreshing + persisting if expired."""
    if not user.google_refresh_token and not user.google_access_token:
        raise GmailNotConnected()

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri=TOKEN_URI,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        scopes=auth.GOOGLE_SCOPES.split(),
    )

    if not creds.valid:
        try:
            creds.refresh(GoogleRequest())
        except RefreshError as exc:
            raise GmailNotConnected() from exc
        # Persist the refreshed access token + expiry for next time.
        user.google_access_token = creds.token
        if creds.expiry:
            expiry = creds.expiry
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            user.google_token_expiry = expiry
        db.commit()

    return creds


def _http_error_message(exc: HttpError) -> str:
    """Extract a human-readable message from a Gmail HttpError."""
    try:
        reason = exc.error_details[0].get("message")  # type: ignore[index]
        if reason:
            return reason
    except (AttributeError, IndexError, KeyError, TypeError):
        pass
    return getattr(exc, "reason", None) or "Gmail request failed."


def _header(headers: list[dict], name: str) -> str:
    """Return the value of a named header (case-insensitive), or empty string."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def list_recent_messages(
    db: Session, user: models.User, max_results: int = 20
) -> list[dict]:
    """Return recent inbox messages with subject, sender, date, and snippet."""
    creds = _credentials_for(db, user)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    try:
        listing = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=max_results)
            .execute()
        )

        results: list[dict] = []
        for ref in listing.get("messages", []):
            msg = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=ref["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                )
                .execute()
            )
            headers = msg.get("payload", {}).get("headers", [])
            results.append(
                {
                    "id": msg.get("id"),
                    "thread_id": msg.get("threadId"),
                    "internal_date": int(msg.get("internalDate", 0) or 0),
                    "subject": _header(headers, "Subject"),
                    "from": _header(headers, "From"),
                    "date": _header(headers, "Date"),
                    "snippet": msg.get("snippet", ""),
                }
            )
    except HttpError as exc:
        raise GmailError(_http_error_message(exc)) from exc

    return results
