# PAYMENT & COMMERCE ARCHITECTURE — NOVYRAX / METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Publisher / Studio**: NovyraX (`https://novyrax.vercel.app`)  
**Official Email**: `novyrax04@gmail.com`  

---

## 1. Commercial Flow Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER (BUYER)                         │
│  • Visits https://novyrax.vercel.app/pricing                │
│  • Selects Professional ($490/yr) or Business ($1,490/yr)   │
└──────────────────────────────┬──────────────────────────────┘
                               │ Clicks Checkout
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             HOSTED MERCHANT OF RECORD (Dodo / MoR)          │
│  • PCI-DSS Level 1 Hosted Checkout Page                     │
│  • Processes Credit Card, PayPal, Apple Pay, Google Pay     │
│  • Manages Global Sales Tax (VAT/GST) & Receipts            │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS POST Webhook (HMAC-SHA256 Signed)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│             NOVYRAX ENTITLEMENT BACKEND                     │
│  • Verifies Webhook Signature (X-Signature)                 │
│  • Checks Idempotency (Event ID uniqueness)                 │
│  • Maps Product ID -> Plan ID (PROFESSIONAL, BUSINESS, etc.)│
│  • Issues Cryptographically Signed Entitlement Token        │
│  • Delivers Token & Download Link to Customer Email         │
└──────────────────────────────┬──────────────────────────────┘
                               │ Customer Downloads & Pastes Token
                               ▼
┌─────────────────────────────────────────────────────────────┐
│         METROLOGY WORKSTATION (DESKTOP CLIENT)              │
│  • Verified Installer: Metrology-Workstation-v1.0.0-Setup   │
│  • User enters token in "Plans & Licensing" UI              │
│  • Verifies HMAC signature locally with embedded public key │
│  • Operates 100% Offline with 30-Day Grace Period           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Webhook Event Specification

| Event Name | Trigger | Backend Action | Resulting Entitlement State |
| :--- | :--- | :--- | :---: |
| `payment.succeeded` | One-time or annual purchase completed | Issues signed token with `expires_at: +365 days` | `ACTIVE` |
| `subscription.renewed` | Annual/monthly recurring bill charged | Issues extended token with new `expires_at` | `ACTIVE` |
| `subscription.cancelled`| Customer cancels auto-renew | Token expires at term end; enters 30-day grace | `ACTIVE` $\to$ `GRACE` |
| `refund.processed` | Payment refunded / chargeback | Issues revocation notice / clears entitlement | `REVOKED` / `FREE` |

---

## 3. Strict Security Boundaries
1. **Zero Cardholder Data**: The NovyraX server and desktop client never receive or store credit card numbers, CVVs, or bank data.
2. **Asymmetric Verification Protocol**: The desktop client embeds only public verification material (`PUBLIC_VERIFY_KEY`).
3. **Idempotency & Replay Resistance**: Every webhook payload contains an `event_id` checked against the database to prevent replay attacks.
