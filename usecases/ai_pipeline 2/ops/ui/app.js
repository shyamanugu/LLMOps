const API = "http://127.0.0.1:8000/api";
const $ = (h) => { const t = document.createElement("template"); t.innerHTML = h.trim(); return t.content.firstChild; };
const view = document.getElementById("view");
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (v) => (v * 100).toFixed(0) + "%";
const num = (v) => (v ?? 0).toLocaleString("en-US");

async function api(path, opts) {
  const r = await fetch(API + path, opts);
  if (!r.ok) { let e = {}; try { e = await r.json(); } catch {} throw new Error(e.error || r.status); }
  return r.json();
}
const post = (p, body) => api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });

const TABS = [
  ["playground", "Playground"], ["prompts", "Prompts"], ["monitoring", "Monitoring"],
  ["feedback", "Feedback"], ["guardrails", "Guardrails"],
];
let current = "playground";

document.getElementById("api-url").textContent = API;

async function boot() {
  try {
    const h = await api("/health");
    const pill = document.getElementById("mode-pill");
    pill.textContent = (h.mode === "real" ? "● REAL" : "● MOCK") + " MODE";
    pill.className = "pill" + (h.mode === "real" ? " real" : "");
  } catch (e) {
    view.innerHTML = `<div class="card err">Cannot reach backend at <code>${API}</code>.<br>Start it: <code>python ops/start_backend.py</code><br><br>${esc(e.message)}</div>`;
    return;
  }
  const tabs = document.getElementById("tabs");
  TABS.forEach(([id, label]) => {
    const b = $(`<button class="tab" data-id="${id}">${label}</button>`);
    b.onclick = () => { current = id; render(); };
    tabs.appendChild(b);
  });
  render();
}

function render() {
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.id === current));
  view.innerHTML = `<div class="loading">Loading…</div>`;
  ({ playground: Playground, prompts: Prompts, monitoring: Monitoring, feedback: Feedback, guardrails: Guardrails }[current])();
}

