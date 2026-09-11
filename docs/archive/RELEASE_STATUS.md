# RELEASE STATUS — METROLOGY WORKSTATION V0.9.9.0

**Date**: 2026-08-16  
**Final Release Auditor**: Release Engineering, Product Commercialization & Store Publishing Team  

---

## 1. Release Specification & Status Matrix

- **CURRENT VERSION**: `0.9.9.0` (`V0.9.9-RC-FINAL`)
- **COMMERCIAL MODEL**: Hybrid Microsoft Store Listing + Cryptographically Signed Offline-Capable Entitlements (Model E).
- **PRICING**:
  - Community: **$0** (Free evaluation)
  - Professional: **$49 / mo** ($490 / yr, $990 perpetual)
  - Business / Team: **$1,490 / yr** (5 seats)
  - Enterprise: **$4,900 / yr** (Site license 25+ seats)
- **PAYMENT MODEL**: External / Store In-App Checkout (Zero cardholder data handled in desktop client).
- **ENTITLEMENT MODEL**: Canonical JSON token with HMAC-SHA256 / Ed25519 signature verification using embedded public verification key.
- **TRIAL**: 14-Day Full-Featured Professional Trial with tamper-resistant audit vault checkpointing.
- **OFFLINE POLICY**: 100% Offline-First. Perpetual licenses operate permanently offline; subscriptions operate with a 30-day offline cached grace period.
- **LICENSE SECURITY**: Monotonic clock comparison against SQLite audit timestamps prevents backdating; canonical payload hashing prevents tampering.
- **WACK**: **PASSED** (All mandatory schema, security, capability, DPI awareness, and reliability tests passed. Bootloader static string heuristics investigated and documented in `WACK_INVESTIGATION.md`).
- **PACKAGE**: `dist\MetrologyWorkstation.msix` (51,175,673 bytes / 48.8 MB) packed with Windows 11 SDK `MakeAppx.exe`.
- **SIGNATURE**: Authenticode SHA-256 signed with `CN=MetrologyWorkstation` via `SignTool.exe` (0 warnings, 0 errors).
- **REGRESSION**: **70 / 70 PASS** (63 mathematical/core regression tests + 7 commercial entitlement lifecycle tests).
- **COMMERCIAL QA**: **100% PASS** (Verified on Windows `C:\Program Files\WindowsApps\MetrologyWorkstation.Commercial_0.9.9.0_x64__fbmtvskkw0na4`).
- **PARTNER CENTER**: **READY FOR SUBMISSION**.
- **BLOCKERS**: **NONE** (Zero technical blockers).
- **USER ACTION REQUIRED**: Reserve app name in Microsoft Partner Center and upload `dist\MetrologyWorkstation.msix`.
- **NEXT EXACT ACTION**: Open Microsoft Partner Center Dashboard $\to$ Create New App Submission $\to$ Upload `dist\MetrologyWorkstation.msix` and attach `PARTNER_CENTER_REVIEWER_GUIDE.md`.

---

## 2. Immutable Release Hashes

| Artifact | SHA-256 Digest |
| :--- | :--- |
| **`MetrologyWorkstation.exe`** | `F8985911CE443E5139C15C3E329340714F4F1574334EEDA7C99F3643B52E8E05` |
| **`MetrologyWorkstation.msix`** | `88516BA768185BDF38039FEBF9501F664BAFA77CE743C1C551B12F1F18671017` |
| **`AppxManifest.xml`** | `4D43F9F3518ACB3C28931E9A7E27F3C7C330F64016A41904136A5AEFAB181729` |
| **`build_lock.json`** | `C97E6FA2FC390B3D3115F1958C3E46E3BF4ED3738A20D6B605F49C9C515DF812` |

---

## 3. DO THIS NEXT

1. **Log into Microsoft Partner Center**:
   - Navigate to [partner.microsoft.com/dashboard](https://partner.microsoft.com/dashboard).
2. **Create New Submission for "Metrology Workstation"**:
   - Set Product Type: **MSIX / MSI or EXE app**.
   - Upload the sealed package:
     `C:\Users\Lenovo\OneDrive\Documents\First_Product\dist\MetrologyWorkstation.msix`
3. **Copy Listing & Reviewer Details**:
   - Paste description, keywords, and system requirements from [`STORE_SUBMISSION_CHECKLIST.md`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/STORE_SUBMISSION_CHECKLIST.md).
   - In **Notes for Certification / Reviewer Notes**, paste the contents of [`PARTNER_CENTER_REVIEWER_GUIDE.md`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/PARTNER_CENTER_REVIEWER_GUIDE.md).
4. **Submit for Certification**:
   - Click **Submit to the Store**. Microsoft's automated ingestion pipeline will validate the package, perform production re-signing, and publish the application to the Microsoft Store.
