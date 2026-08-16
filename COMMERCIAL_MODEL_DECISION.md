# COMMERCIAL MODEL DECISION — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Document Status**: APPROVED & ARCHITECTURAL BASELINE  

---

## 1. Evaluation of Microsoft Commercial Models

We evaluated five commercial distribution models against Microsoft Store policies, metrology industry procurement norms (ISO/IEC 17025 accredited labs, aerospace/defense contractors), and offline-first architectural constraints:

| Model | User Experience | Offline Support | Enterprise Procurements | Store Policy Compatibility | Recurring Scalability |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **A. Paid Upfront App** | Simple | Excellent | Low (Credit card only) | High | Low (No recurring tiers) |
| **B. Free App + Store IAP** | Frictionless | Good | Medium | High | High |
| **C. Azure SaaS App** | High friction | Poor (Cloud req) | High (Azure billing) | Moderate | High |
| **D. External Licensing Only** | Moderate | Excellent (Key-based) | High (PO/Invoice ready) | High (Win32 Store Policy) | High |
| **E. Hybrid Store + Key Entitlement** | **Optimal** | **Optimal** | **Optimal** | **High** | **Optimal** |

---

## 2. Recommended Commercial Architecture

### **RECOMMENDED MODEL: Hybrid Store Listing + Cryptographically Signed Offline-Capable Entitlements (Model E)**

### **Why:**
1. **Air-Gapped & Offline Calibration Environments**:
   Metrology and standards laboratories frequently operate in secure, isolated network zones (MIL-STD, defense, ISO/IEC 17025 cleanrooms) where constant internet connectivity to Microsoft Store commerce servers is prohibited. A cryptographically signed token (Ed25519) allows instant, 100% offline activation and validation.
2. **Enterprise Procurement Alignment**:
   Quality managers and calibration lab directors purchase software via Corporate Purchase Orders (PO), annual invoicing, and multi-seat site licenses—channels not supported by direct consumer Microsoft Store credit card checkout.
3. **Microsoft Store Policy Compliance**:
   Under Microsoft's updated Store policies for Win32 applications, developers are permitted to utilize independent commerce engines and licensing systems without revenue share penalties.
4. **Frictionless Onboarding**:
   The application installs freely from the Microsoft Store with a built-in **Evaluation/Community Mode**, enabling users to immediately test calculation accuracy, with instant activation to **Professional**, **Team**, or **Enterprise** upon applying a signed license token.

---

## 3. Secondary / Fallback Model

### **SECONDARY MODEL: Paid Microsoft Store Direct App (Model A)**
- **Role**: Simplified standalone single-seat SKU ($499 one-time perpetual license) directly sold on the Microsoft Store for individual engineers and solo consultants who prefer one-click Windows Store billing.

---

## 4. Why Not the Other Models
- **Model C (Azure Marketplace SaaS)**: Requires deep Azure Active Directory enterprise federation and constant internet connectivity, directly conflicting with the local-first, air-gapped architecture of precision calibration laboratories.
- **Model B (Store-Only IAP)**: Restricts purchase strictly to users with active Microsoft Store payment methods on the specific workstation, blocking institutional procurement departments from purchasing multi-seat licenses on behalf of lab technicians.
