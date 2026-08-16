# CONTRIBUTING TO METROLOGY WORKSTATION

Thank you for your interest in contributing to **Metrology Workstation**.

---

## 1. Scientific & Mathematical Rigor Standard

Metrology Workstation is precision calibration and measurement uncertainty software used in engineering and quality laboratories. All mathematical implementations must conform to published international metrology standards:
- **JCGM 100:2008**: Evaluation of measurement data — Guide to the expression of uncertainty in measurement (GUM).
- **JCGM 101:2008**: Propagation of distributions using a Monte Carlo method.
- **JCGM 106:2012**: The role of measurement uncertainty in conformity assessment.
- **ANSI/NCSL Z540.3-2006**: Requirements for the Calibration of Measuring and Test Equipment.
- **ISO 14253-1:2017**: Decision rules for verifying conformity or nonconformity with specifications.

### Rules for Core Math Changes:
1. All mathematical calculations must utilize exact 50-digit `Decimal` arithmetic (`from decimal import Decimal`). Standard floating-point floats are prohibited in `metrology_core/`.
2. Every new calculation routine must include unit tests matching published standard reference benchmarks.

---

## 2. Development Setup

```powershell
# Clone the repository
git clone https://github.com/your-org/metrology-workstation.git
cd metrology-workstation

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install development dependencies
pip install -r requirements-dev.txt

# Run the 70-test regression suite
python -m pytest -q
```

---

## 3. Pull Request Guidelines
- Ensure all 70 tests pass without warnings.
- Keep commits focused and well-documented.
- Update `CHANGELOG.md` when introducing new capabilities or bug fixes.
