# V4 CLEAN PRODUCTION WORKSTATION SPECIFICATION

**Product**: Metrology Workstation  
**Version**: `v1.0.0` (V4 Clean Production Release)  
**Company / Brand**: NovyraX  
**Official Distribution**: `https://novyrax.vercel.app`  

---

## 1. The V0 $\to$ V4 SDLC Architecture

```text
V0 (Foundation)
 └── Pure 50-digit decimal kernel, JCGM 100/101/106, Z540.3 Method 6 guardbands, ISO 14253-1 rules.
      ↓
V1 (Functional Workstation)
 └── Complete single-point & multi-point measurement workflows, SQLite persistence, and UI navigation.
      ↓
V2 (Engineering Hardening)
 └── Adversarial fuzzing, Welch-Satterthwaite verification, PSD correlation check, and clock rollback defense.
      ↓
V3 (Production & Commercial Release)
 └── Standalone PE executable, native setup installer, offline HMAC-SHA256 licensing, CI/CD, webhooks.
      ↓
V4 (Clean Production Workstation)
 └── Zero demo records, deterministically empty database bootstrap, clean first-run experience, and user data preservation.
```

---

## 2. V4 Clean Database Bootstrap Principle

### The Core Architectural Rule:
> **Test data $\ne$ Product data.**  
> Test fixtures remain isolated within automated tests (`metrology_app/tests/`).  
> In the production application runtime, the database (`%LOCALAPPDATA%\MetrologyWorkstation\data\metrology_workstation.db`) initializes as a **pristine empty database (0 records)**.

### Initial Database State on Fresh Install:
```text
Table: calculations    -> 0 rows
Table: audit_events   -> 0 rows
Table: webhook_events  -> 0 rows
```

---

## 3. V4 First-Run Experience (FRE)

When a customer launches Metrology Workstation for the first time:

1. **Dashboard Empty State**:
   - Total Calibrations: `0`
   - Passed: `0`
   - Failed: `0`
   - Guardband / Review: `0`
   - **Welcome Card**: Displays a clean workspace readiness banner with direct quick-action buttons:
     - `[ + Start New Calibration ]`
     - `[ Multi-Point Studio ]`
     - `[ Browse Procedures ]`
   - Featured telemetry card remains hidden until real calibrations are performed.
2. **Replay Tab**:
   - Displays helpful prompt: *"No calculation selected for replay. Perform a calibration in the Studio or select a record from the Dashboard to inspect its 12-stage mathematical derivation."*
3. **Audit Vault**:
   - Cryptographically linked ledger starts at genesis hash `0000...0000` and appends tamper-evident event blocks only upon real user actions.
4. **Data Isolation & Retention**:
   - Application binary updates and uninstallation preserve user calibration records in `%LOCALAPPDATA%\MetrologyWorkstation\data\`.
