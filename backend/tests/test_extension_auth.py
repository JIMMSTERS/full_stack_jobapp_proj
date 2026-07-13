"""Tests for browser-extension authentication (Bearer token + token minting)."""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def real_auth_client():
    """A TestClient using the real auth dependency plus a seeded user/session.

    Yields ``(client, token)`` where ``token`` is a valid, unexpired session
    token that can be sent as ``Authorization: Bearer <token>``.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    seed = TestingSession()
    user = models.User(google_sub="ext-sub", email="ext@example.com", name="Ext User")
    seed.add(user)
    seed.commit()
    seed.refresh(user)
    session = models.Session(
        token="valid-ext-token",
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    seed.add(session)
    seed.commit()
    seed.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client, "valid-ext-token"
    app.dependency_overrides.clear()


def test_bearer_token_authenticates(real_auth_client):
    client, token = real_auth_client
    resp = client.get("/applications", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_bearer_token_can_create_application(real_auth_client):
    client, token = real_auth_client
    resp = client.post(
        "/applications",
        headers={"Authorization": f"Bearer {token}"},
        json={"company": "Acme", "position": "SWE Intern"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["company"] == "Acme"
    assert body["position"] == "SWE Intern"


def test_missing_and_invalid_bearer_are_rejected(real_auth_client):
    client, _ = real_auth_client
    assert client.get("/applications").status_code == 401
    bad = client.get("/applications", headers={"Authorization": "Bearer nope"})
    assert bad.status_code == 401
    malformed = client.get("/applications", headers={"Authorization": "Basic abc"})
    assert malformed.status_code == 401


def test_extension_token_endpoint_mints_usable_token(real_auth_client):
    client, token = real_auth_client
    minted = client.post(
        "/auth/extension-token", headers={"Authorization": f"Bearer {token}"}
    )
    assert minted.status_code == 200
    new_token = minted.json()["token"]
    assert new_token and new_token != token

    # The freshly minted token authenticates on its own.
    resp = client.get(
        "/applications", headers={"Authorization": f"Bearer {new_token}"}
    )
    assert resp.status_code == 200


def test_extension_token_requires_auth(real_auth_client):
    client, _ = real_auth_client
    assert client.post("/auth/extension-token").status_code == 401
