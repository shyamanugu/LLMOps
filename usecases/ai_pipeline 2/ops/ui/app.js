const API = "http://127.0.0.1:8000/api";
const view = document.getElementById("view");
const $ = (h) => { const t = document.createElement("template"); t.innerHTML = h.trim(); return t.content.firstChild; };
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (v, d = 0) => (v == null ? "—" : (v * 100).toFixed(d) + "%");
const num = (v) => (v ?? 0).toLocaleString("en-US");
const money = (v) => "$" + (v ?? 0).toFixed((v && v < 1) ? 4 : 2);
// small ⓘ with a hover tooltip, to explain a metric during a client demo
const info = (tip) => `<span class="info" data-tip="${esc(tip)}">i</span>`;
const TIP = {
  calls: "One LLM call = one model request. A run = 12 denoise + 12 analysis + 5 summary + 5 individual-metrics calls (KPI is pure aggregation, no LLM) = 34.",
  intok: "Total prompt tokens sent to the model across all calls (system prompt + transcript).",
  outtok: "Total tokens the model generated across all calls (the structured analysis / reflections).",
  cost: "Estimated spend = tokens × per-1k rate from pricing.yaml. Rates here are ILLUSTRATIVE placeholders for the demo — swap in AFNI's contracted rates.",
  latency: "Average wall-clock time per model call. Higher for analysis/summary (larger prompts) than denoise.",
  flags: "Times a guardrail fired (e.g. PII detected). Flagged = recorded for audit but allowed through; blocked = stopped.",
  errors: "Calls that failed (timeout, content filter, bad response). 0 is healthy.",
  agents: "Distinct agents that had calls analysed and received an AI coaching reflection this run.",
  passrate: "Share of golden-dataset cases the prompt+model passed. The evaluation gate blocks a change if this drops below the threshold.",
};

async function api(path, opts) {
  const r = await fetch(API + path, opts);
  if (!r.ok) { let e = {}; try { e = await r.json(); } catch {} throw new Error(e.error || ("HTTP " + r.status)); }
  return r.json();
}
const post = (p, b) => api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });

