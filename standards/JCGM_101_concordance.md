# Standards Concordance: JCGM 101:2008 (GUM Supplement 1)

**Standard Title**: Evaluation of measurement data — Supplement 1 to the "Guide to the expression of uncertainty in measurement" — Propagation of distributions using a Monte Carlo method  
**Publishing Body**: Joint Committee for Guides in Metrology  
**Status**: Authoritative Numerical Verification Path

---

## Concordance Matrix

### 1. Sampling from Probability Density Functions (PDFs)
- **Standard Clause**: JCGM 101:2008 §6.4
- **Distributions**:
  - Rectangular on $[a - w, a + w]$: $x = a + w(2r - 1), r \sim U(0, 1)$ (§6.4.2)
  - Triangular on $[a - w, a + w]$: $x = a + w(r_1 + r_2 - 1)$ (§6.4.3)
  - Gaussian / Normal $\mathcal{N}(\mu, \sigma)$: Box-Muller / polar generation (§6.4.4)
  - Student's $t$ distribution $\mu + \sigma \cdot t_\nu$ (§6.4.5)
  - U-shaped / Arc-sine distribution: $x = a + w \sin(\theta), \theta \sim U(-\pi/2, \pi/2)$ (§6.4.6)
- **Implementation**: [`metrology_core/uncertainty/monte_carlo.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/monte_carlo.py) (`run_monte_carlo_propagation`)
- **Validation Test**: `test_mc_single_gaussian`, `test_mc_rectangular_distribution`
- **Classification**: `VERIFIED (Exact JCGM 101 §6.4)`

---

### 2. Multivariate Correlated Sampling
- **Standard Clause**: JCGM 101:2008 §6.4.8
- **Formula**:
  - Cholesky factorization of correlation matrix $R = L L^T$.
  - Transform independent normal draws $Z$ via $Z_{\text{corr}} = L Z$.
- **Implementation**: [`metrology_core/uncertainty/monte_carlo.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/monte_carlo.py)
- **Validation Test**: `test_differential_correlated`
- **Classification**: `VERIFIED (Exact JCGM 101 §6.4.8)`

---

### 3. Coverage Interval Derivation
- **Standard Clause**: JCGM 101:2008 §7.7
- **Method**: Sort output samples $y_{(1)} \le y_{(2)} \le \dots \le y_{(M)}$; derive shortest or probabilistically symmetric $100(1-\alpha)\%$ coverage interval.
- **Implementation**: [`metrology_core/uncertainty/monte_carlo.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/monte_carlo.py)
- **Validation Test**: `test_mc_single_gaussian`
- **Classification**: `VERIFIED (Exact JCGM 101 §7.7)`

---

### 4. Validation of the GUM Uncertainty Framework
- **Standard Clause**: JCGM 101:2008 §8
- **Criterion**: Check if standard uncertainty and coverage intervals from GUM 1st-order linear framework agree with Monte Carlo results within numerical tolerance $\delta = 0.5 \times 10^{-l}$.
- **Implementation**: [`metrology_core/uncertainty/monte_carlo.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/uncertainty/monte_carlo.py) (`validate_gum_against_monte_carlo`)
- **Validation Test**: `test_differential_linear_sum`, `test_differential_ohms_law`
- **Classification**: `VERIFIED (Exact JCGM 101 §8)`
