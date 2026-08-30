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


def test_api_probes_endpoint_exists():
    r = client.get("/api/probes")
    assert r.status_code == 200
    data = r.get_json()
    assert "probes" in data
    # absent on CI (no service-probe state there) -> empty, not an error
    assert isinstance(data["probes"], dict)


def test_api_probes_serves_status_json(tmp_path, monkeypatch):
    import json as _json
    status = {"generated": "2026-08-27T03:00:00+00:00",
              "probes": {"portal": {"kind": "http", "status": "up",
                                    "latency_ms": 3}}}
    monkeypatch.setattr(hub, "PROBE_STATUS", tmp_path / "status.json")
    (tmp_path / "status.json").write_text(_json.dumps(status))
    data = client.get("/api/probes").get_json()
    assert data["probes"]["portal"]["status"] == "up"


def test_api_chaos_endpoint_exists():
    r = client.get("/api/chaos")
    assert r.status_code == 200
    data = r.get_json()
    assert "drills" in data
    # absent on CI (no chaos-drill state there) -> empty, not an error
    assert isinstance(data["drills"], dict)


def test_api_chaos_serves_status_json(tmp_path, monkeypatch):
    import json as _json
    status = {"generated": "2026-08-30T04:45:00+00:00",
              "last_run": "2026-08-30T04:45:00+00:00",
              "drills": {"ntfy-auth": {"result": "pass",
                                       "detail": "denied+accepted",
                                       "at": "2026-08-30T04:45:05+00:00"}}}
    monkeypatch.setattr(hub, "CHAOS_STATUS", tmp_path / "status.json")
    (tmp_path / "status.json").write_text(_json.dumps(status))
    data = client.get("/api/chaos").get_json()
    assert data["drills"]["ntfy-auth"]["result"] == "pass"
    assert data["last_run"].startswith("2026-08-30")
