"""Tests for the application activity timeline (status events)."""


def _create(client, **overrides):
    payload = {"company": "Acme", "position": "SWE Intern", "status": "applied"}
    payload.update(overrides)
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    return response.json()


def test_creating_application_records_initial_event(client):
    app = _create(client)

    events = client.get(f"/applications/{app['id']}/events").json()

    assert len(events) == 1
    assert events[0]["from_status"] is None
    assert events[0]["to_status"] == "applied"


def test_status_change_appends_event(client):
    app = _create(client)

    client.patch(f"/applications/{app['id']}", json={"status": "interview"})

    events = client.get(f"/applications/{app['id']}/events").json()
    assert len(events) == 2
    assert events[0]["to_status"] == "applied"
    assert events[1]["from_status"] == "applied"
    assert events[1]["to_status"] == "interview"


def test_non_status_update_does_not_add_event(client):
    app = _create(client)

    client.patch(f"/applications/{app['id']}", json={"notes": "called recruiter"})

    events = client.get(f"/applications/{app['id']}/events").json()
    assert len(events) == 1


def test_setting_same_status_does_not_add_event(client):
    app = _create(client)

    client.patch(f"/applications/{app['id']}", json={"status": "applied"})

    events = client.get(f"/applications/{app['id']}/events").json()
    assert len(events) == 1


def test_events_for_missing_application_returns_404(client):
    response = client.get("/applications/999999/events")
    assert response.status_code == 404
