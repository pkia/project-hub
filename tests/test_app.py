"""API smoke tests using Flask's test client.

On a CI runner none of the tracked services or ports exist; the hub must
still render and report everything as offline rather than error out.
"""
import app as hub

client = hub.app.test_client()


def test_index_serves_page():
    r = client.get("/")
    assert r.status_code == 200
    assert b"Project Hub" in r.data


def test_api_status_shape():
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.get_json()
    for key in ("time", "uptime", "temp", "disk", "services", "projects"):
        assert key in data


def test_projects_have_cards():
    projects = client.get("/api/status").get_json()["projects"]
    assert len(projects) >= 5
    for p in projects:
        assert {"name", "desc", "dir", "online", "services"} <= set(p)


def test_ports_report_bool_regardless_of_host():
    # Whether ports are open depends on the host (Pi: live, CI: closed) -
    # the contract is a clean boolean either way, never an error.
    projects = client.get("/api/status").get_json()["projects"]
    with_ports = [p for p in projects if p["port"]]
    assert with_ports and all(isinstance(p["online"], bool) for p in with_ports)


def test_services_table():
    services = client.get("/api/status").get_json()["services"]
    assert len(services) >= 8
    assert all(s["state"] in ("active", "inactive", "unknown", "failed")
               for s in services)
