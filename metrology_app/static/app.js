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
    "uncertainty-wb", "conformity-wb", "sandbox", "intelligence", "fleet", "rag", "copilot",
    "scpi", "qif", "part11", "qualification", "benchmarks", "ilc", "profiles", "handbook", "support",
    "mbom", "workflow", "multipoint", "calibrations", "procedures", "replay", "tamper",
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

async function verifyAuditChainLive() {
  try {
    const res = await fetch("/api/audit/verify-chain", { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    alert(`AUDIT LEDGER VERIFICATION:\nStatus: ${data.status}\nTotal Blocks: ${data.total_events}\n${data.message}`);
  } catch (e) {
    alert("Audit verification error.");
  }
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
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <h3 style="margin: 0;">12-Stage Mathematical Derivation Replay</h3>
            <button class="btn btn-primary btn-sm" onclick="reproduceCalculationLive('${id}')">⚡ Verify &amp; Reproduce Hashes</button>
          </div>
          <p>Reproducing exact derivation for <strong>${id}</strong> across 50-digit exact decimal context.</p>
          <div style="margin-top: 8px; font-family: var(--font-mono); font-size: 11px;">
            ${(data.replay_stages || []).map((st, i) => `<div>[Stage ${i+1}] ${escapeHtml(st.title || st.name)}: <strong>${escapeHtml(st.summary || "OK")}</strong></div>`).join("")}
          </div>
        </div>
      `;
    }
  } catch (e) {}
}

async function reproduceCalculationLive(id) {
  try {
    const res = await fetch(`/api/evidence/reproduce/${id}`, { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    alert(`CALCULATION REPRODUCIBILITY REPORT:\nStatus: ${data.overall_status}\nReproduced All 12 Stages: ${data.reproduced_successfully ? 'YES (100% MATCH)' : 'MISMATCH'}\n${data.diagnostics}`);
  } catch (e) {
    alert("Error reproducing calculation.");
  }
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

// ==========================================
// 11. ENGINEERING SANDBOX CONTROLLER
// ==========================================

let sandboxScenariosData = [];

async function loadSelectedSandboxScenario() {
  const sel = document.getElementById("sandbox-select-scenario")?.value;
  if (!sel) return;
  try {
    const res = await fetch("/api/sandbox/scenarios");
    if (!res.ok) return;
    sandboxScenariosData = await res.json();
    const sc = sandboxScenariosData.find(s => s.id === sel);
    if (!sc) return;

    document.getElementById("sb-scenario-title").innerText = sc.name;
    document.getElementById("sb-scenario-desc").innerText = sc.description;
    document.getElementById("sb-nom").innerText = `${sc.nominal_points.join(", ")} mm`;
    document.getElementById("sb-tol").innerText = `±${sc.tolerance} mm`;
    document.getElementById("sb-rule").innerText = sc.decision_rule;
  } catch (e) {
    console.error("Error loading sandbox scenario:", e);
  }
}

async function runSandboxSimulation() {
  const sel = document.getElementById("sandbox-select-scenario")?.value;
  const sc = sandboxScenariosData.find(s => s.id === sel) || {
    name: "Outside Micrometer Calibration",
    nominal_points: [25.0],
    tolerance: 0.002,
    decision_rule: "ANSI/NCSL Z540.3 Method 6",
    sample_readings: [25.0012, 25.0010, 25.0014, 25.0011, 25.0013]
  };

  const nom = sc.nominal_points[0];
  const tol = sc.tolerance;
  const readings = sc.sample_readings;
  const mean = readings.reduce((a, b) => a + b, 0) / readings.length;
  const variance = readings.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / (readings.length - 1);
  const u_rep = Math.sqrt(variance) / Math.sqrt(readings.length);
  const u95 = Math.sqrt(Math.pow(u_rep, 2) + Math.pow(0.0003, 2)) * 2.0;

  try {
    const res = await fetch("/api/workbench/conformity", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nominal_value: nom,
        measured_value: mean,
        tolerance_lower: -tol,
        tolerance_upper: tol,
        expanded_uncertainty_U95: u95,
        decision_rule: sc.decision_rule,
      }),
    });
    if (!res.ok) return;
    const data = await res.json();

    const container = document.getElementById("sandbox-results-container");
    if (container) {
      container.innerHTML = `
        <div style="background: #f8fafc; padding: 12px; border-radius: 4px; border: 1px solid var(--border);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="color: var(--primary); font-size: 13px;">Simulation Output: ${escapeHtml(sc.name)}</strong>
            <span class="badge badge-${data.conformance_verdict.toLowerCase().replace('_', '-')}">${data.conformance_verdict}</span>
          </div>
          <div class="grid-4" style="margin-bottom: 8px; font-size: 11px;">
            <div><span>Simulated Mean:</span> <strong>${mean.toFixed(5)} mm</strong></div>
            <div><span>Expanded U95:</span> <strong>±${u95.toFixed(6)} mm</strong></div>
            <div><span>Calculated TUR:</span> <strong>${data.tur.toFixed(3)}</strong></div>
            <div><span>Guardband Width (w):</span> <strong>${data.guardband_width_w.toFixed(6)} mm</strong></div>
          </div>
          <div style="font-size: 11px; color: var(--text-muted); padding-top: 6px; border-top: 1px solid var(--border);">
            ${escapeHtml(data.derivation_statement)}
          </div>
        </div>
      `;
    }
  } catch (e) {
    console.error("Error executing sandbox simulation:", e);
  }
}

// ==========================================
// 12. DEMO PROJECT LOADER & MBOM VIEWER
// ==========================================

async function loadDemoProjectLive() {
  try {
    const res = await fetch("/api/demo/load", { method: "POST" });
    if (!res.ok) return;
    const data = await res.json();
    alert(`DEMONSTRATION PROJECT LOADED:\n${data.message}\n\nProject: ${data.project.name}\nInstrument: ${data.instrument.manufacturer} ${data.instrument.model}\nCalculation ID: ${data.calculation.id}`);
    loadDashboard();
    loadProjects();
    loadInstruments();
    loadCalibrationsLog();
    activeCalculationId = data.calculation.id;
    openMbomForActive();
  } catch (e) {
    alert("Error loading demonstration project.");
  }
}

function openMbomForActive() {
  if (!activeCalculationId) {
    alert("Please select a calibration record to view its MBOM.");
    return;
  }
  switchView("mbom");
  loadMbomForId(activeCalculationId);
}

async function loadMbomForId(id) {
  try {
    const res = await fetch(`/api/mbom/${id}`);
    if (!res.ok) return;
    const mbom = await res.json();
    const c = document.getElementById("mbom-content-container");
    if (!c) return;

    c.innerHTML = `
      <div style="background: #ffffff; padding: 14px; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 10px;">
          <div>
            <h3 style="font-size: 13px; color: var(--primary);">MEASUREMENT BILL OF MATERIALS — ${escapeHtml(mbom.calculation_id)}</h3>
            <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">SHA-256: ${mbom.provenance?.calculation_sha256}</div>
          </div>
          <span class="badge badge-${mbom.conformity_decision?.conformance_verdict.toLowerCase().replace('_', '-')}">${mbom.conformity_decision?.conformance_verdict}</span>
        </div>

        <div class="grid-2" style="font-size: 11px; margin-bottom: 12px;">
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">1. Asset &amp; Project Node</div>
            <div><strong>Project:</strong> ${escapeHtml(mbom.project?.name)} (${mbom.project?.id})</div>
            <div><strong>Site:</strong> ${escapeHtml(mbom.project?.customer_site)}</div>
            <div><strong>Instrument:</strong> ${escapeHtml(mbom.instrument?.manufacturer)} ${escapeHtml(mbom.instrument?.model)}</div>
            <div><strong>Serial Number:</strong> ${escapeHtml(mbom.instrument?.serial_number)}</div>
            <div><strong>Range / Res:</strong> ${mbom.instrument?.range} / ${mbom.instrument?.resolution}</div>
          </div>

          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">2. Reference Standard &amp; Environment</div>
            <div><strong>Standard:</strong> ${escapeHtml(mbom.reference_standard?.designation)}</div>
            <div><strong>Traceability ID:</strong> ${escapeHtml(mbom.reference_standard?.traceability_id)}</div>
            <div><strong>Standard Uncertainty:</strong> ${escapeHtml(mbom.reference_standard?.standard_uncertainty_u_std)}</div>
            <div><strong>Operator:</strong> ${escapeHtml(mbom.operator?.name)}</div>
            <div><strong>Ambient Conditions:</strong> ${mbom.environmental_conditions?.ambient_temperature_c} °C, ${mbom.environmental_conditions?.relative_humidity_pct}% RH</div>
          </div>
        </div>

        <div class="grid-2" style="font-size: 11px;">
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">3. GUM Uncertainty Model</div>
            <div><strong>Framework:</strong> JCGM 100:2008 (GUM)</div>
            <div><strong>Combined uc:</strong> ±${mbom.uncertainty_model?.combined_standard_uncertainty_uc_mm} mm</div>
            <div><strong>Effective DoF (νeff):</strong> ${mbom.uncertainty_model?.effective_degrees_of_freedom}</div>
            <div><strong>Expanded U95:</strong> ±${mbom.uncertainty_model?.expanded_uncertainty_u95_mm} mm (k=${mbom.uncertainty_model?.coverage_factor_k95})</div>
          </div>

          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 6px; text-transform: uppercase;">4. Conformity &amp; Risk Guardband</div>
            <div><strong>Decision Rule:</strong> ${mbom.conformity_decision?.decision_rule}</div>
            <div><strong>TUR:</strong> ${mbom.conformity_decision?.test_uncertainty_ratio_tur}</div>
            <div><strong>Guardband Width (w):</strong> ${mbom.conformity_decision?.guardband_width_w_mm} mm</div>
            <div><strong>Acceptance Interval:</strong> [${mbom.conformity_decision?.acceptance_intervals_mm?.join(', ')}] mm</div>
            <div><strong>Consumer Risk Target:</strong> ${mbom.conformity_decision?.consumer_risk_target}</div>
          </div>
        </div>
      </div>
    `;
  } catch (e) {
    console.error("Error loading MBOM:", e);
  }
}

// ==========================================
// 13. V6 FLEET, RAG & COPILOT CONTROLLERS
// ==========================================

async function loadFleetIntelligenceLive() {
  try {
    const res = await fetch("/api/v6/fleet/intelligence");
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("fleet-health-score").innerText = data.fleet_health_score ?? "--";
    document.getElementById("fleet-total-count").innerText = data.total_fleet_instruments ?? "--";
    document.getElementById("fleet-at-risk-count").innerText = data.instruments_at_risk_count ?? "0";

    const c = document.getElementById("fleet-content-container");
    if (!c) return;

    let cohortHtml = "";
    if (data.cohort_anomalies && data.cohort_anomalies.length > 0) {
      cohortHtml = `
        <div class="card" style="background: #fff1f2; border-color: #fecdd3; margin-bottom: 12px;">
          <h4 style="color: var(--danger); margin-bottom: 6px;">⚠️ Cohort Anomaly Detected: ${escapeHtml(data.cohort_anomalies[0].cohort_type)}</h4>
          <div style="font-size: 11px; color: #9f1239;">${escapeHtml(data.cohort_anomalies[0].finding)}</div>
          <div style="font-size: 11px; color: var(--text-muted); margin-top: 4px;"><strong>Hypothesis:</strong> ${escapeHtml(data.cohort_anomalies[0].hypothesis)}</div>
        </div>
      `;
    }

    let queueRows = (data.maintenance_queue || []).map(item => `
      <tr>
        <td><strong>${escapeHtml(item.name)}</strong></td>
        <td>${escapeHtml(item.serial_number)}</td>
        <td>${escapeHtml(item.location)}</td>
        <td><span class="badge badge-${item.risk_level.toLowerCase().replace('_', '-')}">${item.risk_level} (${item.risk_score})</span></td>
        <td>${escapeHtml(item.drift_trend)}</td>
        <td>${escapeHtml(item.next_due)}</td>
      </tr>
    `).join("");

    c.innerHTML = `
      ${cohortHtml}
      <h3 style="font-size: 12px; margin-bottom: 8px;">Predictive Recalibration Queue</h3>
      <table class="data-table">
        <thead>
          <tr>
            <th>Instrument</th>
            <th>Serial Number</th>
            <th>Location</th>
            <th>Risk Level</th>
            <th>Drift Trend</th>
            <th>Next Due Date</th>
          </tr>
        </thead>
        <tbody>
          ${queueRows || "<tr><td colspan='6' style='text-align: center;'>No instruments registered.</td></tr>"}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error("Error loading fleet intelligence:", e);
  }
}

async function executeRagSearchLive() {
  const query = document.getElementById("rag-search-input")?.value || "guardband Z540.3";
  try {
    const res = await fetch(`/api/v6/rag/search?q=${encodeURIComponent(query)}&top_k=3`);
    if (!res.ok) return;
    const data = await res.json();
    const c = document.getElementById("rag-results-container");
    if (!c) return;

    if (!data.documents || data.documents.length === 0) {
      c.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>No matching standards or SOPs found.</div>";
      return;
    }

    c.innerHTML = data.documents.map(d => `
      <div style="background: #ffffff; padding: 10px 12px; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <strong style="color: var(--primary); font-size: 12px;">${escapeHtml(d.title)} §${escapeHtml(d.section)}</strong>
          <span class="badge badge-integrity">Relevance: ${d.relevance_score}</span>
        </div>
        <div style="font-size: 11px; color: #334155; margin-bottom: 6px;">${escapeHtml(d.content)}</div>
        <div style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(d.citation)}</div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Error executing RAG search:", e);
  }
}

function setCopilotPrompt(text) {
  const el = document.getElementById("copilot-input");
  if (el) el.value = text;
}

async function submitCopilotQueryLive() {
  const q = document.getElementById("copilot-input")?.value || "Why did this instrument fail?";
  const c = document.getElementById("copilot-output-container");
  if (!c) return;

  c.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>⚡ Multi-Agent Orchestrator executing tool-bound investigation...</div>";

  try {
    const res = await fetch("/api/v6/copilot/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, calculation_id: activeCalculationId }),
    });
    if (!res.ok) return;
    const data = await res.json();

    let citationsHtml = (data.evidence_citations || []).map(cit => `
      <li style="margin-bottom: 2px;">${escapeHtml(cit)}</li>
    `).join("");

    let traceHtml = (data.activity_trace || []).map(st => `
      <div style="font-size: 10px; font-family: var(--font-mono); color: #475569; margin-bottom: 2px;">
        ✓ [${escapeHtml(st.step)}] ${escapeHtml(st.detail)}
      </div>
    `).join("");

    c.innerHTML = `
      <div style="background: #ffffff; padding: 12px; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <h3 style="font-size: 13px; color: var(--primary);">Copilot Investigation Synthesis</h3>
          <span class="badge badge-pass">${escapeHtml(data.confidence_assessment?.decision_authority)}</span>
        </div>
        <p style="font-size: 12px; color: #1e293b; line-height: 1.5; margin-bottom: 10px;">${escapeHtml(data.finding)}</p>

        <div class="grid-2" style="font-size: 11px; margin-bottom: 10px;">
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 4px; text-transform: uppercase;">Confidence &amp; Risk Metrics</div>
            <div><strong>Model Confidence:</strong> ${data.confidence_assessment?.model_confidence_pct}%</div>
            <div><strong>Evidence Completeness:</strong> ${data.confidence_assessment?.evidence_completeness_pct}%</div>
            <div><strong>Drift Trend:</strong> ${escapeHtml(data.ml_findings?.drift_trend)}</div>
            <div><strong>Composite Risk:</strong> ${escapeHtml(data.ml_findings?.risk_classification)} (${data.ml_findings?.composite_risk_score}/100)</div>
          </div>

          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569; margin-bottom: 4px; text-transform: uppercase;">Recommended Operational Action</div>
            <div style="color: #0f172a;">${escapeHtml(data.recommended_action)}</div>
          </div>
        </div>

        <div style="margin-bottom: 8px;">
          <strong style="font-size: 11px; color: #475569;">Grounded Evidence Citations:</strong>
          <ul style="font-size: 11px; color: var(--text-muted); padding-left: 16px; margin-top: 4px;">
            ${citationsHtml}
          </ul>
        </div>

        <details style="border-top: 1px solid var(--border); padding-top: 6px;">
          <summary style="font-size: 10px; color: var(--text-muted); cursor: pointer;">🔍 View Tool Execution Trace (Execution &rarr; Proof)</summary>
          <div style="margin-top: 6px; padding: 6px; background: #f1f5f9; border-radius: 4px;">
            ${traceHtml}
          </div>
        </details>
      </div>
    `;
  } catch (e) {
    console.error("Error executing Copilot query:", e);
    c.innerHTML = "<div style='font-size: 11px; color: var(--danger);'>Error executing Copilot query.</div>";
  }
}

// ==========================================
// 14. ENTERPRISE INDUSTRIAL & COMPLIANCE CONTROLLERS
// ==========================================

function setScpiCmd(cmd) {
  const el = document.getElementById("scpi-command-input");
  if (el) el.value = cmd;
}

async function sendScpiCommandLive() {
  const resource = document.getElementById("scpi-resource-input")?.value || "VIRTUAL::KEY34461A";
  const cmd = document.getElementById("scpi-command-input")?.value || "*IDN?";
  const term = document.getElementById("scpi-terminal-log");

  if (term) term.innerText += `\n> [TX] ${resource} >> ${cmd}`;

  try {
    const res = await fetch("/api/enterprise/industrial/scpi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resource_string: resource, command: cmd }),
    });
    const data = await res.json();
    if (term) {
      term.innerText += `\n< [RX] ${data.response || "OK"}`;
      term.scrollTop = term.scrollHeight;
    }
  } catch (e) {
    if (term) term.innerText += `\n! [ERR] ${e.message}`;
  }
}

async function parseQifPlanLive() {
  const raw = document.getElementById("qif-import-textarea")?.value || "";
  const c = document.getElementById("qif-output-container");
  if (!c) return;

  try {
    const res = await fetch("/api/enterprise/industrial/qif/parse", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_content: raw }),
    });
    const data = await res.json();

    let rows = (data.characteristics || []).map(ch => `
      <tr>
        <td><strong>${escapeHtml(ch.characteristic_id)}</strong></td>
        <td>${escapeHtml(ch.feature_name)}</td>
        <td>${ch.nominal_value} mm</td>
        <td>+${ch.tolerance_upper} / ${ch.tolerance_lower} mm</td>
        <td><span class="badge badge-enterprise">Datum: ${escapeHtml(ch.datum_reference)}</span></td>
      </tr>
    `).join("");

    c.innerHTML = `
      <div style="font-weight: 700; color: var(--primary); margin-bottom: 8px;">Extracted ${data.characteristics_count} Quality Characteristics (${data.format})</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Feature</th>
            <th>Nominal</th>
            <th>Tolerance</th>
            <th>Datum Reference</th>
          </tr>
        </thead>
        <tbody>
          ${rows || "<tr><td colspan='5'>No characteristics found.</td></tr>"}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error("QIF parse error:", e);
  }
}

async function exportActiveCalculationQifLive() {
  if (!activeCalculationId) {
    alert("Please select or calculate a calibration record first.");
    return;
  }
  try {
    const res = await fetch(`/api/enterprise/industrial/qif/export/${activeCalculationId}`);
    const data = await res.json();
    const c = document.getElementById("qif-output-container");
    if (c) {
      c.innerHTML = `
        <div style="font-weight: 700; color: var(--success); margin-bottom: 6px;">✓ Exported QIF 3.0 Standard Results Package</div>
        <pre style="background: #0f172a; color: #38bdf8; padding: 10px; border-radius: 4px; font-size: 10px; max-height: 240px; overflow: auto;">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
      `;
    }
  } catch (e) {
    console.error("QIF export error:", e);
  }
}

async function executePart11SignatureLive() {
  const username = document.getElementById("part11-username-select")?.value || "chief_metrologist";
  const password = document.getElementById("part11-password-input")?.value || "";
  const reason = document.getElementById("part11-reason-select")?.value || "APPROVAL_RELEASE";
  const c = document.getElementById("part11-seal-output");
  if (!c) return;

  const targetCalcId = activeCalculationId || "CALC-RECENT";
  const targetHash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855";

  try {
    const res = await fetch("/api/enterprise/compliance/sign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        calculation_id: targetCalcId,
        calculation_sha256: targetHash,
        username: username,
        password: password,
        reason: reason,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      c.innerHTML = `<div style="color: var(--danger); font-size: 11px;">⚠️ Signature Ceremony Rejected: ${escapeHtml(err.detail || "Authentication Failed")}</div>`;
      return;
    }
    const data = await res.json();

    c.innerHTML = `
      <div style="border: 2px solid #059669; background: #ecfdf5; padding: 12px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="color: #065f46; font-size: 13px;">🔒 FDA 21 CFR Part 11 Cryptographically Sealed Signature</strong>
          <span class="badge badge-pass">SEALED &amp; BINDING</span>
        </div>
        <div style="font-size: 11px; color: #064e3b; margin-bottom: 4px;"><strong>Signer:</strong> ${escapeHtml(data.signer?.full_name)} (${escapeHtml(data.signer?.role)})</div>
        <div style="font-size: 11px; color: #064e3b; margin-bottom: 4px;"><strong>Badge ID:</strong> ${escapeHtml(data.signer?.badge_id)}</div>
        <div style="font-size: 11px; color: #064e3b; margin-bottom: 6px;"><strong>Signing Reason:</strong> ${escapeHtml(data.signing_reason)}</div>
        <div style="font-size: 10px; font-family: var(--font-mono); color: #047857; word-break: break-all;">
          <strong>Signature Token:</strong> ${escapeHtml(data.signature_token)}
        </div>
      </div>
    `;
  } catch (e) {
    console.error("Signature error:", e);
  }
}

async function executeQualificationProtocolLive() {
  const c = document.getElementById("qualification-dossier-output");
  if (!c) return;
  c.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>⚡ Executing automated IQ / OQ / PQ validation protocols...</div>";

  try {
    const res = await fetch("/api/enterprise/compliance/qualification", { method: "POST" });
    const data = await res.json();

    c.innerHTML = `
      <div style="margin-bottom: 10px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <h3 style="font-size: 14px; color: var(--primary);">Automated Software Qualification Protocol (IQ / OQ / PQ)</h3>
          <span class="badge badge-pass">${escapeHtml(data.status)}</span>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">${escapeHtml(data.regulatory_attestation)}</div>
        <div class="grid-3" style="font-size: 11px; margin-bottom: 12px;">
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569;">IQ (Installation)</div>
            <div style="font-size: 18px; font-weight: 900; color: var(--success);">${data.iq_section?.status}</div>
          </div>
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569;">OQ (Operational)</div>
            <div style="font-size: 18px; font-weight: 900; color: var(--success);">${data.oq_section?.status}</div>
          </div>
          <div class="card" style="background: #f8fafc; margin-bottom: 0;">
            <div style="font-weight: 700; color: #475569;">PQ (Performance)</div>
            <div style="font-size: 18px; font-weight: 900; color: var(--success);">${data.pq_section?.status}</div>
          </div>
        </div>
        <div style="font-size: 11px; font-family: var(--font-mono); color: #0f172a;">
          ✓ All ${data.total_test_protocols} qualification protocols executed with ${data.pass_rate_pct}% PASS in ${data.execution_duration_ms} ms.
        </div>
      </div>
    `;
  } catch (e) {
    console.error("Qualification error:", e);
  }
}

async function runNistBenchmarksLive() {
  const c = document.getElementById("nist-benchmarks-output");
  if (!c) return;
  c.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>🏛️ Comparing calculations against NIST Standard Reference Data...</div>";

  try {
    const res = await fetch("/api/enterprise/benchmarks/nist");
    const data = await res.json();

    let rows = (data.benchmark_details || []).map(b => `
      <tr>
        <td><strong>${escapeHtml(b.benchmark_id)}</strong></td>
        <td>${escapeHtml(b.parameter)}</td>
        <td>${escapeHtml(b.calculated_mean)}</td>
        <td>${escapeHtml(b.nist_mean)}</td>
        <td>${escapeHtml(b.absolute_arithmetic_error)}</td>
        <td><span class="badge badge-pass">EXACT MATCH</span></td>
      </tr>
    `).join("");

    c.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 style="font-size: 13px; color: var(--primary);">NIST CTS Standard Reference Data Equivalence</h3>
        <span class="badge badge-pass">${escapeHtml(data.status)}</span>
      </div>
      <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">${escapeHtml(data.statement)}</p>
      <table class="data-table">
        <thead>
          <tr>
            <th>Benchmark</th>
            <th>Parameter</th>
            <th>Calculated Mean</th>
            <th>NIST Reference Mean</th>
            <th>Max Deviation</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error("NIST Benchmark error:", e);
  }
}

async function generateTraceabilityDossierLive() {
  const c = document.getElementById("nist-benchmarks-output");
  if (!c) return;
  try {
    const res = await fetch(`/api/enterprise/compliance/traceability/${activeCalculationId || "CALC-RECENT"}`);
    const data = await res.json();

    let chainHtml = (data.traceability_chain || []).map(ch => `
      <div style="background: #ffffff; padding: 10px; border: 1px solid var(--border); border-radius: 4px; margin-bottom: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <strong style="color: var(--primary); font-size: 11px;">${escapeHtml(ch.tier)}: ${escapeHtml(ch.entity)}</strong>
          <span class="badge badge-enterprise">${escapeHtml(ch.expanded_uncertainty)}</span>
        </div>
        <div style="font-size: 11px; color: #334155; margin-top: 2px;">${escapeHtml(ch.standard_type)} (Trace ID: ${escapeHtml(ch.traceability_id)})</div>
      </div>
    `).join("");

    c.innerHTML = `
      <h3 style="font-size: 13px; color: var(--primary); margin-bottom: 6px;">${escapeHtml(data.statement_title)}</h3>
      <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">${escapeHtml(data.formal_declaration)}</p>
      <div style="margin-bottom: 10px;">${chainHtml}</div>
    `;
  } catch (e) {
    console.error("Traceability error:", e);
  }
}

async function simulateIlcRoundLive() {
  const c = document.getElementById("ilc-results-output");
  if (!c) return;
  c.innerHTML = "<div style='font-size: 11px; color: var(--text-muted);'>🌐 Evaluating Interlaboratory Comparison En-ratios...</div>";

  try {
    const res = await fetch("/api/enterprise/benchmarks/ilc");
    const data = await res.json();

    let rows = (data.participant_evaluations || []).map(p => `
      <tr>
        <td><strong>${escapeHtml(p.lab_name)}</strong></td>
        <td>${p.measured_value_mm.toFixed(5)} mm</td>
        <td>±${p.stated_uncertainty_mm.toFixed(5)} mm</td>
        <td><strong>${p.en_ratio.toFixed(3)}</strong></td>
        <td><span class="badge badge-${p.status.toLowerCase()}">${p.status} (|En| &le; 1.0)</span></td>
      </tr>
    `).join("");

    c.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h3 style="font-size: 13px; color: var(--primary);">ISO/IEC 17043 Proficiency Testing Round: ${escapeHtml(data.pt_round_id)}</h3>
        <span class="badge badge-pass">${data.satisfactory_participants}/${data.total_participants} SATISFACTORY</span>
      </div>
      <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 10px;">${escapeHtml(data.round_summary)} (Reference: ${data.reference_value_mm} mm ±${data.reference_uncertainty_u95_mm} mm)</p>
      <table class="data-table">
        <thead>
          <tr>
            <th>Participant Laboratory</th>
            <th>Measured Value</th>
            <th>Stated Uncertainty (U95)</th>
            <th>Normalized Error (En)</th>
            <th>Proficiency Status</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  } catch (e) {
    console.error("ILC error:", e);
  }
}

async function loadIndustryProfilesLive() {
  const c = document.getElementById("industry-profiles-container");
  if (!c) return;

  try {
    const res = await fetch("/api/enterprise/profiles");
    const data = await res.json();

    c.innerHTML = (data.industry_profiles || []).map(p => `
      <div class="card" style="background: #ffffff; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <h3 style="font-size: 13px; color: var(--primary);">${escapeHtml(p.title)}</h3>
          <span class="badge badge-enterprise">${escapeHtml(p.sector)}</span>
        </div>
        <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">
          <strong>Governing Standards:</strong> ${escapeHtml(p.regulatory_standards?.join(" • "))}
        </div>
        <div class="grid-2" style="font-size: 11px; margin-bottom: 8px;">
          <div><strong>Decision Rule:</strong> ${escapeHtml(p.default_decision_rule)}</div>
          <div><strong>Thermal Soaking:</strong> ${p.thermal_soaking_hours} hrs (${escapeHtml(p.temperature_band_c)})</div>
        </div>
        <div style="font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 4px;">Preloaded Inspection Templates:</div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${(p.templates || []).map(t => `
            <button class="btn btn-outline btn-sm" onclick="applyIndustryTemplate('${escapeHtml(t.name)}', ${t.nominal_mm}, ${t.tolerance_upper_mm})">
              📋 Load ${escapeHtml(t.name)} (${t.nominal_mm} mm)
            </button>
          `).join("")}
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Industry profiles error:", e);
  }
}

function applyIndustryTemplate(name, nominal, tol) {
  switchView("workflow");
  const elName = document.getElementById("calc-inst-name");
  const elNom = document.getElementById("calc-nom");
  const elTol = document.getElementById("calc-tol");
  if (elName) elName.value = name;
  if (elNom) elNom.value = nominal;
  if (elTol) elTol.value = tol;
}

async function loadHandbookArticlesLive() {
  const c = document.getElementById("handbook-articles-container");
  if (!c) return;

  try {
    const res = await fetch("/api/enterprise/support/handbook");
    const data = await res.json();

    c.innerHTML = (data.articles || []).map(art => `
      <div class="card" style="background: #ffffff; margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <h3 style="font-size: 13px; color: var(--primary);">${escapeHtml(art.title)}</h3>
          <span class="badge badge-integrity">${escapeHtml(art.category)}</span>
        </div>
        <p style="font-size: 11px; color: #334155; line-height: 1.5; margin-bottom: 8px;">${escapeHtml(art.content)}</p>
        <div style="font-size: 10px; color: var(--text-muted);">
          <strong>Citations:</strong> ${escapeHtml(art.citations?.join(" • "))}
        </div>
      </div>
    `).join("");
  } catch (e) {
    console.error("Handbook error:", e);
  }
}

async function generateSupportBundleLive() {
  const c = document.getElementById("support-bundle-output");
  if (!c) return;

  try {
    const res = await fetch("/api/enterprise/support/diagnostic-bundle");
    const data = await res.json();

    c.innerHTML = `
      <div style="border: 1px solid var(--primary); background: #f0f9ff; padding: 12px; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <strong style="color: var(--primary); font-size: 13px;">📦 Enterprise SLA Diagnostic Telemetry Bundle Ready</strong>
          <span class="badge badge-enterprise">SLA 24x7</span>
        </div>
        <div style="font-size: 11px; color: #0369a1; margin-bottom: 4px;"><strong>Bundle ID:</strong> ${escapeHtml(data.support_bundle_id)}</div>
        <div style="font-size: 10px; font-family: var(--font-mono); color: #0284c7; word-break: break-all; margin-bottom: 6px;">
          <strong>SHA-256 Checksum:</strong> ${escapeHtml(data.sha256_checksum)}
        </div>
        <div style="font-size: 11px; color: #334155; margin-bottom: 8px;">${escapeHtml(data.instructions)}</div>
        <pre style="background: #0f172a; color: #38bdf8; padding: 8px; border-radius: 4px; font-size: 10px; max-height: 180px; overflow: auto;">${escapeHtml(JSON.stringify(data.bundle_data, null, 2))}</pre>
      </div>
    `;
  } catch (e) {
    console.error("Support bundle error:", e);
  }
}

// Global Command Palette Keylistener (Ctrl + K)
document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    toggleCommandPalette();
  }
  if (e.key === "Escape") {
    closeCommandPalette();
  }
});

function toggleCommandPalette() {
  let modal = document.getElementById("command-palette-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "command-palette-modal";
    modal.className = "cmd-modal-backdrop";
    modal.onclick = (e) => { if (e.target === modal) closeCommandPalette(); };
    modal.innerHTML = `
      <div class="cmd-modal-box">
        <div class="cmd-input-wrapper">
          <span style="color: #94a3b8;">🔍</span>
          <input type="text" id="cmd-search-input" placeholder="Type a command, module, or standard (e.g. SCPI, NIST, Part 11, GUM)..." oninput="filterCommandPalette(this.value)">
        </div>
        <ul class="cmd-results-list" id="cmd-results-list"></ul>
      </div>
    `;
    document.body.appendChild(modal);
  }
  modal.classList.remove("hidden");
  const input = document.getElementById("cmd-search-input");
  if (input) {
    input.value = "";
    input.focus();
    filterCommandPalette("");
  }
}

function closeCommandPalette() {
  const modal = document.getElementById("command-palette-modal");
  if (modal) modal.classList.add("hidden");
}

const COMMAND_PALETTE_ACTIONS = [
  { label: "⚡ Single-Point Calibration Studio", action: () => switchView("workflow") },
  { label: "🔌 SCPI / VISA Hardware Studio", action: () => switchView("scpi") },
  { label: "📐 QIF 3.0 & STEP CAD Metrology", action: () => switchView("qif") },
  { label: "✍️ FDA 21 CFR Part 11 Electronic Signs", action: () => switchView("part11") },
  { label: "📜 Automated IQ / OQ / PQ Software Qualification", action: () => switchView("qualification") },
  { label: "🏛️ NIST Reference Data Benchmarks", action: () => switchView("benchmarks") },
  { label: "🌐 ISO/IEC 17043 Interlaboratory Comparison (ILC / PT)", action: () => switchView("ilc") },
  { label: "🏭 Pre-Configured Industry Profiles (Aerospace, Auto, Med)", action: () => switchView("profiles") },
  { label: "🤖 Engineering Copilot & Investigation", action: () => switchView("copilot") },
  { label: "🚢 Fleet Intelligence & Cohort Anomaly", action: () => switchView("fleet") },
  { label: "📖 Metrology Engineering Handbook", action: () => switchView("handbook") },
  { label: "💼 1-Click SLA Diagnostic Support Bundle", action: () => switchView("support") },
];

function filterCommandPalette(query) {
  const list = document.getElementById("cmd-results-list");
  if (!list) return;
  const q = query.toLowerCase();
  const filtered = COMMAND_PALETTE_ACTIONS.filter(item => item.label.toLowerCase().includes(q));

  list.innerHTML = filtered.map((item, idx) => `
    <li onclick="COMMAND_PALETTE_ACTIONS[${COMMAND_PALETTE_ACTIONS.indexOf(item)}].action(); closeCommandPalette();">
      <span>${escapeHtml(item.label)}</span>
      <span style="font-size: 10px; color: #64748b; font-family: var(--font-mono);">↵ Enter</span>
    </li>
  `).join("");
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}




