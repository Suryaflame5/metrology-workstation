# ISO/IEC 17025:2017 & Metrology Compliance Guide

**Document ID:** QMS-MET-002  
**Revision:** 3.0  
**Harmonized Standards:** ISO/IEC 17025:2017, JCGM 100:2008 (GUM), ANSI/NCSL Z540.3-2006, ILAC-G8:09/2019  
**Effective Date:** September 2026  

---

## 1. Scope & Quality Management Framework

This technical guide defines the computational models, statistical algorithms, decision rules, and cryptographic safeguards implemented within the **Laboratory Metrology Workstation** to ensure strict adherence to **ISO/IEC 17025:2017** (*General requirements for the competence of testing and calibration laboratories*).

```
+---------------------------------------------------------------------------------------+
|                             ISO/IEC 17025:2017 CLAUSE MAP                            |
|                                                                                       |
|  Clause 6.5: Metrological Traceability  -----> Asset & Standard Registry Chain       |
|  Clause 7.6: Evaluation of Uncertainty   -----> JCGM 100:2008 GUM & Monte Carlo        |
|  Clause 7.8: Reporting of Results        -----> NumberedCanvas PDF & PTB DCC v3.3.0   |
|  Clause 7.8.6: Statements of Conformity  -----> ANSI Z540.3 Method 6 Guardbanding    |
|  Clause 7.11: Control of Data & Systems  -----> SHA-256 Evidence Locker & Signatures  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Metrological Traceability (Clause 6.5)

To establish an unbroken, documented chain of calibrations linking measurements to the International System of Units (SI):

1. **Reference Standard Hierarchy**:
   Every working standard or calibrator recorded in the Workstation Instrument Registry requires:
   - Primary Calibration Certificate Number.
   - Accredited Calibration Provider (NIST, NPL, PTB, or A2LA/NVLAP accredited laboratory).
   - Calibration validity expiration date.
   - Expanded uncertainty specification and coverage factor ($k$).
2. **Chain Verification**:
   During work order execution, the system validates that all reference standards utilized are active, within their calibration interval, and possess a Test Uncertainty Ratio ($TUR$) exceeding minimum criteria (typically $TUR \ge 4:1$).

---

## 3. Evaluation of Measurement Uncertainty (Clause 7.6 & JCGM 100:2008)

The Workstation implements the internationally harmonized **Guide to the Expression of Uncertainty in Measurement (GUM)**:

### 3.1 Mathematical Measurement Model
Given an output measurand $Y$ determined from $N$ input estimates $X_1, X_2, \dots, X_N$ through functional relationship:
$$Y = f(X_1, X_2, \dots, X_N)$$

### 3.2 Type A Uncertainty Evaluation
Evaluated from repeated observations under repeatability conditions:
- Arithmetic Mean:
  $$\bar{q} = \frac{1}{n}\sum_{k=1}^n q_k$$
- Experimental Sample Standard Deviation:
  $$s(q_k) = \sqrt{\frac{1}{n - 1}\sum_{k=1}^n (q_k - \bar{q})^2}$$
- Standard Uncertainty of the Mean:
  $$u_A = s(\bar{q}) = \frac{s(q_k)}{\sqrt{n}}$$
- Degrees of Freedom: $\nu_A = n - 1$.

### 3.3 Type B Uncertainty Evaluation
Evaluated by non-statistical scientific judgement, calibration certificates, and instrument datasheets:
- **Normal Distribution**:
  $$u_B = \frac{U_{\text{cert}}}{k} \quad (\text{typically } k=2.0 \text{ for } 95.45\% \text{ confidence})$$
- **Rectangular (Uniform) Distribution**:
  When limits $\pm a$ are known with no confidence profile (e.g., resolution, rounding, digital display quantization):
  $$u_B = \frac{a}{\sqrt{3}}$$
- **Triangular Distribution**:
  When values are more likely near the center of the interval $\pm a$:
  $$u_B = \frac{a}{\sqrt{6}}$$
- **U-Shaped Distribution**:
  For cyclic or thermal ambient fluctuations:
  $$u_B = \frac{a}{\sqrt{2}}$$

### 3.4 Sensitivity Coefficients & Combined Standard Uncertainty
Sensitivity coefficients are evaluated via partial derivatives $c_i = \frac{\partial f}{\partial x_i}$ evaluated at the input estimates. For uncorrelated input quantities:
$$u_c^2(y) = \sum_{i=1}^N c_i^2 \cdot u^2(x_i)$$

### 3.5 Effective Degrees of Freedom (Welch-Satterthwaite Formula)
To determine the appropriate coverage factor for non-normal or low sample size conditions:
$$\nu_{\text{eff}} = \frac{u_c^4(y)}{\sum_{i=1}^N \frac{c_i^4 \cdot u^4(x_i)}{\nu_i}}$$

### 3.6 Expanded Uncertainty
$$U = k \cdot u_c(y)$$
Where $k$ is selected based on Student's $t$-distribution for effective degrees of freedom $\nu_{\text{eff}}$ at the desired level of confidence (default $95.45\%$).

---

## 4. Statements of Conformity & Decision Rules (Clause 7.8.6)

In compliance with **ILAC-G8:09/2019** and **ANSI/NCSL Z540.3-2006 (Method 6)**, binary conformity statements must manage and report False Acceptance Risk ($PFA$).

```
                LSL                        USL
   Specification: |<------------------------>|
   Guardband (w):    |<---->|          |<---->|
   Acceptance:          |<---------------->|
                  Fail  | Pass w/ Guardband | Fail
