# Laboratory Metrology Workstation — Operator Manual

**Document ID:** SOP-OPS-001  
**Revision:** 2.0  
**Compliance Standard:** ISO/IEC 17025:2017 & 21 CFR Part 11  
**Effective Date:** September 2026  

---

## 1. Introduction & Overview

The **Laboratory Metrology Workstation** is an enterprise-grade, ISO/IEC 17025 compliant calibration and measurement intelligence workstation. It provides end-to-end management of calibration work orders, direct VISA/SCPI hardware acquisition, automated statistical and GUM uncertainty evaluations, guardbanded conformity decisions, dual electronic signatures, and tamper-evident PDF/DCC certification.

`
+-----------------------------------------------------------------------------------+
|                            METROLOGY WORKSTATION v6                               |
|                                                                                   |
|  [Jobs Hub] ---> [Instrument Registry] ---> [Active Cockpit] ---> [Exceptions]    |
|       |                                             |                             |
|  [Excel / CSV]                                [Measurement DB]                    |
|       |                                             |                             |
|       v                                             v                             |
|  [Universal Importer] ---> [GUM Engine] ---> [ISO 17025 PDF & DCC XML Cert]       |
+-----------------------------------------------------------------------------------+
`

---

## 2. Navigation & User Interface Layout

The Workstation sidebar is organized into dedicated operational domains:

1. **OPERATIONS**
   - **Overview**: Real-time laboratory KPI dashboard, throughput statistics, pending approvals, and active work orders.
   - **Projects**: Lifecycle management of metrology programs, client deliverables, milestones, and batch jobs.
   - **Jobs Hub**: Creation, assignment, status tracking, and dispatching of calibration work orders.
   - **Assets**: Metrology asset registry with calibration intervals, serial numbers, accuracy specifications, and barcode scanning.
   - **Instruments**: Physical and simulated hardware bus configuration (VISA, GPIB, USB, Ethernet/LXI, Serial RS-232/485).
2. **EXECUTION**
   - **Procedures**: Standard calibration procedures (SCPs) with test points, parametric tolerances, and version locking.
   - **Active Run**: Live technician execution cockpit with real-time SCPI communication, live reading stream, and step transitions.
   - **Exceptions**: Out-of-tolerance (OOT) detection, hardware communication fault triage, and escalation disposition.
3. **METROLOGY CORE**
   - **Measurements**: Raw dataset inspection, outlier detection, normality tests, and interactive Excel/CSV ingestion.
   - **Uncertainty Studio**: JCGM 100:2008 (GUM) Type A & Type B uncertainty budget modeling, sensitivity coefficients, and effective degrees of freedom.
   - **Conformity Assessment**: ISO 14253-1 / ANSI Z540.3 Method 6 decision rules, guardbanding, and false accept risk (PFA) analysis.
   - **Reports & Certificates**: ISO/IEC 17025 compliant 4-page formal PDF certificates and DCC v3.3.0 machine-readable XML artifacts.
   - **Evidence Locker**: Cryptographic SHA-256 manifests, audit trails, raw measurement snapshots, and tamper-proof verification packages.

---

## 3. Step-by-Step Operator Workflow

### Step 1: Work Order Initiation (Jobs Hub)
1. Navigate to **Jobs Hub** in the sidebar.
2. Click **Create Calibration Job**.
3. Select the target **Asset** (or scan the asset QR/barcode).
4. Select the customer/organization and assign the responsible **Lead Technician**.
5. Choose the appropriate **Procedure** (e.g., *Digital Multimeter Verification*, *Micrometer Calibration*).
6. Set the due date and target environmental requirements (Nominal Temperature: 20.0 deg C +/- 1.0 deg C, Humidity: 45% +/- 10%).
7. Click **Create Job**. The job status initializes to SCHEDULED.

### Step 2: Instrument Connection & Self-Test
1. Navigate to **Instruments**.
2. Select the required reference standard (e.g., Fluke 5522A Calibrator, Keysight 3458A 8.5-Digit DMM).
3. Verify the connection interface (e.g., GPIB0::22::INSTR or TCPIP0::192.168.1.105::inst0::INSTR).
4. Click **Connect & Query IDN**.
5. Confirm the SCPI response returns valid manufacturer, model, and firmware version.
6. Run a diagnostic self-test (*TST?) to ensure zero hardware error registers.

### Step 3: Executing Calibration (Active Run Cockpit)
1. Navigate to **Active Run**.
2. Ensure the active Job ID is selected in the top bar.
3. Review the current procedure step, test point, nominal target, and tolerance limits.
4. For automated instruments:
   - Click **Trigger Reading** to issue the query (READ? or VAL1?).
   - The instrument response streams into the buffer, calculates residual error, and evaluates instantaneous conformity.
5. For manual instruments:
   - Enter the observed reading directly into the value input field.
   - Click **Record Measurement**.
