/**
 * METROLOGY WORKSTATION V5
 * Client-side Workstation Controllers & Workbench Logic.
 */

let activeView = "dashboard";
let activeCalculationId = null;
let uncertaintyComponentsList = [];

document.addEventListener("DOMContentLoaded", () => {
  initWorkstation();
});

function initWorkstation() {
  loadDashboard();
  loadProjects();
  loadInstruments();
  loadMeasurementPlans();
  loadDefaultUncertaintyBudget();
  calculateConformityWorkbench();
  loadAuditLedger();
}

function switchView(viewName) {
  activeView = viewName;
  document.querySelectorAll(".sidebar-menu li").forEach(li => li.classList.remove("active"));
  const activeNav = document.getElementById(`nav-${viewName}`);
  if (activeNav) activeNav.classList.add("active");

  const views = [
    "dashboard", "projects", "instruments", "plans", "acquisition",
    "uncertainty-wb", "conformity-wb", "intelligence", "workflow",
    "multipoint", "calibrations", "procedures", "replay", "tamper",
    "audit", "backups", "standards", "settings", "license"
  ];

  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
  });

  const topLabel = document.getElementById("topbar-current-view");
  if (topLabel) {
    topLabel.innerText = viewName.toUpperCase().replace("-", " ");
  }

  // View specific refresh triggers
  if (viewName === "dashboard") loadDashboard();
  if (viewName === "projects") loadProjects();
  if (viewName === "instruments") loadInstruments();
  if (viewName === "plans") loadMeasurementPlans();
  if (viewName === "acquisition") loadAcquisitionPlans();
  if (viewName === "calibrations") loadCalibrationsLog();
  if (viewName === "audit") loadAuditLedger();
  if (viewName === "backups") loadBackups();
  if (viewName === "intelligence") loadMeasurementIntelligence();
}

// ==========================================
// 1. DASHBOARD CONTROLLER
// ==========================================

async function loadDashboard() {
  try {
    const res = await fetch("/api/v5/stats");
    if (!res.ok) return;
    const data = await res.json();

    const elProj = document.getElementById("stat-active-projects");
    if (elProj) elProj.innerText = data.active_projects || 0;

    const elInst = document.getElementById("stat-total-instruments");
    if (elInst) elInst.innerText = data.total_instruments || 0;

    const elOverdue = document.getElementById("stat-overdue-instruments");
    if (elOverdue) elOverdue.innerText = data.overdue_instruments || 0;

    const elTotal = document.getElementById("stat-total");
    if (elTotal) elTotal.innerText = data.total_calibrations || 0;

    const emptyCard = document.getElementById("empty-workspace-card");
    const featCard = document.getElementById("featured-calibration-card");

    if (data.total_calibrations === 0 && data.active_projects === 0 && data.total_instruments === 0) {
      if (emptyCard) emptyCard.classList.remove("hidden");
      if (featCard) featCard.classList.add("hidden");
    } else {
      if (emptyCard) emptyCard.classList.add("hidden");
      loadLatestCalibrationTelemetry();
    }
  } catch (err) {
    console.error("Failed to load dashboard stats:", err);
  }
}

async function loadLatestCalibrationTelemetry() {
  try {
    const res = await fetch("/api/calibrations?limit=1");
    if (!res.ok) return;
    const list = await res.json();
    if (list.length > 0) {
      const c = list[0];
      activeCalculationId = c.id;
      const featCard = document.getElementById("featured-calibration-card");
      if (featCard) featCard.classList.remove("hidden");

      document.getElementById("feat-title").innerText = `${c.instrument_name} — ${c.procedure_name}`;
      document.getElementById("feat-id-label").innerText = c.id;
      document.getElementById("feat-meas").innerText = `${c.nominal_value} mm / ${c.result_data?.summary?.measured_mean_mm || c.nominal_value} mm`;
      document.getElementById("feat-unc").innerText = `±${c.result_data?.uncertainty_summary?.expanded_uncertainty_U95_mm || "0.00078"} mm`;
      document.getElementById("feat-tur").innerText = `TUR: ${c.result_data?.decision_summary?.tur || "2.564"}`;
      document.getElementById("feat-verdict").innerHTML = `<span class="badge badge-${c.conformity_verdict.toLowerCase()}">${c.conformity_verdict}</span>`;

      // Update Inspector
      document.getElementById("insp-inst-name").innerText = c.instrument_name;
      document.getElementById("insp-hash-in").innerText = c.input_sha256;
      document.getElementById("insp-hash-calc").innerText = c.calculation_sha256;
    }
  } catch (e) {
    console.error("Error loading telemetry:", e);
  }
}