```

### 4.1 ANSI/NCSL Z540.3 Method 6 Guardbanding
To restrict Probability of False Accept ($PFA$) to $\le 2.0\%$:
- Guardband multiplier:
  $$w = U \cdot \left(1 - \frac{2}{\sqrt{TUR^2 + 1}}\right)$$
- Acceptance Limits:
  $$AL_{\text{upper}} = USL - w$$
  $$AL_{\text{lower}} = LSL + w$$

### 4.2 Four-State Verdict Classification
1. **Pass (Accept)**: Measured value falls entirely within acceptance limits:
   $$AL_{\text{lower}} \le y \le AL_{\text{upper}}$$
2. **Conditional Pass**: Measured value lies between acceptance limit and specification limit ($AL_{\text{upper}} < y \le USL$). Consumer risk warning flagged.
3. **Conditional Fail**: Measured value lies outside specification limit by less than expanded uncertainty ($USL < y \le USL + U$).
4. **Fail (Reject)**: Measured value lies outside specification limit by more than expanded uncertainty ($y > USL + U$).

---

## 5. Reporting of Results & Certificates (Clause 7.8)

### 5.1 ISO 17025 Multi-Page Reporting Structure
Calibration reports are generated using ReportLab with dynamic `NumberedCanvas` execution:
- **Header & Accreditation**: Laboratory identity, accreditation body symbol, ISO 17025 accreditation certificate number.
- **Traceability Statement**: Explicit references to national metrology institutes (NIST, BIPM) and calibration standard serials.
- **Sequential Numbering**: Unambiguous "Page X of Y" on every page to prevent document alteration or omitted annexes.
- **Uncertainty Citation**: Explicit statement of expanded uncertainty $U$, coverage factor $k$, and coverage probability ($95.45\%$).

### 5.2 PTB Digital Calibration Certificate (DCC v3.3.0)
The Workstation automatically emits machine-interpretable DCC XML matching PTB schema version 3.3.0, enabling automated ingestion by enterprise ERP/MES pipelines.

---

## 6. Control of Data and Electronic Records (Clause 7.11 & 21 CFR Part 11)

- **Audit Trails**: Non-repudiable audit logs record user identifier, UTC timestamp, pre-change value, and post-change value for every measurement modification.
- **Electronic Signatures**: Dual sign-off workflow requires explicit technician sign-off followed by quality approval. Cryptographic SHA-256 tokens bind the signer's identity to the exact snapshot of measurement data.
- **Evidence Locker**: A unified SHA-256 manifest aggregates raw readings, procedure definitions, environment logs, and generated PDF/XML files into a verifiable zip container.

---

*This compliance guide represents the authoritative metrological basis for the Laboratory Metrology Workstation.*
