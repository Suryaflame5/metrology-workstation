# METROLOGY WORKSTATION

**Commercial Precision Metrology, Measurement Uncertainty, and Conformity Assessment Platform.**  
**Studio / Company**: NovyraX  
**Official Website**: [https://novyrax.vercel.app](https://novyrax.vercel.app)  
**Support Contact**: `novyrax04@gmail.com`  
**Current Release**: `v1.0.0` (Windows x64)  

---

## 1. Overview

**Metrology Workstation** is a sovereign, local-first Windows desktop platform engineered for accredited calibration laboratories (ISO/IEC 17025), aerospace/defense quality teams, and precision manufacturing inspectors.

### Key Capabilities
- **Exact 50-Digit Decimal Mathematics**: JCGM 100:2008 (GUM) uncertainty propagation, Welch-Satterthwaite effective degrees of freedom, and t-distribution coverage factors ($k$).
- **ANSI/NCSL Z540.3 Method 6 Decisions**: Dynamic Test Uncertainty Ratio (TUR) curve evaluation with exact root guardband calculation ensuring consumer risk ($P_{\text{CR}} \le 2.0\%$).
- **12-Stage Mathematical Replay**: Step-by-step cryptographic audit playback verifying every formula, sensitivity coefficient, and intermediate result from raw readings to final certificate.
- **7 Pre-Loaded Instrument Catalogs**: Outside Micrometers, Vernier Calipers, Dial Indicators, Height Gauges, Gauge Block Comparators, Digital Multimeters (DCV), and RTD Digital Thermometers.
- **100% Local-First & Air-Gapped**: Runtime data strictly isolated in `%LOCALAPPDATA%\MetrologyWorkstation\`. Zero cloud telemetry, zero recurring network requirement.

---

## 2. Download & Installation

### Windows 10 / 11 (64-bit) Installer:
Download the latest verified setup executable from [GitHub Releases](https://github.com/novyrax/metrology-workstation/releases/latest) or the [NovyraX Download Page](https://novyrax.vercel.app/download):
- **Installer**: `Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe`
- **SHA-256 Checksum**: `5275c1b26accdda867e1e9aa1222e7a45901d4b09a2231c508a6afd1758d8c67`

### Checksum Verification in PowerShell:
```powershell
Get-FileHash .\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe -Algorithm SHA256
```

### Silent Laboratory IT Deployment:
```powershell
.\Metrology-Workstation-v1.0.0-Windows-x64-Setup.exe --silent --no-launch
```

---

## 3. Commercial Plans & Licensing

| Plan | Pricing | Target Audience | Key Capabilities |
| :--- | :---: | :--- | :--- |
| **Community** | **$0** (Free) | Evaluation & Students | Exact GUM math, Micrometer catalog, 10 records, 100% offline |
| **Professional** | **$49/mo** or **$490/yr** | Single Workstation | All 7 instrument catalogs, Multi-point studio, Evidence ZIPs, PDF certificates, Backups |
| **Business / Team**| **$1,490/yr** | Laboratory Teams | 5 seats included, Custom lab branding, Peer review audit trails, Priority 24h SLA |
| **Enterprise** | **$4,900/yr** | Site License | 25+ seats, Air-gapped token provisioning, Custom transfer equations, 4h SLA |

*Includes a 14-day Professional trial with no credit card required.*

---

## 4. Development & Testing

```powershell
# Clone repository
git clone https://github.com/novyrax/metrology-workstation.git
cd metrology-workstation

# Run the 74-test regression suite
python -m pytest -q

# Run mathematical self-test
python -m metrology_app.cli selftest
```

---

## 5. Security & Privacy Policy

- **Zero Telemetry**: We do not collect, transmit, or monitor telemetry or analytics data.
- **Local Data Storage**: All databases and evidence packages reside exclusively on your local machine.
- **PCI-DSS Compliance**: Hosted checkout managed by PCI-DSS Level 1 compliant Merchant of Record partners. NovyraX never stores payment card data.

---

## 6. Support & Contact

- **Email**: [novyrax04@gmail.com](mailto:novyrax04@gmail.com)
- **Website**: [https://novyrax.vercel.app](https://novyrax.vercel.app)
- **Documentation**: [https://novyrax.vercel.app/docs](https://novyrax.vercel.app/docs)