// ==========================================
// 2. PROJECTS CONTROLLER
// ==========================================

function showNewProjectForm() {
  const c = document.getElementById("new-project-form-container");
  if (c) c.classList.remove("hidden");
}

function hideNewProjectForm() {
  const c = document.getElementById("new-project-form-container");
  if (c) c.classList.add("hidden");
}

async function loadProjects() {
  try {
    const res = await fetch("/api/projects");
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("projects-tbody");
    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No projects found. Create one above.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(p => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: bold;">${p.id}</td>
        <td style="font-weight: 600;">${escapeHtml(p.name)}</td>
        <td>${escapeHtml(p.customer_site || "—")}</td>
        <td><span class="badge badge-${p.status.toLowerCase()}">${p.status}</span></td>
        <td>${p.created_at.substring(0, 10)}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="setActiveProject('${p.id}', '${escapeHtml(p.name)}')">Select</button>
          <button class="btn btn-danger btn-sm" onclick="deleteProjectById('${p.id}')">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Error loading projects:", e);
  }
}

async function submitCreateProject() {
  const name = document.getElementById("inp-proj-name").value.trim();
  if (!name) {
    alert("Please enter a project name.");
    return;
  }
  const site = document.getElementById("inp-proj-site").value.trim();
  const desc = document.getElementById("inp-proj-desc").value.trim();

  try {
    const res = await fetch("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, customer_site: site, description: desc }),
    });
    if (res.ok) {
      hideNewProjectForm();
      document.getElementById("inp-proj-name").value = "";
      document.getElementById("inp-proj-site").value = "";
      document.getElementById("inp-proj-desc").value = "";
      loadProjects();
      loadDashboard();
    } else {
      alert("Failed to create project.");
    }
  } catch (e) {
    alert("Network error creating project.");
  }
}

async function deleteProjectById(id) {
  if (!confirm(`Delete project ${id}?`)) return;
  try {
    await fetch(`/api/projects/${id}`, { method: "DELETE" });
    loadProjects();
    loadDashboard();
  } catch (e) {
    alert("Error deleting project.");
  }
}

function setActiveProject(id, name) {
  document.getElementById("insp-proj-name").innerText = name;
  document.getElementById("insp-proj-site").innerText = id;
}

// ==========================================
// 3. INSTRUMENTS CONTROLLER
// ==========================================

function showNewInstrumentForm() {
  const c = document.getElementById("new-instrument-form-container");
  if (c) c.classList.remove("hidden");
}

function hideNewInstrumentForm() {
  const c = document.getElementById("new-instrument-form-container");
  if (c) c.classList.add("hidden");
}

async function loadInstruments() {
  try {
    const res = await fetch("/api/instruments");
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("instruments-tbody");
    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-muted);">No instruments registered. Register one above.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(inst => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: bold;">${inst.id}</td>
        <td style="font-weight: 600;">${escapeHtml(inst.manufacturer)} ${escapeHtml(inst.model)}</td>
        <td>${escapeHtml(inst.serial_number || "—")}</td>
        <td>${inst.instrument_type}</td>
        <td>${inst.range_min}–${inst.range_max} mm</td>
        <td>${inst.resolution} mm</td>
        <td><span class="badge badge-${inst.calibration_status.toLowerCase()}">${inst.calibration_status}</span></td>
        <td>${inst.next_calibration_due ? inst.next_calibration_due.substring(0, 10) : "—"}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="setActiveInstrument('${inst.id}', '${escapeHtml(inst.manufacturer)} ${escapeHtml(inst.model)}')">Select</button>
          <button class="btn btn-danger btn-sm" onclick="deleteInstrumentById('${inst.id}')">Delete</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Error loading instruments:", e);
  }
}

