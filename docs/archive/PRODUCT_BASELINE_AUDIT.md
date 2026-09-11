# PRODUCT BASELINE AUDIT — METROLOGY WORKSTATION

**Date**: August 18, 2026  
**Auditor**: Principal Metrology & Systems Architect  
**Product**: Metrology Workstation  
**Current Baseline**: `v1.1.0` (Production Baseline)  

---

## 1. Application Architecture Baseline

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            METROLOGY WORKSTATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. DESKTOP RUNTIME & OS INTEGRATION                                         │
│    • Entrypoint: desktop_app.py (PySide6 / Webview2 native window wrapper)   │
│    • Standalone Binary: dist/MetrologyWorkstation.exe (53.2 MB PE x64)       │
│    • Setup Installer: dist/Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe│
│    • Data Isolation: %LOCALAPPDATA%\MetrologyWorkstation (data, backups, log)│
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. PRESENTATION LAYER (metrology_app/static/)                               │
│    • HTML5 / CSS3 / Vanilla ECMAScript (Zero CDN dependencies)              │
│    • Views: Dashboard, Single-Point Studio, Multi-Point Studio,             │
│             Measurement Intelligence Hub, Calibrations Log, Procedures,      │
│             12-Stage Replay, Tamper Detection Lab, Audit Vault, Backups,     │
│             Standards Concordance Registry, Lab Settings, Licensing          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. APPLICATION & SERVICE LAYER (metrology_app/services/)                    │
│    • FastAPI ASGI Server: metrology_app/server.py                           │
│    • calculation_service.py: Single & multi-point uncertainty orchestration │
│    • intelligence_service.py: 5 core measurement intelligence engines       │
│    • verifier_service.py: 12-stage mathematical replay & tamper detection   │
│    • audit_service.py: SHA-256 hash-chained immutable event ledger          │
│    • license_service.py: HMAC-SHA256 offline cryptographic entitlements     │
│    • webhook_service.py: Idempotent payment webhook event processing        │
│    • evidence_service.py: Machine-verifiable ZIP evidence bundle generator  │
│    • backup_service.py: Live SQLite atomic snapshots and restoration        │
│    • report_service.py: Formal calibration certificate & audit reports      │
│    • selftest_service.py: 8-point numerical integrity verification suite    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. PERSISTENCE & DATA INTEGRITY (metrology_app/db.py)                       │
│    • SQLite 3 with WAL mode, foreign keys, and atomic commits               │
│    • Tables: calculations, audit_events, webhook_events                     │
│    • Immutable revision lineage (root_id, revision_number, parent_sha256)   │
│    • Zero demo records on fresh installation bootstrap                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. METROLOGICAL NUMERICAL KERNEL (metrology_core/)                          │
│    • Context: 50-digit exact decimal arithmetic (metrology_core/context.py) │
│    • Uncertainty: Type A, Type B, GUM propagation, covariance PSD check,   │
│                   Welch-Satterthwaite DoF, Monte Carlo (JCGM 101:2008)      │
│    • Decision: ANSI/NCSL Z540.3 Method 5 & 6, ISO 14253-1:2017, TUR         │
│    • Rounding: Metrological round-half-to-even & resolution matching        │
│    • Provenance: CalculationTrace with SHA-256 canonical input hashing      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Source Inventory & Component Mapping

| Subsystem | Source Path | Key Capabilities |
| :--- | :--- | :--- |
| **Exact Decimal Math** | `metrology_core/context.py` | 50-digit `Decimal`, `decimal_sqrt`, `to_decimal`, error bounds |
| **Type A Uncertainty** | `metrology_core/uncertainty/type_a.py` | Sample mean, sample standard deviation, degrees of freedom |
| **Type B Uncertainty** | `metrology_core/uncertainty/type_b.py` | Normal, Rectangular, Triangular, U-shaped distributions |
| **GUM Propagation** | `metrology_core/uncertainty/propagation.py` | First-order Taylor series variance summation, sensitivity |
| **Covariance Engine** | `metrology_core/uncertainty/covariance.py` | Cholesky decomposition, Positive Semi-Definite (PSD) check |
| **Effective DoF** | `metrology_core/uncertainty/degrees_of_freedom.py` | Welch-Satterthwaite formula & Student's t coverage factor |
| **Monte Carlo MCM** | `metrology_core/uncertainty/monte_carlo.py` | $10^5$ to $10^6$ trials numerical propagation (JCGM 101) |
| **TUR Decision Rule** | `metrology_core/decision/tur.py` | Test Uncertainty Ratio $(T_U - T_L) / (2 \cdot U_{95})$ |
| **Z540.3 Method 6** | `metrology_core/decision/method6.py` | Exact guardband curve $M(\text{TUR})$, root-finding, $P_{\text{CR}} \le 2\%$ |
| **Z540.3 Method 5** | `metrology_core/decision/method5.py` | Root-Sum-Square (RSS) guardbanding $w = \sqrt{U^2 - (T/\text{TUR})^2}$ |
| **ISO 14253-1** | `metrology_core/decision/iso14253.py` | Complete guardband conformance zone $w = U_{95}$ |
| **Metrological Rounding** | `metrology_core/rounding/metrological.py` | ISO 80000-1 round-half-even, precision matching, unit strings |
| **Provenance Trace** | `metrology_core/provenance.py` | Canonical JSON hashing, input SHA-256, calculation trace |
| **Persistence Layer** | `metrology_app/db.py` | SQLite schema, revisions, stats, hash-chained audit storage |
| **Intelligence Engine** | `metrology_app/services/intelligence_service.py` | Why?, What Changed?, Health Score, Forecasting, Actions |
| **Verifier & Replay** | `metrology_app/services/verifier_service.py` | 12-stage independent derivation reproduction, tamper lab |
| **Licensing Engine** | `metrology_app/services/license_service.py` | HMAC-SHA256 token verification, offline trial, rollback guard |
| **Webhook Ingestion** | `metrology_app/services/webhook_service.py` | MoR payment webhook handler, idempotency, token issuance |

---

## 3. Test Suite Baseline

- **Total Automated Tests**: 89
- **Passing Status**: 89/89 (100% PASS)
- **Categories Covered**:
  - Exact Decimal Arithmetic & Rounding (12 tests)
  - GUM Uncertainty Propagation & Covariance PSD (16 tests)
  - Decision Rules, Guardbands & TUR Fuzzing (15 tests)
  - Monte Carlo JCGM 101 Validation (5 tests)
  - Persistence, Revisions & Audit Chain (7 tests)
  - Independent Verification & Tamper Detection (5 tests)
  - V4 Clean Production & Fresh-Install Bootstrapping (4 tests)
  - V5 Measurement Intelligence Engines & REST APIs (11 tests)
  - Entitlements, Licensing & Webhook Processing (9 tests)
  - Live Backup, Restore & Data Retention (5 tests)

---

## 4. Release Artifacts Baseline

1. **Standalone Windows Application**:
   - `dist/MetrologyWorkstation.exe` (`53,242,966 bytes`)
2. **Native Windows Setup Installer**:
   - `dist/Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe` (`58,719,118 bytes`)
   - **SHA-256 Checksum**: `5275c1b26accdda867e1e9aa1222e7a45901d4b09a2231c508a6afd1758d8c67`
3. **Checksum Manifest**:
   - `dist/SHA256SUMS.txt`
