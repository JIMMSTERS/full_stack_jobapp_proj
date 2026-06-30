"""Tests for the optional follow-up date on applications."""


def test_create_with_follow_up_date(client):
    res = client.post(
        "/applications",
        json={"company": "Acme", "position": "SWE", "follow_up_date": "2026-07-15"},
    )
    assert res.status_code == 201
    assert res.json()["follow_up_date"] == "2026-07-15"


def test_follow_up_defaults_to_null(client):
    res = client.post("/applications", json={"company": "Acme", "position": "SWE"})
    assert res.status_code == 201
    assert res.json()["follow_up_date"] is None


def test_set_follow_up_via_update(client):
    created = client.post(
        "/applications", json={"company": "Acme", "position": "SWE"}
    ).json()
    res = client.patch(
        f"/applications/{created['id']}", json={"follow_up_date": "2026-08-01"}
    )
    assert res.status_code == 200
    assert res.json()["follow_up_date"] == "2026-08-01"


def test_clear_follow_up_via_update(client):
    created = client.post(
        "/applications",
        json={"company": "Acme", "position": "SWE", "follow_up_date": "2026-08-01"},
    ).json()
    res = client.patch(
        f"/applications/{created['id']}", json={"follow_up_date": None}
    )
    assert res.status_code == 200
    assert res.json()["follow_up_date"] is None


def test_setting_follow_up_does_not_add_timeline_event(client):
    created = client.post(
        "/applications", json={"company": "Acme", "position": "SWE"}
    ).json()
    client.patch(f"/applications/{created['id']}", json={"follow_up_date": "2026-08-01"})
    events = client.get(f"/applications/{created['id']}/events").json()
    assert len(events) == 1