async function submitCreateInstrument() {
  const mfg = document.getElementById("inp-inst-mfg").value.trim();
  const model = document.getElementById("inp-inst-model").value.trim();
  if (!mfg || !model) {
    alert("Please provide manufacturer and model.");
    return;
  }
  const sn = document.getElementById("inp-inst-sn").value.trim();
  const type = document.getElementById("inp-inst-type").value;
  const min = parseFloat(document.getElementById("inp-inst-min").value);
  const max = parseFloat(document.getElementById("inp-inst-max").value);
  const resVal = parseFloat(document.getElementById("inp-inst-res").value);
  const interval = parseInt(document.getElementById("inp-inst-interval").value);

  try {
    const res = await fetch("/api/instruments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        manufacturer: mfg,
        model: model,
        serial_number: sn,
        instrument_type: type,
        range_min: min,
        range_max: max,
        resolution: resVal,
        calibration_interval_months: interval,
      }),
    });
    if (res.ok) {
      hideNewInstrumentForm();
      loadInstruments();
      loadDashboard();
    } else {
      alert("Failed to register instrument.");
    }
  } catch (e) {
    alert("Error registering instrument.");
  }
}

async function deleteInstrumentById(id) {
  if (!confirm(`Delete instrument ${id}?`)) return;
  try {
    await fetch(`/api/instruments/${id}`, { method: "DELETE" });
    loadInstruments();
    loadDashboard();
  } catch (e) {
    alert("Error deleting instrument.");
  }
}

function setActiveInstrument(id, name) {
  document.getElementById("insp-inst-name").innerText = `${name} (${id})`;
}

// ==========================================
// 4. MEASUREMENT PLANS CONTROLLER
// ==========================================

function showNewPlanForm() {
  const c = document.getElementById("new-plan-form-container");
  if (c) c.classList.remove("hidden");
}

function hideNewPlanForm() {
  const c = document.getElementById("new-plan-form-container");
  if (c) c.classList.add("hidden");
}

