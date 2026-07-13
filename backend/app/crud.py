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


# Pipeline milestones for the conversion funnel, in order. ``rejected`` is a
# terminal off-pipeline state and is excluded from progression.
FUNNEL_STAGES = ["applied", "screening", "interview", "offer"]
_STAGE_RANK = {stage: rank for rank, stage in enumerate(FUNNEL_STAGES)}


def _median(values: list[float]) -> float | None:
    """Return the median of ``values`` rounded to 1 dp, or None if empty."""
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        median = ordered[mid]
    else:
        median = (ordered[mid - 1] + ordered[mid]) / 2
    return round(median, 1)


def get_application_analytics(db: Session, user_id: int) -> dict:
    """Derive a conversion funnel and response-time metrics from the timeline.

    Uses the immutable ``status_events`` history: for each application we take
    the furthest pipeline stage it ever reached (ignoring rejections) to build a
    monotonic funnel, and measure elapsed days from the first event to the first
    response (any later event) and to an offer.
    """
    events = (
        db.query(
            models.StatusEvent.application_id,
            models.StatusEvent.to_status,
            models.StatusEvent.created_at,
        )
        .join(models.Application, models.Application.id == models.StatusEvent.application_id)
        .filter(models.Application.user_id == user_id)
        .order_by(models.StatusEvent.created_at, models.StatusEvent.id)
        .all()
    )

    by_app: dict[int, list] = {}
    for row in events:
        by_app.setdefault(row.application_id, []).append(row)

    total = len(by_app)
    reached = {stage: 0 for stage in FUNNEL_STAGES}
    days_to_response: list[float] = []
    days_to_offer: list[float] = []

    for app_events in by_app.values():
        ranks = [_STAGE_RANK[e.to_status] for e in app_events if e.to_status in _STAGE_RANK]
        furthest = max(ranks) if ranks else 0
        for stage in FUNNEL_STAGES:
            if furthest >= _STAGE_RANK[stage]:
                reached[stage] += 1

        first = _as_utc(app_events[0].created_at)
        if len(app_events) > 1:
            second = _as_utc(app_events[1].created_at)
            days_to_response.append((second - first).total_seconds() / 86400)
        offer_event = next((e for e in app_events if e.to_status == "offer"), None)
        if offer_event is not None:
            offer_at = _as_utc(offer_event.created_at)
            days_to_offer.append((offer_at - first).total_seconds() / 86400)

    funnel = [
        {
            "stage": stage,
            "reached": reached[stage],
            "conversion": round(reached[stage] / total, 4) if total else 0.0,
        }
        for stage in FUNNEL_STAGES
    ]

    return {
        "sample_size": total,
        "funnel": funnel,
        "median_days_to_response": _median(days_to_response),
        "median_days_to_offer": _median(days_to_offer),
    }
