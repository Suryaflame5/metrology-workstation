# POST-RELEASE OPERATIONS & INCIDENT RESPONSE — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: OPERATIONAL MANUAL  

---

## 1. Customer Support & License Fulfillment Workflows

```text
               PURCHASE & FULFILLMENT WORKFLOW
                              │
     Customer Purchases via Web Portal / Microsoft Store / PO
                              │
                              ▼
    Entitlement Authority generates signed token (Ed25519 / HMAC)
                              │
               ┌──────────────┴──────────────┐
               │                             │
        Instant Online Ingest        Air-Gapped Delivery (.json token)
               │                             │
               └──────────────┬──────────────┘
                              ▼
           User inputs token in "Plans & Licensing" UI
                              │
                              ▼
        Client verifies signature & unlocks capabilities
```

---

## 2. Standard Operating Procedures (SOPs)

### SOP-01: License Recovery & Migration
- **Scenario**: Customer replaces workstation hardware or reinstalls Windows.
- **Resolution**: Customer logs into web billing portal (or contacts support with Purchase Order ID). Entitlement token is re-issued for the active subscription period. Client imports token with 0 data loss.

### SOP-02: Refund & Subscription Cancellation
- **Scenario**: Customer cancels subscription.
- **Behavior**: Token remains in `ACTIVE` until `expires_at`, enters `GRACE` for 30 days, then reverts to `EXPIRED` (`FREE` community mode). All stored local calibration databases remain 100% accessible.

### SOP-03: Security & Cryptographic Key Rotation
- **Frequency**: Annual key rollover (`key_id: "METROLOGY-PUB-2027-V1"`).
- **Procedure**: New release builds bundle updated public verification keys while retaining verification compatibility with active legacy key IDs.

### SOP-04: Software Defect & Urgent Patch Release
- **Severity 1 (Math Anomaly)**: If a bug is identified in uncertainty equations, patch is developed, tested against 70+ tests, version incremented (e.g. `0.9.9.1`), packed with `MakeAppx`, signed with `SignTool`, and pushed as high-priority Store update.
