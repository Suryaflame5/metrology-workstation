"""
Automated Test Suite for 21 CFR Part 11 Electronic Signatures, IQ/OQ/PQ Validation, and Traceability.
"""

import pytest
from metrology_app.compliance.part11_signatures import (
    execute_electronic_signature,
    verify_electronic_signature,
    SignatureReason,
)
from metrology_app.compliance.iq_oq_pq import execute_full_qualification_protocol
from metrology_app.compliance.traceability import generate_traceability_dossier


def test_21_cfr_part_11_signature_ceremony():
    calc_id = "CALC-PART11-TEST"
    calc_hash = "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"

    # 1. Valid Signature by Lead Signatory
    sig = execute_electronic_signature(
        calculation_id=calc_id,
        calculation_sha256=calc_hash,
        username="chief_metrologist",
        password_plain="Signatory@2026",
        reason=SignatureReason.APPROVAL_RELEASE,
    )
    assert sig["status"] == "SEALED_AND_BINDING"
    assert sig["signature_token"].startswith("SIG-21CFR11-")
    assert sig["signer"]["username"] == "chief_metrologist"

    # 2. Verify signature seal
    verif = verify_electronic_signature(sig)
    assert verif["is_valid"] is True
    assert verif["status"] == "SIGNATURE_VERIFIED"

    # 3. Rejection of invalid credentials
    bad_sig = execute_electronic_signature(
        calculation_id=calc_id,
        calculation_sha256=calc_hash,
        username="chief_metrologist",
        password_plain="BadPass",
        reason=SignatureReason.APPROVAL_RELEASE,
    )
    assert "error" in bad_sig


def test_automated_iq_oq_pq_qualification_suite():
    qual = execute_full_qualification_protocol()
    assert qual["status"] == "QUALIFIED_AND_VALIDATED"
    assert qual["pass_rate_pct"] == 100.0
    assert qual["iq_section"]["status"] == "PASS"
    assert qual["oq_section"]["status"] == "PASS"
    assert qual["pq_section"]["status"] == "PASS"
    assert qual["total_test_protocols"] >= 6


def test_statement_of_traceability():
    dossier = generate_traceability_dossier(instrument_name="Micrometer 0-25mm")
    assert len(dossier["traceability_chain"]) == 4
    assert "NIST" in dossier["traceability_chain"][0]["entity"]
    assert "Speed of light" in dossier["si_base_unit"].lower() or "meter" in dossier["si_base_unit"].lower()
