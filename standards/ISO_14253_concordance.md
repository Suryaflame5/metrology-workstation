# Standards Concordance: ISO 14253-1:2017

**Standard Title**: Geometrical product specifications (GPS) — Inspection by measurement of workpieces and measuring equipment — Part 1: Decision rules for verifying conformity or nonconformity with specifications  
**Publishing Body**: International Organization for Standardization (ISO)  
**Current Status**: Active International Standard (Replaces withdrawn 2013 edition)

---

## Concordance Matrix

### 1. Default Decision Rule for Proving Conformity
- **Standard Clause**: ISO 14253-1:2017 §5.2
- **Rule**: Complete specification operator with stringent guardband equal to expanded uncertainty ($w = U$).
- **Conformance Zone**: $[T_L + U, T_U - U]$
- **Implementation**: [`metrology_core/decision/iso14253.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/iso14253.py) (`calculate_iso14253_limits`, `evaluate_iso14253_conformance`)
- **Validation Test**: `test_iso14253_conformance`
- **Classification**: `VERIFIED (Exact ISO 14253-1:2017 §5.2)`

---

### 2. Default Decision Rule for Proving Non-Conformity
- **Standard Clause**: ISO 14253-1:2017 §5.3
- **Rule**: Stringent rejection zone: $(-\infty, T_L - U] \cup [T_U + U, +\infty)$.
- **Implementation**: [`metrology_core/decision/iso14253.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/iso14253.py)
- **Validation Test**: `test_iso14253_conformance`
- **Classification**: `VERIFIED (Exact ISO 14253-1:2017 §5.3)`

---

### 3. Uncertainty Range / Undetermined Zone
- **Standard Clause**: ISO 14253-1:2017 §5.4
- **Rule**: Values in $(T_L - U, T_L + U)$ and $(T_U - U, T_U + U)$ are in the uncertainty range (neither conformity nor non-conformity can be proven).
- **Implementation**: [`metrology_core/decision/iso14253.py`](file:///c:/Users/Lenovo/OneDrive/Documents/First_Product/metrology_core/decision/iso14253.py)
- **Validation Test**: `test_iso14253_conformance`
- **Classification**: `VERIFIED (Exact ISO 14253-1:2017 §5.4)`
