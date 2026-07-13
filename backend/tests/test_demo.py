"""Tests for the public demo login (seeded throwaway accounts)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import config
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def demo_client():
    """A TestClient with the real auth stack and a fresh in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_demo_login_creates_seeded_account(demo_client):
    resp = demo_client.post("/auth/demo")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_demo"] is True
    assert body["name"] == "Demo User"

    # The session cookie is now stored on the client; the seeded apps are visible.
    apps = demo_client.get("/applications")
    assert apps.status_code == 200
    assert len(apps.json()) == 8


def test_demo_account_has_stats_and_timeline(demo_client):
    demo_client.post("/auth/demo")

    stats = demo_client.get("/applications/stats").json()
    assert stats["total"] == 8
    assert stats["offers"] == 1

    first_id = demo_client.get("/applications").json()[0]["id"]
    events = demo_client.get(f"/applications/{first_id}/events").json()
    assert len(events) >= 1
    assert events[0]["from_status"] is None  # first event is the initial "applied"


def test_demo_accounts_are_isolated(demo_client):
    demo_client.post("/auth/demo")
    first_user = demo_client.get("/auth/me").json()

    # A second demo login replaces the cookie with a different account.
    demo_client.post("/auth/demo")
    second_user = demo_client.get("/auth/me").json()
    assert first_user["id"] != second_user["id"]


def test_demo_login_disabled_returns_404(demo_client, monkeypatch):
    monkeypatch.setattr(config, "DEMO_MODE_ENABLED", False)
    assert demo_client.post("/auth/demo").status_code == 404
