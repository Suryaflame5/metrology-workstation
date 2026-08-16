# PARTNER CENTER REVIEWER & CERTIFICATION GUIDE

**Application**: Metrology Workstation  
**Package Identity**: `MetrologyWorkstation.Commercial`  
**Version**: `0.9.9.0`  
**Target OS**: Windows 10 (1809+) / Windows 11 (x64)  

---

## 1. Application Overview for Microsoft Certification Engineers

**Metrology Workstation** is a standalone, local-first engineering desktop application built for calibration laboratories, quality control inspectors, and metrology engineers. It provides mathematically rigorous measurement uncertainty analysis (JCGM 100:2008 / GUM) and conformity assessment decision rules (ANSI/NCSL Z540.3 Method 6 / ISO 14253-1).

---

## 2. Reviewer Testing & Smoke Test Steps

1. **Launch**:
   - Launch `Metrology Workstation` from the Windows Start Menu.
   - The application starts an in-process local HTTP workstation service on `127.0.0.1:8000` and automatically opens the user's default browser to the Workstation dashboard.
2. **Execute Single-Point Calibration**:
   - In the sidebar, click **⚡ Single-Point Studio**.
   - Review the pre-populated Outside Micrometer (0–25 mm) inspection data (Nominal: `25.00000 mm`, Readings: `25.0012, 25.0010, ...`).
   - Click **Run Uncertainty & Decision Evaluation**.
   - Observe the real-time GUM uncertainty calculation ($u_c, \nu_{\text{eff}}, k, U_{95}$) and the ANSI/NCSL Z540.3 Method 6 decision verdict (`PASS`).
3. **Review 12-Stage Mathematical Replay**:
   - Click **🔄 12-Stage Replay** to review the complete, audit-traceable derivation showing exact formulas and intermediate values for all 12 stages.
4. **Inspect Plans & Licensing**:
   - Click **💎 Plans & Licensing** in the sidebar.
   - Observe the active Community Evaluation mode.
   - Click **⚡ Activate 14-Day Pro Trial** to test instant local commercial entitlement activation.

---

## 3. Security, Privacy & Network Declarations

- **Network Access**: The application communicates **only** with `127.0.0.1` (localhost) to connect the local UI to the embedded local service. It requires **no external internet connectivity** to function.
- **Data Storage**: All application databases and settings are strictly contained in `%LOCALAPPDATA%\MetrologyWorkstation\`.
- **Packaging Notes**: The application is compiled with standard standalone C runtime bootstrapping (PyInstaller) and declared with `<rescap:Capability Name="runFullTrust" />`.
