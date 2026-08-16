# PRIVACY POLICY — METROLOGY WORKSTATION

**Effective Date**: August 16, 2026  
**Application**: Metrology Workstation (Windows Desktop Application)  
**Publisher**: Metrology Workstation Engineering  

---

## 1. Zero-Telemetry & Local-First Commitment
Metrology Workstation is designed as an **evidence-first, local-first, offline-capable desktop application** for metrology laboratories, quality engineering, and conformity assessment.

- **Zero Cloud Data Transmission**: All calibration measurements, instrument procedures, uncertainty budgets, mathematical derivations, customer certificates, and SQLite databases are stored **strictly on your local device** in `%LOCALAPPDATA%\MetrologyWorkstation\`.
- **Zero Analytics / Tracking**: We do not embed telemetry SDKs, user behavior trackers, advertising cookies, or remote session monitoring.
- **Zero Cardholder Data**: All payment transactions occur externally via Microsoft Store Commerce or authorized invoice/billing portals. The desktop application never processes, transmits, or stores credit card numbers, CVVs, or financial data.

---

## 2. Information Handled by the Application
1. **Local Laboratory Settings**: Laboratory name, accreditation reference, technician names, and certificate headers configured by the user are stored locally in `%LOCALAPPDATA%\MetrologyWorkstation\settings.json`.
2. **Entitlement Verification**: Cryptographically signed license tokens imported by the user (containing customer name, organization identifier, seat limit, and expiration timestamp) are stored locally in `%LOCALAPPDATA%\MetrologyWorkstation\license.json` and verified locally using embedded public keys.

---

## 3. Data Deletion & Retention
Users retain 100% sovereign control over all data. Uninstalling the application or deleting `%LOCALAPPDATA%\MetrologyWorkstation\` permanently removes all local databases, audit ledgers, settings, and cached license tokens from the device.

---

## 4. Contact & Compliance
For questions regarding this Privacy Policy or ISO/IEC 17025 data protection inquiries:  
**Email**: privacy@metrologyworkstation.com  
**Website**: https://metrologyworkstation.com