// ── Playground ─────────────────────────────────────────────────────────
async function Playground() {
  const [prompts, models, datasets] = await Promise.all([api("/prompts"), api("/models"), api("/datasets")]);
  view.innerHTML = "";
  const card = $(`<div class="card"><h2>Playground</h2>
    <p class="sub">Run a prompt + model against a golden dataset and score it. In mock mode this uses a deterministic mock LLM — no keys needed.</p></div>`);
  const controls = $(`<div class="row"></div>`);
  const left = $(`<div></div>`), right = $(`<div></div>`);
  const promptOpts = prompts.map(p => `<option value="${p.program}|${p.name}">${p.program} / ${p.name}</option>`).join("");
  const modelOpts = models.map(m => `<option value="${m.alias}">${m.alias}${m.deployment ? " → " + m.deployment : " (env fallback)"}</option>`).join("");
  const dsOpts = datasets.map(d => `<option>${d}</option>`).join("");
  left.innerHTML = `
    <label>Prompt</label><select id="pg-prompt">${promptOpts || "<option>(none — add one in Prompts)</option>"}</select>
    <label>Version</label><select id="pg-version"></select>
    <label>Model alias</label><select id="pg-model">${modelOpts}</select>
    <label>Golden dataset</label><select id="pg-dataset">${dsOpts}</select>
    <label>Ad-hoc input (optional, overrides dataset)</label><textarea id="pg-adhoc" style="min-height:80px" placeholder="Paste one transcript to test a single case…"></textarea>
    <div class="btnrow"><button class="btn go" id="pg-run">Run evaluation</button></div>`;
  right.innerHTML = `<div id="pg-out" class="muted">Results appear here.</div>`;
  controls.append(left, right); card.appendChild(controls); view.appendChild(card);

  async function fillVersions() {
    const sel = document.getElementById("pg-prompt").value;
    const vsel = document.getElementById("pg-version");
    if (!sel) { vsel.innerHTML = ""; return; }
    const [prog, name] = sel.split("|");
    const p = await api(`/prompts/${prog}/${name}`);
    vsel.innerHTML = (p.versions || []).map(v =>
      `<option value="${v.version}" ${v.version === p.active_version ? "selected" : ""}>v${v.version}${v.version === p.active_version ? " (active)" : ""}</option>`).join("");
  }
  document.getElementById("pg-prompt").onchange = fillVersions;
  await fillVersions();

  document.getElementById("pg-run").onclick = async () => {
    const out = document.getElementById("pg-out");
    const sel = document.getElementById("pg-prompt").value;
    if (!sel) { out.innerHTML = `<div class="err">No prompt selected.</div>`; return; }
    const [prog, name] = sel.split("|");
    out.innerHTML = `<div class="loading">Running…</div>`;
    try {
      const res = await post("/playground", {
        program: prog, prompt_name: name, version: Number(document.getElementById("pg-version").value),
        model_alias: document.getElementById("pg-model").value,
        dataset: document.getElementById("pg-dataset").value,
        ad_hoc_input: document.getElementById("pg-adhoc").value.trim() || null,
      });
      const s = res.summary;
      out.innerHTML = `
        <div class="grid">
          <div class="stat"><b>${pct(s.pass_rate)}</b><span>Pass rate</span></div>
          <div class="stat"><b>${s.passed}/${s.n_cases}</b><span>Cases passed</span></div>
          <div class="stat"><b>${num(s.input_tokens + s.output_tokens)}</b><span>Tokens</span></div>
          <div class="stat"><b>${s.latency_ms}ms</b><span>Latency</span></div>
        </div>
        <table style="margin-top:12px"><thead><tr><th>Case</th><th>Result</th><th>Reason / output</th></tr></thead><tbody>
        ${res.results.map(r => `<tr><td>${esc(r.case_id)}</td>
          <td><span class="badge ${r.passed ? "b-pass" : "b-fail"}">${r.passed ? "PASS" : "FAIL"}</span></td>
          <td>${esc(r.reason || r.output).slice(0, 160)}</td></tr>`).join("")}
        </tbody></table>`;
    } catch (e) { out.innerHTML = `<div class="err">${esc(e.message)}</div>`; }
  };
}

// ── Prompts ────────────────────────────────────────────────────────────
async function Prompts() {
  const prompts = await api("/prompts");
  view.innerHTML = "";
  const card = $(`<div class="card"><h2>Prompt Registry</h2>
    <p class="sub">Versioned prompts. Save creates a new version; Activate makes it the one the pipeline uses — no redeploy. Or pin any version via env: <code>AI_PIPELINE_PROMPT_&lt;PROGRAM&gt;_&lt;NAME&gt;=v3</code>.</p></div>`);
  const row = $(`<div class="row"></div>`);
  const list = $(`<div></div>`), editor = $(`<div id="pr-editor" class="muted">Select a prompt.</div>`);
  list.innerHTML = `<label>Prompts</label>` + (prompts.length ? prompts.map(p =>
    `<div class="ver" style="display:block;margin-bottom:6px" data-k="${p.program}|${p.name}">
       <b>${p.program} / ${p.name}</b><br><span class="muted">${p.versions.length} version(s) · active v${p.active_version ?? "—"}</span></div>`).join("")
    : `<div class="muted">No prompts yet.</div>`);
  row.append(list, editor); card.appendChild(row); view.appendChild(card);

  list.querySelectorAll(".ver").forEach(el => el.onclick = () => openPrompt(...el.dataset.k.split("|")));
  if (prompts[0]) openPrompt(prompts[0].program, prompts[0].name);

  async function openPrompt(prog, name) {
    const p = await api(`/prompts/${prog}/${name}`);
    let sel = p.active_version || (p.versions.at(-1) || {}).version;
    const ed = document.getElementById("pr-editor");
    function draw() {
      const v = p.versions.find(x => x.version === sel) || {};
      ed.innerHTML = `<h2>${prog} / ${name}</h2>
        <div class="ver-list">${p.versions.map(x => `<span class="ver ${x.version === sel ? "sel" : ""}" data-v="${x.version}">v${x.version}${x.version === p.active_version ? " ●" : ""}</span>`).join("")}</div>
        <label>Template (editing v${sel} — Save creates a new version)</label>
        <textarea id="pr-tpl">${esc(v.template || "")}</textarea>
        <label>Note</label><input id="pr-note" placeholder="what changed" />
        <div class="btnrow">
          <button class="btn" id="pr-save">Save as new version</button>
          <button class="btn go" id="pr-activate">Activate v${sel}</button>
          <span class="badge b-active">active: v${p.active_version ?? "—"}</span>
        </div>`;
      ed.querySelectorAll(".ver[data-v]").forEach(e => e.onclick = () => { sel = Number(e.dataset.v); draw(); });
      document.getElementById("pr-save").onclick = async () => {
        const spec = await post(`/prompts/${prog}/${name}`, { template: document.getElementById("pr-tpl").value, note: document.getElementById("pr-note").value });
        alert(`Saved v${spec.version}`); openPrompt(prog, name);
      };
      document.getElementById("pr-activate").onclick = async () => {
        await post(`/prompts/${prog}/${name}/activate/${sel}`, {});
        alert(`Activated v${sel} — the pipeline will use it on next run.`); openPrompt(prog, name);
      };
    }
    draw();
  }
}

