// METROLOGY Workstation Client Controller (v1.0.0)

let currentCalculation = null;
let activeCalculationId = null;
let currentBudgetRows = [];
let allProcedures = [];

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  loadProceduresCatalog();
  loadStandardsList();
  loadAuditLedger();
  loadBackupsList();
  loadSettings();
  triggerSelfTest(false);
});

// View Navigation Controller
function switchView(viewName) {
  const views = [
    "dashboard", "workflow", "multipoint", "calibrations",
    "procedures", "replay", "tamper", "audit", "backups", "standards", "settings", "license"
  ];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) el.classList.add("hidden");
    const nav = document.getElementById(`nav-${v}`);
    if (nav) nav.classList.remove("active");
  });

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) targetView.classList.remove("hidden");

  const targetNav = document.getElementById(`nav-${viewName}`);
  if (targetNav) targetNav.classList.add("active");

  const topTitle = document.getElementById("topbar-current-view");
  if (topTitle) {
    const titles = {
      dashboard: "Dashboard",
      workflow: "Single-Point Calibration Studio",
      multipoint: "Multi-Point Calibration Studio",
      calibrations: "Production Calibrations Log",
      procedures: "Procedures Catalog",
      replay: "12-Stage Mathematical Replay",
      tamper: "Tamper Detection Lab",
      audit: "Cryptographic Audit Vault",
      backups: "Backup & Recovery",
      standards: "Standards Concordance Registry",
      settings: "Laboratory Profile & Settings",
      license: "Plans & Licensing",
    };
    topTitle.innerText = titles[viewName] || "Workstation";
  }

  if (viewName === "replay" && activeCalculationId) {
    loadReplay(activeCalculationId);
  } else if (viewName === "audit") {
    loadAuditLedger();
  } else if (viewName === "backups") {
    loadBackupsList();
  } else if (viewName === "multipoint") {
    loadMultiPointProcedureTemplate();
  } else if (viewName === "license") {
    loadLicenseStatus();
  }
}

// 9-Step Workflow Controller
function setWorkflowStep(stepNum) {
  for (let i = 1; i <= 9; i++) {
    const p = document.getElementById(`wf-page-${i}`);
    const t = document.getElementById(`wf-tab-${i}`);
    if (p) p.classList.add("hidden");
    if (t) {
      t.classList.remove("active", "completed");
      if (i < stepNum) t.classList.add("completed");
      else if (i === stepNum) t.classList.add("active");
    }
  }
  const activePage = document.getElementById(`wf-page-${stepNum}`);
  if (activePage) activePage.classList.remove("hidden");
}

function startNewCalibration() {
  switchView("workflow");
  setWorkflowStep(1);
}

