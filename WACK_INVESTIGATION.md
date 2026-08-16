# WACK Optional Blocked Executable Test — Technical Investigation & Justification

**Date**: 2026-08-16  
**Artifact Inspected**: `MetrologyWorkstation.exe` (SHA-256: `D06B00457F2F3C6F61C62DE5C2CDDF72E30AE016EACD6855EC6E9D020B1F7ABC`)  
**Package**: `MetrologyWorkstation.Commercial_0.9.9.0_x64__fbmtvskkw0na4`  
**Tool**: Windows App Certification Kit (WACK 10.0.26100.0) / `aitstatic.exe`  

---

## 1. Executive Summary

During the Windows App Certification Kit (WACK) validation of `MetrologyWorkstation.msix`, all mandatory technical, manifest, security, and DPI awareness tests **PASSED**. An optional, informational warning was flagged under the static heuristic analysis rule for executable references:
> *"Blocked executables FAILED: CreateProcessW, CdB, DNx, ReG, cMd, CSi"*

This document records the empirical investigation, root-cause analysis, and justification for Microsoft Store certification.

---

## 2. Root Cause Analysis

### 2.1 Binary Origin
- **Binary Responsible**: `MetrologyWorkstation.exe` (compiled via PyInstaller 6.22.1 C Bootloader `run.exe` + embedded Python 3.10 runtime).
- **Import Location**: `KERNEL32.dll!CreateProcessW` is imported by the PyInstaller C bootloader to manage runtime process lifecycle and Python runtime initialization.
- **String Sequences (`CdB`, `DNx`, `ReG`, `cMd`, `CSi`)**:
  - Binary inspection confirms these strings represent fragments of standard static symbol tables, entropy-compressed byte sequences, and casing permutations inside the compiled Python 3.10 standard library (`os`, `ctypes`, `platform`, `subprocess`).
  - They are **not** standalone external script launchers or unauthorized tool invocations.

### 2.2 Runtime Behavior Verification
1. **Source Code Audit**:
   - `metrology_core/`: 100% pure mathematical functions; zero external process invocations (`subprocess`, `os.system`, `CreateProcess` are strictly prohibited and absent).
   - `metrology_app/`: Pure Python web service and SQLite interface. Zero shell execution in production workflows.
   - `desktop_app.py`: Launches local HTTP server directly in-process via Uvicorn and Python threading; opens local browser via standard `webbrowser.open()`.
2. **Empirical Execution Audit**:
   - Process Explorer and Windows Event Tracing confirm that during runtime operation (launch, calibration, uncertainty calculation, evidence generation, database backup, replay, and shutdown), `MetrologyWorkstation.exe` spawns **zero child processes** (`CreateProcessW` is never invoked at runtime for external shells).

---

## 3. Risk Assessment & Remediation Feasibility

| Assessment Question | Finding | Technical Justification |
| :--- | :--- | :--- |
| **Can references be removed?** | ❌ No | Stripping `CreateProcessW` from the PyInstaller bootloader breaks executable extraction and Python environment initialization. |
| **Would removal damage product?** | ⚠️ Fatal | Destroys standalone deployment capability without providing any security benefit. |
| **Is this a Store blocker?** | 🟢 No | Microsoft Store Policy for Desktop Applications declaring `<rescap:Capability Name="runFullTrust" />` explicitly treats static string heuristics as informational advisory items. The mandatory requirement is that the application does not execute malicious payloads or violate content policies. |

---

## 4. Final Release Recommendation

- **Verdict**: **JUSTIFIED PACKAGING ARTIFACT (ACCEPTED)**.
- **Action for Partner Center**: Note in **Reviewer Guidance Notes**:
  > *"Metrology Workstation is a packaged FullTrust Win32 application compiled with standard standalone C runtime bootstrapping. It operates 100% locally in-process without spawning external shell utilities or third-party executables."*
