"""
Interactive Metrology Engineering Handbook & Standard Reference System.
Provides in-app technical reference for metrologists, quality engineers, and calibration technicians.
"""

from typing import Dict, Any, List, Optional


METROLOGY_HANDBOOK_ARTICLES: List[Dict[str, Any]] = [
    {
        "article_id": "HB-GUM-01",
        "title": "GUM Uncertainty Evaluation & Welch-Satterthwaite Formulation",
        "category": "Mathematical Foundations",
        "summary": "Step-by-step mathematical breakdown of combined standard uncertainty uc(y) and effective degrees of freedom (nu_eff).",
        "content": (
            "The Guide to the Expression of Uncertainty in Measurement (JCGM 100:2008) dictates that combined variance uc^2(y) "
            "is the sum of squared sensitivity-weighted standard uncertainties: uc^2(y) = sum(ci^2 * u^2(xi)). "
            "The effective degrees of freedom nu_eff is calculated via the Welch-Satterthwaite equation: "
            "nu_eff = uc^4(y) / sum((ci^4 * u^4(xi)) / nu_i). Coverage factor k95 is then determined from the Student-t distribution."
        ),
        "citations": ["JCGM 100:2008 §5.1", "ISO/IEC Guide 98-3"],
    },
    {
        "article_id": "HB-Z540-02",
        "title": "ANSI/NCSL Z540.3 Method 6 & 2% False Accept Risk (PFA)",
        "category": "Decision Rules & Guardbanding",
        "summary": "Understanding empirical guardband multipliers and Test Uncertainty Ratios (TUR).",
        "content": (
            "Where TUR < 4:1, standard acceptance limits must be reduced by guardband width w = M * U to limit Consumer Risk "
            "(Probability of False Accept, PFA) to <= 2.0%. Under Method 6: M(TUR) = A - B * ln(TUR). When TUR >= 4.59, "
            "guardband multiplier drops to zero (100% acceptance interval permitted)."
        ),
        "citations": ["ANSI/NCSL Z540.3-2006 Handbook §5.3", "NCSL International RP-1"],
    },
    {
        "article_id": "HB-21CFR11-03",
        "title": "FDA 21 CFR Part 11 Electronic Signature Compliance in Calibration Labs",
        "category": "Regulatory Quality Systems",
        "summary": "Dual-credential authentication, immutable audit trails, and signature manifest requirements.",
        "content": (
            "Under 21 CFR Part 11 and EU Annex 11, electronic signatures executed on calibration records must contain: "
            "1) Printed name of the signer; 2) Date and time of signature; 3) Meaning associated with the signature (such as review, approval, responsibility). "
            "The signature must be cryptographically linked to the record to prevent tampering."
        ),
        "citations": ["FDA Title 21 CFR Part 11 §11.50", "GAMP 5 Category 4"],
    },
    {
        "article_id": "HB-SCPI-04",
        "title": "SCPI & VISA Instrument Automation Protocols",
        "category": "Hardware & Factory Automation",
        "summary": "IEEE 488.2 mandatory commands, query syntax, and automated data acquisition.",
        "content": (
            "Standard Commands for Programmable Instruments (SCPI) defines a hierarchical syntax for controlling laboratory measuring equipment. "
            "Key queries include *IDN? for instrument identification, MEAS:VOLT:DC? for triggering immediate voltage acquisition, "
            "and SYST:ERR? for polling hardware diagnostic buffers."
        ),
        "citations": ["IEEE Standard 488.2-1992", "SCPI Consortium Standard 1999"],
    },
]


def list_handbook_articles() -> List[Dict[str, Any]]:
    """Retrieve all engineering handbook articles."""
    return METROLOGY_HANDBOOK_ARTICLES


def get_handbook_article(article_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve specific handbook article."""
    for art in METROLOGY_HANDBOOK_ARTICLES:
        if art["article_id"] == article_id:
            return art
    return None
