# Standards Concordance: JCGM 100:2008 (GUM)

**Standard Title**: Evaluation of measurement data — Guide to the expression of uncertainty in measurement (GUM 1995 with minor corrections)  
**Publishing Body**: Joint Committee for Guides in Metrology (BIPM, IEC, IFCC, ILAC, ISO, IUPAC, IUPAP, OIML)  
**Status**: Authoritative Reference Baseline (with 2026 Non-Linearity Amendment considerations)

---

## Concordance Matrix

### 1. Type A Evaluation of Standard Uncertainty
- **Standard Clause**: JCGM 100:2008 §4.2
- **Formula**:
  - Arithmetic Mean: $\bar{q} = \frac{1}{n} \sum_{k=1}^n q_k$ (§4.2.1)
  - Experimental Variance: $s^2(q_k) = \frac{1}{n-1} \sum_{k=1}^n (q_k - \bar{q})^2$ (§4.2.2)
  - Standard Uncertainty of the Mean: $u(\bar{q}) = \frac{s(q_k)}{\sqrt{n}}$ (§4.2.3)
  - Degrees of Freedom: $\nu = n - 1$ (§4.2.6)
- **Implementation**: [`metrology_core/uncertainty/type_a.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/type_a.py) (`evaluate_type_a`)
- **Validation Test**: `test_type_a_evaluation_basic`
- **Classification**: `VERIFIED (Exact GUM §4.2)`

---

### 2. Type B Evaluation of Standard Uncertainty
- **Standard Clause**: JCGM 100:2008 §4.3 & Table 1
- **Formula**:
  - Rectangular / Uniform Distribution: $u = \frac{a}{\sqrt{3}}$ (§4.3.7)
  - Triangular Distribution: $u = \frac{a}{\sqrt{6}}$ (§4.3.9)
  - Normal Distribution with specified expanded uncertainty: $u = \frac{U}{k}$ (§4.3.3)
  - U-shaped / Arc-sine Distribution: $u = \frac{a}{\sqrt{2}}$ (§4.3.8)
- **Implementation**: [`metrology_core/uncertainty/type_b.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/type_b.py) (`evaluate_type_b`)
- **Validation Test**: `test_type_b_rectangular`, `test_type_b_triangular`, `test_type_b_normal`, `test_type_b_u_shaped`
- **Classification**: `VERIFIED (Exact GUM §4.3)`

---

### 3. Law of Propagation of Uncertainty (Combined Uncertainty $u_c$)
- **Standard Clause**: JCGM 100:2008 §5.1 & §5.2
- **Formula**:
  $$u_c^2(y) = \sum_{i=1}^N \left(\frac{\partial f}{\partial x_i}\right)^2 u^2(x_i) + 2 \sum_{i=1}^{N-1} \sum_{j=i+1}^N \frac{\partial f}{\partial x_i} \frac{\partial f}{\partial x_j} u(x_i, x_j)$$
  (Equations 10 and 13)
- **Implementation**: [`metrology_core/uncertainty/propagation.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/propagation.py) (`propagate_uncertainty`)
- **Validation Test**: `test_propagate_uncertainty_independent`, `test_propagation_with_correlation`
- **Classification**: `VERIFIED (Exact GUM §5.1/5.2) — First-order Taylor approximation`
- **Engineering Caveat**: First-order linear approximation assumes weak model curvature. Strongly non-linear models must be cross-checked with JCGM 101:2008 Monte Carlo.

---

### 4. Effective Degrees of Freedom (Welch-Satterthwaite Equation)
- **Standard Clause**: JCGM 100:2008 Annex G, §G.4.1
- **Formula**:
  $$\nu_{\text{eff}} = \frac{u_c^4(y)}{\sum_{i=1}^N \frac{c_i^4 u^4(x_i)}{\nu_i}}$$
  (Equation G.2b)
- **Implementation**: [`metrology_core/uncertainty/degrees_of_freedom.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/degrees_of_freedom.py) (`calculate_welch_satterthwaite`)
- **Validation Test**: `test_welch_satterthwaite`
- **Classification**: `VERIFIED (Exact GUM Annex G)`

---

### 5. Reporting Uncertainty and Significant Digits
- **Standard Clause**: JCGM 100:2008 §7.2.6
- **Guidance**: Numerical value of expanded uncertainty $U$ rounded to at most two significant digits; measurement result rounded to match the last significant decimal place of $U$.
- **Implementation**: [`metrology_core/rounding/metrological.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/rounding/metrological.py) (`round_uncertainty`, `format_metrological_result`)
- **Validation Test**: `test_reference_tc03`, `test_anti_sequential_rounding`
- **Classification**: `VERIFIED (Exact GUM §7.2.6)`
