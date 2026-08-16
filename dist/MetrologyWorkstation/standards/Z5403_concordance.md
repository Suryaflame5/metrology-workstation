# Standards Concordance: ANSI/NCSL Z540.3-2006 (R2013) & Handbook

**Standard Title**: Requirements for the Calibration of Measuring and Test Equipment & Handbook for the Application of ANSI/NCSL Z540.3-2006  
**Publishing Body**: ANSI / NCSL International  
**Status**: Recognized Industry Calibration Standard & Handbook

---

## Concordance Matrix

### 1. Test Uncertainty Ratio ($\text{TUR}$)
- **Standard Clause**: ANSI/NCSL Z540.3-2006 §5.3.b
- **Definition**: Ratio of the span of the tolerance of a measurement quantity to twice the $95\%$ expanded uncertainty of the measurement process:
  $$\text{TUR} = \frac{T_U - T_L}{2 U_{95}}$$
- **Implementation**: [`metrology_core/decision/tur.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/tur.py) (`calculate_tur`)
- **Validation Test**: `test_fuzz_tur_boundary_transitions_250_cases`
- **Classification**: `VERIFIED (Exact ANSI/NCSL Z540.3 §5.3.b)`

---

### 2. High-TUR Threshold Rule ($\text{TUR} \ge 4.0$)
- **Standard Clause**: ANSI/NCSL Z540.3-2006 §5.3.b & Handbook §3.3
- **Rule**: When $\text{TUR} \ge 4:1$, the probability of false accept is deemed adequately controlled ($\le 2\%$) without additional guardband ($w = 0$).
- **Implementation**: [`metrology_core/decision/method6.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/method6.py), [`metrology_core/decision/method5.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/method5.py)
- **Validation Test**: `test_reference_tc01`, `test_reference_tc04_exact_tur4`, `test_reference_tc05_tur_greater_than_4`
- **Classification**: `VERIFIED (Exact ANSI/NCSL Z540.3 §5.3.b Threshold)`

---

### 3. Method 5 — Root-Sum-Square (RSS) Guardbanding
- **Standard Clause**: Handbook for ANSI/NCSL Z540.3 §3.3.4
- **Formula**: $w = \sqrt{U_{95}^2 - (T_{\text{half}} / \text{TAR})^2}$
- **Implementation**: [`metrology_core/decision/method5.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/method5.py) (`calculate_method5_guardband`)
- **Validation Test**: `test_method5_rss_guardband`
- **Classification**: `VERIFIED (Handbook Method 5 Specification)`

---

### 4. Method 6 — Empirical 2% PFA Curve
- **Standard Clause**: Handbook for ANSI/NCSL Z540.3 §3.3.5
- **Formula**: $M(\text{TUR}) = A - B \ln(\text{TUR})$ with $w = M \cdot U_{95}$
- **Implementation**: [`metrology_core/decision/method6.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/method6.py) (`calculate_method6_guardband`)
- **Validation Test**: `test_reference_tc02_repaired`, `test_reference_tc06_tur_root_crossing`, `test_reference_tc07_tur_greater_than_root`
- **Classification**: `VERIFIED (Handbook Empirical Model)`
- **Engineering Caveat**: Method 6 is an empirical curve fit from the Z540.3 Handbook calculated for specific normal prior probability distributions and $2\%$ maximum consumer's risk, not an analytical theorem of JCGM 100.