async function loadMeasurementPlans() {
  try {
    const res = await fetch("/api/plans");
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("plans-tbody");
    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No measurement plans defined. Create one above.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(p => `
      <tr>
        <td style="font-family: var(--font-mono); font-weight: bold;">${p.id}</td>
        <td style="font-weight: 600;">${escapeHtml(p.plan_name)}</td>
        <td>${p.measurand}</td>
        <td>${p.nominal_value} mm</td>
        <td>[${p.tolerance_lower}, +${p.tolerance_upper}] mm</td>
        <td>${p.required_repetitions}</td>
        <td>${p.decision_rule}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openPlanInAcquisition('${p.id}')">Acquire &rarr;</button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Error loading plans:", e);
  }
}

async function submitCreatePlan() {
  const name = document.getElementById("inp-plan-name").value.trim();
  if (!name) {
    alert("Please enter a plan name.");
    return;
  }
  const meas = document.getElementById("inp-plan-measurand").value;
  const nom = parseFloat(document.getElementById("inp-plan-nominal").value);
  const toll = parseFloat(document.getElementById("inp-plan-toll").value);
  const tolu = parseFloat(document.getElementById("inp-plan-tolu").value);
  const reps = parseInt(document.getElementById("inp-plan-reps").value);
  const rule = document.getElementById("inp-plan-rule").value;

  try {
    const res = await fetch("/api/plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan_name: name,
        measurand: meas,
        nominal_value: nom,
        tolerance_lower: toll,
        tolerance_upper: tolu,
        required_repetitions: reps,
        decision_rule: rule,
      }),
    });
    if (res.ok) {
      hideNewPlanForm();
      loadMeasurementPlans();
    } else {
      alert("Failed to save plan.");
    }
  } catch (e) {
    alert("Error saving plan.");
  }
}

// ==========================================
// 5. ACQUISITION STUDIO CONTROLLER
// ==========================================

async function loadAcquisitionPlans() {
  try {
    const res = await fetch("/api/plans");
    if (!res.ok) return;
    const list = await res.json();
    const sel = document.getElementById("acq-select-plan");
    if (!sel) return;
    sel.innerHTML = `<option value="">-- Select Plan --</option>` + list.map(p => `<option value="${p.id}">${escapeHtml(p.plan_name)} (${p.nominal_value} mm)</option>`).join("");
  } catch (e) {}
}

function onAcquisitionPlanChanged() {
  const sel = document.getElementById("acq-select-plan");
  if (sel && sel.value) {
    populateSampleReadings();
  }
}

function populateSampleReadings() {
  const t = document.getElementById("acq-readings-input");
  if (t) {
    t.value = "25.0012, 25.0010, 25.0014, 25.0011, 25.0013";
    liveAnalyzeAcquisition();
  }
}

function liveAnalyzeAcquisition() {
  const text = document.getElementById("acq-readings-input")?.value || "";
  const nums = text.split(/[\s,]+/).map(s => parseFloat(s)).filter(n => !isNaN(n));
  const n = nums.length;

  document.getElementById("acq-stat-n").innerText = n;
  if (n === 0) return;

  const mean = nums.reduce((a, b) => a + b, 0) / n;
  document.getElementById("acq-stat-mean").innerText = `${mean.toFixed(5)} mm`;

  if (n > 1) {
    const variance = nums.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (n - 1);
    const sd = Math.sqrt(variance);
    const u_rep = sd / Math.sqrt(n);
    document.getElementById("acq-stat-sd").innerText = `${sd.toFixed(6)} mm`;
    document.getElementById("acq-stat-urep").innerText = `±${u_rep.toFixed(6)} mm`;
  }
}

async function submitAcquisition() {
  const planId = document.getElementById("acq-select-plan").value;
  const operator = document.getElementById("acq-operator").value;
  const text = document.getElementById("acq-readings-input").value;
  const raw = text.split(/[\s,]+/).map(s => parseFloat(s)).filter(n => !isNaN(n));

  if (raw.length === 0) {
    alert("Please enter readings.");
    return;
  }

  try {
    const res = await fetch("/api/measurements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan_id: planId || null,
        raw_values: raw,
        operator: operator,
      }),
    });
    if (res.ok) {
      alert("Measurement dataset acquired and verified.");
      loadDashboard();
    }
  } catch (e) {
    alert("Error saving acquisition.");
  }
}

function openPlanInAcquisition(planId) {
  switchView("acquisition");
  setTimeout(() => {
    const sel = document.getElementById("acq-select-plan");
    if (sel) {
      sel.value = planId;
      populateSampleReadings();
    }
  }, 100);
}

// ==========================================
// 6. UNCERTAINTY WORKBENCH CONTROLLER
// ==========================================

function loadDefaultUncertaintyBudget() {
  uncertaintyComponentsList = [
    { name: "Repeatability (Type A)", distribution: "normal", semi_range: 0.00014, coverage_factor_k: 1.0, sensitivity_coefficient: 1.0, degrees_of_freedom: 4.0 },
    { name: "Digital Resolution", distribution: "rectangular", semi_range: 0.0005, coverage_factor_k: 1.0, sensitivity_coefficient: 1.0, degrees_of_freedom: 50.0 },
    { name: "Reference Standard Uncertainty", distribution: "normal", semi_range: 0.00040, coverage_factor_k: 2.0, sensitivity_coefficient: 1.0, degrees_of_freedom: 50.0 },
    { name: "Thermal Expansion Uncertainty", distribution: "rectangular", semi_range: 0.00030, coverage_factor_k: 1.0, sensitivity_coefficient: 1.0, degrees_of_freedom: 50.0 }
  ];
  renderUncertaintyTable();
  calculateUncertaintyWorkbench();
}

function renderUncertaintyTable() {
  const tbody = document.getElementById("uncertainty-wb-tbody");
  if (!tbody) return;

  tbody.innerHTML = uncertaintyComponentsList.map((c, idx) => `
    <tr>
      <td><input type="text" class="form-control" style="font-size: 11px; padding: 2px 4px;" value="${escapeHtml(c.name)}" onchange="uncertaintyComponentsList[${idx}].name=this.value"></td>
      <td>
        <select class="form-control" style="font-size: 11px; padding: 2px 4px;" onchange="uncertaintyComponentsList[${idx}].distribution=this.value">
          <option value="normal" ${c.distribution === "normal" ? "selected" : ""}>Normal</option>
          <option value="rectangular" ${c.distribution === "rectangular" ? "selected" : ""}>Rectangular (√3)</option>
          <option value="triangular" ${c.distribution === "triangular" ? "selected" : ""}>Triangular (√6)</option>
          <option value="u_shaped" ${c.distribution === "u_shaped" ? "selected" : ""}>U-Shaped (√2)</option>
        </select>
      </td>
      <td><input type="number" step="0.00001" class="form-control" style="font-size: 11px; padding: 2px 4px;" value="${c.semi_range}" onchange="uncertaintyComponentsList[${idx}].semi_range=parseFloat(this.value)"></td>
      <td><input type="number" step="0.1" class="form-control" style="font-size: 11px; padding: 2px 4px;" value="${c.coverage_factor_k}" onchange="uncertaintyComponentsList[${idx}].coverage_factor_k=parseFloat(this.value)"></td>
      <td><input type="number" step="0.1" class="form-control" style="font-size: 11px; padding: 2px 4px;" value="${c.sensitivity_coefficient}" onchange="uncertaintyComponentsList[${idx}].sensitivity_coefficient=parseFloat(this.value)"></td>
      <td><input type="number" class="form-control" style="font-size: 11px; padding: 2px 4px;" value="${c.degrees_of_freedom}" onchange="uncertaintyComponentsList[${idx}].degrees_of_freedom=parseFloat(this.value)"></td>
      <td><button class="btn btn-danger btn-sm" onclick="removeUncertaintyRow(${idx})">✕</button></td>
    </tr>
  `).join("");
}

function addUncertaintyRow() {
  uncertaintyComponentsList.push({
    name: `Uncertainty Factor #${uncertaintyComponentsList.length + 1}`,
    distribution: "rectangular",
    semi_range: 0.00020,
    coverage_factor_k: 1.0,
    sensitivity_coefficient: 1.0,
    degrees_of_freedom: 50.0,
  });
  renderUncertaintyTable();
}

