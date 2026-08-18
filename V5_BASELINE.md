# METROLOGY WORKSTATION V5 BASELINE FREEZE

**Date**: August 18, 2026  
**Auditor**: Principal Metrology Systems Architect  
**Baseline Generation**: `v5.0.0` (Production Baseline)  
**Git Baseline Commit**: `e22241f`  

---

## 1. Baseline State & Physical Hashes

```text
┌─────────────────────────┬──────────────────────────────────────────────────────────────────────────────┐
│ Baseline Attribute      │ Frozen Value / Hash                                                          │
├─────────────────────────┼──────────────────────────────────────────────────────────────────────────────┤
│ Product Name            │ Metrology Workstation                                                        │
│ Generation              │ V5 (Measurement Reliability Intelligence)                                    │
│ Standalone Executable   │ dist/MetrologyWorkstation.exe (53,245,056 bytes)                             │
│ Executable SHA-256      │ a007ff711762b23f84bca0ea0ec5ac7197aca3af59fa7c281e1c0b4e96f31b83            │
│ Target Installer Name   │ dist/Metrology-Workstation-v1.1.0-Windows-x64-Setup.exe (Standardized)      │
│ Automated Test Baseline │ 97 / 97 Tests Passing (100%)                                                 │
│ Database Schema         │ SQLite WAL: projects, instruments, measurement_plans, measurements,           │
│                         │ calculations, audit_events, webhook_events                                   │
└─────────────────────────┴──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Frozen Capabilities Map

- **Kernel**: 50-digit exact decimal arithmetic, JCGM 100 GUM propagation, Welch-Satterthwaite DoF, JCGM 101 Monte Carlo.
- **Decision Engine**: ANSI/NCSL Z540.3 Method 5 & 6 ($P_{\text{CR}} \le 2\%$), ISO 14253-1:2017, TUR.
- **Persistence**: SQLite 3 with WAL mode, foreign keys, non-destructive auto-migrations.
- **Audit Ledger**: Block-by-block SHA-256 hash chaining.
- **Licensing**: Offline HMAC-SHA256 token verification with clock rollback detection.
- **Webhooks**: Idempotent MoR payment event processing.

This baseline is frozen and preserved. All V5.1/V5.2 additions build upon this verified engineering core.