6. If a measurement falls outside the tolerance band, an **Exception Warning** is raised immediately.
7. Repeat until all test points in the procedure are completed. Click **Finalize Execution**.

### Step 4: Importing External Datasets (Excel / CSV Ingestion)
If readings were logged via external acquisition software or dataloggers:
1. Navigate to **Measurements**.
2. Click **Import Excel / CSV**.
3. Drag and drop the .xlsx or .csv workbook into the dropzone.
4. Select the target worksheet.
5. Review the auto-detected column roles:
   - *Measurement Value*
   - *Nominal Target*
   - *Upper Tolerance Limit (USL)*
   - *Lower Tolerance Limit (LSL)*
   - *Timestamp / Unit*
6. Adjust dropdown mappings if required and click **Import Dataset**.
7. The data instantly cascades across the GUM Uncertainty engine and Conformity assessment workspace.

### Step 5: Uncertainty Budget & Conformity Evaluation
1. Navigate to **Uncertainty Studio**:
   - Verify Type A repeatability ( = s / \sqrt{n}$).
   - Inspect Type B contributors (Reference Standard calibration certificate uncertainty, resolution limits, temperature stability drift).
   - Review the calculated Combined Standard Uncertainty ($) and Expanded Uncertainty ( = k \cdot u_c$, default =2.0$, 95.45% coverage).
2. Navigate to **Conformity Assessment**:
   - Choose the decision rule (Simple Acceptance, Guardbanded Binary Acceptance ANSI Z540.3 Method 6, or ISO 14253-1).
   - Check the Probability of False Accept ( \le 2.0\%$ required under Z540.3).
   - Confirm the overall compliance verdict: **PASS**, **CONDITIONAL PASS**, or **FAIL**.

### Step 6: Technical Review & Dual Electronic Signatures (21 CFR Part 11)
1. Ensure the Job is in COMPLETED execution state.
2. In the Job Actions menu, click **Submit for Technical Sign-Off**.
3. **Technician Signature**:
   - Enter Technician Name, Title, and secure password/credential.
   - Select reason: *Author / Technical Performer*.
   - Click **Apply Electronic Signature**. A cryptographically secure SHA-256 signature token is logged into the immutable audit trail.
4. **Metrology Manager Approval**:
   - Login as Authorized Approver.
   - Review measurement residuals, uncertainty budgets, and out-of-tolerance records.
   - Apply approval signature: *Quality Reviewer / Authorized Signatory*.
   - Job status transitions to APPROVED.

### Step 7: Generating Official Certificate & DCC Export
1. Navigate to **Reports & Certificates**.
2. Click **Generate ISO 17025 Certificate (PDF)**:
   - The engine compiles a publication-ready, 4-page formal calibration report with exact 'Page X of Y' two-pass canvas numbering.
   - Page 1: Header, Laboratory accreditation logos, Asset description, Environmental conditions, General verdict.
   - Page 2: Traceability chain, Primary reference standards, Calibration dates, Traceability certificate numbers.
   - Page 3: Measurement tables, Nominals, Errors, Tolerances, Expanded Uncertainty ($), and Guardband status.
   - Page 4: GUM budget breakdown, Coverage factors ($), Degrees of freedom ($
u_{\\text{eff}}$), Dual digital signature blocks, and QR code verification link.
3. Click **Export DCC XML**:
   - Generates an internationally recognized PTB Digital Calibration Certificate (DCC v3.3.0) XML file for machine-to-machine exchange.

---

## 4. Handling Calibration Exceptions (Exception Center)

When an Out-of-Tolerance (OOT) condition or communication timeout occurs:
1. Navigate to **Exceptions**.
2. Locate the active incident flagged with OOT_ALERT or COMM_FAULT.
3. Open the incident drawer to review:
   - Delta error magnitude and percentage of tolerance consumed.
   - Historical drift on previous calibration cycles.
   - Raw SCPI communication logs.
4. Select a disposition action:
   - **Adjust and Re-measure**: Re-zero/calibrate the unit under test (UUT) and record post-adjustment readings.
   - **Limited Calibration**: Issue a limited certificate restricting specific ranges or functions.
   - **Reject / Out of Service**: Quarantine the asset, mark asset status as OUT_OF_SERVICE, and notify customer.
5. Enter justification notes and click **Resolve Incident**.

---

## 5. Security, Audit Trails & Compliance

- **Audit Trail Immutability**: Every CRUD operation, reading collection, and signature event is stored in the system SQLite database with microsecond timestamps and user IDs.
- **Path Traversal Protection**: File uploads and backup restores are sanitized against directory traversal attacks (../).
- **Data Integrity**: Every completed certificate generates an evidence bundle validated by an automatic SHA-256 digest in the **Evidence Locker**.

---

*Metrology Workstation is developed and maintained in strict conformance with ISO/IEC 17025:2017.*
