"""
Windows App Certification Kit (WACK) Pre-Flight Validator for MSIX / Store Submission.
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, List

DIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dist", "MetrologyWorkstation")
MANIFEST_PATH = os.path.join(DIST_DIR, "AppxManifest.xml")
ASSETS_DIR = os.path.join(DIST_DIR, "Assets")


def run_wack_preflight() -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    all_passed = True

    # Check 1: Manifest existence and XML parsing
    if not os.path.exists(MANIFEST_PATH):
        return {"status": "FAIL", "reason": "AppxManifest.xml not found", "checks": []}

    try:
        tree = ET.parse(MANIFEST_PATH)
        root = tree.getroot()
        checks.append({"name": "AppxManifest XML Well-Formed", "status": "PASS", "details": "Valid XML structure"})
    except Exception as e:
        return {"status": "FAIL", "reason": f"Manifest XML parse error: {e}", "checks": []}

    # Check 2: Identity Attributes
    identity = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")
    if identity is not None:
        name = identity.attrib.get("Name")
        version = identity.attrib.get("Version")
        arch = identity.attrib.get("ProcessorArchitecture")
        if name and version and arch == "x64":
            checks.append({"name": "Package Identity & Architecture", "status": "PASS", "details": f"Name={name}, Version={version}, Arch={arch}"})
        else:
            all_passed = False
            checks.append({"name": "Package Identity & Architecture", "status": "FAIL", "details": "Missing required identity attributes or non-x64 arch"})

    # Check 3: Capabilities (runFullTrust)
    caps = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Capabilities")
    has_full_trust = False
    if caps is not None:
        for c in caps:
            if "runFullTrust" in c.attrib.get("Name", ""):
                has_full_trust = True
    if has_full_trust:
        checks.append({"name": "FullTrust Capability Declaration", "status": "PASS", "details": "runFullTrust declared for packaged Win32 application"})
    else:
        all_passed = False
        checks.append({"name": "FullTrust Capability Declaration", "status": "FAIL", "details": "Missing runFullTrust capability"})

    # Check 4: Asset Logos Verification
    required_assets = ["StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png", "Wide310x150Logo.png"]
    missing_assets = []
    for a in required_assets:
        p = os.path.join(ASSETS_DIR, a)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            missing_assets.append(a)

    if not missing_assets:
        checks.append({"name": "Store Logo Assets Verification", "status": "PASS", "details": f"All {len(required_assets)} required logo PNGs present"})
    else:
        all_passed = False
        checks.append({"name": "Store Logo Assets Verification", "status": "FAIL", "details": f"Missing assets: {missing_assets}"})

    # Check 5: Procedures & Standards bundling
    proc_dir = os.path.join(DIST_DIR, "procedures")
    std_dir = os.path.join(DIST_DIR, "standards")
    if os.path.exists(proc_dir) and os.path.exists(std_dir):
        proc_count = len([f for f in os.listdir(proc_dir) if f.endswith(".json")])
        std_count = len([f for f in os.listdir(std_dir) if f.endswith(".md")])
        checks.append({"name": "Bundled Metrology Procedures & Standards", "status": "PASS", "details": f"{proc_count} procedures, {std_count} standards documents bundled"})
    else:
        all_passed = False
        checks.append({"name": "Bundled Metrology Procedures & Standards", "status": "FAIL", "details": "Procedures or standards folder missing in dist"})

    return {
        "status": "PASS" if all_passed else "FAIL",
        "total_checks": len(checks),
        "passed_checks": len([c for c in checks if c["status"] == "PASS"]),
        "checks": checks,
    }


if __name__ == "__main__":
    res = run_wack_preflight()
    print("=" * 70)
    print(" WINDOWS APP CERTIFICATION (WACK) PRE-FLIGHT VALIDATION")
    print("=" * 70)
    print(f" Overall Status: {res['status']} ({res['passed_checks']}/{res['total_checks']} checks passed)")
    print("-" * 70)
    for c in res["checks"]:
        sym = "[PASS]" if c["status"] == "PASS" else "[FAIL]"
        print(f"  {sym:<8} | {c['name']:<35} | {c['details']}")
    print("=" * 70)
