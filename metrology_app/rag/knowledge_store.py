"""
Engineering Standards, SOPs & Calibration Manuals Knowledge Store.
Contains structured sections with authentic clauses, revisions, effective dates, and authority metadata.
"""

from typing import List, Dict, Any

ENGINEERING_KNOWLEDGE_BASE: List[Dict[str, Any]] = [
    {
        "doc_id": "ISO-IEC-17025-2017",
        "title": "ISO/IEC 17025:2017 General requirements for the competence of testing and calibration laboratories",
        "authority": "International Organization for Standardization (ISO) / IEC",
        "revision": "2017 Edition",
        "effective_date": "2017-11-01",
        "section": "7.6",
        "section_title": "Evaluation of measurement uncertainty",
        "page": 14,
        "content": (
            "Laboratories shall identify the contributions to measurement uncertainty. When evaluating measurement uncertainty, "
            "all uncertainty contributions that are of significance, including those arising from sampling, shall be taken into account "
            "using appropriate methods of analysis. A calibration laboratory, or a testing laboratory performing its own calibrations, "
            "shall evaluate the measurement uncertainty for all calibrations."
        ),
        "tags": ["uncertainty", "GUM", "evaluation", "17025", "calibration", "competence"],
    },
    {
        "doc_id": "ISO-IEC-17025-2017",
        "title": "ISO/IEC 17025:2017 General requirements for the competence of testing and calibration laboratories",
        "authority": "International Organization for Standardization (ISO) / IEC",
        "revision": "2017 Edition",
        "effective_date": "2017-11-01",
        "section": "7.8.6",
        "section_title": "Reporting statements of conformity",
        "page": 17,
        "content": (
            "When a statement of conformity to a specification or standard is provided, the laboratory shall document the decision rule "
            "employed, taking into account the level of risk (such as false accept and false reject and statistical assumptions) associated "
            "with the decision rule employed, and apply the decision rule. The statement of conformity shall clearly identify: a) to which "
            "results the statement of conformity applies; b) which specifications, standards or parts thereof are met or not met; c) the decision rule applied."
        ),
        "tags": ["conformity", "decision_rule", "risk", "statement", "pass_fail", "guardband"],
    },
    {
        "doc_id": "ANSI-NCSL-Z540.3-2006",
        "title": "ANSI/NCSL Z540.3-2006 Requirements for the Calibration of Measuring and Test Equipment",
        "authority": "American National Standards Institute / NCSL International",
        "revision": "Z540.3-2006",
        "effective_date": "2006-08-03",
        "section": "5.3",
        "section_title": "Calibration Decision Rules and 2% Probability of False Accept (PFA)",
        "page": 9,
        "content": (
            "Where calibrations are performed to verify product or process tolerance compliance, the probability that an out-of-tolerance "
            "item will be accepted (Probability of False Accept, PFA or Consumer Risk) shall not exceed 2.0%. Where the Test Uncertainty Ratio (TUR) "
            "is less than 4:1, guardbanding methods (e.g. Method 6 or Method 5 RSS) must be applied to reduce the acceptance interval by guardband width w."
        ),
        "tags": ["Z540.3", "Method6", "Method5", "guardband", "PFA", "consumer_risk", "TUR"],
    },
    {
        "doc_id": "JCGM-100-2008",
        "title": "JCGM 100:2008 Guide to the Expression of Uncertainty in Measurement (GUM)",
        "authority": "Joint Committee for Guides in Metrology (BIPM, IEC, IFCC, ILAC, ISO, IUPAC, IUPAP, OIML)",
        "revision": "GUM 1995 with minor corrections",
        "effective_date": "2008-09-01",
        "section": "4.2",
        "section_title": "Type A evaluation of standard uncertainty",
        "page": 10,
        "content": (
            "Type A evaluation of standard uncertainty is calculated from the statistical dispersion of repeated observations. "
            "For n independent observations, the experimental variance of the mean is s^2(q_bar) = s^2 / n, and the standard uncertainty "
            "u(q_bar) is equal to s / sqrt(n), with degrees of freedom nu = n - 1."
        ),
        "tags": ["Type_A", "repeatability", "standard_uncertainty", "GUM", "dispersion"],
    },
    {
        "doc_id": "JCGM-100-2008",
        "title": "JCGM 100:2008 Guide to the Expression of Uncertainty in Measurement (GUM)",
        "authority": "Joint Committee for Guides in Metrology (BIPM, IEC, IFCC, ILAC, ISO, IUPAC, IUPAP, OIML)",
        "revision": "GUM 1995 with minor corrections",
        "effective_date": "2008-09-01",
        "section": "5.1",
        "section_title": "Determining combined standard uncertainty and Welch-Satterthwaite degrees of freedom",
        "page": 19,
        "content": (
            "The combined standard uncertainty u_c(y) is the positive square root of the combined variance: u_c^2(y) = sum(c_i^2 * u^2(x_i)). "
            "The effective degrees of freedom nu_eff is determined by the Welch-Satterthwaite formula: nu_eff = u_c^4(y) / sum((c_i^4 * u^4(x_i)) / nu_i)."
        ),
        "tags": ["combined_uncertainty", "Welch_Satterthwaite", "degrees_of_freedom", "propagation"],
    },
    {
        "doc_id": "ISO-14253-1-2017",
        "title": "ISO 14253-1:2017 Geometrical product specifications (GPS) — Inspection by measurement of workpieces and measuring equipment",
        "authority": "International Organization for Standardization (ISO)",
        "revision": "Third Edition 2017",
        "effective_date": "2017-10-01",
        "section": "5.2",
        "section_title": "Rule for proving conformance with specifications (Complete Guardbanding by U)",
        "page": 8,
        "content": (
            "Conformance with a specification is proven when the measured result falls within the specification zone reduced on both sides "
            "by the expanded uncertainty U: Acceptance Interval = [Lower_Limit + U, Upper_Limit - U]. When the result falls within the uncertainty "
            "guardband zone, the verdict is Non-conclusive (Indeterminate / Review Required)."
        ),
        "tags": ["ISO14253", "guardband", "conformance", "acceptance_interval", "uncertainty_zone"],
    },
    {
        "doc_id": "SOP-CAL-042",
        "title": "Standard Operating Procedure: Calibration of Outside Micrometers (0–25 mm, 0–50 mm)",
        "authority": "Primary Metrology Laboratory Quality Manual",
        "revision": "Rev 4.1",
        "effective_date": "2025-01-15",
        "section": "4.3",
        "section_title": "Environmental Conditioning & Reference Gauge Block Standards",
        "page": 3,
        "content": (
            "Instruments and Grade 0 Tungsten Carbide gauge blocks must undergo thermal soaking for at least 2 hours in the calibration laboratory "
            "at 20.0 +/- 0.5 deg C and 30-55% relative humidity before calibration. A minimum of 5 repeated readings must be recorded at each nominal point. "
            "If historical drift exceeds 0.0010 mm/year or TUR < 4.0, Method 6 guardband verification is mandatory."
        ),
        "tags": ["SOP", "micrometer", "thermal_soaking", "gauge_blocks", "procedure", "temperature"],
    },
    {
        "doc_id": "SOP-DMM-015",
        "title": "Standard Operating Procedure: Verification of 6.5-Digit Digital Multimeters (Keysight 34401A / 34461A)",
        "authority": "Electrical Standards Laboratory",
        "revision": "Rev 3.0",
        "effective_date": "2024-06-10",
        "section": "3.1",
        "section_title": "DC Voltage Linearity & Test Points (10V Range)",
        "page": 5,
        "content": (
            "Calibration of the 10V DC range must be conducted using a Fluke 5720A / 5730A Multi-Product Calibrator with 4-wire sense connections. "
            "Test points are 1.00000 V, 2.50000 V, 5.00000 V, 7.50000 V, and 10.00000 V. Allow 60 minutes warm-up time. "
            "Relative humidity must not exceed 60% to prevent leakage currents."
        ),
        "tags": ["SOP", "DMM", "Keysight", "voltage", "linearity", "multimeter", "cg-15"],
    },
]


def get_all_documents() -> List[Dict[str, Any]]:
    """Return all preloaded knowledge base documents."""
    return ENGINEERING_KNOWLEDGE_BASE