function removeUncertaintyRow(idx) {
  uncertaintyComponentsList.splice(idx, 1);
  renderUncertaintyTable();
  calculateUncertaintyWorkbench();
}

async function calculateUncertaintyWorkbench() {
  if (uncertaintyComponentsList.length === 0) return;
  try {
    const res = await fetch("/api/workbench/uncertainty", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ components: uncertaintyComponentsList }),
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("uwb-res-uc").innerText = `±${data.combined_uncertainty_uc.toFixed(6)} mm`;
    document.getElementById("uwb-res-dof").innerText = data.effective_degrees_of_freedom.toFixed(1);
    document.getElementById("uwb-res-k").innerText = data.coverage_factor_k.toFixed(3);
    document.getElementById("uwb-res-u95").innerText = `±${data.expanded_uncertainty_U95.toFixed(6)} mm`;

    const tb = document.getElementById("uwb-breakdown-tbody");
    if (tb) {
      tb.innerHTML = data.budget_breakdown.map(row => `
        <tr>
          <td style="font-weight: 600;">${escapeHtml(row.name)}</td>
          <td>${row.distribution}</td>
          <td style="font-family: var(--font-mono);">±${row.standard_uncertainty.toFixed(6)} mm</td>
          <td style="font-family: var(--font-mono);">${row.variance_contribution.toExponential(4)}</td>
          <td><strong style="color: var(--primary);">${row.percentage_contribution}</strong></td>
        </tr>
      `).join("");
    }
  } catch (e) {
    console.error("Error calculating GUM workbench:", e);
  }
}

// ==========================================
// 7. CONFORMITY WORKBENCH CONTROLLER
// ==========================================

