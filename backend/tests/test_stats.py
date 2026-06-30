"""Tests for the analytics dashboard aggregation (crud.get_application_stats)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, models
from app.database import Base


@pytest.fixture()
def db():
    """A fresh in-memory DB session seeded with one user."""
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


def _add(db, status):
    db.add(
        models.Application(
            user_id=db.user_id, company="Acme", position="SWE", status=status
        )
    )
    db.commit()


def test_stats_empty(db):
    stats = crud.get_application_stats(db, db.user_id)
    assert stats["total"] == 0
    assert stats["response_rate"] == 0.0
    assert stats["by_status"]["applied"] == 0
    assert len(stats["weekly"]) == crud.WEEKS_OF_HISTORY


def test_stats_counts_and_rates(db):
    for status in ["applied", "applied", "interview", "offer", "rejected"]:
        _add(db, status)

    stats = crud.get_application_stats(db, db.user_id)

    assert stats["total"] == 5
    assert stats["by_status"]["applied"] == 2
    assert stats["by_status"]["interview"] == 1
    assert stats["offers"] == 1
    # responded = anything past "applied" => 3 of 5
    assert stats["responded"] == 3
    assert stats["response_rate"] == 0.6
    # interview rate = (interview + offer) / total = 2 / 5
    assert stats["interview_rate"] == 0.4
    assert stats["offer_rate"] == 0.2
    # active = not offer, not rejected => applied(2) + interview(1) = 3
    assert stats["active"] == 3


def test_stats_isolated_per_user(db):
    other = models.User(google_sub="sub2", email="x@example.com")
    db.add(other)
    db.commit()
    db.refresh(other)
    db.add(
        models.Application(
            user_id=other.id, company="Other", position="SWE", status="offer"
        )
    )
    db.commit()
    _add(db, "applied")

    stats = crud.get_application_stats(db, db.user_id)
    assert stats["total"] == 1
    assert stats["offers"] == 0


def test_stats_weekly_recent_activity(db):
    _add(db, "applied")
    stats = crud.get_application_stats(db, db.user_id)
    # The most recent week bucket should hold the just-created application.
    assert stats["weekly"][-1]["count"] == 1
    assert stats["this_week"] == 1
