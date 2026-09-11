# 5-Minute Commercial Sales Demonstration Script
## Metrology Workstation V6 (Professional Edition — $599/Year)

> **Audience**: Chief Metrologists, Laboratory Directors, Calibration Quality Managers, ISO/IEC 17025 Lead Assessors.  
> **Key Objective**: Prove why Metrology Workstation replaces error-prone Excel spreadsheets and expensive $15,000 enterprise legacy software with an exact 50-digit sovereign calibration workstation for just $599/year.

---

## Overview Timeline & Stage Map

| Timestamp | Phase | On-Screen Action | Key Value Proposition |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:30** | The Hook & Kernel | Command Center (`/overview`) & First-Run Tour | 50-digit exact decimal arithmetic, 100% air-gapped sovereignty. |
| **0:30 – 1:00** | Import & Validation | Measurements Table (`/measurements`) | Automated Grubbs outlier filter, settling slew validation. |
| **1:00 – 1:45** | Measurement Model & GUM | Uncertainty Workbench (`/uncertainty`) | 8-step GUM budget, Type A/B synthesis, Welch-Satterthwaite DoF. |
| **1:45 – 2:30** | Monte Carlo & Conformity | Monte Carlo (`/monte-carlo`) & Conformity (`/conformity`) | 10,000-draw PDF propagation, ANSI Z540.3 Method 6 root guardband ($P_{CR} \le 2.0\%$). |
| **2:30 – 3:15** | Provenance & Tamper Test | Calculation Chain (`/calculation-chain`) | 12-stage cryptographic replay; live malicious tamper detection alert. |
| **3:15 – 4:00** | Digital Sign & PDF Export | Reports Workspace (`/reports`) | FDA 21 CFR Part 11 signature ceremony, ReportLab ISO 17025 PDF certificate, Evidence ZIP. |
| **4:00 – 4:45** | Connectivity & Intelligence | Instruments Workspace (`/instrument`) | SCPI IEEE-488 bus terminal, live 1Hz telemetry, adaptive interval optimization. |
| **4:45 – 5:00** | Commercial Close | Pricing & Next Steps (`website/pricing.html`) | $599/year ($50/mo equiv); Founding Customer Program ($299/yr for first 10 labs). |

---

## Detailed Step-by-Step Script & Narration

### Part 1: The Hook & Exact 50-Digit Sovereign Engine (0:00 – 0:30)
- **On-Screen**: Open workstation at `http://localhost:3000`. Show the sleek Command Center with active instruments, passing statistics, and the First-Run Onboarding Tour.
- **Narrator**:
  > *"Every accredited calibration lab shares a terrifying vulnerability: standard spreadsheets use 64-bit floating-point math that introduces silent roundoff errors into your uncertainty budgets. When an ISO 17025 assessor audits your lab, a single rounding discrepancy can trigger non-conformances and suspend your scope.*
  > 
  > *Welcome to Metrology Workstation V6. Powered by an arbitrary-precision 50-digit decimal kernel, it completely eliminates floating-point cancellation. It operates 100% locally and air-gapped—zero cloud dependency, zero telemetry, keeping your proprietary defense and aerospace calibration data sovereign."*

---

### Part 2: Automated Ingestion & Statistical Outlier Filtering (0:30 – 1:00)
- **On-Screen**: Navigate to **Measurements** (`/measurements`). Show the 48-reading voltage series. Point out the statistical summary (Mean: 25.00120 mm, $s = 0.00028$ mm).
- **Narrator**:
  > *"We begin with raw observations. Whether acquired directly from an instrument bus or imported from a spreadsheet batch, the system instantly evaluates the data against ISO standards. 
  > 
  > Notice the Validation rule engine: it automatically executes Grubbs outlier rejection at 95% confidence, purges settling transients, and validates degrees of freedom before any math is approved."*

---

### Part 3: GUM Uncertainty Budget Assembly (1:00 – 1:45)
- **On-Screen**: Switch to **Uncertainty Workbench** (`/uncertainty`). Show the 8-step budget breakdown: Type A repeatability ($u_A$), Reference Standard ($u_{std}$), Resolution ($u_{res}$), Thermal expansion coefficient ($u_{temp}$).
- **Narrator**:
  > *"Next, we evaluate the measurement model under JCGM 100:2008 (GUM). Our 8-step workflow guides the technician effortlessly. 
  > 
  > The system computes the sensitivity coefficients, synthesizes Type A and Type B distributions, and calculates effective degrees of freedom via the Welch-Satterthwaite equation. With one click, we calculate a combined uncertainty of 0.00017 mm and an expanded uncertainty $U_{95}$ of 0.00034 mm with exact $k=2.00$ coverage."*

---

