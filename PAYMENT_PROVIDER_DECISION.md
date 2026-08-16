# PAYMENT PROVIDER DECISION — NOVYRAX / METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Brand**: NovyraX  
**Contact**: `novyrax04@gmail.com`  

---

## 1. Provider Requirements for Indian Developer Global Distribution

1. **Geographic Availability**: Must natively support Indian bank accounts and payouts (INR/USD) without requiring an offshore entity.
2. **Merchant of Record (MoR)**: Must handle global sales tax (EU VAT, US State Sales Tax, GST) and compliance automatically.
3. **Zero Upfront Cost**: No monthly fixed fees during initial launch (percentage per transaction only).
4. **Hosted Checkout**: PCI-DSS Level 1 compliant hosted checkout pages (zero card data handled by NovyraX servers or desktop client).
5. **Robust Webhook Infrastructure**: Cryptographically signed webhooks (HMAC-SHA256) for automated license entitlement generation.

---

## 2. Evaluation of Available Payment Providers

| Provider | Merchant of Record? | Indian Payout Support | Subscription & Webhooks | Fee Structure | Launch Suitability |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Dodo Payments** | ✅ Yes | ✅ Native (Built for India $\to$ Global) | ✅ Full Webhooks | 4% + 40¢ | **RECOMMENDED PRIMARY** |
| **Lemon Squeezy** | ✅ Yes | 🟡 Supported (Subject to MoR KYC) | ✅ Full Webhooks | 5% + 50¢ | **SECONDARY BACKUP** |
| **Paddle** | ✅ Yes | 🟡 Supported (Higher volume focus) | ✅ Full Webhooks | 5% + 50¢ | **ENTERPRISE BACKUP** |
| **Razorpay Standard**| ❌ No | ✅ Native (Domestic India focus) | 🟡 Complex Intl Tax | 2% - 3% | Low (Not MoR for global sales) |
| **Gumroad** | ✅ Yes | 🟡 Supported | 🟡 Limited Custom Webhooks | 10% Flat | Moderate (High fee) |

---

## 3. Final Decision

### **SELECTED PRIMARY: Dodo Payments (with Lemon Squeezy as Secondary MoR)**

### **Why:**
1. **Designed for Global Software Sales from India**: Simplifies cross-border compliance, automatic currency conversion, and payouts directly to Indian banks.
2. **Clean Webhook Signatures**: Standard `webhook_id`, `event_type` (`payment.succeeded`, `subscription.created`, `subscription.cancelled`, `refund.processed`), and HMAC-SHA256 signature verification.
3. **Zero Maintenance Overhead**: Customer billing portal, invoicing, receipts, and refund requests are handled directly by the hosted MoR platform.
