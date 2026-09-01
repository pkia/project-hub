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

async function fetchProbes() {
    try {
        const r = await fetch("/api/probes");
        return await r.json();
    } catch (e) {
        return null;
    }
}

async function fetchChaos() {
    try {
        const r = await fetch("/api/chaos");
        return await r.json();
    } catch (e) {
        return null;
    }
}

async function fetchHeals() {
    try {
        const r = await fetch("/api/heals");
        return await r.json();
    } catch (e) {
        return null;
    }
}

function renderProbes(data) {
    const panel = document.getElementById("probes-panel");
    const entries = Object.entries((data && data.probes) || {});
    if (!entries.length) { panel.hidden = true; return; }
    panel.hidden = false;
    document.getElementById("probes").innerHTML = entries.map(([name, p]) => {
        const lat = p.status === "up" && p.latency_ms != null
            ? ` <span class="muted">${p.latency_ms} ms</span>` : "";
        const err = p.error
            ? ` <span class="muted" title="${esc(p.error)}">·</span>` : "";
        return `
        <div class="svc">
            ${dot(p.status === "up")}
            <span class="name">${esc(name)}</span>
            <span class="group">${esc(p.kind)}${lat}${err}</span>
        </div>`;
    }).join("");
    const gen = data.generated ? `· swept ${esc(data.generated)}Z`.replace("T", " ") : "";
    document.getElementById("probes-age").textContent = gen;
}

function renderChaos(data) {
    const panel = document.getElementById("chaos-panel");
    const entries = Object.entries((data && data.drills) || {});
    if (!entries.length) { panel.hidden = true; return; }
    panel.hidden = false;
    document.getElementById("chaos").innerHTML = entries.map(([name, d]) => {
        const ok = d.result === "pass";
        const cls = ok ? "on" : d.result === "skip" ? "na" : "off";
        const at = d.at ? ` <span class="muted">${esc(d.at)}Z</span>`.replace("T", " ") : "";
        const note = d.detail
            ? ` <span class="muted" title="${esc(d.detail)}">${esc(d.result)}</span>` : "";
        return `
        <div class="svc">
            <span class="dot ${cls}" title="${esc(d.result)}"></span>
            <span class="name">${esc(name)}</span>
            <span class="group">${at}${note}</span>
        </div>`;
    }).join("");
    const gen = data.last_run ? `· drilled ${esc(data.last_run)}Z`.replace("T", " ") : "";
    document.getElementById("chaos-age").textContent = gen;
}

function renderHeals(data) {
    const panel = document.getElementById("heals-panel");
    const heals = (data && Array.isArray(data.heals)) ? data.heals : [];
    if (!heals.length) { panel.hidden = true; return; }
    panel.hidden = false;
    document.getElementById("heals").innerHTML = heals.slice(-8).reverse().map(h => {
        const at = h.ts ? ` <span class="muted">${esc(h.ts)}</span>`.replace("T", " ") : "";
        const what = h.what ? esc(h.what.replace(/-/g, " ")) : "heal";
        const detail = h.detail
            ? ` <span class="muted" title="${esc(h.detail)}">${esc(h.detail)}</span>` : "";
        return `
        <div class="svc">
            <span class="dot on" title="self-healed"></span>
            <span class="name">${what}</span>
            <span class="group">${at}${detail}</span>
        </div>`;
    }).join("");
    const gen = data.updated ? `· healed ${esc(data.updated)}Z`.replace("T", " ") : "";
    document.getElementById("heals-age").textContent = gen;
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
    renderProbes(await fetchProbes());
    renderChaos(await fetchChaos());
    renderHeals(await fetchHeals());
}

refresh();
setInterval(refresh, 10000);
