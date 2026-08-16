# Metrology Workstation V0.9.1 — Store Certification Gate Checklist

This document is the final pre-submission release engineering verification gate before Microsoft Partner Center upload and V1.0 commercial publication.

---

## Strict Discipline Policy
> [!IMPORTANT]
> **FEATURE FREEZE IS IN EFFECT.** No new mathematical models, instrument families, UI features, or external dependencies are permitted. All activities are strictly limited to release engineering, package validation, and certification compliance.

---

## 1. Workstream Status & Release Verification Matrix

| # | Workstream | Gate Criteria | Validation Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Build Reproducibility** | Clean release build, deterministic version `1.0.0.0`, explicit x64 target architecture | `python build_windows_dist.py` creates self-contained `dist/MetrologyWorkstation` | 🟢 READY |
| **2** | **MSIX Validation** | `AppxManifest.xml` conforming to Windows 10/11 FullTrust MSIX schema, correct assets | Manifest schema validation, asset dimension checks ($50\times 50$, $150\times 150$, $44\times 44$, $310\times 150$) | 🟢 READY |
| **3** | **Clean-Machine Test** | Standalone runtime without external Python/Node/Git dependencies; isolated `%LOCALAPPDATA%` | Isolated path routing in `config.py` & bundled server | 🟢 VERIFIED |
| **4** | **Data Integrity** | Existing V0.9 data, SHA-256 digests, and hash-chained audit ledgers survive V1.0 upgrades | Automated in `test_upgrade_retention.py` | 🟢 **PASS** |
| **5** | **Store Certification** | Store listing copy, privacy policy, reviewer instructions, offline capability statement | `STORE_SUBMISSION_METADATA.md` complete | 🟢 READY |
| **6** | **Commercial Smoke Test** | Full workflow: Install $\to$ Launch $\to$ Calibrate $\to$ Verify $\to$ Certificate $\to$ Export $\to$ Backup $\to$ Restore | End-to-end regression suite (62/62 passing) | 🟢 **PASS** |
| **7** | **Release Sign-Off** | Mathematical kernel (`metrology_core`) frozen; zero unresolved regressions | 62 automated tests passing in 2.04s | 🟢 READY |

---

## 2. Release Sequence to Commercial Publication

```text
                  V0.9.1 STORE CERTIFICATION GATE
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
       Standalone Packaging              Certification Assets
       • AppxManifest.xml validated      • Store Listing & Descriptions
       • Asset logos verified            • Offline Privacy Declaration
       • Zero dev-only file leaks        • Reviewer Guidance Notes
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                    PARTNER CENTER SUBMISSION
                                 │
                                 ▼
                     MICROSOFT CERTIFICATION
                   (Security, Technical, Policy)
                                 │
                                 ▼
                 METROLOGY WORKSTATION V1.0 PUBLISHED
               (Live Commercial Release on Microsoft Store)
```

---

## 3. Reviewer Verification Guidance (For Store Certification)

1. **Launch**: Open `MetrologyWorkstation.exe`.
2. **Dashboard**: Verify live metrics and system health indicators (`Engine: VERIFIED`, `Audit: INTACT`, `DB: OK`).
3. **Execute Calibration**:
   - Click **+ New Calibration**.
   - Review parameters in Steps 1–4.
   - Click **Execute Uncertainty Engine**.
   - Inspect the interactive GUM budget, click any component row for deep provenance, and review the conformity decision diagram.
4. **Certificate**: Navigate to Step 9 and open the standalone, printable calibration report.
5. **Audit Vault & Backup**: Inspect the hash-chained audit ledger and create a live database backup.
