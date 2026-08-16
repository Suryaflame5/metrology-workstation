# Standards Concordance: Metrological Rounding (GUM & ISO 80000-1)

**Standard Titles**: 
- JCGM 100:2008 §7.2.6 (*Expression of Uncertainty — Rounding*)
- ISO 80000-1:2022 (*Quantities and units — Part 1: General — Rounding rules*)
- ASTM E29 / IEEE 754 (*Standard Practice for Using Significant Digits / Round to Nearest Even*)  
**Status**: Authoritative Rounding Rules

---

## Concordance Matrix

### 1. Significant Figures for Uncertainty
- **Standard Clause**: JCGM 100:2008 §7.2.6
- **Rule**: Numerical values of standard uncertainty $u$ and expanded uncertainty $U$ should be stated with at most two significant digits (or one significant digit when the leading digit is $\ge 3$ under certain lab policies). Default is 2 significant figures.
- **Implementation**: [`metrology_core/rounding/metrological.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/rounding/metrological.py) (`round_uncertainty`)
- **Validation Test**: `test_round_uncertainty_various_magnitudes`, `test_single_significant_figure`
- **Classification**: `VERIFIED (Exact GUM §7.2.6)`

---

### 2. Measurement Result Resolution Matching
- **Standard Clause**: JCGM 100:2008 §7.2.6 & ISO 80000-1 §B.3
- **Rule**: The measurement result (best estimate) must be rounded to the same least significant decimal digit (decimal position / resolution) as its uncertainty.
- **Implementation**: [`metrology_core/rounding/metrological.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/rounding/metrological.py) (`round_measurement_to_uncertainty`)
- **Validation Test**: `test_measurement_resolution_matching`
- **Classification**: `VERIFIED (Exact GUM §7.2.6)`

---

### 3. Protection Against Sequential (Double) Rounding
- **Standard Clause**: ISO 80000-1 §B.3 & IEEE 754
- **Rule**: Direct single-pass quantization to target resolution. Sequential rounding (e.g. $12.3446 \to 12.345 \to 12.35$) is mathematically erroneous and strictly prohibited.
- **Implementation**: [`metrology_core/rounding/metrological.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/rounding/metrological.py)
- **Validation Test**: `test_anti_sequential_rounding`
- **Classification**: `VERIFIED (Exact ISO 80000-1 / IEEE 754)`
