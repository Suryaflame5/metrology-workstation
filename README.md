# CALIBRA METROLOGY WORKSTATION

**Commercial Precision Metrology, Measurement Uncertainty, and Conformity Assessment Platform.**  
**Studio / Company**: NOVYRAX Engineering Intelligence  
**Official Website**: [https://novyrax.vercel.app](https://novyrax.vercel.app)  
**Support Contact**: `novyrax04@gmail.com`  
**Current Release**: `v7.0.0` (Windows x64 Native Desktop Workstation)  

---

## 1. Product Portfolio & Separated Edition Folders

CALIBRA is modularized into four dedicated product editions, each packaged in its own folder with self-contained manifests, procedures, standards, setup wizards, and automation scripts tailored to its specific **Value of Money**:

| Product Edition | GitHub Folder Repository Link | Value of Money | Target Audience | Primary Deliverables |
| :--- | :--- | :---: | :--- | :--- |
| **Community Demo** | [`products/demo/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/demo) | **$0.00** (Free Perpetual) | Students, researchers, ISO 17025 reviewers | Standalone GUI Setup Wizard, 50-digit GUM math, Micrometer/Caliper procedures, sample datasets, local encrypted vault |
| **Professional** | [`products/professional/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/professional) | **$590.00 / yr** ($1,490 Perpetual) | Accredited calibration laboratories (1 seat) | All 7 instrument families, ANSI Z540.3 Method 5 & 6 guardbanding, unwatermarked certificates, ISO 17025 Sec 7.11 qualification |
| **Team Fleet** | [`products/team/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/team) | **$1,890.00 / yr** ($2,990 Team License) | Multi-technician calibration facilities (5 seats) | Multi-bay deployment scripts, shared air-gapped procedure vault sync, multi-instrument batch pipeline, peer-review sign-offs |
| **Enterprise Platform** | [`products/enterprise/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/enterprise) | **$4,900.00 / yr** ($4,990 Site License) | Aerospace, defense & Tier-1 manufacturing | Live SCPI/VISA hardware instrument streaming, QIF 3.0 CAD blueprints, Docker air-gap cluster, 60-second audit package |

---

## 2. Overview & Metrological Kernel

**CALIBRA Metrology Workstation** is a sovereign, local-first Windows desktop platform engineered for accredited calibration laboratories (ISO/IEC 17025), aerospace/defense quality teams, and precision manufacturing inspectors.

### Key Capabilities
- **Exact 50-Digit Decimal Mathematics**: JCGM 100:2008 (GUM) uncertainty propagation, Welch-Satterthwaite effective degrees of freedom, and t-distribution coverage factors ($k$).
- **ANSI/NCSL Z540.3 Method 6 Decisions**: Dynamic Test Uncertainty Ratio (TUR) curve evaluation with exact root guardband calculation ensuring consumer risk ($P_{\text{CR}} \le 2.0\%$).
- **12-Stage Mathematical Replay**: Step-by-step cryptographic audit playback verifying every formula, sensitivity coefficient, and intermediate result from raw readings to final certificate.
- **7 Pre-Loaded Instrument Catalogs**: Outside Micrometers, Vernier Calipers, Dial Indicators, Height Gauges, Gauge Block Comparators, Digital Multimeters (DCV), and RTD Digital Thermometers.
- **100% Local-First & Air-Gapped**: Runtime data strictly isolated in `%LOCALAPPDATA%\MetrologyWorkstation\`. Zero cloud telemetry, zero recurring network requirement.

---

## 3. Product Folder Breakdown

### A. [`products/demo/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/demo) — Free Community Evaluation ($0)
- **Manifest**: [`products/demo/manifest.json`](products/demo/manifest.json)
- **Setup Wizard**: Native Tkinter & Inno Setup wizard (`products/demo/setup_wizard/`)
- **Procedures**: Outside Micrometer (0–25 mm), Vernier Caliper (0–150 mm)
- **Standards**: Grade 0 Ceramic Gauge Block Set (STD-GB-01)
- **Zero Trial Nags**: Standalone perpetual evaluation with zero forced trial countdowns.

