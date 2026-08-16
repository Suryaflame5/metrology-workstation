# PAYMENT & COMMERCE ARCHITECTURE — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: ARCHITECTURAL BASELINE  

---

## 1. System Separation & Trust Boundaries

```text
┌─────────────────────────────────────────────────────────────┐
│                    PAYMENT & COMMERCE LAYER                 │
│  • Web Portal / Microsoft Store Commerce                     │
│  • Stripe / Invoicing / Corporate Purchase Orders (PO)      │
│  • Handles Credit Cards, Taxes, Invoices, Billing Portals   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Purchase Verified
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 ENTITLEMENT AUTHORITY (SERVER)              │
│  • Holds Private Signing Key (Ed25519 / RSA)                │
│  • Issues Cryptographically Signed Entitlement Tokens       │
│  • Manages Subscriptions, Upgrades, Revocations, & Seats    │
└──────────────────────────────┬──────────────────────────────┘
                               │ Signed Token (.json / .jwt)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             METROLOGY WORKSTATION (DESKTOP CLIENT)          │
│  • Bundles Public Verification Key ONLY (Zero Private Keys) │
│  • Verifies Digital Signature & Enforces Plan Features      │
│  • Cached in %LOCALAPPDATA%\MetrologyWorkstation\license.dat│
│  • Operates 100% Offline with Grace Period Policy           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Strict Security Boundaries
1. **Zero Cardholder Data**: The desktop client application never accepts, transmits, or stores credit card numbers, CVVs, or bank details.
2. **Zero Private Keys in Binary**: The desktop client contains only the public verification key (`METROLOGY_PUBLIC_KEY`). Signature creation occurs exclusively on the remote/air-gapped Entitlement Authority.
3. **Tamper-Proof Local Cache**: The local license cache includes canonical payload hashing and signature validation on every application boot. Modifying any character of the local file immediately reverts the application to Free Community Evaluation mode.
