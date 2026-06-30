"""Routes for reading the signed-in user's Gmail messages."""

from fastapi import APIRouter, Depends, HTTPException, status

from app import classifier, gmail, importer, models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/gmail", tags=["gmail"])


@router.get("/messages")
def list_messages(
    limit: int = 20,
    db=Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return the current user's recent inbox messages, each tagged by the
    classifier with whether it's job-related and any detected status."""
    try:
        messages = gmail.list_recent_messages(db, current_user, max_results=limit)
    except gmail.GmailNotConnected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected. Sign out and sign in again to grant access.",
        )
    except gmail.GmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    for message in messages:
        message["classification"] = classifier.classify(
            subject=message.get("subject", ""),
            sender=message.get("from", ""),
            snippet=message.get("snippet", ""),
        )
    return messages


@router.post("/import", response_model=schemas.ImportSummary)
def import_applications(
    limit: int = 25,
    db=Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Scan recent Gmail messages and create/update applications from the
    job-related ones (deduped by Gmail thread)."""
    try:
        return importer.import_from_gmail(db, current_user, max_results=limit)
    except gmail.GmailNotConnected:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected. Sign out and sign in again to grant access.",
        )
    except gmail.GmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
