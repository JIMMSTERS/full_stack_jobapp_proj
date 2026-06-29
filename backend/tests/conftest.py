"""Shared pytest fixtures: an isolated in-memory DB and test client."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    """A TestClient backed by a fresh in-memory SQLite database per test.

    Authentication is bypassed via a dependency override that returns a
    pre-seeded test user, so application tests can focus on CRUD behavior.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Seed a test user that owns the applications created during tests.
    seed_db = TestingSession()
    test_user = models.User(
        google_sub="test-sub", email="test@example.com", name="Test User"
    )
    seed_db.add(test_user)
    seed_db.commit()
    seed_db.refresh(test_user)
    test_user_id = test_user.id
    seed_db.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user():
        db = TestingSession()
        try:
            return db.get(models.User, test_user_id)
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def unauthenticated_client():
    """A TestClient with a real (non-overridden) auth dependency."""
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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
