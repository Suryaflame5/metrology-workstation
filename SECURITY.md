# SECURITY POLICY — METROLOGY WORKSTATION

**Effective Date**: August 16, 2026  
**Application**: Metrology Workstation  
**Publisher**: Metrology Workstation Engineering  

---

## 1. Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported | Security Maintenance |
| :--- | :---: | :--- |
| **1.0.x** | ✅ Yes | Active Release & Security Patches |
| **< 1.0.0** | ❌ No | Deprecated Pre-Release |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability or potential cryptographic issue in Metrology Workstation, please disclose it responsibly:

- **Security Contact**: `security@metrologyworkstation.com`
- **Response SLA**: Within 48 hours of receipt.
- **Please Include**:
  - Detailed description of the issue.
  - Step-by-step reproduction instructions or proof-of-concept.
  - Potential impact assessment.

Please **do not** report security vulnerabilities via public GitHub issues.

---

## 3. Release Integrity & Verification

Every official release artifact published on GitHub is accompanied by a cryptographic SHA-256 checksum in `SHA256SUMS.txt`. Always verify your downloaded installer:

```powershell
Get-FileHash .\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe -Algorithm SHA256
```

---

## 4. Privacy & Data Boundaries
Metrology Workstation operates as a **100% local-first, zero-telemetry application**:
- Zero network telemetry or analytics tracking.
- All calibration records and databases are strictly stored locally in `%LOCALAPPDATA%\MetrologyWorkstation\`.
- Zero cardholder or financial data is ever collected or processed.
