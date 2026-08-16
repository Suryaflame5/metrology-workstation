# Microsoft Partner Center — Store Submission & Certification Package

## 1. Product Identity & Category Guidance

- **Product Name**: Metrology Workstation
- **Package Identity**: `MetrologyWorkstation.Commercial`
- **Publisher Display Name**: Metrology Workstation Engineering
- **Version**: `1.0.0.0`
- **Category Selection**: To be selected directly from available Microsoft Partner Center category/subcategory options at time of submission (e.g. *Developer Tools / Productivity* or *Utilities*).
- **Target OS**: Windows 10 (Version 1809+, Build 17763.0+) & Windows 11 (x64)
- **Distribution Type**: Packaged Win32 Desktop Application (MSIX via `runFullTrust`)
- **Operational Model**: Local-first and offline-capable after installation. Calibration calculations, evidence generation, audit records, and database operations run locally without requiring a cloud service.

---

## 2. Store Listing Copy

### 2.1 Short Description (100 Characters)
> Local-first measurement uncertainty calculation, guardbanding, and calibration evidence workstation.

### 2.2 Full Description
> **Metrology Workstation** is a professional, local-first Windows application for calibration laboratories, quality engineers, and metrology specialists. Built on an exact 50-digit arithmetic reference kernel, it automates measurement uncertainty evaluation, decision rules, guardbanding, and audit-proof evidence generation.
>
> ### Key Features:
> - **International Standards Compliance**: Formulated strictly against JCGM 100:2008 (GUM), JCGM 101:2008 (Monte Carlo), JCGM 106:2012, ANSI/NCSL Z540.3-2006 (Methods 5 & 6), and ISO 14253-1:2017.
> - **Single & Multi-Point Calibration Studios**: High-density workflows for Outside Micrometers, Calipers, Dial Indicators, Height Gauges, Gauge Blocks, Digital Multimeters, and RTD Thermometers.
> - **Traceable Uncertainty Budgets**: Interactive GUM tables with clickable component provenance (distribution divisors, sensitivity coefficients, degrees of freedom, variance contribution, and component SHA-256 digests).
> - **Visual Conformity & Guardband Diagrams**: Real-time decision-zone visualizations displaying tolerance boundaries, acceptance zones, test uncertainty ratios (TUR), and measured error markers.
> - **12-Stage Mathematical Calculation Replay**: Step-by-step mathematical reproduction engine that proves every intermediate formula and numerical derivation.
> - **Cryptographic Audit Vault**: Hash-chained immutable event ledger that guarantees zero undetected tampering across all calibration records.
> - **Local-First Architecture**: All calibration records, SQLite databases, and evidence packages remain stored locally on your workstation (`%LOCALAPPDATA%\MetrologyWorkstation`).
>
> *Note: Metrology Workstation provides validated calculation and evidence tools to support documented conformity assessment. Operating laboratories retain statutory responsibility for their own measurement procedures and accreditation scope.*

### 2.3 Keywords / Search Terms
- `metrology`
- `measurement uncertainty`
- `calibration`
- `ISO 17025`
- `GUM`
- `guardband`
- `Z540.3`
- `ISO 14253`
- `calibration certificate`
- `uncertainty budget`

---

## 3. Privacy Policy Declaration
> **Privacy Statement for Metrology Workstation:**
> Metrology Workstation operates as a local-first desktop application. No calibration data, measurement observations, certificate details, or user identity information is transmitted to external servers or cloud services. All calculations and database records are stored exclusively in the local application directory on the user's computer (`%LOCALAPPDATA%\MetrologyWorkstation`).

---

## 4. Microsoft Store Screenshots Plan (4+ High-Res Views)

1. **Screenshot 1 — Workstation Dashboard & Telemetry**:
   - Live production calibration metrics, status badges (`PASS`, `VERIFIED`, `INTEGRITY OK`), and active instrument telemetry.
2. **Screenshot 2 — 9-Step Calibration Studio**:
   - GUM uncertainty budget table, sensitivity coefficients, and interactive component provenance drawer.
3. **Screenshot 3 — Multi-Point Calibration Studio**:
   - Multi-checkpoint measurement grid across 5 nominal points with error of indication curves.
4. **Screenshot 4 — Decision Zone & Guardband Model**:
   - Visual tolerance band diagram with acceptance limits $A_L, A_U$, guardband $w$, and TUR calculation.
5. **Screenshot 5 — Cryptographic Audit Vault**:
   - Hash-chained audit event ledger with live mathematical verification.
6. **Screenshot 6 — 12-Stage Mathematical Replay**:
   - Intermediate derivation verification from raw statistics to ISO 80000-1 rounding.

---

## 5. Certification Notes to Microsoft Reviewers
> *"Metrology Workstation is a scientific calibration and measurement uncertainty calculation application for quality engineering professionals. All calculations and database storage are self-contained locally on the user's PC using standard local-first technologies. No special account or cloud credentials are required to review the complete application. To verify, simply launch the app, click '+ New Calibration', click 'Execute Uncertainty Engine', and inspect the resulting verified budget and certificate."*