async function calculateConformityWorkbench() {
  const nom = parseFloat(document.getElementById("cwb-nominal")?.value || 25.0);
  const meas = parseFloat(document.getElementById("cwb-measured")?.value || 25.0012);
  const toll = parseFloat(document.getElementById("cwb-toll")?.value || -0.002);
  const tolu = parseFloat(document.getElementById("cwb-tolu")?.value || 0.002);
  const u95 = parseFloat(document.getElementById("cwb-u95")?.value || 0.00078);
  const rule = document.getElementById("cwb-rule")?.value || "ANSI/NCSL Z540.3 Method 6";

  try {
    const res = await fetch("/api/workbench/conformity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nominal_value: nom,
        measured_value: meas,
        tolerance_lower: toll,
        tolerance_upper: tolu,
        expanded_uncertainty_U95: u95,
        decision_rule: rule,
      }),
    });
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("cwb-res-error").innerText = `${data.error_of_indication >= 0 ? "+" : ""}${data.error_of_indication.toFixed(5)} mm`;
    document.getElementById("cwb-res-tur").innerText = data.tur.toFixed(3);
    document.getElementById("cwb-res-w").innerText = `${data.guardband_width_w.toFixed(6)} mm`;
    document.getElementById("cwb-res-pfa").innerText = `≤ ${data.consumer_risk_pfa_pct.toFixed(1)}%`;
    document.getElementById("cwb-res-interval").innerText = `[${data.acceptance_lower.toFixed(5)}, ${data.acceptance_upper.toFixed(5)}] mm`;
    document.getElementById("cwb-res-statement").innerText = data.derivation_statement;

    const b = document.getElementById("cwb-verdict-badge");
    if (b) {
      b.className = `badge badge-${data.conformance_verdict.toLowerCase().replace("_", "-")}`;
      b.innerText = data.conformance_verdict;
    }
  } catch (e) {
    console.error("Error calculating conformity:", e);
  }
}

// ==========================================
// 8. AUDIT LEDGER CONTROLLER
// ==========================================

async function loadAuditLedger() {
  try {
    const res = await fetch("/api/audit?limit=50");
    if (!res.ok) return;
    const list = await res.json();
    const tbody = document.getElementById("audit-tbody");
    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No audit events recorded.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(ev => `
      <tr>
        <td style="font-family: var(--font-mono);">${ev.id}</td>
        <td>${ev.timestamp.substring(0, 19).replace("T", " ")}</td>
        <td><strong style="color: var(--primary);">${ev.action}</strong></td>
        <td style="font-family: var(--font-mono);">${escapeHtml(ev.target_id)}</td>
        <td>${escapeHtml(ev.actor)}</td>
        <td style="font-family: var(--font-mono); font-size: 10px; color: var(--accent);">${ev.event_hash ? ev.event_hash.substring(0, 16) : "—"}...</td>
      </tr>
    `).join("");
  } catch (e) {}
}

// ==========================================
// 9. REPLAY & TAMPER CONTROLLER
// ==========================================

function openReplayForActive() {
  if (!activeCalculationId) return;
  switchView("replay");
  loadReplayForId(activeCalculationId);
}

async function loadReplayForId(id) {
  try {
    const res = await fetch(`/api/replay/${id}`);
    if (!res.ok) return;
    const data = await res.json();
    const out = document.getElementById("replay-output");
    if (out) {
      out.innerHTML = `
        <div style="background: #f8fafc; padding: 12px; border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 10px;">
          <h3 style="margin-bottom: 6px;">12-Stage Mathematical Derivation Replay</h3>
          <p>Reproducing exact derivation for <strong>${id}</strong> across 50-digit exact decimal context.</p>
          <div style="margin-top: 8px; font-family: var(--font-mono); font-size: 11px;">
            ${(data.replay_stages || []).map((st, i) => `<div>[Stage ${i+1}] ${escapeHtml(st.title || st.name)}: <strong>${escapeHtml(st.summary || "OK")}</strong></div>`).join("")}
          </div>
        </div>
      `;
    }
  } catch (e) {}
}

function openActiveEvidence() {
  if (activeCalculationId) {
    window.open(`/api/evidence/${activeCalculationId}`, "_blank");
  }
}

// ==========================================
// 10. SYSTEM SELF-TEST
// ==========================================

async function triggerSelfTest() {
  try {
    const res = await fetch("/api/selftest", { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    alert(`System Self-Test Completed:\n${data.tests_run} tests executed.\nStatus: ${data.status.toUpperCase()}`);
    loadDashboard();
  } catch (e) {
    alert("Self-test execution error.");
  }
}

function startNewCalibration() {
  switchView("workflow");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
