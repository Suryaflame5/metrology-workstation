"""
Tests for UPI Payment Integration, Merchant VPA Validation, and Checkout State Machine.
"""

import pytest
from metrology_app.services.upi_payment_service import (
    validate_merchant_vpa,
    generate_transaction_reference,
    generate_order_id,
    build_dynamic_upi_uri,
    validate_checkout_transition,
    issue_entitlement_for_verified_order,
)
from metrology_app.services.license_service import (
    PlanId,
    EntitlementState,
    verify_token_signature,
)


def test_merchant_vpa_validation():
    """Verify that valid VPAs pass and raw phone numbers are strictly rejected."""
    # Valid VPAs
    assert validate_merchant_vpa("novyrax@icici") is True
    assert validate_merchant_vpa("novyrax.merchant@upi") is True
    assert validate_merchant_vpa("payments_hub@okaxis") is True
    assert validate_merchant_vpa("quality-lab-01@hdfcbank") is True

    # Raw phone numbers without handle MUST be rejected
    assert validate_merchant_vpa("6374337463") is False
    assert validate_merchant_vpa("+917418320315") is False
    assert validate_merchant_vpa("917418320315") is False
    assert validate_merchant_vpa("1234567890") is False

    # Invalid string formats
    assert validate_merchant_vpa("") is False
    assert validate_merchant_vpa(None) is False
    assert validate_merchant_vpa("invalid_without_at") is False
    assert validate_merchant_vpa("@only_handle") is False


def test_transaction_reference_and_order_id_generation():
    """Verify unique formatting and prefixes for transaction references and orders."""
    tr1 = generate_transaction_reference()
    tr2 = generate_transaction_reference()
    assert tr1.startswith("NOV-TRX-")
    assert tr2.startswith("NOV-TRX-")
    assert tr1 != tr2

    ord1 = generate_order_id()
    ord2 = generate_order_id()
    assert ord1.startswith("NOV-ORD-")
    assert ord2.startswith("NOV-ORD-")
    assert ord1 != ord2


def test_build_dynamic_upi_uri():
    """Verify standard NPCI parameters in dynamic UPI URI generation."""
    tr = generate_transaction_reference()
    uri = build_dynamic_upi_uri(
        amount_inr=40670.00,
        transaction_ref=tr,
        note="NOVYRAX Professional Annual License",
        merchant_vpa="novyrax.merchant@upi",
        merchant_name="NOVYRAX Studio",
    )

    assert uri.startswith("upi://pay?")
    assert "pa=novyrax.merchant%40upi" in uri or "pa=novyrax.merchant@upi" in uri
    assert "pn=NOVYRAX+Studio" in uri or "pn=NOVYRAX%20Studio" in uri
    assert f"tr={tr}" in uri
    assert "am=40670.00" in uri
    assert "cu=INR" in uri

    # Rejection of invalid inputs
    with pytest.raises(ValueError, match="Invalid merchant VPA"):
        build_dynamic_upi_uri(
            amount_inr=100.0,
            transaction_ref=tr,
            note="Test",
            merchant_vpa="6374337463",  # Raw phone number rejected
        )

    with pytest.raises(ValueError, match="Payment amount must be greater than zero"):
        build_dynamic_upi_uri(
            amount_inr=-50.0,
            transaction_ref=tr,
            note="Test",
            merchant_vpa="valid@upi",
        )


def test_checkout_state_machine_transitions():
    """Verify checkout state machine enforces strict server-side sequence."""
    # Valid standard progression
    assert validate_checkout_transition("CREATED", "PAYMENT_PENDING") is True
    assert validate_checkout_transition("PAYMENT_PENDING", "PAYMENT_VERIFIED") is True
    assert validate_checkout_transition("PAYMENT_VERIFIED", "ENTITLEMENT_ISSUED") is True

    # Valid failure & refund progressions
    assert validate_checkout_transition("PAYMENT_PENDING", "PAYMENT_FAILED") is True
    assert validate_checkout_transition("PAYMENT_FAILED", "CANCELLED") is True
    assert validate_checkout_transition("PAYMENT_VERIFIED", "REFUNDED") is True
    assert validate_checkout_transition("REFUNDED", "REVOKED") is True
    assert validate_checkout_transition("ENTITLEMENT_ISSUED", "REVOKED") is True

    # ILLEGAL transitions must be blocked
    # Cannot issue entitlement directly without payment verification
    assert validate_checkout_transition("CREATED", "ENTITLEMENT_ISSUED") is False
    assert validate_checkout_transition("PAYMENT_PENDING", "ENTITLEMENT_ISSUED") is False
    # Cannot resurrect revoked order
    assert validate_checkout_transition("REVOKED", "PAYMENT_VERIFIED") is False
    assert validate_checkout_transition("CANCELLED", "ENTITLEMENT_ISSUED") is False


def test_issue_entitlement_for_verified_order():
    """Verify cryptographic HMAC-SHA256 signature on issued entitlement token."""
    order_id = generate_order_id()
    token = issue_entitlement_for_verified_order(
        order_id=order_id,
        customer_email="qa_lead@aerospace.com",
        customer_name="Aero Calibration Labs",
        plan_id=PlanId.PROFESSIONAL,
        duration_days=365,
        seat_limit=1,
    )

    assert token["product_id"] == "MetrologyWorkstation.Commercial"
    assert token["plan_id"] == "PROFESSIONAL"
    assert token["status"] == "ACTIVE"
    assert token["customer_email"] == "qa_lead@aerospace.com"
    assert token["customer_name"] == "Aero Calibration Labs"
    assert "signature" in token
    assert token["signature"] is not None

    # Verify cryptographic signature using local public verifier
    assert verify_token_signature(token) is True
