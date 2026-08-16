# ENTITLEMENT PRODUCTION AUDIT — NOVYRAX / METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Auditor**: Lead Security & Entitlement Architecture Team  

---

## 1. Cryptographic Entitlement Pipeline

```text
┌─────────────────────────────────────────────────────────────┐
│              HOSTED PAYMENT WEBHOOK (MoR)                   │
│  • Event: payment.succeeded / subscription.renewed          │
│  • Headers: X-Signature (HMAC-SHA256 of payload)            │
└──────────────────────────────┬──────────────────────────────┘
                               │ Verified by webhook_service.py
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               ENTITLEMENT ISSUANCE ENGINE                   │
│  • Generates canonical JSON payload                         │
│  • Signs payload via compute_token_signature()              │
│  • Embeds key_id, seat_limit, and expiration timestamp      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Customer pastes JSON token in UI
                               ▼
┌─────────────────────────────────────────────────────────────┐
│          METROLOGY WORKSTATION CLIENT VERIFICATION          │
│  • Strips "signature" key and canonicalizes JSON            │
│  • Recomputes HMAC digest with PUBLIC_VERIFY_KEY            │
│  • Performs constant-time comparison (hmac.compare_digest)  │
│  • Validates against SQLite audit monotonic timestamps      │
│  • Enables entitled plan features in-memory                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Cryptographic Security Guarantees

| Security Feature | Implementation Mechanism | Verification Result |
| :--- | :--- | :---: |
| **Payload Integrity** | Canonical JSON encoding (`sort_keys=True, separators=(",", ":")`) | ✅ **VERIFIED** |
| **Tamper Resistance** | Constant-time HMAC-SHA256 digest comparison | ✅ **VERIFIED** |
| **Idempotent Webhooks** | SQLite unique constraint on `event_id` in `webhook_events` | ✅ **VERIFIED** |
| **Clock Rollback Protection** | Monotonic check against `MAX(timestamp)` in SQLite audit vault | ✅ **VERIFIED** |
| **Zero Private Keys in Client** | Desktop client contains only public verification material | ✅ **VERIFIED** |