### Part 4: Monte Carlo Verification & ANSI Z540.3 Guardbanding (1:45 – 2:30)
- **On-Screen**: Switch to **Monte Carlo** (`/monte-carlo`), click "Run 10,000 Draws". Then navigate to **Conformity** (`/conformity`) to display the Method 6 root guardband curve and acceptance zone.
- **Narrator**:
  > *"To validate complex or asymmetric distributions, we run 10,000 Monte Carlo draws. The numerical propagation aligns with the GUM analytical budget to within 10 decimal digits.
  > 
  > In conformity assessment, passing the tolerance isn't enough: under ANSI/NCSL Z540.3 Method 6, we apply a root guardband. This shrinks the specification limits inward, guaranteeing consumer risk $P_{CR} \le 2.0\%$. The decision rule provides an unassailable mathematical justification for every PASS/FAIL verdict."*

---

### Part 5: 12-Stage Provenance Replay & Live Tamper Test (2:30 – 3:15)
- **On-Screen**: Open **Calculation Chain** (`/calculation-chain`). Select `MC-00001042`. Expand Stages 1, 8, and 11 to reveal equations and cryptographic digests. Click **"Simulate Tamper Test"** to trigger the red alert banner, then click **"Restore Intact State"**.
- **Narrator**:
  > *"Here is the crown jewel: our 12-Stage Mathematical Replay and Cryptographic Provenance.
  > 
  > Every calculation step is permanently logged with an immutable SHA-256 hash. You can replay the entire derivation from raw sensor bits to final rounding.
  > 
  > Watch what happens if an unauthorized actor tampers with a single raw reading by just 50 microns: [Click Simulate Tamper Test]. The system immediately flags the hash divergence and locks the record. Assessors can verify that calibration results have remained 100% tamper-free."*

---

### Part 6: FDA 21 CFR Part 11 Electronic Signature & ISO 17025 PDF (3:15 – 4:00)
- **On-Screen**: Open **Reports** (`/reports`). Click **"21 CFR Part 11 Signature Ceremony"**. Enter technician credentials and approve. Click **"Download ISO 17025 PDF"** and **"Evidence Package (.ZIP)"**.
- **Narrator**:
  > *"When the technician completes the evaluation, they initiate the FDA 21 CFR Part 11 digital signature ceremony. Entering authorized credentials cryptographically seals the record with a legal timestamp and HMAC token.
  > 
  > We then export a publication-ready ISO/IEC 17025 calibration certificate powered by our ReportLab PDF engine, complete with QR code verification, uncertainty budget tables, and unbroken NIST traceability paths. We can also export a self-contained Evidence ZIP package containing SQLite records, calculation hashes, and audit manifests."*

---

### Part 7: Hardware Studio & Calibration Interval Optimization (4:00 – 4:45)
- **On-Screen**: Switch to **Instruments** (`/instrument`). Show the SCPI terminal running `*IDN?`, toggle **"Start Stream"** to show 1Hz live telemetry, and click **"Calculate Optimal Interval"**.
- **Narrator**:
  > *"Metrology Workstation also connects directly to your test bench. Our SCPI Hardware Studio communicates with Keysight, Fluke, and Keithley instruments over GPIB IEEE-488 and USB VISA. We can stream live ADC telemetry at 1 Hz with real-time temperature tracking.
  > 
  > Furthermore, our Adaptive Interval engine analyzes multi-cycle drift regression under ILAC-G24. With a measured drift rate of only 0.42 ppm/year, the workstation mathematically justifies extending the calibration cycle from 12 to 15 months, saving laboratories thousands in unnecessary downtime."*

---

### Part 8: The Commercial Value & Close (4:45 – 5:00)
- **On-Screen**: Show `website/pricing.html` highlighting **$599/year ($50/month equivalent)** and the **Founding Customer Program ($299/year)**.
- **Narrator**:
  > *"Legacy calibration packages charge upwards of $10,000 to $15,000 plus annual maintenance fees for clunky, outdated software.
  > 
  > Metrology Workstation Professional delivers exact 50-digit math, 22 specialized engineering workspaces, ISO 17025 PDF certificate generation, and machine-verifiable audit chains for just $599 per year—less than $50 a month.
  > 
  > We are currently accepting 10 accredited laboratories into our Founding Customer Program at $299 for life in exchange for direct feedback. Secure your lab's license today at metrology.novyrax.com."*

---

## Objections & Rapid Fire Responses

| Common Customer Objection | Winning Metrologist Response |
| :--- | :--- |
| **"We already have Excel macros that do our uncertainty budgets."** | *"Excel uses IEEE 754 floating-point arithmetic which is subject to catastrophic cancellation, lacks 21 CFR Part 11 tamper prevention, and has no cryptographic audit trail. Assessors are increasingly rejecting ad-hoc Excel sheets."* |
| **"Our data cannot leave our premises or go to any cloud."** | *"Metrology Workstation is 100% sovereign and air-gapped. The SQLite database, decimal engine, and PDF generator run entirely on your local workstation with zero network access required."* |
| **"Is this accredited under ISO/IEC 17025 §7.6?"** | *"Yes. We provide automated IQ/OQ/PQ validation dossiers and NIST CTS Standard Reference benchmark test results with exact zero relative error, fully satisfying Section 7.6 software qualification requirements."* |
