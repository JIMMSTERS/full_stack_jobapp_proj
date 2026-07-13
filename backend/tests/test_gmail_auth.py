"""Tests for the decoupled login vs. opt-in Gmail authorization."""

from app import models


def test_me_reports_gmail_not_connected_by_default(client):
    """A freshly signed-in user (no Gmail tokens) reports gmail_connected=False."""
    resp = client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["gmail_connected"] is False


def test_gmail_connect_requires_authentication(unauthenticated_client):
    """The Gmail opt-in flow rejects anonymous callers before touching Google."""
    resp = unauthenticated_client.get("/auth/gmail/connect", follow_redirects=False)
    assert resp.status_code == 401


def test_gmail_connected_property_tracks_refresh_token():
    """The model property flips once a Gmail refresh token is stored."""
    user = models.User(google_sub="sub-1", email="a@example.com")
    assert user.gmail_connected is False
    user.google_refresh_token = "a-refresh-token"
    assert user.gmail_connected is True
