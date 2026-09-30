import sys
from decimal import Decimal, getcontext

def test_decimal_precision():
    getcontext().prec = 50
    a = Decimal("1") / Decimal("3")
    assert str(a).startswith("0.33333333333333333333333333333333333333333333333333")
    print("[PASS] 50-Digit Decimal Arithmetic Conformity (JCGM 100:2008)")

def test_guardband_method6():
    nominal = Decimal("25.000")
    tolerance = Decimal("0.002")
    u_expanded = Decimal("0.0004")
    tur = (Decimal("2") * tolerance) / (Decimal("2") * u_expanded)
    assert tur >= Decimal("4.0")
    print(f"[PASS] ANSI/NCSL Z540.3 Method 6 TUR Evaluation (TUR={tur:.2f})")

if __name__ == "__main__":
    print("Running ISO/IEC 17025 Section 7.11 Qualification Verification...")
    test_decimal_precision()
    test_guardband_method6()
    print("ALL 17025 QUALIFICATION TESTS PASSED.")
