"""Database access functions (CRUD) for applications."""

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app import models, schemas

# Canonical pipeline order used for the analytics dashboard.
STATUS_ORDER = ["applied", "screening", "interview", "offer", "rejected"]
# How many weeks of "applications over time" history to report.
WEEKS_OF_HISTORY = 8


def get_applications(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> list[models.Application]:
    """Return a page of the user's applications, newest first."""
    return (
        db.query(models.Application)
        .filter(models.Application.user_id == user_id)
        .order_by(models.Application.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_application(
    db: Session, application_id: int, user_id: int
) -> models.Application | None:
    """Return a single application owned by the user, or None."""
    return (
        db.query(models.Application)
        .filter(
            models.Application.id == application_id,
            models.Application.user_id == user_id,
        )
        .one_or_none()
    )


def get_application_by_thread(
    db: Session, user_id: int, gmail_thread_id: str
) -> models.Application | None:
    """Return the user's application imported from a given Gmail thread, or None."""
    return (
        db.query(models.Application)
        .filter(
            models.Application.user_id == user_id,
            models.Application.gmail_thread_id == gmail_thread_id,
        )
        .one_or_none()
    )


def create_application(
    db: Session, application: schemas.ApplicationCreate, user_id: int
) -> models.Application:
    """Insert a new application owned by the user."""
    db_application = models.Application(**application.model_dump(), user_id=user_id)
    db.add(db_application)
    db.flush()
    db.add(
        models.StatusEvent(
            application_id=db_application.id,
            from_status=None,
            to_status=db_application.status,
        )
    )
    db.commit()
    db.refresh(db_application)
    return db_application


def create_imported_application(
    db: Session,
    user_id: int,
    company: str,
    position: str,
    status: str,
    gmail_thread_id: str,
) -> models.Application:
    """Insert an application imported from a Gmail thread."""
    db_application = models.Application(
        user_id=user_id,
        company=company,
        position=position,
        status=status,
        source="gmail",
        gmail_thread_id=gmail_thread_id,
    )
    db.add(db_application)
    db.flush()
    db.add(
        models.StatusEvent(
            application_id=db_application.id,
            from_status=None,
            to_status=status,
        )
    )
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(
    db: Session, db_application: models.Application, updates: schemas.ApplicationUpdate
) -> models.Application:
    """Apply partial updates to an existing application.

    When the ``status`` changes, append a row to the activity timeline so the
    transition is recorded.
    """
    previous_status = db_application.status
    changes = updates.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(db_application, field, value)
    new_status = db_application.status
    if "status" in changes and new_status != previous_status:
        db.add(
            models.StatusEvent(
                application_id=db_application.id,
                from_status=previous_status,
                to_status=new_status,
            )
        )
    db.commit()
    db.refresh(db_application)
    return db_application


def get_application_events(
    db: Session, application_id: int
) -> list[models.StatusEvent]:
    """Return an application's timeline entries, oldest first."""
    return (
        db.query(models.StatusEvent)
        .filter(models.StatusEvent.application_id == application_id)
        .order_by(models.StatusEvent.created_at, models.StatusEvent.id)
        .all()
    )


def delete_application(db: Session, db_application: models.Application) -> None:
    """Delete an application."""
    db.delete(db_application)
    db.commit()


def _as_utc(value: datetime) -> datetime:
    """Normalise a (possibly naive) datetime to an aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _week_start(value: datetime) -> date:
    """Return the Monday (date) of the week containing ``value``."""
    day = value.date()
    return day - timedelta(days=day.weekday())


def get_application_stats(db: Session, user_id: int) -> dict:
    """Compute analytics over the user's applications for the dashboard.

    Pulls each application's ``status`` and ``created_at`` once, then derives
    headline KPIs (response/interview/offer rates), the status distribution,
    and weekly application activity. Rates are fractions in ``[0, 1]``.
    """
    rows = (
        db.query(models.Application.status, models.Application.created_at)
        .filter(models.Application.user_id == user_id)
        .all()
    )

    total = len(rows)
    status_counts = Counter(row.status for row in rows)

    # Every known status appears (0 if unused) so the chart axis is stable;
    # any unexpected statuses are folded in so no data is silently dropped.
    by_status: dict[str, int] = {s: status_counts.get(s, 0) for s in STATUS_ORDER}
    for status_value, count in status_counts.items():
        by_status.setdefault(status_value, count)

    applied = status_counts.get("applied", 0)
    offers = status_counts.get("offer", 0)
    interviewing_or_past = status_counts.get("interview", 0) + offers
    # "Responded" = anything that moved beyond the initial applied state.
    responded = total - applied
    # "Active" = still in play (not a terminal offer or rejection).
    active = sum(
        count
        for status_value, count in status_counts.items()
        if status_value not in ("offer", "rejected")
    )

    def rate(numerator: int) -> float:
        return round(numerator / total, 4) if total else 0.0

    # Weekly application activity for the last WEEKS_OF_HISTORY weeks.
    now = datetime.now(timezone.utc)
    current_week = now.date() - timedelta(days=now.date().weekday())
    week_starts = [
        current_week - timedelta(weeks=offset)
        for offset in range(WEEKS_OF_HISTORY - 1, -1, -1)
    ]
    week_counts: Counter = Counter()
    week_ago = now - timedelta(days=7)
    this_week = 0
    for row in rows:
        if row.created_at is None:
            continue
        created = _as_utc(row.created_at)
        week_counts[_week_start(created)] += 1
        if created >= week_ago:
            this_week += 1
    weekly = [
        {"week": ws.isoformat(), "count": week_counts.get(ws, 0)} for ws in week_starts
    ]

    return {
        "total": total,
        "by_status": by_status,
        "active": active,
        "responded": responded,
        "offers": offers,
        "this_week": this_week,
        "response_rate": rate(responded),
        "interview_rate": rate(interviewing_or_past),
        "offer_rate": rate(offers),
        "weekly": weekly,
    }