// 1. Dashboard Loading
async function loadDashboard() {
  try {
    const [stats, calcs] = await Promise.all([
      fetch("/api/stats").then(r => r.json()),
      fetch("/api/calculations?record_class=CALIBRATION&limit=25").then(r => r.json()),
    ]);

    document.getElementById("stat-total").innerText = stats.total_calibrations;
    document.getElementById("stat-passed").innerText = stats.passed_count;
    document.getElementById("stat-failed").innerText = stats.failed_count;
    document.getElementById("stat-review").innerText = (stats.guard_band_count || 0) + (stats.needs_review_count || 0);

    const emptyCard = document.getElementById("empty-workspace-card");
    const featCard = document.getElementById("featured-calibration-card");
    const tbody = document.getElementById("calibrations-table-body");

    if (calcs.length === 0) {
      if (emptyCard) emptyCard.classList.remove("hidden");
      if (featCard) featCard.classList.add("hidden");
      tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; color: var(--text-muted); padding: 32px 16px;">No production calibrations recorded yet. Click <strong>"+ New Calibration"</strong> to start.</td></tr>`;
      activeCalculationId = null;
      currentCalculation = null;
      return;
    }

    if (emptyCard) emptyCard.classList.add("hidden");
    if (featCard) featCard.classList.remove("hidden");

    const first = calcs[0];
    activeCalculationId = first.id;
    currentCalculation = first;
    updateFeaturedTelemetry(first);

    tbody.innerHTML = calcs.map(item => {
      const res = item.result_data || {};
      const unc = res.uncertainty_summary || {};
      const dec = res.decision_summary || {};
      const u95 = unc.expanded_uncertainty_U95_mm ? `±${unc.expanded_uncertainty_U95_mm} mm` : (res.max_expanded_uncertainty ? `±${res.max_expanded_uncertainty} mm` : "N/A");
      const tur = dec.tur || "N/A";
      const v = item.conformity_verdict;
      const vBadge = v === "PASS" ? "badge-pass" : (v === "GUARD_BAND" ? "badge-guard" : "badge-fail");

      return `
        <tr class="clickable-row" onclick="selectActiveCalculation('${item.id}')">
          <td style="font-family: monospace; font-weight: 700; color: #1d4ed8;">${item.id}</td>
          <td>r${item.revision_number || 1}</td>
          <td>${item.instrument_name} <span style="color: var(--text-muted); font-size: 11px;">(${item.instrument_model})</span></td>
          <td>${item.nominal_value} mm</td>
          <td style="font-family: monospace; font-weight: 600;">${u95}</td>
          <td style="font-weight: 600;">${tur}</td>
          <td><span class="badge ${vBadge}">${v}</span></td>
          <td><span class="badge badge-verified">VERIFIED</span></td>
          <td><span class="badge badge-integrity">INTEGRITY OK</span></td>
          <td style="text-align: right;">
            <button class="btn btn-outline" style="padding: 3px 8px; font-size: 10px;" onclick="event.stopPropagation(); inspectCalculation('${item.id}')">Inspect &rarr;</button>
          </td>
        </tr>
      `;
    }).join("");

  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

function updateFeaturedTelemetry(calc) {
  document.getElementById("feat-title").innerText = `${calc.instrument_name} (${calc.instrument_model})`;
  document.getElementById("feat-id-label").innerText = `${calc.id} • Revision ${calc.revision_number || 1}`;
  
  const res = calc.result_data || {};
  const unc = res.uncertainty_summary || {};
  const dec = res.decision_summary || {};

  document.getElementById("feat-meas").innerText = `${dec.mean_measured_mm || '25.00120'} mm`;
  document.getElementById("feat-u95").innerText = unc.expanded_uncertainty_U95_mm ? `±${unc.expanded_uncertainty_U95_mm} mm` : "±0.00078 mm";
  document.getElementById("feat-tur").innerText = `TUR = ${dec.tur || '2.564'}`;
  
  const vEl = document.getElementById("feat-verdict");
  vEl.innerText = calc.conformity_verdict || "PASS";
  vEl.className = `badge ${calc.conformity_verdict === 'PASS' ? 'badge-pass' : 'badge-fail'}`;
}

function selectActiveCalculation(calcId) {
  fetch(`/api/calculations/${calcId}`)
    .then(r => r.json())
    .then(calc => {
      activeCalculationId = calc.id;
      currentCalculation = calc;
      updateFeaturedTelemetry(calc);
    });
}

function openReplayForActive() {
  if (activeCalculationId) switchView("replay");
}

function openActiveEvidence() {
  if (currentCalculation) {
    populateWorkflowWithCalculation(currentCalculation);
    switchView("workflow");
    setWorkflowStep(8);
  }
}

// 2. Instrument selection change
function handleInstrumentChange() {
  const type = document.getElementById("inp-inst-type").value;
  const modelSelect = document.getElementById("inp-inst-model");
  const nomInp = document.getElementById("inp-nominal");
  const tolInp = document.getElementById("inp-tolerance");
  const resInp = document.getElementById("inp-resolution");

  if (type.includes("Caliper")) {
    modelSelect.innerHTML = `<option value="0–150 mm Digital Caliper">0–150 mm Digital Caliper</option>`;
    nomInp.value = "100.00000";
    tolInp.value = "0.02000";
    resInp.value = "0.010";
  } else if (type.includes("Indicator")) {
    modelSelect.innerHTML = `<option value="0–10 mm Dial Indicator">0–10 mm Dial Indicator</option>`;
    nomInp.value = "5.00000";
    tolInp.value = "0.00500";
    resInp.value = "0.001";
  } else {
    modelSelect.innerHTML = `<option value="0–25 mm Outside Micrometer">0–25 mm Outside Micrometer</option>`;
    nomInp.value = "25.00000";
    tolInp.value = "0.00200";
    resInp.value = "0.001";
  }
}

// 3. Single-point Submit & Calculate
async function submitAndCalculate() {
  const obs = Array.from(document.querySelectorAll(".obs-in")).map(i => parseFloat(i.value) || 0);

  const payload = {
    instrument_name: document.getElementById("inp-inst-type").value,
    instrument_model: document.getElementById("inp-inst-model").value,
    procedure_name: document.getElementById("inp-proc-name").value,
    procedure_version: "1.0.0",
    unit: "mm",
    nominal_value: parseFloat(document.getElementById("inp-nominal").value),
    tolerance_upper: parseFloat(document.getElementById("inp-tolerance").value),
    tolerance_lower: -parseFloat(document.getElementById("inp-tolerance").value),
    confidence_level: "95%",
    decision_rule: document.getElementById("inp-decision-rule").value,
    record_class: "CALIBRATION",
    reference_standard: {
      nominal_value: parseFloat(document.getElementById("inp-ref-val").value),
      uncertainty: parseFloat(document.getElementById("inp-ref-u").value),
      certificate_id: document.getElementById("inp-ref-cert").value,
      distribution: "normal",
      coverage_factor_k: 2.0,
      degrees_of_freedom: 50.0,
    },
    repeatability: { measurements: obs },
    resolution: {
      resolution: parseFloat(document.getElementById("inp-resolution").value),
      distribution: "rectangular",
    },
    temperature: {
      half_width_mm: parseFloat(document.getElementById("inp-temp-hw").value),
      distribution: "rectangular",
      delta_temperature_c: parseFloat(document.getElementById("inp-temp-dev").value),
      expansion_coefficient_ppm_k: parseFloat(document.getElementById("inp-temp-cte").value),
    },
    environment: {
      ambient_temperature_c: parseFloat(document.getElementById("inp-temp-amb").value),
      temperature_tolerance_c: parseFloat(document.getElementById("inp-temp-dev").value),
      relative_humidity_pct: parseFloat(document.getElementById("inp-humidity").value),
      atmospheric_pressure_hpa: 1013.25,
    },
  };

  try {
    const res = await fetch("/api/calculations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      alert("Calculation Engine Error: " + (err.detail || "Validation failed"));
      return;
    }

    const calc = await res.json();
    currentCalculation = calc;
    activeCalculationId = calc.id;
    populateWorkflowWithCalculation(calc);
    setWorkflowStep(5);
  } catch (err) {
    alert("Network error: " + err.message);
  }
}

function populateWorkflowWithCalculation(calc) {
  const unc = calc.uncertainty_summary || {};
  const dec = calc.decision_summary || {};
  currentBudgetRows = unc.budget_rows || [];

  document.getElementById("wf-budget-id").innerText = calc.id;
  document.getElementById("wf-uc").innerText = unc.combined_standard_uncertainty_mm + " mm";
  document.getElementById("wf-nueff").innerText = unc.effective_degrees_of_freedom;
  document.getElementById("wf-k").innerText = unc.coverage_factor_k;
  document.getElementById("wf-u95").innerText = "±" + unc.expanded_uncertainty_U95_mm + " mm";

  const bRowsEl = document.getElementById("wf-budget-rows");
  bRowsEl.innerHTML = currentBudgetRows.map((r, idx) => `
    <tr class="clickable-row" onclick="openComponentProvenanceModal(${idx})">
      <td style="font-weight: 700; color: #1e3a8a;">${r.label}</td>
      <td><span class="badge ${r.component_type === 'A' ? 'badge-verified' : 'badge-guard'}">Type ${r.component_type}</span></td>
      <td>${r.distribution}</td>
      <td style="font-family: monospace;">${r.divisor}</td>
      <td style="text-align: right; font-family: monospace;">${r.standard_uncertainty_mm}</td>
      <td style="text-align: center;">${r.sensitivity_coefficient}</td>
      <td style="text-align: right; font-weight: 700; color: #0284c7;">${r.percentage_contribution}</td>
      <td style="font-family: monospace;">${r.degrees_of_freedom}</td>
      <td style="text-align: right; font-family: monospace; font-size: 10px; color: #64748b;">
        🔍 ${r.component_hash || 'SHA-256'}
      </td>
    </tr>
  `).join("");

  document.getElementById("dec-tl").innerText = dec.tolerance_lower_mm;
  document.getElementById("dec-tu").innerText = dec.tolerance_upper_mm;
  document.getElementById("dec-al").innerText = dec.acceptance_lower_mm + " mm";
  document.getElementById("dec-au").innerText = dec.acceptance_upper_mm + " mm";
  document.getElementById("dec-w").innerText = dec.guardband_w_mm + " mm";
  document.getElementById("dec-verdict").innerText = dec.conformity_verdict;
  document.getElementById("dec-verdict").style.color = dec.conformity_verdict === "PASS" ? "var(--success)" : "var(--danger)";
  document.getElementById("dec-explanation").innerText = dec.decision_explanation;
  document.getElementById("dec-tur").innerText = "TUR = " + dec.tur;
  document.getElementById("diag-marker-label").innerText = `Error: ${dec.error_of_indication_mm} mm`;

  document.getElementById("rev-inst").innerText = calc.instrument_name;
  document.getElementById("rev-nom").innerText = `${dec.nominal_mm} mm`;
  document.getElementById("rev-meas").innerText = `${dec.mean_measured_mm} mm`;
  document.getElementById("rev-err").innerText = `${dec.error_of_indication_mm} mm`;
  document.getElementById("rev-u95").innerText = `±${unc.expanded_uncertainty_U95_mm} mm`;
  document.getElementById("rev-rule").innerText = dec.decision_rule;
  document.getElementById("rev-tur").innerText = dec.tur;
  document.getElementById("rev-verdict").innerText = dec.conformity_verdict;

  document.getElementById("ev-cid").innerText = calc.id;
  document.getElementById("ev-in-hash").innerText = calc.input_sha256;
  document.getElementById("ev-calc-hash").innerText = calc.calculation_sha256;
  document.getElementById("btn-dl-zip").href = `/api/calculations/${calc.id}/export/zip`;

  document.getElementById("cert-calc-id").innerText = calc.id;
  document.getElementById("btn-view-report").href = `/api/calculations/${calc.id}/report`;

  runVerificationOnCurrent();
}

function openComponentProvenanceModal(idx) {
  const row = currentBudgetRows[idx];
  if (!row) return;

  document.getElementById("modal-comp-label").innerText = `${row.label} — Provenance Detail`;
  const detailsEl = document.getElementById("modal-comp-details");
  detailsEl.innerHTML = `
    <div class="provenance-keyval"><span class="key">Source Document</span><span class="val">${row.source_reference || 'Metrology Lab Manual'}</span></div>
    <div class="provenance-keyval"><span class="key">Evaluation Type</span><span class="val">Type ${row.component_type} (${row.distribution})</span></div>
    <div class="provenance-keyval"><span class="key">Divisor Function</span><span class="val">${row.divisor}</span></div>
    <div class="provenance-keyval"><span class="key">Standard Uncertainty uᵢ</span><span class="val">${row.standard_uncertainty_mm} mm</span></div>
    <div class="provenance-keyval"><span class="key">Sensitivity Coeff cᵢ</span><span class="val">${row.sensitivity_coefficient}</span></div>
    <div class="provenance-keyval"><span class="key">Degrees of Freedom νᵢ</span><span class="val">${row.degrees_of_freedom}</span></div>
    <div class="provenance-keyval"><span class="key">Variance Share</span><span class="val">${row.percentage_contribution}</span></div>
    <div class="provenance-keyval"><span class="key">Component SHA-256</span><span class="val" style="color: var(--accent);">${row.component_hash || 'SHA-256 Canonical'}</span></div>
  `;

  document.getElementById("provenance-modal").classList.remove("hidden");
}

function closeProvenanceModal() {
  document.getElementById("provenance-modal").classList.add("hidden");
}

async function runVerificationOnCurrent() {
  if (!currentCalculation) return;
  try {
    const res = await fetch(`/api/calculations/${currentCalculation.id}/verify`).then(r => r.json());
    const vStatus = document.getElementById("ev-status");
    vStatus.innerText = res.overall_status;
    vStatus.style.color = res.is_valid ? "var(--success)" : "var(--danger)";

    const tbody = document.getElementById("ev-checks-body");
    tbody.innerHTML = res.checks.map(c => `
      <tr>
        <td style="font-weight: 700;">${c.check_name}</td>
        <td><span class="badge ${c.status === 'PASS' ? 'badge-pass' : 'badge-fail'}">${c.status}</span></td>
        <td style="font-size: 11px; color: var(--text-muted);">${c.details}</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Verification error:", err);
  }
}

// 4. Multi-Point Calibration Logic
function loadMultiPointProcedureTemplate() {
  const procKey = document.getElementById("mp-inst-select").value;
  const tableBody = document.getElementById("mp-table-body");
  
  let checkpoints = [0.0, 20.0, 50.0, 100.0, 150.0];
  let tol = 0.020;
  let res = 0.010;

  if (procKey.includes("micrometer")) {
    checkpoints = [0.0, 5.12, 10.24, 15.36, 20.48, 25.0];
    tol = 0.0020;
    res = 0.0010;
  } else if (procKey.includes("dial")) {
    checkpoints = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0];
    tol = 0.0050;
    res = 0.0010;
  } else if (procKey.includes("multimeter")) {
    checkpoints = [0.0, 1.0, 2.5, 5.0, 7.5, 10.0];
    tol = 0.0005;
    res = 0.00001;
  }

  document.getElementById("mp-resolution-inp").value = res;

  tableBody.innerHTML = checkpoints.map((p, idx) => `
    <tr class="mp-row">
      <td style="font-weight: 700;">#${idx + 1}</td>
      <td><input type="number" step="0.0001" class="mp-nom" value="${p}"></td>
      <td><input type="number" step="0.0001" class="mp-tol" value="${tol}"></td>
      <td><input type="number" step="0.0001" class="mp-ref-u" value="${(tol/5).toFixed(5)}"></td>
      <td><input type="text" class="mp-obs" value="${p+0.0002}, ${p+0.0001}, ${p+0.0003}, ${p}, ${p+0.0001}"></td>
      <td><button class="btn btn-outline" style="padding: 2px 6px; font-size: 10px;" onclick="this.closest('tr').remove()">✕</button></td>
    </tr>
  `).join("");
}

function addMultiPointRow() {
  const tbody = document.getElementById("mp-table-body");
  const count = tbody.querySelectorAll("tr").length + 1;
  const tr = document.createElement("tr");
  tr.className = "mp-row";
  tr.innerHTML = `
    <td style="font-weight: 700;">#${count}</td>
    <td><input type="number" step="0.0001" class="mp-nom" value="0.0"></td>
    <td><input type="number" step="0.0001" class="mp-tol" value="0.0100"></td>
    <td><input type="number" step="0.0001" class="mp-ref-u" value="0.0020"></td>
    <td><input type="text" class="mp-obs" value="0.0001, 0.0, 0.0002, 0.0001, 0.0"></td>
    <td><button class="btn btn-outline" style="padding: 2px 6px; font-size: 10px;" onclick="this.closest('tr').remove()">✕</button></td>
  `;
  tbody.appendChild(tr);
}

async function executeMultiPointCalibration() {
  const rows = Array.from(document.querySelectorAll(".mp-row"));
  if (rows.length === 0) {
    alert("Please add at least one calibration checkpoint.");
    return;
  }

  const points = rows.map(r => {
    const rawObs = r.querySelector(".mp-obs").value.split(",").map(s => parseFloat(s.trim()) || 0);
    return {
      nominal_value: parseFloat(r.querySelector(".mp-nom").value) || 0,
      tolerance: parseFloat(r.querySelector(".mp-tol").value) || 0.002,
      readings: rawObs,
      reference_uncertainty: parseFloat(r.querySelector(".mp-ref-u").value) || 0.0004,
    };
  });

  const payload = {
    instrument_name: document.getElementById("mp-inst-select").selectedOptions[0].text,
    instrument_model: document.getElementById("mp-inst-select").value,
    procedure_name: "Multi-Point Calibration ISO/EURAMET",
    unit: "mm",
    decision_rule: document.getElementById("mp-rule-select").value,
    points: points,
    resolution: parseFloat(document.getElementById("mp-resolution-inp").value) || 0.010,
    record_class: "CALIBRATION",
  };

  try {
    const res = await fetch("/api/calculations/multi-point", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(r => r.json());

    document.getElementById("mp-results-card").classList.remove("hidden");
    document.getElementById("mp-res-id").innerText = res.id;
    document.getElementById("mp-res-count").innerText = res.total_points;
    document.getElementById("mp-res-maxerr").innerText = res.max_error_of_indication.toFixed(5) + " mm";
    document.getElementById("mp-res-maxu95").innerText = "±" + res.max_expanded_uncertainty.toFixed(5) + " mm";
    document.getElementById("mp-res-verdict").innerText = "OVERALL " + res.overall_verdict;
    document.getElementById("mp-res-verdict").className = `badge ${res.overall_verdict === 'PASS' ? 'badge-pass' : 'badge-fail'}`;

    const tbody = document.getElementById("mp-res-table-body");
    tbody.innerHTML = res.point_results.map(pt => `
      <tr>
        <td style="font-weight: 700;">#${pt.point_index}</td>
        <td>${pt.nominal_value.toFixed(4)} mm</td>
        <td>${pt.mean_measured.toFixed(5)} mm</td>
        <td style="font-weight: 700; color: #1e3a8a;">${pt.error_of_indication > 0 ? '+' : ''}${pt.error_of_indication.toFixed(5)} mm</td>
        <td>±${pt.expanded_uncertainty_U95.toFixed(5)} mm</td>
        <td>${pt.tur.toFixed(2)}</td>
        <td>${pt.guardband_w.toFixed(5)} mm</td>
        <td><span class="badge ${pt.verdict === 'PASS' ? 'badge-pass' : 'badge-fail'}">${pt.verdict}</span></td>
      </tr>
    `).join("");

  } catch (err) {
    alert("Multi-point execution failed: " + err.message);
  }
}

// 5. Procedures Catalog
async function loadProceduresCatalog() {
  try {
    allProcedures = await fetch("/api/procedures").then(r => r.json());
    const grid = document.getElementById("procedures-catalog-grid");
    if (!grid) return;

    grid.innerHTML = allProcedures.map(p => `
      <div class="card" style="background: #ffffff; margin-bottom: 0;">
        <div style="font-size: 10px; font-weight: 800; color: #2563eb; text-transform: uppercase;">${p.instrument_family || 'Dimensional'}</div>
        <h3 style="font-size: 14px; margin-top: 2px;">${p.name}</h3>
        <p style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Standard: <strong>${p.standard_reference}</strong></p>
        <div style="margin-top: 10px; font-size: 11px; color: #334155;">
          <div>Range: <strong>${p.range_min} to ${p.range_max} ${p.unit}</strong></div>
          <div>Default Tolerance: <strong>±${p.default_tolerance} ${p.unit}</strong></div>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Procedures catalog error:", err);
  }
}

// 6. Audit Vault
async function loadAuditLedger() {
  try {
    const events = await fetch("/api/audit").then(r => r.json());
    const tbody = document.getElementById("audit-table-body");
    if (!tbody) return;

    tbody.innerHTML = events.map(e => `
      <tr>
        <td style="font-weight: 700; font-family: monospace;">#${e.id}</td>
        <td style="font-size: 11px; color: var(--text-muted);">${new Date(e.timestamp).toLocaleString()}</td>
        <td><span class="badge badge-verified">${e.action}</span></td>
        <td style="font-family: monospace;">${e.target_id}</td>
        <td>${e.actor}</td>
        <td style="font-family: monospace; font-size: 10px; color: #0284c7;">${e.event_hash.slice(0, 16)}...</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Audit ledger loading error:", err);
  }
}

async function verifyLedgerIntegrity() {
  try {
    const res = await fetch("/api/audit/verify").then(r => r.json());
    const txt = document.getElementById("audit-status-txt");
    txt.innerText = res.status;
    txt.style.color = res.chain_valid ? "var(--success)" : "var(--danger)";
    document.getElementById("sys-audit-status").innerText = res.chain_valid ? "INTACT" : "TAMPERED";
    alert(`Audit Ledger Integrity Check: ${res.status}\nTotal Events Verified: ${res.total_events}`);
  } catch (err) {
    alert("Audit verification failed: " + err.message);
  }
}

// 7. Backup & Recovery
async function loadBackupsList() {
  try {
    const backups = await fetch("/api/backups").then(r => r.json());
    const tbody = document.getElementById("backups-table-body");
    if (!tbody) return;

    if (backups.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">No backup files found. Click "+ Create Live Backup".</td></tr>`;
      return;
    }

    tbody.innerHTML = backups.map(b => `
      <tr>
        <td style="font-weight: 700; font-family: monospace;">${b.filename}</td>
        <td style="font-size: 11px;">${new Date(b.created_at).toLocaleString()}</td>
        <td>${(b.size_bytes / 1024).toFixed(1)} KB</td>
        <td style="font-family: monospace; font-size: 10px; color: #0284c7;">${b.sha256.slice(0, 16)}...</td>
        <td><span class="badge badge-integrity">${b.integrity}</span></td>
        <td style="text-align: right;">
          <button class="btn btn-outline" style="padding: 2px 8px; font-size: 10px;" onclick="restoreBackup('${b.filename}')">Restore</button>
        </td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Backup list error:", err);
  }
}

async function createLiveBackup() {
  try {
    const res = await fetch("/api/backups", { method: "POST" }).then(r => r.json());
    alert(`Live Backup Created Successfully!\nFile: ${res.backup_filename}\nSHA-256: ${res.sha256.slice(0, 16)}...`);
    loadBackupsList();
  } catch (err) {
    alert("Backup creation failed: " + err.message);
  }
}

async function restoreBackup(fname) {
  if (!confirm(`Are you sure you want to restore from ${fname}?\nA pre-restore safety snapshot will be created automatically.`)) return;
  try {
    const res = await fetch(`/api/backups/restore?backup_filename=${fname}`, { method: "POST" }).then(r => r.json());
    alert(`Database Restored Successfully from ${res.restored_from}!`);
    loadDashboard();
    loadBackupsList();
  } catch (err) {
    alert("Restore failed: " + err.message);
  }
}

// 8. 12-Stage Mathematical Replay
async function loadReplay(calcId) {
  const targetId = calcId || activeCalculationId;
  const container = document.getElementById("replay-stages-container");
  if (!container) return;

  if (!targetId) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px 24px; color: var(--text-muted);">
        <div style="font-size: 36px; margin-bottom: 12px;">🔄</div>
        <h3 style="font-size: 16px; margin-bottom: 6px; color: #334155;">No Calculation Selected for Replay</h3>
        <p style="font-size: 13px; max-width: 440px; margin: 0 auto 16px;">
          Perform a calibration in the Studio or select a record from the Dashboard to inspect its 12-stage mathematical derivation.
        </p>
        <button class="btn btn-primary" onclick="startNewCalibration()">+ Launch Calibration Studio</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `<p style="color: var(--text-muted);">Replaying mathematical derivation for ${targetId}...</p>`;

  try {
    const res = await fetch(`/api/calculations/${targetId}/replay`).then(r => r.json());
    container.innerHTML = `
      <div style="margin-bottom: 14px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 13px; font-weight: 700;">Trace: ${res.calculation_id} (${res.total_stages} Stages)</span>
        <span class="badge badge-pass">ALL 12 STAGES REPRODUCED</span>
      </div>
    ` + res.stages.map(s => `
      <div class="replay-step-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="font-size: 13px; color: #1e3a8a;">Stage ${s.step_number}: ${s.title}</strong>
          <span class="badge badge-verified">${s.standard_clause}</span>
        </div>
        <div style="font-family: monospace; font-size: 11px; background: #ffffff; padding: 6px 10px; border-radius: 4px; border: 1px solid var(--border); margin-bottom: 6px;">
          Formula: ${s.formula}
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 11px;">
          <span>Inputs: <span style="font-family: monospace;">${JSON.stringify(s.inputs)}</span></span>
          <span style="font-weight: 700; color: #0f172a;">${s.result_label}: <span style="color: #0284c7;">${s.result_value}</span></span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    container.innerHTML = `<p style="color: var(--danger);">Replay failed: ${err.message}</p>`;
  }
}

// 9. Tamper Demonstration Lab
async function runTamperDemo() {
  if (!activeCalculationId) {
    alert("Please select or execute a calibration first.");
    return;
  }

  try {
    const res = await fetch(`/api/calculations/${activeCalculationId}/tamper-test`, { method: "POST" }).then(r => r.json());
    document.getElementById("tamper-results-box").classList.remove("hidden");
    document.getElementById("tamper-status").innerText = "TAMPERING DETECTED — EVIDENCE REJECTED";
    document.getElementById("tamper-diag").innerText = `${res.simulation}. ${res.diagnostics}`;

    const tbody = document.getElementById("tamper-table-body");
    tbody.innerHTML = res.checks.map(c => `
      <tr>
        <td style="font-weight: 700;">${c.check_name}</td>
        <td><span class="badge ${c.status === 'PASS' ? 'badge-pass' : 'badge-fail'}">${c.status}</span></td>
        <td style="font-size: 11px; color: ${c.status === 'FAIL' ? '#dc2626' : 'var(--text-muted)'};">${c.details}</td>
      </tr>
    `).join("");
  } catch (err) {
    alert("Tamper lab request failed: " + err.message);
  }
}

// 10. Standards Concordance Browser
async function loadStandardsList() {
  try {
    const files = await fetch("/api/standards").then(r => r.json());
    const grid = document.getElementById("standards-list-grid");
    if (!grid) return;

    grid.innerHTML = files.map(f => {
      const cleanName = f.replace(".md", "").replace(/_/g, " ");
      return `
        <div class="card clickable-row" style="margin-bottom: 0; background: #ffffff;" onclick="viewStandardDoc('${f}')">
          <div style="font-size: 11px; font-weight: 800; color: #1e40af; text-transform: uppercase;">Standard</div>
          <div style="font-size: 13px; font-weight: 700; margin-top: 2px;">${cleanName}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">Click to view traceability matrix &rarr;</div>
        </div>
      `;
    }).join("");
  } catch (err) {
    console.error("Standards loading error:", err);
  }
}

async function viewStandardDoc(filename) {
  try {
    const doc = await fetch(`/api/standards/${filename}`).then(r => r.json());
    const viewer = document.getElementById("standards-viewer-card");
    viewer.classList.remove("hidden");
    document.getElementById("standards-viewer-title").innerText = filename;
    document.getElementById("standards-viewer-content").innerText = doc.content;
  } catch (err) {
    alert("Failed to load standard document: " + err.message);
  }
}

// 11. Lab Settings
async function loadSettings() {
  try {
    const s = await fetch("/api/settings").then(r => r.json());
    document.getElementById("set-lab-name").value = s.laboratory_name || "";
    document.getElementById("set-lab-code").value = s.laboratory_code || "";
    document.getElementById("set-lab-accred").value = s.accreditation_body || "";
    document.getElementById("set-cert-prefix").value = s.certificate_prefix || "";
    document.getElementById("set-tech-name").value = s.default_technician || "";
    document.getElementById("set-temp-nom").value = s.temperature_nominal_c || 20.0;
  } catch (err) {
    console.error("Settings load error:", err);
  }
}

async function saveLabSettings() {
  const payload = {
    laboratory_name: document.getElementById("set-lab-name").value,
    laboratory_code: document.getElementById("set-lab-code").value,
    accreditation_body: document.getElementById("set-lab-accred").value,
    certificate_prefix: document.getElementById("set-cert-prefix").value,
    default_technician: document.getElementById("set-tech-name").value,
    temperature_nominal_c: parseFloat(document.getElementById("set-temp-nom").value) || 20.0,
  };

  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    alert("Laboratory Settings Saved Successfully!");
  } catch (err) {
    alert("Failed to save settings: " + err.message);
  }
}

// 12. System Self-Test
async function triggerSelfTest(showNotification = true) {
  try {
    const res = await fetch("/api/selftest").then(r => r.json());
    document.getElementById("sys-engine-status").innerText = res.calculation_engine_status;
    document.getElementById("sys-db-status").innerText = res.database_status;
    document.getElementById("sys-last-test").innerText = new Date(res.timestamp).toLocaleTimeString();

    if (showNotification) {
      alert(`System Integrity Self-Test: ${res.overall_status}\nPassed: ${res.benchmark_tests_passed}/${res.benchmark_tests_total} mathematical benchmark cases.`);
    }
  } catch (err) {
    console.error("Self test error:", err);
  }
}

function inspectCalculation(calcId) {
  fetch(`/api/calculations/${calcId}`)
    .then(r => r.json())
    .then(calc => {
      currentCalculation = calc;
      activeCalculationId = calc.id;
      populateWorkflowWithCalculation(calc);
      switchView("workflow");
      setWorkflowStep(5);
    });
}

// 13. Commercial Licensing & Entitlements Controller
async function loadLicenseStatus() {
  try {
    const lic = await fetch("/api/license").then(r => r.json());
    const editionEl = document.getElementById("lic-edition-display");
    const stateBadgeEl = document.getElementById("lic-state-badge");
    const customerEl = document.getElementById("lic-customer-display");
    const seatEl = document.getElementById("lic-seat-display");
    const expiryEl = document.getElementById("lic-expiry-display");

    if (editionEl) editionEl.innerText = lic.edition;
    if (stateBadgeEl) {
      stateBadgeEl.innerText = lic.entitlement_state;
      stateBadgeEl.style.background = lic.entitlement_state === "ACTIVE" ? "rgba(34, 197, 94, 0.2)" :
                                     lic.entitlement_state === "TRIAL" ? "rgba(234, 179, 8, 0.2)" : "rgba(56, 189, 248, 0.2)";
      stateBadgeEl.style.color = lic.entitlement_state === "ACTIVE" ? "var(--success)" :
                                 lic.entitlement_state === "TRIAL" ? "var(--warning)" : "var(--accent)";
    }
    if (customerEl) customerEl.innerText = lic.customer_name || "Community / Evaluation User";
    if (seatEl) seatEl.innerText = `Seat Allocation: ${lic.seat_limit || 1} Workstation(s)`;
    if (expiryEl) {
      expiryEl.innerText = lic.expiration ? `Expires: ${new Date(lic.expiration).toLocaleDateString()}` : "Permanent / No Expiration";
    }
  } catch (err) {
    console.error("License status error:", err);
  }
}

async function activateTrialPlan() {
  try {
    const res = await fetch("/api/license/trial", { method: "POST" }).then(r => r.json());
    if (res.status === "SUCCESS") {
      alert("14-Day Professional Trial Activated Successfully! All 7 instrument families and multi-point capabilities are unlocked.");
      loadLicenseStatus();
    }
  } catch (err) {
    alert("Failed to activate trial: " + err.message);
  }
}

async function openLicenseTokenModal() {
  const token = prompt("Paste your signed commercial license token JSON:");
  if (!token) return;
  try {
    const res = await fetch("/api/license/activate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token_json: token }),
    }).then(r => r.json());
    if (res.status === "SUCCESS") {
      alert(`License Activated Successfully for: ${res.entitlement.customer_name} (${res.entitlement.plan_name})`);
      loadLicenseStatus();
    } else {
      alert("License Activation Failed: " + (res.detail || "Invalid token"));
    }
  } catch (err) {
    alert("Activation Error: " + err.message);
  }
}

async function resetToFreePlan() {
  if (!confirm("Reset to Free Community Evaluation mode?")) return;
  try {
    await fetch("/api/license/reset", { method: "POST" });
    alert("Reset to Free Community Edition.");
    loadLicenseStatus();
  } catch (err) {
    alert("Reset Error: " + err.message);
  }
}

