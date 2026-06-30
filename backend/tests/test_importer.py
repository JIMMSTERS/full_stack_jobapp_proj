"""Tests for the Gmail -> Application importer (grouping, create, update, dedupe)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, importer, models
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


def _msg(id, thread_id, internal_date, subject, sender, snippet=""):
    return {
        "id": id,
        "thread_id": thread_id,
        "internal_date": internal_date,
        "subject": subject,
        "from": sender,
        "snippet": snippet,
        "date": "",
    }


def test_import_creates_application_from_job_email(db):
    messages = [
        _msg(
            "1", "t1", 1000,
            "Thank you for applying to Stripe",
            "Stripe Recruiting <no-reply@greenhouse.io>",
            "We received your application for the Backend Engineer role.",
        )
    ]
    result = importer.import_messages(db, db.user_id, messages)
    assert result == {"created": 1, "updated": 0, "unchanged": 0}

    apps = crud.get_applications(db, db.user_id)
    assert len(apps) == 1
    assert apps[0].company == "Stripe"
    assert apps[0].position == "Backend Engineer"
    assert apps[0].status == "applied"
    assert apps[0].source == "gmail"
    assert apps[0].gmail_thread_id == "t1"


def test_non_job_email_is_skipped(db):
    messages = [
        _msg("1", "t1", 1000, "Your Amazon order shipped", "ship@amazon.com")
    ]
    result = importer.import_messages(db, db.user_id, messages)
    assert result == {"created": 0, "updated": 0, "unchanged": 0}
    assert crud.get_applications(db, db.user_id) == []


def test_same_thread_is_deduped_and_status_advances(db):
    first = [
        _msg(
            "1", "t1", 1000,
            "Thanks for applying to Datadog",
            "Datadog <jobs@datadog.com>",
            "We received your application for the Software Engineer role.",
        )
    ]
    importer.import_messages(db, db.user_id, first)

    # A later email in the same thread invites an interview.
    second = [
        _msg(
            "2", "t1", 2000,
            "Next steps with Datadog",
            "Datadog <jobs@datadog.com>",
            "We'd like to schedule a call. What's your availability for an interview?",
        )
    ]
    result = importer.import_messages(db, db.user_id, second)
    assert result == {"created": 0, "updated": 1, "unchanged": 0}

    apps = crud.get_applications(db, db.user_id)
    assert len(apps) == 1
    assert apps[0].status == "interview"


def test_reimport_same_messages_is_unchanged(db):
    messages = [
        _msg(
            "1", "t1", 1000,
            "Thanks for applying to Notion",
            "Notion <recruiting@notion.so>",
            "We received your application for the Frontend Engineer role.",
        )
    ]
    importer.import_messages(db, db.user_id, messages)
    result = importer.import_messages(db, db.user_id, messages)
    assert result == {"created": 0, "updated": 0, "unchanged": 1}
    assert len(crud.get_applications(db, db.user_id)) == 1


def test_two_threads_create_two_applications(db):
    messages = [
        _msg("1", "t1", 1000, "Applying to Stripe",
             "Stripe <jobs@stripe.com>", "your application for the Backend role"),
        _msg("2", "t2", 1500, "Applying to Airbnb",
             "Airbnb <jobs@airbnb.com>", "your application for the iOS Engineer role"),
    ]
    result = importer.import_messages(db, db.user_id, messages)
    assert result["created"] == 2
    companies = {a.company for a in crud.get_applications(db, db.user_id)}
    assert companies == {"Stripe", "Airbnb"}


def test_latest_email_in_thread_sets_status(db):
    # Out-of-order arrival: the rejection (newer) should win over the interview.
    messages = [
        _msg("2", "t1", 3000, "Update from Airbnb",
             "Airbnb <jobs@airbnb.com>",
             "Unfortunately we will not be moving forward."),
        _msg("1", "t1", 1000, "Interview with Airbnb",
             "Airbnb <jobs@airbnb.com>",
             "Let's schedule an interview for the role."),
    ]
    importer.import_messages(db, db.user_id, messages)
    apps = crud.get_applications(db, db.user_id)
    assert len(apps) == 1
    assert apps[0].status == "rejected"
