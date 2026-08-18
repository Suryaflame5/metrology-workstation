# METROLOGY WORKSTATION V5 — OFFICIAL RELEASE NOTES

**Release**: `v5.0.0` (Production Engineering Workstation)  
**Date**: August 18, 2026  
**Publisher**: NovyraX Engineering Studio  

---

## 🌟 What's New in V5

Metrology Workstation V5 marks the transition from a flat point-in-time calculation utility into an integrated **Engineering Measurement Workstation**.

### 1. 3-Pane Engineering Workstation Shell
- **Left Navigation Sidebar**: Clean grouping of Engineering Workspaces, Calibration Studios, Evidence & Security, and Administration.
- **Center Workspace**: High-density engineering interfaces with full parameter inspectability.
- **Right Engineering Inspector**: Real-time context, mathematical kernel status, GUM sensitivity breakdown, and Z540.3 Method 6 multiplier curves.
- **Bottom Status Bar**: Continuous monitoring of 50-digit engine status, SQLite WAL mode, SHA-256 audit chaining, and version identity.

### 2. The 11-Stage Engineering Workflow
- **Projects (`/api/projects`)**: Workspace hierarchy managing customer site, scope, linked assets, and calibrations.
- **Instruments Registry (`/api/instruments`)**: Asset registry tracking manufacturer, model, serial number, measuring range, resolution, accuracy specification, calibration status, intervals, and next due date.
- **Measurement Plans (`/api/plans`)**: Standardized protocols defining measurand, nominal target, tolerance limits, repetitions, and decision rules.
- **Acquisition Studio (`/api/measurements`)**: Live reading capture, mean $\bar{x}$, sample SD $s$, Type A repeatability $u_{\text{rep}}$, and automated 3-sigma outlier detection.
- **Interactive Uncertainty Workbench (`/api/workbench/uncertainty`)**: Dynamic GUM budget builder with real-time propagation, variance waterfalls, and Welch-Satterthwaite effective degrees of freedom.
- **Dedicated Conformity Workbench (`/api/workbench/conformity`)**: Guardbanded conformity evaluation under ANSI/NCSL Z540.3 Method 6 ($P_{\text{CR}} \le 2\%$), Method 5 RSS, and ISO 14253-1 with TUR analysis.
- **Measurement Reliability Intelligence (`/api/intelligence/*`)**: 5 killer predictive engines ("WHY?", "WHAT CHANGED?", 0–100 Health Score, Drift Forecaster, and Action Recommender).

### 3. Non-Destructive Database Auto-Migration
- Upgraded SQLite schema in `metrology_app/db.py` without modifying or deleting existing records.
- 100% data retention and SHA-256 audit hash continuity for existing customers.

---

## 📦 Verified Release Binaries

- **Windows Setup Installer**: `Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe` (`58.7 MB`)
  - `SHA256: bb4d077fa55bc7195d2b277fa8dd04eba20eae18ef40bdd30aaf74cf61398b75`
- **Standalone Binary**: `MetrologyWorkstation.exe` (`53.2 MB`)
  - `SHA256: a007ff711762b23f84bca0ea0ec5ac7197aca3af59fa7c281e1c0b4e96f31b83`
