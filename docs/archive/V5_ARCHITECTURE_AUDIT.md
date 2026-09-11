# V5 ARCHITECTURE AUDIT & TRANSITION STRATEGY

**Date**: August 18, 2026  
**Auditor**: Principal Metrology Architect & Systems Engineer  
**Product**: Metrology Workstation  
**Baseline**: `v1.1.0` (V4 Baseline) $\to$ `v5.0.0` (V5 Production Engineering Workstation)  

---

## 1. Current V4 Architecture Baseline

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CURRENT V4 WORKSPACE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ • Flat Calculation Paradigm: Users create isolated single-point or         │
│   multi-point calibration records.                                          │
│ • Database Schema: Single `calculations` table with revisions,               │
│   `audit_events` table, and `webhook_events` table.                         │
│ • UI Layout: Single-column / tab navigation switching between isolated      │
│   calculators (Single-Point Studio, Multi-Point Studio, Replay, Tamper).    │
│ • Calculation Engine: Deterministic 50-digit decimal GUM kernel.            │
│ • Limitation: No native Project/Work order hierarchy, no distinct           │
│   persistent Instrument Asset database, no explicit Measurement Plan        │
│   orchestration, no dedicated Uncertainty or Conformity Workbenches.        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. V4 Capabilities & Technical Inventory

| Subsystem | V4 Implementation Status | V4 Limitation |
| :--- | :--- | :--- |
| **Mathematical Kernel** | 50-Digit exact decimal, GUM propagation, Z540.3 Method 5 & 6, ISO 14253-1 | Calculation occurs inside monolithic request models |
| **Instrument Management** | Embedded text strings inside calibration record (`instrument_name`, `instrument_model`) | No separate persistent instrument entity with serial number, intervals, due dates |
| **Measurement Lifecycle** | Measurements entered directly into calculation modal | No structured measurement plan, no outlier analysis, no independent acquisition phase |
| **Uncertainty Workbench** | Uncertainty budget rendered as static table in results | No interactive workbench to adjust components and see real-time sensitivity response |
| **Conformity Workbench** | Verdict rendered as a single badge (`PASS`/`GUARD_BAND`/`FAIL`) | No dedicated workbench showing interactive guardband curves, risk bounds, acceptance zones |
| **Project Workspace** | No project entity (flat global calibration log) | Cannot group calibrations by site, customer, project, or work order |
| **Audit Ledger** | SHA-256 hash-chained SQLite event log | Flat table; lacks project-level cryptographic roll-up verification |

---

## 3. V5 Architectural Evolution: The 11-Stage Engineering Workflow

V5 fundamentally evolves the product into an engineering workstation structured around an 11-stage project workflow:

```text
PROJECT (Customer, Site, Standards)
   ↓
INSTRUMENT (ID, Serial, Range, Interval, Due Date, Reference Standards)
   ↓
MEASUREMENT PLAN (Measurand, Nominal, Specification, Repetitions, Decision Rule)
   ↓
MEASUREMENT ACQUISITION (Manual/Import, Real-Time Dispersion, Outlier Filtering)
   ↓
DATA VALIDATION (Range Checking, Units, Resolution, Stability)
   ↓
UNCERTAINTY WORKBENCH (Interactive Type A/B Components, Sensitivity, GUM Propagation)
   ↓
EXACT NUMERICAL CALCULATION (Authoritative 50-Digit Decimal Kernel)
   ↓
CONFORMITY WORKBENCH (Guardband Width w, Acceptance Interval, TUR, Consumer Risk P_CR)
   ↓
DEFENSIBLE ENGINEERING DECISION (PASS, GUARD_BAND, FAIL with Analytical Proof)
   ↓
EVIDENCE ARTIFACT (Cryptographic SHA-256 Hash, 12-Stage Replay Trace, Evidence Package)
   ↓
REPORT & AUDIT TRAIL (Traceable Calibration Certificate & Cryptographically Chained Ledger)
```

---

## 4. Persistent Application Shell Architecture (3-Pane Workspace)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                METROLOGY WORKSTATION V5                                  │
├──────────────┬───────────────────────────────────────────┬───────────────────────────────┤
│ LEFT PANE    │ CENTER PANE (ACTIVE WORKSPACE)            │ RIGHT PANE (INSPECTOR)        │
│ Navigation   │                                           │ Live Engineering Context      │
│ ──────────── │ ───────────────────────────────────────── │ ───────────────────────────── │
│ • Dashboard  │ • Project Workspace Editor                │ • Active Project Summary      │
│ • Projects   │ • Instrument Registry & History           │ • Active Instrument Health    │
│ • Instruments│ • Measurement Plan Builder                │ • GUM Derivation Parameters   │
│ • Plans      │ • Acquisition & Statistical Dispersion    │ • Z540.3 Guardband Curve      │
│ • Acquisition│ • Uncertainty Workbench (GUM Budget)      │ • Traceable Evidence Hashing  │
│ • Uncertainty│ • Conformity Workbench (Guardbanding)     │ • License / Entitlement State │
│ • Conformity │ • Evidence & 12-Stage Mathematical Replay │                               │
│ • Evidence   │ • Comprehensive Engineering Reports       │                               │
│ • Reports    │ • Cryptographic Audit Ledger & Verifier   │                               │
│ • Audit      │ • Laboratory Configuration & Settings     │                               │
├──────────────┴───────────────────────────────────────────┴───────────────────────────────┤
│ BOTTOM STATUS BAR: Engine: 50-Digit Verified • DB: WAL Locked • Audit: Hash-Chained Intact│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Schema Migration Strategy (V4 $\to$ V5)

To guarantee that customer databases are not corrupted, `metrology_app/db.py` will execute non-destructive schema migrations:
1. `CREATE TABLE IF NOT EXISTS projects (...)`
2. `CREATE TABLE IF NOT EXISTS instruments (...)`
3. `CREATE TABLE IF NOT EXISTS measurement_plans (...)`
4. `CREATE TABLE IF NOT EXISTS measurements (...)`
5. Check existing `calculations` table columns via `PRAGMA table_info(calculations)` and dynamically execute `ALTER TABLE calculations ADD COLUMN project_id TEXT`, `instrument_id TEXT`, `plan_id TEXT`, `measurement_id TEXT` if missing.
6. Seamlessly preserve all 89 existing regression tests.

---

## 6. Compatibility & Regression Protection

- **Frozen Mathematical Kernel**: `metrology_core` is protected and strictly imported by the V5 service layer.
- **Offline Entitlement Integrity**: HMAC-SHA256 license verification remains unchanged.
- **Deterministic Clean Bootstrap**: Fresh installations continue to open 100% empty (0 demo records).
