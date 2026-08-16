# CHANGELOG — METROLOGY WORKSTATION

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-16

### Added
- **50-Digit Exact Decimal Kernel**: JCGM 100:2008 (GUM) uncertainty propagation, Welch-Satterthwaite effective degrees of freedom, and t-distribution coverage factors ($k$).
- **Conformity Assessment Engine**: ANSI/NCSL Z540.3 Method 5 and Method 6 guardbanding curves and ISO 14253-1:2017 decision rules.
- **7 Standard Instrument Procedure Catalogs**: Outside Micrometers, Vernier Calipers, Dial Indicators, Height Gauges, Gauge Block Comparators, Digital Multimeters (DCV), and RTD Digital Thermometers.
- **12-Stage Mathematical Replay**: Interactive step-by-step derivation viewer verifying formulas and intermediate values from raw readings to final expanded uncertainty.
- **Cryptographic Audit Vault**: SQLite database with SHA-256 hash-chained immutable audit ledger and dynamic tamper detection.
- **Atomic Online Backups**: Verified non-locking SQLite database snapshot creation and point-in-time restore.
- **Native Windows Setup Installer**: Standalone setup executable (`Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe`) and Inno Setup configuration.
- **Commercial Entitlement Engine**: Canonical JSON token signing and verification, 14-day trial activation, monotonic clock rollback protection, and Plans & Licensing UI.
- **Comprehensive Quality Suite**: 70 passing automated tests covering numerical accuracy, adversarial fuzzing, correlation matrix PSD enforcement, and upgrade retention.

### Security
- Integrated monotonic clock rollback auditing against SQLite audit ledger timestamps.
- Zero-telemetry, 100% local-first data isolation in `%LOCALAPPDATA%\MetrologyWorkstation\`.
