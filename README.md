# METROLOGY — Evidence-First Local Calibration System (v0.3.0)

A local-first calculation and evidence system that turns calibration measurements into reproducible uncertainty analysis, conformity decisions, and machine-verifiable evidence packages.

---

## Zero-Cost Local-First Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRODUCT LAYER                                 │
│                                                                         │
│  [Screen 1] Dashboard          [Screen 2] Setup                         │
│  [Screen 3] Measurements       [Screen 4] Uncertainty Budget            │
│  [Screen 5] Decision           [Screen 6] Evidence & Verification       │
├─────────────────────────────────────────────────────────────────────────┤
│                     EVIDENCE & PROVENANCE ENGINE                        │
│                                                                         │
│  • SQLite Local Database (`metrology_data.db`)                          │
│  • Machine-Verifiable JSON Evidence Bundles                             │
│  • Canonical SHA-256 Tamper-Evident Receipts                            │
│  • Standalone HTML / PDF Certificate Generator                          │
│  • Independent Local Evidence Verifier CLI                              │
├─────────────────────────────────────────────────────────────────────────┤
│                 CALCULATION ENGINE (metrology-core)                     │
│                                                                         │
│  • JCGM 100:2008 (GUM) Law of Propagation                               │
│  • JCGM 101:2008 Monte Carlo Distribution Propagation                   │
│  • Welch-Satterthwaite Effective Degrees of Freedom                     │
│  • Exact Decimal Cholesky PSD Matrix Verification                       │
│  • ANSI/NCSL Z540.3 Method 5 & Method 6 Guardbanding                    │
│  • ISO 14253-1:2017 Decision Rules                                      │
│  • GUM 7.2.6 & ISO 80000-1 Metrological Rounding                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Run Complete Automated Test Suite (53 Tests):
```powershell
python -m pytest -v
```

### 2. Run Demo Micrometer Calculation CLI:
```powershell
python -m metrology_app.cli demo
```

### 3. Independently Verify Calculation Provenance:
```powershell
python -m metrology_app.cli verify MC-00001042
```

### 4. Export Machine-Verifiable Evidence Package:
```powershell
python -m metrology_app.cli export MC-00001042
```
Output files created under `evidence_packages/MC-00001042/`:
- `calculation.json`
- `measurements.json`
- `uncertainty_budget.json`
- `decision.json`
- `provenance.json`
- `verification.json`

### 5. Launch Local Web Application:
```powershell
python -m metrology_app.cli serve --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## The 6 Screens Vertical Slice (Micrometer 0–25 mm)

1. **Dashboard**: Metrics summary (Total, Validated, Needs Review) and list of cryptographically tracked calibration records.
2. **Setup**: Instrument selection, procedure selection (`Micrometer Calibration v1`), nominal checkpoint, tolerance limits ($\pm 0.002\text{ mm}$), confidence level, and target decision rule.
3. **Measurement Input**: Reference standard calibration data ($25.00000\text{ mm}$, $U = 0.00040\text{ mm}$, $k=2$), 5 repeated Type A runs ($25.0012, 25.0010, 25.0014, 25.0011, 25.0013\text{ mm}$), resolution, and thermal expansion parameters.
4. **Uncertainty Budget (The Centerpiece)**: Full breakdown table with component types (A/B), distributions, divisors, $u_i$, sensitivities $c_i$, variance contributions, $\%$ share, effective degrees of freedom $\nu_{\text{eff}}$, coverage factor $k$, combined $u_c$, and expanded uncertainty $U_{95}$.
5. **Conformity Decision**: Visual decision diagram displaying tolerance zone vs acceptance zone, measured error, guardband $w$, TUR ($\approx 3.21$), and verdict (**PASS**).
6. **Evidence & Verification**: Canonical SHA-256 input and calculation digests, one-click export of the machine-verifiable JSON bundle and printable calibration certificate, plus an interactive independent local verification button.
