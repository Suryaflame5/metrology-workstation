# Standards Concordance: JCGM 106:2012

**Standard Title**: Evaluation of measurement data — The role of measurement uncertainty in conformity assessment  
**Publishing Body**: Joint Committee for Guides in Metrology  
**Status**: Authoritative Decision Rule & Conformity Framework

---

## Concordance Matrix

### 1. Acceptance and Rejection Zones
- **Standard Clause**: JCGM 106:2012 §7 & §8
- **Definitions**:
  - Tolerance Interval / Specification Limits: $[T_L, T_U]$ (§3.3.4)
  - Acceptance Interval: $A = [A_L, A_U]$ (§3.3.8)
  - Rejection Interval: $R = (-\infty, A_L) \cup (A_U, +\infty)$ (§3.3.9)
  - Guardband: $g = T_U - A_U$ (or $w = A_L - T_L$) (§3.3.11)
- **Implementation**: [`metrology_core/decision/`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision)
- **Validation Test**: `test_method6_conformance_zones`, `test_iso14253_conformance`
- **Classification**: `VERIFIED (Exact JCGM 106 §7)`

---

### 2. Binary Decision Rules & Risk Management
- **Standard Clause**: JCGM 106:2012 §8.1 & §8.2
- **Rules**: Binary decision based on whether measured best estimate $\hat{y}$ falls within acceptance interval $A$. Guardbanding controls specific and global consumer's risk (false accept risk).
- **Implementation**: [`metrology_core/decision/method6.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/method6.py), [`metrology_core/decision/iso14253.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/iso14253.py)
- **Classification**: `VERIFIED (Conforming to JCGM 106 Decision Framework)`
