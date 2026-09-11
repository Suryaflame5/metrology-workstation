# User Interface (UI) Architecture & Components

This directory contains all User Interface applications and assets for the **Metrology Workstation** platform, cleanly separated from the Python mathematical and backend services.

---

## Directory Structure

```text
ui/
├── workstation/                    # Desktop Workstation Single-Page Application (SPA)
│   ├── index.html                  # Workstation Dashboard, Calibration Wizards, and Live Workbenches
│   ├── app.js                      # Core frontend client, real-time charts & REST API connectors
│   └── styles.css                  # Modern responsive design, typography & metrology component styles
│
└── website/                        # Commercial Marketing & Documentation Portal
    ├── index.html                  # Main marketing landing page
    ├── metrology-workstation.html  # Product capabilities & interactive metrology showcase
    ├── pricing.html                # Commercial tiers, features & licensing comparison
    ├── download.html               # Verified Windows installer downloads & SHA-256 hashes
    ├── docs.html                   # Metrology standards & REST API developer documentation
    ├── contact.html                # Commercial sales & technical support contact form
    ├── styles.css                  # Marketing theme, responsive grid & navigation styling
    ├── eula.html                   # End User License Agreement
    ├── privacy.html                # Privacy policy (Zero telemetry, 100% local storage)
    ├── terms.html                  # Commercial terms of service
    ├── refund.html                 # 14-day refund & cancellation policy
    ├── checkout-success.html       # Post-payment order confirmation & license key delivery
    └── checkout-cancelled.html     # Cancelled transaction fallback page
```

---

## 1. Desktop Workstation (`ui/workstation/`)

The Workstation UI is a zero-dependency, ultra-fast Single Page Application (SPA) served directly by the local FastAPI backend at `http://127.0.0.1:8000/`.

### Key Features:
- **Interactive Workbenches**:
  - GUM Uncertainty Budget Builder with dynamic sensitivity coefficients and Welch-Satterthwaite degrees of freedom.
  - Conformity Assessment Workbench with real-time ANSI/NCSL Z540.3 Method 6 root guardband curves and $P_{\text{CR}} \le 2.0\%$ risk zones.
- **Calibration Wizard**:
  - Step-by-step single-point and multi-point nominal calibration workflows with live standard block selection.
- **12-Stage Calculation Replay & Tamper Detection**:
  - Step-through mathematical playback engine with cryptographic SHA-256 verification.
- **V5/V6 Autonomous Intelligence Hub**:
  - "Why?" explainability engine, "What Changed?" longitudinal differencing, reliability health profiles, and 12-month drift forecasting.
- **Audit Ledger & 21 CFR Part 11 Signatures**:
  - Real-time cryptographic hash-chained audit viewer and electronic signature ceremony modal.

---

## 2. Commercial Website (`ui/website/`)

The NovyraX commercial web portal is designed for deployment on static edge CDNs (Vercel, Netlify, Cloudflare Pages, or GitHub Pages).

### Key Features:
- **Responsive Layout**: Optimized for desktop, tablet, and mobile browsers with dark/light mode accents.
- **Download Verification Card**: Direct download links with one-click PowerShell SHA-256 checksum verification commands.
- **PCI-DSS Compliant Payment Integration**: Dynamic UPI QR and Merchant of Record checkout handoffs.
- **Documentation & Standards Concordance**: Embedded guides for ISO/IEC 17025, ANSI/NCSL Z540.3, and JCGM 100 (GUM).
