/* Project Hub - live status rendering. */
async function fetchStatus() {
    try {
        const r = await fetch("/api/status");
        return await r.json();
    } catch (e) {
        return null;
    }
}

function dot(state) {
    const cls = state === true || state === "active" ? "on"
              : state === false || state === "inactive" || state === "failed" ? "off"
              : "na";
    return `<span class="dot ${cls}" title="${state}"></span>`;
}

function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
}

function renderProjects(projects) {
    const el = document.getElementById("cards");
    // Build links against the host the hub was opened with, so IP access
    // (http://192.168.0.7:8090) and hostname access both work.
    const base = `${location.protocol}//${location.hostname}`;
    el.innerHTML = projects.map(p => {
        const url = p.port ? `${base}:${p.port}` : null;
        const svcs = Object.entries(p.services || {}).map(([n, st]) =>
            `<span class="chip ${st}">${esc(n)}</span>`).join("");
        const link = url
            ? `<a href="${esc(url)}" target="_blank">Open ↗</a>`
            : `<span class="nolink">no web UI</span>`;
        const status = p.online !== null && p.online !== undefined
            ? dot(p.online)
            : (p.healthy !== null ? dot(p.healthy) : dot(null));
        return `
        <div class="card">
            <div class="card-head">
                <div>
                    <h3>${esc(p.name)}</h3>
                    <div class="dir">${esc(p.dir)}</div>
                </div>
                ${status}
            </div>
            <p>${esc(p.desc)}</p>
            <div class="chips">${svcs}</div>
            <div class="card-actions">${link}</div>
        </div>`;
    }).join("");
}

function renderServices(services) {
    const el = document.getElementById("services");
    el.innerHTML = services.map(s => `
        <div class="svc">
            ${dot(s.state)}
            <span class="name">${esc(s.name)}</span>
            <span class="group">${esc(s.group)}</span>
        </div>`).join("");
}

function renderSys(s) {
    document.getElementById("sys-time").textContent = s.time;
    document.getElementById("sys-uptime").textContent = "up " + s.uptime;
    const temp = document.getElementById("sys-temp");
    temp.textContent = s.temp;
    temp.className = parseFloat(s.temp) > 70 ? "hot" : "";
    document.getElementById("sys-disk").textContent =
        s.disk ? `disk ${s.disk}` : "";
}

async function refresh() {
    const s = await fetchStatus();
    if (!s) return;
    renderSys(s);
    renderProjects(s.projects);
    renderServices(s.services);
}

refresh();
setInterval(refresh, 10000);
