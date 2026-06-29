"""End-to-end tests for the applications API."""


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_create_application(client):
    res = client.post("/applications", json={"company": "Acme", "position": "SWE Intern"})
    assert res.status_code == 201
    body = res.json()
    assert body["company"] == "Acme"
    assert body["position"] == "SWE Intern"
    assert body["status"] == "applied"
    assert "id" in body


def test_list_applications(client):
    client.post("/applications", json={"company": "Acme", "position": "SWE"})
    client.post("/applications", json={"company": "Globex", "position": "ML"})
    res = client.get("/applications")
    assert res.status_code == 200
    companies = {a["company"] for a in res.json()}
    assert companies == {"Acme", "Globex"}


def test_get_application(client):
    created = client.post("/applications", json={"company": "Acme", "position": "SWE"}).json()
    res = client.get(f"/applications/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_update_application(client):
    created = client.post("/applications", json={"company": "Acme", "position": "SWE"}).json()
    res = client.patch(f"/applications/{created['id']}", json={"status": "interview"})
    assert res.status_code == 200
    assert res.json()["status"] == "interview"


def test_delete_application(client):
    created = client.post("/applications", json={"company": "Acme", "position": "SWE"}).json()
    assert client.delete(f"/applications/{created['id']}").status_code == 204
    assert client.get(f"/applications/{created['id']}").status_code == 404


def test_get_missing_application_returns_404(client):
    assert client.get("/applications/9999").status_code == 404
