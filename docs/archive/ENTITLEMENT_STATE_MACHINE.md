# ENTITLEMENT STATE MACHINE — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: FORMAL STATE MACHINE SPECIFICATION  

---

## 1. Formal State Definitions

```text
       ┌───────────┐
       │   FREE    │ ◄──────────────────────────────┐
       └─────┬─────┘                                │
             │                                      │
             ├──► [Activate 14-Day Trial]           │
             │           │                          │
             │           ▼                          │
             │     ┌───────────┐                    │
             │     │   TRIAL   │ ──► [Trial Ended] ─┤
             │     └─────┬─────┘                    │
             │           │                          │
             └──► [Apply Valid Signed Token]        │
                         │                          │
                         ▼                          │
                   ┌───────────┐                    │
                   │  ACTIVE   │ ◄───┐              │
                   └─────┬─────┘     │              │
                         │           │ (Renewed)    │
                 [Term Expired]      │              │
                         │           │              │
                         ▼           │              │
                   ┌───────────┐     │              │
                   │   GRACE   │ ────┤              │
                   └─────┬─────┘     │              │
                         │           │              │
               [Grace Period Over]   │              │
                         │           │              │
                         ▼           │              │
                   ┌───────────┐     │              │
                   │  EXPIRED  │ ────┘              │
                   └─────┬─────┘                    │
                         │                          │
                [Revocation Notice]                 │
                         │                          │
                         ▼                          │
                   ┌───────────┐                    │
                   │  REVOKED  │ ───────────────────┘
                   └───────────┘
```

---

## 2. Transition Rules & Behavioral Contracts

| Source State | Event / Trigger | Target State | Behavioral Effect |
| :--- | :--- | :---: | :--- |
| **FREE** | No token / Default state | `FREE` | Allows Outside Micrometer single-point calibration & 10 records. |
| **FREE** | User initiates trial | `TRIAL` | Unlocks Professional features for 14 calendar days. |
| **FREE / TRIAL** | Valid signed token applied | `ACTIVE` | Unlocks entitled features according to `plan_id`. |
| **ACTIVE** | System time > `expires_at` | `GRACE` | Retains full feature access for 30 days with renewal notice. |
| **GRACE** | Valid renewal token applied | `ACTIVE` | Extends `expires_at` and clears grace notice. |
| **GRACE** | System time > (`expires_at` + `grace_period_days`) | `EXPIRED` | Reverts capabilities to `FREE` mode; stored records preserved. |
| **ANY** | Revocation token applied | `REVOKED` | Reverts to `FREE` mode immediately; audit event recorded. |
| **ANY** | Signature invalid or clock rollback detected | `FREE` | Safe fallback; flags security warning in UI. |
