"""
Pre-Configured Enterprise Industry Compliance Profiles & Templates.
Contains specialized calibration workflows and decision rules for Aerospace, Automotive, Medical, and Semiconductor manufacturing.
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class IndustrySector(str, Enum):
    AEROSPACE_DEFENSE = "AEROSPACE_DEFENSE"
    AUTOMOTIVE_EV = "AUTOMOTIVE_EV"
    MEDICAL_PHARMA = "MEDICAL_PHARMA"
    SEMICONDUCTOR_PHOTONICS = "SEMICONDUCTOR_PHOTONICS"


ENTERPRISE_INDUSTRY_PROFILES: Dict[IndustrySector, Dict[str, Any]] = {
    IndustrySector.AEROSPACE_DEFENSE: {
        "sector": "AEROSPACE_DEFENSE",
        "title": "Aerospace & Defense Manufacturing",
        "regulatory_standards": [
            "AS9100D Quality Management System for Aviation & Defense",
            "ANSI/NCSL Z540.3-2006 (Mandatory Method 6 Guardband <= 2.0% PFA)",
            "Boeing D6-51991 Quality Assurance Standard",
            "MIL-STD-45662A Calibration System Requirements",
        ],
        "default_decision_rule": "ANSI/NCSL Z540.3 Method 6",
        "tur_target": 4.0,
        "thermal_soaking_hours": 2.0,
        "temperature_band_c": "+/- 0.5 °C",
        "templates": [
            {
                "template_id": "AERO-01",
                "name": "Titanium Turbine Blade Root Thickness",
                "nominal_mm": 18.5000,
                "tolerance_upper_mm": 0.0015,
                "tolerance_lower_mm": -0.0015,
                "standard": "Grade 0 Tungsten Carbide Gauge Block",
                "required_readings": 5,
            },
            {
                "template_id": "AERO-02",
                "name": "Airframe Fastener Shank Diameter",
                "nominal_mm": 6.3500,
                "tolerance_upper_mm": 0.0010,
                "tolerance_lower_mm": -0.0010,
                "standard": "Optical Micrometer / Master Ring Gauge",
                "required_readings": 5,
            },
        ],
    },
    IndustrySector.AUTOMOTIVE_EV: {
        "sector": "AUTOMOTIVE_EV",
        "title": "Automotive & Electric Vehicle Manufacturing",
        "regulatory_standards": [
            "IATF 16949:2016 Automotive Quality Management",
            "VDA 5 Capability of Measurement Processes",
            "AIAG Measurement Systems Analysis (MSA 4th Edition)",
        ],
        "default_decision_rule": "ANSI/NCSL Z540.3 Method 5 (RSS Guardband)",
        "tur_target": 4.0,
        "thermal_soaking_hours": 1.0,
        "temperature_band_c": "+/- 1.0 °C",
        "templates": [
            {
                "template_id": "AUTO-01",
                "name": "EV Lithium Pouch Battery Weld Seam Thickness",
                "nominal_mm": 1.2500,
                "tolerance_upper_mm": 0.0020,
                "tolerance_lower_mm": -0.0020,
                "standard": "Precision Thickness Foil Standard",
                "required_readings": 5,
            },
            {
                "template_id": "AUTO-02",
                "name": "EV Motor Rotor Shaft Journal Diameter",
                "nominal_mm": 35.0000,
                "tolerance_upper_mm": 0.0025,
                "tolerance_lower_mm": -0.0025,
                "standard": "Master Setting Cylinder",
                "required_readings": 5,
            },
        ],
    },
    IndustrySector.MEDICAL_PHARMA: {
        "sector": "MEDICAL_PHARMA",
        "title": "Medical Devices & Pharmaceutical Regulated Systems",
        "regulatory_standards": [
            "ISO 13485:2016 Medical Devices Quality Management",
            "FDA 21 CFR Part 820 Quality System Regulation",
            "FDA 21 CFR Part 11 Electronic Records & Signatures",
            "GAMP 5 Category 4 Configured Software Guidelines",
        ],
        "default_decision_rule": "ISO 14253-1:2017 (Complete Conformance Guardbanding by U)",
        "tur_target": 4.0,
        "thermal_soaking_hours": 2.0,
        "temperature_band_c": "+/- 0.5 °C",
        "templates": [
            {
                "template_id": "MED-01",
                "name": "Surgical Catheter Extrusion Wall Thickness",
                "nominal_mm": 0.3500,
                "tolerance_upper_mm": 0.0008,
                "tolerance_lower_mm": -0.0008,
                "standard": "Laser Micrometer Calibration Pin Set",
                "required_readings": 5,
            },
            {
                "template_id": "MED-02",
                "name": "Hypodermic Needle Outer Diameter",
                "nominal_mm": 0.5140,
                "tolerance_upper_mm": 0.0010,
                "tolerance_lower_mm": -0.0010,
                "standard": "Grade 0 Micro-Pin Standard",
                "required_readings": 5,
            },
        ],
    },
    IndustrySector.SEMICONDUCTOR_PHOTONICS: {
        "sector": "SEMICONDUCTOR_PHOTONICS",
        "title": "Semiconductor & Precision Photonics",
        "regulatory_standards": [
            "SEMI E10 Equipment Reliability & Productivity Standard",
            "ISO 14644-1 Cleanroom Environmental Classification",
            "EURAMET cg-15 Calibration of Digital Multimeters",
        ],
        "default_decision_rule": "ANSI/NCSL Z540.3 Method 6",
        "tur_target": 4.5,
        "thermal_soaking_hours": 4.0,
        "temperature_band_c": "+/- 0.2 °C",
        "templates": [
            {
                "template_id": "SEMI-01",
                "name": "300 mm Silicon Wafer Bow / Warp Thickness",
                "nominal_mm": 0.7750,
                "tolerance_upper_mm": 0.0005,
                "tolerance_lower_mm": -0.0005,
                "standard": "Optical Interferometer Step Height Standard",
                "required_readings": 5,
            },
        ],
    },
}


def list_industry_profiles() -> List[Dict[str, Any]]:
    """Retrieve list of all pre-configured industry compliance profiles."""
    return list(ENTERPRISE_INDUSTRY_PROFILES.values())


def get_industry_profile(sector: IndustrySector) -> Optional[Dict[str, Any]]:
    """Retrieve profile for a specific industry sector."""
    return ENTERPRISE_INDUSTRY_PROFILES.get(sector)