// ── Monitoring ─────────────────────────────────────────────────────────
async function Monitoring() {
  const [m, runs] = await Promise.all([api("/monitoring"), api("/eval-runs")]);
  const t = m.totals, cost0 = !t.cost_usd;
  const maxLat = Math.max(1, ...m.by_step.map(s => s.avg_latency_ms));
  view.innerHTML = "";
  view.appendChild($(`<div class="card"><h2>Monitoring — LLM metrics</h2>
    <p class="sub">Per-call cost, tokens, latency, and guardrail flags across the pipeline. ${cost0 ? "Cost shows $0 until per-token rates are set in pricing.yaml." : ""}</p>
    <div class="grid">
      <div class="stat"><b>${num(t.llm_calls)}</b><span>LLM calls</span></div>
      <div class="stat"><b>${num(t.input_tokens)}</b><span>Input tokens</span></div>
      <div class="stat"><b>${num(t.output_tokens)}</b><span>Output tokens</span></div>
      <div class="stat"><b>$${(t.cost_usd || 0).toFixed(4)}</b><span>Cost</span></div>
      <div class="stat"><b>${t.avg_latency_ms}ms</b><span>Avg latency</span></div>
      <div class="stat"><b>${num(t.guardrail_flags)}</b><span>Guardrail flags</span></div>
      <div class="stat"><b>${num(t.errors)}</b><span>Errors</span></div>
    </div></div>`));
  view.appendChild($(`<div class="card"><h2>Latency by step</h2>
    <table><tbody>${m.by_step.map(s => `<tr><td style="width:160px">${esc(s.step)}</td>
      <td><div class="bar"><i style="width:${Math.round(s.avg_latency_ms / maxLat * 100)}%"></i></div></td>
      <td style="width:90px;text-align:right">${Math.round(s.avg_latency_ms)}ms</td>
      <td style="width:90px;text-align:right">${s.calls} calls</td></tr>`).join("")}</tbody></table></div>`));
  view.appendChild($(`<div class="card"><h2>Evaluation runs (per prompt/model vs golden set)</h2>
    <table><thead><tr><th>When</th><th>Prompt</th><th>v</th><th>Model</th><th>Dataset</th><th>Pass rate</th><th></th></tr></thead>
    <tbody>${runs.length ? runs.map(r => `<tr><td>${esc((r.ts || "").slice(0, 19))}</td><td>${esc(r.prompt)}</td><td>v${r.version}</td>
      <td>${esc(r.model_alias)}</td><td>${esc(r.dataset || "")}</td><td>${pct(r.pass_rate)}</td>
      <td><span class="badge ${r.passed ? "b-pass" : "b-fail"}">${r.passed ? "PASS" : "FAIL"}</span></td></tr>`).join("")
    : `<tr><td colspan="7" class="muted">No eval runs yet — run one from the Playground.</td></tr>`}</tbody></table></div>`));
}

