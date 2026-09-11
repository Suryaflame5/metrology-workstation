# ENTITLEMENT DATA MODEL — METROLOGY WORKSTATION

**Date**: 2026-08-16  
**Status**: CANONICAL SPECIFICATION  

---

## 1. Canonical Entitlement Token Schema

The signed entitlement token is represented as a UTF-8 JSON structure:

```json
{
  "header": {
    "alg": "HMAC-SHA256",
    "key_id": "METROLOGY-PUB-2026-V1",
    "version": "1.0"
  },
  "payload": {
    "entitlement_id": "ENT-9842-8812-7731",
    "customer_id": "CUST-ACME-CORP",
    "customer_name": "ACME Precision Standards Laboratory",
    "organization_id": "ORG-7782",
    "product_id": "MetrologyWorkstation.Commercial",
    "plan_id": "PROFESSIONAL",
    "license_type": "ANNUAL_SUBSCRIPTION",
    "status": "ACTIVE",
    "seat_limit": 1,
    "device_limit": 2,
    "issued_at": "2026-08-16T00:00:00Z",
    "expires_at": "2027-08-16T23:59:59Z",
    "renewal_at": "2027-08-16T00:00:00Z",
    "grace_period_days": 30,
    "features": [
      "ALL_7_INSTRUMENT_FAMILIES",
      "MULTI_POINT_STUDIO",
      "UNLIMITED_RECORDS",
      "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
      "UNWATERMARKED_CERTIFICATES",
      "HASH_CHAINED_AUDIT_VAULT",
      "SQLITE_ATOMIC_BACKUPS",
      "OFFLINE_OPERATION"
    ]
  },
  "signature": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

## 2. Supported Plan Identifiers

- `FREE`: Community / Evaluation Edition (Default state).
- `PROFESSIONAL`: Professional Single-Workstation License.
- `BUSINESS`: Business / Team Multi-Seat License.
- `ENTERPRISE`: Enterprise Multi-Site Air-Gapped License.

---

## 3. Feature Permissions Flag Catalog

| Feature Flag | Free | Professional | Business | Enterprise |
| :--- | :---: | :---: | :---: | :---: |
| `SINGLE_POINT_MICROMETER` | ✅ | ✅ | ✅ | ✅ |
| `ALL_7_INSTRUMENT_FAMILIES` | ❌ | ✅ | ✅ | ✅ |
| `MULTI_POINT_STUDIO` | ❌ | ✅ | ✅ | ✅ |
| `UNLIMITED_RECORDS` | ❌ (10 max) | ✅ | ✅ | ✅ |
| `MACHINE_VERIFIABLE_EVIDENCE_ZIP` | ❌ | ✅ | ✅ | ✅ |
| `UNWATERMARKED_CERTIFICATES` | ❌ | ✅ | ✅ | ✅ |
| `HASH_CHAINED_AUDIT_VAULT` | ❌ | ✅ | ✅ | ✅ |
| `SQLITE_ATOMIC_BACKUPS` | ❌ | ✅ | ✅ | ✅ |
| `CUSTOM_LAB_BRANDING` | ❌ | ❌ | ✅ | ✅ |
| `MULTI_SEAT_ORGANIZATION` | ❌ | ❌ | ✅ | ✅ |
| `AIR_GAPPED_CUSTOM_KEYS` | ❌ | ❌ | ❌ | ✅ |
