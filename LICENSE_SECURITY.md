# LICENSE SECURITY & TAMPER RESISTANCE — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: SECURITY STANDARD  

---

## 1. Threat Model & Security Controls

| Threat Scenario | Vulnerability Mechanism | Implemented Countermeasure |
| :--- | :--- | :--- |
| **Local File Tampering** | User edits `license.json` to change `"plan_id": "ENTERPRISE"` | Canonical JSON serialization + digital signature validation. Any modified bit renders the token invalid. |
| **System Clock Rollback** | User sets OS clock back 5 years to bypass subscription expiry | **Monotonic Timestamp Auditing**: Client compares system time against the latest event in the hash-chained SQLite ledger. If $T_{\text{system}} < T_{\text{ledger}} - 300\text{s}$, a clock rollback is flagged and the app reverts to Free mode until time is corrected. |
| **Signature Forgery** | User crafts fake signature | Asymmetric / HMAC signature verified with embedded public key. Client contains **zero private signing material**. |
| **Token Replay / Sideload** | Transferring single-seat token to 500 machines | Hardware / machine GUID hashing combined with seat limits in Business/Enterprise tokens. |
| **Memory Modification** | Patching boolean flag in RAM | Centralized `EntitlementService` derives permissions deterministically from verified payload on each request rather than caching vulnerable global boolean variables. |

---

## 2. Offline Verification & Grace Window Policy

```text
                  TOKEN VERIFICATION FLOW
                             │
            Is Digital Signature Cryptographically Valid?
                      ├── NO  ──► REVERT TO FREE / COMMUNITY
                      └── YES ──► Check Expiration Date
                                       │
                      ┌────────────────┴────────────────┐
                      │                                 │
             Current Time < ExpiresAt          Current Time > ExpiresAt
                      │                                 │
             STATUS = ACTIVE                   Current Time < (ExpiresAt + GraceDays)
                                                        ├── YES ──► STATUS = GRACE (Warning)
                                                        └── NO  ──► STATUS = EXPIRED (Revert to Free)
```

1. **Perpetual Licenses**: `expires_at: null` $\implies$ Status remains `ACTIVE` permanently offline.
2. **Subscription Licenses**: Valid offline throughout the paid term + 30-day offline grace period.
3. **Grace Period Behavior**: Allows full operation with a prominent reminder to reconnect for renewal verification.
