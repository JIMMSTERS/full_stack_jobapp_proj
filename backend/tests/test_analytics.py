"""Tests for the timeline-derived conversion funnel + response-time analytics."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, models
from app.database import Base

BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    user = models.User(google_sub="sub", email="me@example.com", name="Me")
    session.add(user)
    session.commit()
    session.refresh(user)
    session.user_id = user.id  # type: ignore[attr-defined]
    try:
        yield session
    finally:
        session.close()


def _app_with_events(db, transitions: list[tuple[str | None, str, int]]):
    """Create an application plus a timeline. Each tuple is (from, to, day_offset)."""
    app = models.Application(user_id=db.user_id, company="Acme", position="SWE")
    db.add(app)
    db.flush()
    for from_status, to_status, day in transitions:
        db.add(
            models.StatusEvent(
                application_id=app.id,
                from_status=from_status,
                to_status=to_status,
                created_at=BASE + timedelta(days=day),
            )
        )
    db.commit()


def test_analytics_endpoint_empty(client):
    """Routing works (declared before /{id}) and empty state is well-formed."""
    resp = client.get("/applications/analytics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sample_size"] == 0
    assert [s["stage"] for s in body["funnel"]] == [
        "applied",
        "screening",
        "interview",
        "offer",
    ]
    assert body["median_days_to_response"] is None


def test_funnel_is_monotonic_and_timings(db):
    _app_with_events(db, [(None, "applied", 0)])  # applied only
    _app_with_events(db, [(None, "applied", 0), ("applied", "interview", 3)])
    _app_with_events(
        db,
        [(None, "applied", 0), ("applied", "interview", 2), ("interview", "offer", 5)],
    )
    _app_with_events(db, [(None, "applied", 0), ("applied", "rejected", 1)])

    analytics = crud.get_application_analytics(db, db.user_id)

    assert analytics["sample_size"] == 4
    reached = {s["stage"]: s["reached"] for s in analytics["funnel"]}
    assert reached == {"applied": 4, "screening": 2, "interview": 2, "offer": 1}

    # Responses: 3d, 2d, 1d -> median 2.0. Offer: only the day-5 one.
    assert analytics["median_days_to_response"] == 2.0
    assert analytics["median_days_to_offer"] == 5.0


def test_rejection_without_interview_only_reaches_applied(db):
    _app_with_events(db, [(None, "applied", 0), ("applied", "rejected", 2)])

    analytics = crud.get_application_analytics(db, db.user_id)
    reached = {s["stage"]: s["reached"] for s in analytics["funnel"]}
    assert reached["applied"] == 1
    assert reached["interview"] == 0
    assert analytics["median_days_to_offer"] is None
