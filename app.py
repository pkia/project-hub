#!/usr/bin/env python3
"""Project Hub - one-page portal to every project and web UI on dunbot."""
import socket
import subprocess
import time

from flask import Flask, jsonify, render_template

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

HOST = "dunbot"

# Web UIs and code projects shown as cards on the home page.
# "port" is turned into a link client-side against whichever host the
# visitor opened the hub with, so IP and hostname access both work.
PROJECTS = [
    {
        "name": "Maritime Dashboard",
        "port": 8000,
        "desc": "AIS ship tracker + NOAA weather satellite images (kiosk app).",
        "dir": "/home/ev/maritime-dashboard",
        "services": ["maritime-dashboard", "noaa-scheduler", "online-ships"],
    },
    {
        "name": "AIS-catcher",
        "port": 8080,
        "desc": "Live AIS receiver map from the RTL-SDR dongle.",
        "dir": "/home/ev/AIS-catcher-src",
        "services": ["ais-catcher", "sdr-monitor"],
    },
    {
        "name": "Satellite Audio",
        "port": 8085,
        "desc": "Live audio tap of the NOAA satellite receiver.",
        "dir": "/home/ev/apps/sat-audio",
        "services": ["sat-audio"],
    },
    {
        "name": "AdGuard Home",
        "port": 3001,
        "desc": "Network-wide DNS ad blocking for the LAN.",
        "dir": "/home/ev/apps/AdGuardHome",
        "services": ["AdGuardHome"],
    },
    {
        "name": "AIS Analysis",
        "port": None,
        "desc": "Scripts for capturing and demodulating raw AIS samples "
                "(rtl_ais experiments, logs).",
        "dir": "/home/ev/ais_analysis",
        "services": [],
    },
    {
        "name": "AIS-catcher Source",
        "port": None,
        "desc": "Local source tree of the AIS-catcher receiver (C++).",
        "dir": "/home/ev/AIS-catcher-src",
        "services": [],
    },
]

# Every unit tracked in the status table, with the project it belongs to.
SERVICES = [
    ("maritime-dashboard", "Maritime Dashboard"),
    ("noaa-scheduler", "Maritime Dashboard"),
    ("online-ships", "Maritime Dashboard"),
    ("ais-catcher", "AIS-catcher"),
    ("sdr-monitor", "AIS-catcher"),
    ("sat-audio", "Satellite Audio"),
    ("AdGuardHome", "AdGuard Home"),
    ("ais-kiosk", "Kiosk Screen"),
    ("tailscaled", "Remote Access"),
]


def sh(cmd, timeout=5):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def port_open(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def service_state(unit):
    state = sh(f"systemctl is-active {unit} 2>/dev/null") or "unknown"
    if state not in ("active", "inactive", "failed"):
        state = "inactive"
    return state


def read_temp():
    try:
        t = int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000.0
        return f"{t:.1f}°C"
    except Exception:
        return "n/a"


@app.route("/")
def index():
    return render_template("index.html", host=HOST)


@app.route("/api/status")
def api_status():
    services = {name: service_state(name) for name, _ in SERVICES}
    projects = []
    for p in PROJECTS:
        entry = {
            "name": p["name"],
            "port": p["port"],
            "desc": p["desc"],
            "dir": p["dir"],
            "online": port_open(p["port"]) if p["port"] else None,
            "services": {s: services.get(s, "unknown") for s in p["services"]},
        }
        entry["healthy"] = (
            all(v == "active" for v in entry["services"].values())
            if entry["services"] else None
        )
        projects.append(entry)

    # Disk usage of the whole card collection, for the footer.
    disk = sh("df -h / --output=pcent | tail -1").strip()
    return jsonify({
        "time": time.strftime("%H:%M:%S"),
        "uptime": sh("uptime -p").replace("up ", "") or "n/a",
        "temp": read_temp(),
        "disk": disk,
        "services": [{"name": n, "group": g, "state": services[n]}
                     for n, g in SERVICES],
        "projects": projects,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8090)