### B. [`products/professional/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/professional) — Accredited Lab Workstation ($590/yr)
- **Manifest**: [`products/professional/manifest.json`](products/professional/manifest.json)
- **Setup Wizard**: Gold Commercial Inno Setup installer (`products/professional/setup_wizard/setup_pro.iss`)
- **Procedures**: Complete accredited 7-instrument procedure suite
- **Licensing**: Standalone HMAC-SHA256 offline license token generator & validator
- **Qualification**: Automated ISO/IEC 17025 Section 7.11 mathematical conformity runner

### C. [`products/team/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/team) — Multi-Seat Laboratory Fleet ($1,890/yr)
- **Manifest**: [`products/team/manifest.json`](products/team/manifest.json)
- **Deployment**: 5-bench automated PowerShell provisioning script (`deploy_team_bays.ps1`)
- **Fleet Sync**: Air-gapped procedure and asset vault synchronizer (`shared_vault_sync.py`)
- **Batch Processing**: Multi-instrument batch calibration pipeline (`run_batch_calibration.py`)
- **Licensing**: Multi-seat team bundle generator (`generate_team_bundle.py`)

### D. [`products/enterprise/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/enterprise) — Industrial Platform & Site License ($4,900/yr)
- **Manifest**: [`products/enterprise/manifest.json`](products/enterprise/manifest.json)
- **Hardware SCPI / VISA**: Live hardware instrument bus communication (`scpi_bus_bridge.py`)
- **CAD QIF Engine**: ANSI/DMSC QIF 3.0 / STEP AP242 blueprint extraction (`qif_plan_parser.py`)
- **Air-Gap Server**: Containerized on-premise Docker deployment (`docker-compose.enterprise.yml`)
- **Audit Defense**: Single-click ISO/IEC 17025 & AS9100 Evidence ZIP package generator

---

## 4. Download & Installation

### Windows 10 / 11 (64-bit) Installers:
Download verified binaries from [GitHub Releases](https://github.com/Suryaflame5/metrology-releases/releases/latest) or the [NovyraX Storefront](https://novyrax.vercel.app/products/metrology-workstation/download):

| Installer | Target Edition | Dedicated Folder Link | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| `Metrology-Workstation-Demo-v7.0.0-Setup.exe` | Community Demo ($0) | [`products/demo/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/demo) | `cdc15b3ab2b2df203003b614f940bf9d9ba6ad7257b22f8fc1c31e5b37e6e486` |
| `Metrology-Workstation-Pro-v7.0.0-Setup.exe` | Professional ($590 / $1,490) | [`products/professional/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/professional) | `1072bcb7893b06edef53128fb7aecb96822e524245baf779273a9150ddabcb92` |
| `Metrology-Workstation-Team-v7.0.0-Setup.exe` | Team Fleet ($1,890 / $2,990) | [`products/team/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/team) | `a8d652ee51eba6ed77fa414094e27d491abab9fa5603248b9075804c1b820c89` |
| `Metrology-Workstation-Enterprise-v7.0.0-Setup.exe` | Enterprise ($4,900 / $4,990) | [`products/enterprise/`](https://github.com/Suryaflame5/metrology-workstation/tree/master/products/enterprise) | `bee2e78c78cf0825248cc9324acdbaa5232cf4f0330f841d418159a67963bf6c` |

### Checksum Verification in PowerShell:
```powershell
Get-FileHash .\Metrology-Workstation-Demo-v7.0.0-Setup.exe -Algorithm SHA256
Get-FileHash .\Metrology-Workstation-Pro-v7.0.0-Setup.exe -Algorithm SHA256
Get-FileHash .\Metrology-Workstation-Team-v7.0.0-Setup.exe -Algorithm SHA256
Get-FileHash .\Metrology-Workstation-Enterprise-v7.0.0-Setup.exe -Algorithm SHA256
```

---

## 5. Development & Testing

```powershell
# Run the complete test suite
python -m pytest -q

# Run mathematical ISO/IEC 17025 qualification self-test
python products/professional/qualification/run_iso17025_qualification.py
```

---

## 6. Security, Offline Privacy & Support

- **Zero Cloud Telemetry**: Runtime data strictly isolated in `%LOCALAPPDATA%\MetrologyWorkstation\`.
- **Air-Gap Concordance**: All cryptographic signatures and audit ledgers calculate locally without network dependency.
- **Support**: `novyrax04@gmail.com` | Official Portal: [https://novyrax.vercel.app](https://novyrax.vercel.app)