// ── Feedback ───────────────────────────────────────────────────────────
async function Feedback() {
  const fb = await api("/feedback");
  view.innerHTML = "";
  const add = $(`<div class="card"><h2>Submit feedback (per transcript)</h2>
    <p class="sub">Application-level feedback coaches/reviewers give on a call; surfaced here so developers can tune prompts & models.</p>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(160px,1fr))">
      <div><label>Contact ID</label><input id="fb-cid" placeholder="C1000"></div>
      <div><label>Step</label><input id="fb-step" value="analysis"></div>
      <div><label>Rating</label><input id="fb-rating" placeholder="up | down | reject"></div>
      <div><label>Rater</label><input id="fb-rater" value="coach"></div>
    </div>
    <label>Comment</label><input id="fb-comment" placeholder="what was right/wrong">
    <label>Corrected output (optional — promotes to golden set)</label><input id="fb-corr" placeholder='{"score":4}'>
    <div class="btnrow"><button class="btn" id="fb-add">Submit</button></div></div>`);
  view.appendChild(add);
  document.getElementById("fb-add").onclick = async () => {
    await post("/feedback", { contact_id: document.getElementById("fb-cid").value, step: document.getElementById("fb-step").value,
      rating: document.getElementById("fb-rating").value, comment: document.getElementById("fb-comment").value,
      corrected_output: document.getElementById("fb-corr").value || null, rater: document.getElementById("fb-rater").value });
    Feedback();
  };
  view.appendChild($(`<div class="card"><h2>Feedback log</h2>
    <table><thead><tr><th>When</th><th>Contact</th><th>Step</th><th>Rating</th><th>Rater</th><th>Comment</th></tr></thead>
    <tbody>${fb.length ? fb.map(f => `<tr><td>${esc((f.ts || "").slice(0, 19))}</td><td>${esc(f.contact_id)}</td><td>${esc(f.step)}</td>
      <td><span class="badge ${f.rating === "down" || f.rating === "reject" ? "b-fail" : "b-pass"}">${esc(f.rating)}</span></td>
      <td>${esc(f.rater)}</td><td>${esc(f.comment)}</td></tr>`).join("")
    : `<tr><td colspan="6" class="muted">No feedback yet.</td></tr>`}</tbody></table></div>`));
}

// ── Guardrails ─────────────────────────────────────────────────────────
async function Guardrails() {
  const g = await api("/guardrails");
  view.innerHTML = "";
  view.appendChild($(`<div class="card"><h2>Guardrail audit</h2>
    <p class="sub">Every guardrail decision (PII flagged, secrets blocked, injection) captured for audit.</p>
    <table><thead><tr><th>When</th><th>Run</th><th>Step</th><th>Deployment</th><th>Decision</th><th>Reason</th></tr></thead>
    <tbody>${g.length ? g.map(x => `<tr><td>${esc((x.ts || "").slice(0, 19))}</td><td>${esc(x.run_id)}</td><td>${esc(x.step)}</td>
      <td>${esc(x.deployment)}</td><td><span class="badge ${x.decision === "blocked" ? "b-fail" : "b-flag"}">${esc(x.decision)}</span></td>
      <td>${esc(x.reason)}</td></tr>`).join("")
    : `<tr><td colspan="6" class="muted">No guardrail events yet.</td></tr>`}</tbody></table></div>`));
}

boot();