/* ── inline SVG charts (no libraries, no CDN) ───────────────────────────── */
const PAL = ["#3b74c4", "#2bb8a3", "#7a6cd6", "#c98a2b", "#cc5b5b", "#3f9d6b"];
function svgBars(data, { h = 190, unit = "", color = "#3b74c4", fmt = (v) => v } = {}) {
  const w = Math.max(260, data.length * 74), pad = 30, bw = (w - pad * 2) / data.length * 0.6;
  const max = Math.max(1, ...data.map(d => d.v));
  const bars = data.map((d, i) => {
    const x = pad + (i + 0.2) * ((w - pad * 2) / data.length);
    const bh = (d.v / max) * (h - 42), y = h - 22 - bh;
    return `<rect x="${x}" y="${y}" width="${bw}" height="${Math.max(1, bh)}" rx="4" fill="${color}"/>
      <text x="${x + bw / 2}" y="${y - 5}" font-size="10" fill="#64748b" text-anchor="middle">${fmt(d.v)}</text>
      <text x="${x + bw / 2}" y="${h - 6}" font-size="10" fill="#64748b" text-anchor="middle">${esc(d.k)}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" preserveAspectRatio="xMidYMid meet">${bars}</svg>`;
}
function svgHBars(data, { rowH = 30, unit = "%" } = {}) {
  const w = 320, lab = 130, max = Math.max(1, ...data.map(d => d.v)), h = data.length * rowH + 8;
  const rows = data.map((d, i) => {
    const y = i * rowH + 6, bw = (d.v / max) * (w - lab - 46);
    const col = unit === "%" ? (d.v >= 0.8 ? "#3f9d6b" : d.v >= 0.6 ? "#c98a2b" : "#cc5b5b") : "#3b74c4";
    const val = unit === "%" ? Math.round(d.v * 100) + "%" : num(d.v);
    return `<text x="0" y="${y + 15}" font-size="11.5" fill="#18222e">${esc(d.k)}</text>
      <rect x="${lab}" y="${y + 5}" width="${Math.max(2, bw)}" height="15" rx="4" fill="${col}"/>
      <text x="${lab + Math.max(2, bw) + 6}" y="${y + 16}" font-size="11" fill="#64748b">${val}</text>`;
  }).join("");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">${rows}</svg>`;
}
function svgLine(points, { h = 180, unit = "%" } = {}) {
  const w = Math.max(280, points.length * 60), pad = 34;
  const max = 1, min = 0, sx = (w - pad * 2) / Math.max(1, points.length - 1);
  const pts = points.map((p, i) => [pad + i * sx, h - 24 - (p.v - min) / (max - min) * (h - 44)]);
  const path = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  const dots = pts.map((p, i) => `<circle cx="${p[0]}" cy="${p[1]}" r="3.5" fill="#3b74c4"/>
    <text x="${p[0]}" y="${p[1] - 8}" font-size="10" fill="#64748b" text-anchor="middle">${Math.round(points[i].v * 100)}%</text>
    <text x="${p[0]}" y="${h - 6}" font-size="9.5" fill="#94a3b8" text-anchor="middle">${esc(points[i].k)}</text>`).join("");
  const grid = [0, .25, .5, .75, 1].map(g => { const y = h - 24 - g * (h - 44); return `<line x1="${pad}" y1="${y}" x2="${w - 8}" y2="${y}" stroke="#eef2f7"/>`; }).join("");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}">${grid}<path d="${path}" fill="none" stroke="#3b74c4" stroke-width="2.5"/>${dots}</svg>`;
}
function donut(passed, total) {
  const r = 52, c = 2 * Math.PI * r, frac = total ? passed / total : 0, col = frac >= 0.8 ? "#3f9d6b" : frac >= 0.5 ? "#c98a2b" : "#cc5b5b";
  return `<svg viewBox="0 0 130 130" width="130" height="130">
    <circle cx="65" cy="65" r="${r}" fill="none" stroke="#eef2f7" stroke-width="14"/>
    <circle cx="65" cy="65" r="${r}" fill="none" stroke="${col}" stroke-width="14" stroke-linecap="round"
      stroke-dasharray="${(frac * c).toFixed(1)} ${c}" transform="rotate(-90 65 65)"/>
    <text x="65" y="61" font-size="24" font-weight="700" fill="#18222e" text-anchor="middle">${Math.round(frac * 100)}%</text>
    <text x="65" y="80" font-size="11" fill="#64748b" text-anchor="middle">${passed}/${total} pass</text></svg>`;
}

/* ── shell / nav ────────────────────────────────────────────────────────── */
const TABS = [
  ["application", "📊", "Application"], ["playground", "🧪", "Playground"],
  ["evaluation", "✅", "Evaluation"], ["datasets", "📁", "Golden Datasets"],
  ["monitoring", "📈", "Monitoring"], ["feedback", "💬", "Feedback"], ["guardrails", "🛡", "Guardrails"],
];
let current = "application", HEALTH = {};

async function boot() {
  try { HEALTH = await api("/health"); }
  catch (e) {
    view.innerHTML = `<div class="card err">Cannot reach backend at <code>${API}</code>.<br>
      Start it: <code>python ops/start_backend.py</code><br><br>${esc(e.message)}</div>`;
    return;
  }
  const pill = document.getElementById("mode-pill");
  pill.textContent = (HEALTH.mode === "real" ? "● REAL DATA" : "● MOCK DATA");
  pill.className = "pill" + (HEALTH.mode === "real" ? " real" : "");
  document.getElementById("side-meta").innerHTML =
    `traces ${HEALTH.traces} · evals ${HEALTH.eval_runs}<br>feedback ${HEALTH.feedback} · guardrails ${HEALTH.guardrails}`;
  const nav = document.getElementById("nav");
  TABS.forEach(([id, ico, label]) => {
    const b = $(`<button data-id="${id}"><span class="ico">${ico}</span>${label}</button>`);
    b.onclick = () => { current = id; render(); };
    nav.appendChild(b);
  });
  render();
}
function render() {
  document.querySelectorAll(".nav button").forEach(t => t.classList.toggle("active", t.dataset.id === current));
  view.innerHTML = `<div class="loading">Loading…</div>`;
  ({ application: Application, playground: Playground, evaluation: Evaluation, datasets: Datasets,
     monitoring: Monitoring, feedback: Feedback, guardrails: Guardrails }[current])().catch(e =>
    view.innerHTML = `<div class="card err">${esc(e.message)}</div>`);
}
function head(title, sub) { return `<div class="page-head"><h1>${title}</h1><p>${sub}</p></div>`; }

/* ── Application: run + dashboard ──────────────────────────────────────── */
async function Application() {
  view.innerHTML = head("AI Pipeline — Application",
    "Run the call-analytics pipeline and view the coaching intelligence it produces.");
  if (HEALTH.mode !== "real")
    view.appendChild($(`<div class="card" style="border-left:4px solid var(--amber);background:#fff8e9">
      <b>Demo data.</b> <span class="muted">Numbers below are an illustrative sample generated from 12 example
      transcripts — not from a live system or database. Flip <code>AI_PIPELINE_MODE=real</code> in <code>.env</code>
      (with Azure creds) to run against real data.</span></div>`));
  const runCard = $(`<div class="card"><h2>Run a pipeline batch</h2>
    <p class="sub">Mock mode executes instantly with sample transcripts — no Azure needed.</p>
    <div class="field-row">
      <div><label>Program</label><select id="ap-prog">${(HEALTH.programs || ["telesales"]).map(p => `<option>${p}</option>`).join("")}</select></div>
      <div><label>Date</label><input id="ap-date" value="2025-08-28"></div>
      <div style="display:flex;align-items:flex-end"><button class="btn go" id="ap-run" style="width:100%">▶ Run pipeline</button></div>
    </div>
    <div id="ap-progress" style="margin-top:14px"></div></div>`);
  view.appendChild(runCard);
  const dash = $(`<div id="ap-dash"></div>`); view.appendChild(dash);

  async function doRun() {
    const prog = document.getElementById("ap-prog").value, date = document.getElementById("ap-date").value;
    const pel = document.getElementById("ap-progress");
    const steps = ["denoise", "analysis", "summary", "individual_metrics", "kpi"];
    pel.innerHTML = `<div class="flow">${steps.map(s => `<div class="flow-node" id="fn-${s}"><div class="flow-label">${s}</div><div class="flow-desc"><span class="spin"></span> queued</div></div>`).join('<div class="flow-arrow">→</div>')}</div>`;
    document.getElementById("ap-run").disabled = true;
    const res = await post("/run", { program: prog, date });
    // animate step completion
    for (let i = 0; i < res.steps.length; i++) {
      await new Promise(r => setTimeout(r, 260));
      const s = res.steps[i], node = document.getElementById("fn-" + s.step);
      if (node) { node.classList.add("done"); node.querySelector(".flow-desc").innerHTML = `✓ ${s.calls ? s.calls + " calls" : "aggregated"}`; }
    }
    document.getElementById("ap-run").disabled = false;
    HEALTH = await api("/health");
    renderDashboard(res.dashboard);
  }
  document.getElementById("ap-run").onclick = () => doRun().catch(e => document.getElementById("ap-progress").innerHTML = `<div class="err">${esc(e.message)}</div>`);
  doRun().catch(() => {});   // auto-run once so the client sees output immediately

  function renderDashboard(d) {
    const t = (d.llmops || {}).totals || {}, emps = d.employees || [], kpis = d.kpis || [];
    dash.innerHTML = "";
    dash.appendChild($(`<div class="card"><h2>Run output — ${esc(d.meta.program || "")} · ${esc(d.meta.date || "")}</h2>
      <p class="sub">Coaching intelligence generated from 100% of analysed calls. ${d.meta.mode === "mock" ? "<b>Mock data</b> — illustrative sample, not from a live system." : ""}</p>
      <div class="grid">
        <div class="stat accent"><b>${num(emps.length)}</b><span>Agents coached ${info(TIP.agents)}</span></div>
        <div class="stat"><b>${num(t.llm_calls)}</b><span>LLM calls ${info(TIP.calls)}</span></div>
        <div class="stat"><b>${num((t.input_tokens || 0) + (t.output_tokens || 0))}</b><span>Tokens ${info(TIP.intok)}</span></div>
        <div class="stat"><b>${money(t.cost_usd)}</b><span>Cost ${info(TIP.cost)}<span class="illus">illustrative</span></span></div>
        <div class="stat"><b>${Math.round(t.avg_latency_ms || 0)}ms</b><span>Avg latency ${info(TIP.latency)}</span></div>
        <div class="stat"><b>${num(t.guardrail_flags)}</b><span>Guardrail flags ${info(TIP.flags)}</span></div>
      </div></div>`));
    if (kpis.length) dash.appendChild($(`<div class="card"><h2>Key performance indicators</h2>
      <div class="grid">${kpis.map(k => `<div class="stat"><b>${k.unit === "percent" ? pct(k.value) : num(Math.round(k.value))}</b>
        <span>${esc(k.label)}${k.delta != null ? ` · <span style="color:${k.delta >= 0 ? "#3f9d6b" : "#cc5b5b"}">${k.delta >= 0 ? "▲" : "▼"}${Math.abs(k.unit === "percent" ? (k.delta * 100).toFixed(0) + "pp" : Math.round(k.delta))}</span>` : ""}</span></div>`).join("")}</div></div>`));
    if (emps.length) {
      const card = $(`<div class="card"><h2>Agent coaching</h2><div class="row-split"><div id="emp-list"></div><div id="emp-detail"></div></div></div>`);
      dash.appendChild(card);
      const list = card.querySelector("#emp-list");
      emps.forEach((e, i) => {
        const b = $(`<button class="list-item${i === 0 ? " sel" : ""}"><b>${esc(e.name)}</b><br><span class="muted">Coach ${esc(e.coach || "—")} · ${num(e.calls_analyzed)} calls</span></button>`);
        b.onclick = () => { list.querySelectorAll(".list-item").forEach(x => x.classList.remove("sel")); b.classList.add("sel"); showEmp(e); };
        list.appendChild(b);
      });
      const showEmp = (e) => {
        const det = card.querySelector("#emp-detail");
        const scores = (e.scores || []).map(s => ({ k: s.label, v: s.value }));
        det.innerHTML = `<h2 style="font-size:16px">${esc(e.name)}</h2>
          ${e.reflection ? `<div class="callout"><div class="lab">AI coaching reflection</div><p>${esc(e.reflection)}</p></div>` : ""}
          <div class="chart-title">Behaviour scores</div>${svgHBars(scores, { unit: "%" })}
          ${(e.top_calls || []).length ? `<div class="chart-title" style="margin-top:12px">Top calls</div>
            ${e.top_calls.map(c => `<div class="list-item" style="cursor:default">
              <b>#${esc(c.contact_id)}</b> ${c.outcome ? `<span class="badge b-pass">${esc(c.outcome)}</span>` : ""}
              <div style="font-size:12.5px;margin-top:3px">${esc(c.intent || "")}</div>
              <div style="margin-top:5px">${(c.tags || []).map(t => `<span class="tag">${esc(t)}</span>`).join("")}</div>
              ${c.excerpt ? `<div class="muted" style="margin-top:5px;font-style:italic">${esc(c.excerpt)}</div>` : ""}</div>`).join("")}` : ""}`;
      };
      showEmp(emps[0]);
    }
  }
}

/* ── Playground ────────────────────────────────────────────────────────── */
async function Playground() {
  const [prompts, models, datasets] = await Promise.all([api("/prompts"), api("/models"), api("/datasets")]);
  view.innerHTML = head("Playground", "Edit a prompt, pick a model + golden dataset, and score it live. Mock mode uses a deterministic mock LLM — no keys needed. Compare models and prompt wordings before you save a version.");
  const card = $(`<div class="card"><div class="row-split"><div id="pg-l"></div><div id="pg-r"><div class="muted">Results appear here.</div></div></div></div>`);
  view.appendChild(card);
  let TEMPLATES = {};   // version -> template text for the selected prompt
  card.querySelector("#pg-l").innerHTML = `
    <label>Prompt</label><select id="pg-prompt">${prompts.map(p => `<option value="${p.program}|${p.name}">${p.program} / ${p.name}</option>`).join("") || "<option>(none)</option>"}</select>
    <label>Version</label><select id="pg-version"></select>
    <label>Prompt text ${info("Edit freely and Run to test the wording without saving. Save as new version to persist it; Activate (Prompts tab) makes the pipeline use it.")}</label>
    <textarea id="pg-text" style="min-height:150px" placeholder="Prompt template…"></textarea>
    <div class="btnrow"><button class="btn alt sm" id="pg-save">💾 Save as new version</button>
      <span class="muted" id="pg-savenote"></span></div>
    <label>Model ${info("Each alias maps to an Azure deployment (config-as-code). Pick different models to compare quality vs. cost on the same golden set.")}</label>
    <select id="pg-model">${models.map(m => `<option value="${m.alias}" title="${esc(m.note || "")}">${m.alias}${m.deployment ? " → " + m.deployment : ""}${m.note ? " — " + m.note : ""}</option>`).join("")}</select>
    <div class="muted" id="pg-modelrate" style="margin-top:4px"></div>
    <label>Golden dataset</label><select id="pg-dataset">${datasets.map(d => `<option value="${d.name}">${d.name} (${d.cases} cases)</option>`).join("")}</select>
    <label>Ad-hoc input (optional) ${info("Paste one transcript to test a single case instead of the whole dataset — great for a quick live demo.")}</label>
    <textarea id="pg-adhoc" style="min-height:60px" placeholder="Paste one transcript to test a single case…"></textarea>
    <div class="btnrow"><button class="btn go" id="pg-run">▶ Run evaluation</button></div>`;

  const MODELS = Object.fromEntries(models.map(m => [m.alias, m]));
  const showRate = () => {
    const m = MODELS[document.getElementById("pg-model").value] || {};
    document.getElementById("pg-modelrate").innerHTML = m.input_per_1k != null
      ? `Rate: $${m.input_per_1k}/1k in · $${m.output_per_1k}/1k out <span class="illus">illustrative</span>` : "";
  };
  document.getElementById("pg-model").onchange = showRate; showRate();

  const fillV = async () => {
    const sel = document.getElementById("pg-prompt").value; if (!sel) return;
    const [pr, nm] = sel.split("|"); const p = await api(`/prompts/${pr}/${nm}`);
    TEMPLATES = {}; (p.versions || []).forEach(v => TEMPLATES[v.version] = v.template || "");
    const vsel = document.getElementById("pg-version");
    vsel.innerHTML = (p.versions || []).map(v =>
      `<option value="${v.version}" ${v.version === p.active_version ? "selected" : ""}>v${v.version}${v.version === p.active_version ? " (active)" : ""}</option>`).join("");
    loadText();
  };
  const loadText = () => {
    const v = document.getElementById("pg-version").value;
    document.getElementById("pg-text").value = TEMPLATES[v] || "";
  };
  document.getElementById("pg-prompt").onchange = fillV;
  document.getElementById("pg-version").onchange = loadText;
  await fillV();

  document.getElementById("pg-save").onclick = async () => {
    const sel = document.getElementById("pg-prompt").value; if (!sel) return;
    const [pr, nm] = sel.split("|");
    const note = document.getElementById("pg-savenote");
    try {
      const spec = await post(`/prompts/${pr}/${nm}`, { template: document.getElementById("pg-text").value, note: "saved from playground" });
      note.textContent = `saved v${spec.version}`;
      await fillV();
      document.getElementById("pg-version").value = spec.version; loadText();
    } catch (e) { note.textContent = "save failed: " + e.message; }
  };

  document.getElementById("pg-run").onclick = async () => {
    const out = card.querySelector("#pg-r"); const sel = document.getElementById("pg-prompt").value;
    if (!sel) { out.innerHTML = `<div class="err">No prompt.</div>`; return; }
    const [pr, nm] = sel.split("|"); out.innerHTML = `<div class="loading"><span class="spin"></span> Running…</div>`;
    try {
      const res = await post("/playground", { program: pr, prompt_name: nm, version: Number(document.getElementById("pg-version").value),
        prompt_text: document.getElementById("pg-text").value,
        model_alias: document.getElementById("pg-model").value, dataset: document.getElementById("pg-dataset").value,
        ad_hoc_input: document.getElementById("pg-adhoc").value.trim() || null });
      const s = res.summary;
      out.innerHTML = `<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">${donut(s.passed, s.n_cases)}
        <div class="grid" style="flex:1">
          <div class="stat"><b>${num(s.input_tokens + s.output_tokens)}</b><span>Tokens ${info(TIP.intok)}</span></div>
          <div class="stat"><b>${money(s.cost_usd)}</b><span>Cost ${info(TIP.cost)}</span></div>
          <div class="stat"><b>${s.latency_ms}ms</b><span>Latency ${info(TIP.latency)}</span></div>
          <div class="stat"><b>${esc(s.deployment || s.mode)}</b><span>Model</span></div></div></div>
        <div class="scroll" style="margin-top:12px"><table><thead><tr><th>Case</th><th>Result</th><th>Detail</th></tr></thead><tbody>
        ${res.results.map(r => `<tr><td>${esc(r.case_id)}</td><td><span class="badge ${r.passed ? "b-pass" : "b-fail"}">${r.passed ? "PASS" : "FAIL"}</span></td>
          <td>${esc((r.reason || r.output || "").slice(0, 140))}</td></tr>`).join("")}</tbody></table></div>`;
    } catch (e) { out.innerHTML = `<div class="err">${esc(e.message)}</div>`; }
  };
}

/* ── Evaluation ────────────────────────────────────────────────────────── */
async function Evaluation() {
  const runs = await api("/eval-runs");
  view.innerHTML = head("Evaluation", "Golden-dataset evaluation metrics per prompt & model — the quality gate that guards every change.");
  if (!runs.length) { view.appendChild($(`<div class="card"><div class="muted">No evaluation runs yet — run one from the Playground.</div></div>`)); return; }
  const passed = runs.filter(r => r.passed).length, avg = runs.reduce((a, r) => a + r.pass_rate, 0) / runs.length;
  const trend = runs.slice().reverse().map((r, i) => ({ k: "#" + (i + 1), v: r.pass_rate }));
  // pass-rate by prompt version
  const byVer = {}; runs.forEach(r => { const k = `${r.prompt} v${r.version}`; (byVer[k] = byVer[k] || []).push(r.pass_rate); });
  const verBars = Object.entries(byVer).map(([k, a]) => ({ k, v: a.reduce((x, y) => x + y, 0) / a.length }));

  view.appendChild($(`<div class="card"><div class="grid">
    <div class="stat accent"><b>${pct(avg)}</b><span>Avg pass rate ${info(TIP.passrate)}</span></div>
    <div class="stat"><b>${runs.length}</b><span>Eval runs ${info("Each Playground run against a golden dataset is recorded here.")}</span></div>
    <div class="stat"><b>${passed}</b><span>Passed gate ${info("Runs at or above the environment threshold (dev 0.8 / test 0.9 / prod 1.0).")}</span></div>
    <div class="stat"><b>${runs.length - passed}</b><span>Failed gate ${info("Runs below threshold — these would block a prompt/model change from shipping.")}</span></div></div></div>`));
  const charts = $(`<div class="cards-2"></div>`);
  charts.appendChild($(`<div class="card"><div class="chart-title">Pass-rate trend (oldest → newest)</div>${svgLine(trend)}</div>`));
  charts.appendChild($(`<div class="card"><div class="chart-title">Avg pass rate by prompt version</div>${svgHBars(verBars, { unit: "%" })}</div>`));
  view.appendChild(charts);
  view.appendChild($(`<div class="card"><h2>Evaluation run history</h2><div class="scroll"><table>
    <thead><tr><th>When</th><th>Prompt</th><th>Ver</th><th>Model</th><th>Dataset</th><th>Cases</th><th>Pass rate</th><th>Gate</th></tr></thead>
    <tbody>${runs.map(r => `<tr><td>${esc((r.ts || "").slice(0, 19).replace("T", " "))}</td><td>${esc(r.prompt)}</td><td>v${r.version}</td>
      <td>${esc(r.model_alias)}</td><td>${esc(r.dataset || "")}</td><td>${r.n_cases}</td><td>${pct(r.pass_rate)}</td>
      <td><span class="badge ${r.passed ? "b-pass" : "b-fail"}">${r.passed ? "PASS" : "FAIL"}</span></td></tr>`).join("")}</tbody></table></div></div>`));
}

/* ── Golden Datasets: view / edit / add / upload ───────────────────────── */
async function Datasets() {
  const list = await api("/datasets");
  view.innerHTML = head("Golden Datasets", "Curated ground-truth cases used to evaluate prompts & models. Edit, add, or upload — saved locally (mock).");
  const card = $(`<div class="card"><div class="row-split"><div id="ds-l"></div><div id="ds-r"><div class="muted">Select a dataset.</div></div></div></div>`);
  view.appendChild(card);
  const L = card.querySelector("#ds-l");
  L.innerHTML = `<label>Datasets</label>${list.map(d => `<button class="list-item" data-n="${esc(d.name)}"><b>${esc(d.name)}</b><br><span class="muted">${d.cases} case(s)</span></button>`).join("") || `<div class="muted">none</div>`}
    <div class="btnrow"><button class="btn alt sm" id="ds-upload">⬆ Upload dataset</button></div>`;
  L.querySelectorAll(".list-item").forEach(b => b.onclick = () => { L.querySelectorAll(".list-item").forEach(x => x.classList.remove("sel")); b.classList.add("sel"); openDS(b.dataset.n); });
  document.getElementById("ds-upload").onclick = uploadDS;
  if (list[0]) { L.querySelector(".list-item").classList.add("sel"); openDS(list[0].name); }

  async function openDS(name) {
    const d = await api(`/datasets/${encodeURIComponent(name)}`);
    const R = card.querySelector("#ds-r");
    R.innerHTML = `<h2 style="font-size:15px">${esc(name)} <span class="muted">· ${d.cases.length} cases</span></h2>
      <div class="scroll"><table><thead><tr><th>ID</th><th>Evaluator</th><th>Input (transcript)</th><th></th></tr></thead><tbody id="ds-rows"></tbody></table></div>
      <div class="btnrow"><button class="btn sm" id="ds-add">+ Add case</button></div>`;
    const tb = R.querySelector("#ds-rows");
    d.cases.forEach(c => {
      const inp = (c.input && (c.input.transcript || c.input.text)) || JSON.stringify(c.expected || "");
      const tr = $(`<tr><td>${esc(c.id)}</td><td><span class="badge b-mut">${esc(c.evaluator || "schema")}</span></td>
        <td>${esc(String(inp).slice(0, 90))}</td><td style="white-space:nowrap">
        <button class="btn alt sm" data-a="edit">Edit</button> <button class="btn danger sm" data-a="del">✕</button></td></tr>`);
      tr.querySelector('[data-a="edit"]').onclick = () => editCase(name, c);
      tr.querySelector('[data-a="del"]').onclick = async () => { await post(`/datasets/${encodeURIComponent(name)}/delete/${encodeURIComponent(c.id)}`, {}); openDS(name); };
      tb.appendChild(tr);
    });
    R.querySelector("#ds-add").onclick = () => editCase(name, { id: "", evaluator: "schema", input: { transcript: "" }, output_schema: { type: "object" } });
  }
  function editCase(name, c) {
    const R = card.querySelector("#ds-r");
    R.innerHTML = `<h2 style="font-size:15px">Edit case — ${esc(name)}</h2>
      <label>Case ID</label><input id="ec-id" value="${esc(c.id || "")}" placeholder="auto if blank">
      <label>Evaluator</label><select id="ec-ev"><option ${c.evaluator === "schema" ? "selected" : ""}>schema</option><option ${c.evaluator === "exact_match" ? "selected" : ""}>exact_match</option></select>
      <label>Input transcript</label><textarea id="ec-in">${esc((c.input && c.input.transcript) || "")}</textarea>
      <label>Expected / output_schema (JSON — optional)</label><textarea id="ec-exp" style="min-height:80px">${esc(JSON.stringify(c.output_schema || c.expected || { type: "object" }, null, 2))}</textarea>
      <div class="btnrow"><button class="btn go" id="ec-save">Save case</button><button class="btn alt" id="ec-cancel">Cancel</button></div>`;
    R.querySelector("#ec-cancel").onclick = () => openDS(name);
    R.querySelector("#ec-save").onclick = async () => {
      let extra = {}; try { extra = JSON.parse(R.querySelector("#ec-exp").value || "{}"); } catch { alert("Expected/schema is not valid JSON"); return; }
      const ev = R.querySelector("#ec-ev").value;
      const nc = { id: R.querySelector("#ec-id").value.trim(), evaluator: ev, input: { transcript: R.querySelector("#ec-in").value } };
      if (ev === "schema") nc.output_schema = extra; else nc.expected = extra;
      const path = c.id ? `/datasets/${encodeURIComponent(name)}/cases/${encodeURIComponent(c.id)}` : `/datasets/${encodeURIComponent(name)}/cases`;
      await post(path, { case: nc }); openDS(name);
    };
  }
  function uploadDS() {
    const R = card.querySelector("#ds-r");
    R.innerHTML = `<h2 style="font-size:15px">Upload a golden dataset</h2>
      <p class="sub">Paste JSONL (one case per line) or a JSON array. Saved locally.</p>
      <label>Dataset name</label><input id="up-name" placeholder="my_golden.jsonl">
      <label>Content</label><textarea id="up-body" style="min-height:180px" placeholder='{"id":"c1","input":{"transcript":"..."},"evaluator":"schema","output_schema":{"type":"object"}}'></textarea>
      <div class="btnrow"><button class="btn go" id="up-save">Upload</button></div>`;
    R.querySelector("#up-save").onclick = async () => {
      const name = R.querySelector("#up-name").value.trim() || "uploaded.jsonl";
      try { await post(`/datasets/${encodeURIComponent(name)}/upload`, { content: R.querySelector("#up-body").value }); Datasets(); }
      catch (e) { alert(e.message); }
    };
  }
}

/* ── Monitoring ────────────────────────────────────────────────────────── */
async function Monitoring() {
  const [m, runs] = await Promise.all([api("/monitoring"), api("/runs")]);
  const t = m.totals || {};
  view.innerHTML = head("Monitoring", "Full LLM observability across the pipeline: cost, tokens, latency, guardrail flags — traced per call. Hover any ⓘ for an explanation.");
  view.appendChild($(`<div class="card"><div class="grid">
    <div class="stat accent"><b>${num(t.llm_calls)}</b><span>LLM calls ${info(TIP.calls)}</span></div>
    <div class="stat"><b>${num(t.input_tokens)}</b><span>Input tokens ${info(TIP.intok)}</span></div>
    <div class="stat"><b>${num(t.output_tokens)}</b><span>Output tokens ${info(TIP.outtok)}</span></div>
    <div class="stat"><b>${money(t.cost_usd)}</b><span>Cost ${info(TIP.cost)}<span class="illus">illustrative</span></span></div>
    <div class="stat"><b>${Math.round(t.avg_latency_ms || 0)}ms</b><span>Avg latency ${info(TIP.latency)}</span></div>
    <div class="stat"><b>${num(t.guardrail_flags)}</b><span>Guardrail flags ${info(TIP.flags)}</span></div>
    <div class="stat"><b>${num(t.errors)}</b><span>Errors ${info(TIP.errors)}</span></div></div>
    <div class="note" style="margin-top:12px">Cost uses <b>illustrative</b> per-token rates from <code>pricing.yaml</code> — swap in AFNI's contracted rates for exact figures. Tokens, latency &amp; guardrails are computed live.</div></div>`));
  const bs = (m.by_step || []).map(s => ({ k: s.step, v: Math.round(s.avg_latency_ms || 0) }));
  const cs = (m.by_step || []).map(s => ({ k: s.step, v: s.calls || 0 }));
  const two = $(`<div class="cards-2"></div>`);
  two.appendChild($(`<div class="card"><div class="chart-title">Avg latency by step (ms)</div>${svgBars(bs, { color: "#3b74c4" })}</div>`));
  two.appendChild($(`<div class="card"><div class="chart-title">LLM calls by step</div>${svgBars(cs, { color: "#2bb8a3" })}</div>`));
  view.appendChild(two);
  view.appendChild($(`<div class="card"><h2>Recent pipeline runs</h2><div class="scroll"><table>
    <thead><tr><th>When</th><th>Run</th><th>Program</th><th>Date</th><th>Steps</th><th>Mode</th></tr></thead>
    <tbody>${runs.length ? runs.map(r => `<tr><td>${esc((r.ts || "").slice(0, 19).replace("T", " "))}</td><td>${esc(r.run_id)}</td>
      <td>${esc(r.program)}</td><td>${esc(r.date)}</td><td>${r.n_steps}</td><td><span class="badge b-mut">${esc(r.mode)}</span></td></tr>`).join("")
    : `<tr><td colspan="6" class="muted">No runs yet — start one from the Application tab.</td></tr>`}</tbody></table></div></div>`));
}

/* ── Feedback ──────────────────────────────────────────────────────────── */
async function Feedback() {
  const fb = await api("/feedback");
  view.innerHTML = head("Feedback", "Per-transcript feedback from coaches/reviewers (application-level), surfaced for developers to tune prompts & models.");
  const add = $(`<div class="card"><h2>Submit feedback</h2>
    <div class="field-row">
      <div><label>Contact ID</label><input id="fb-cid" placeholder="C1000"></div>
      <div><label>Step</label><input id="fb-step" value="analysis"></div>
      <div><label>Rating</label><input id="fb-rating" placeholder="up | down | reject"></div>
      <div><label>Rater</label><input id="fb-rater" value="coach"></div></div>
    <label>Comment</label><input id="fb-comment" placeholder="what was right/wrong">
    <label>Corrected output (optional — promotes to golden set)</label><input id="fb-corr" placeholder='{"score":4}'>
    <div class="btnrow"><button class="btn go" id="fb-add">Submit feedback</button></div></div>`);
  view.appendChild(add);
  document.getElementById("fb-add").onclick = async () => {
    await post("/feedback", { contact_id: v("fb-cid"), step: v("fb-step"), rating: v("fb-rating"),
      comment: v("fb-comment"), corrected_output: v("fb-corr") || null, rater: v("fb-rater") }); Feedback();
  };
  view.appendChild($(`<div class="card"><h2>Feedback log</h2><div class="scroll"><table>
    <thead><tr><th>When</th><th>Contact</th><th>Step</th><th>Rating</th><th>Rater</th><th>Comment</th></tr></thead>
    <tbody>${fb.length ? fb.map(f => `<tr><td>${esc((f.ts || "").slice(0, 19).replace("T", " "))}</td><td>${esc(f.contact_id)}</td><td>${esc(f.step)}</td>
      <td><span class="badge ${["down", "reject"].includes(f.rating) ? "b-fail" : "b-pass"}">${esc(f.rating)}</span></td>
      <td>${esc(f.rater)}</td><td>${esc(f.comment)}</td></tr>`).join("") : `<tr><td colspan="6" class="muted">No feedback yet.</td></tr>`}</tbody></table></div></div>`));
}
const v = (id) => document.getElementById(id).value;

/* ── Guardrails ────────────────────────────────────────────────────────── */
async function Guardrails() {
  const g = await api("/guardrails");
  const flagged = g.filter(x => x.decision === "flagged").length, blocked = g.filter(x => x.decision === "blocked").length;
  view.innerHTML = head("Guardrail Audit", "Every guardrail decision captured for audit — PII flagged (never dropped), secrets blocked, injection checked.");
  view.appendChild($(`<div class="card"><div class="grid">
    <div class="stat"><b>${g.length}</b><span>Total decisions</span></div>
    <div class="stat"><b>${flagged}</b><span>Flagged (allowed)</span></div>
    <div class="stat"><b>${blocked}</b><span>Blocked</span></div></div></div>`));
  view.appendChild($(`<div class="card"><h2>Audit trail</h2><div class="scroll"><table>
    <thead><tr><th>When</th><th>Run</th><th>Step</th><th>Deployment</th><th>Decision</th><th>Reason</th></tr></thead>
    <tbody>${g.length ? g.map(x => `<tr><td>${esc((x.ts || "").slice(0, 19).replace("T", " "))}</td><td>${esc(x.run_id)}</td><td>${esc(x.step)}</td>
      <td>${esc(x.deployment)}</td><td><span class="badge ${x.decision === "blocked" ? "b-fail" : "b-flag"}">${esc(x.decision)}</span></td>
      <td>${esc(x.reason)}</td></tr>`).join("") : `<tr><td colspan="6" class="muted">No guardrail events yet.</td></tr>`}</tbody></table></div></div>`));
}

boot();
