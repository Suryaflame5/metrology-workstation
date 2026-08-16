"""
Windows Distribution & Microsoft Store Package Builder for Metrology Workstation.
"""

import os
import json
import shutil
from datetime import datetime

DIST_DIR = os.path.join(os.path.dirname(__file__), "dist", "MetrologyWorkstation")
APPX_MANIFEST_FILE = os.path.join(DIST_DIR, "AppxManifest.xml")

APPX_MANIFEST_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="MetrologyWorkstation.Commercial"
            Publisher="CN=MetrologyWorkstation"
            Version="0.9.9.0"
            ProcessorArchitecture="x64" />

  <Properties>
    <DisplayName>Metrology Workstation</DisplayName>
    <PublisherDisplayName>Metrology Workstation Engineering</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
    <Description>Evidence-First Calibration, Measurement Uncertainty, and Conformity Assessment Platform.</Description>
  </Properties>

  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>

  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>

  <Applications>
    <Application Id="MetrologyWorkstation" Executable="MetrologyWorkstation.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="Metrology Workstation"
                          Description="Evidence-First Calibration &amp; Measurement Uncertainty Platform"
                          BackgroundColor="#0f172a"
                          Square150x150Logo="Assets\\Square150x150Logo.png"
                          Square44x44Logo="Assets\\Square44x44Logo.png">
        <uap:DefaultTile ShortName="Metrology" Wide310x150Logo="Assets\\Wide310x150Logo.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
</Package>
"""


def build_distribution():
    print(f"Building Windows Store Release Candidate distribution in: {DIST_DIR}")
    os.makedirs(os.path.join(DIST_DIR, "Assets"), exist_ok=True)
    
    # 1. Write AppxManifest.xml
    with open(APPX_MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write(APPX_MANIFEST_TEMPLATE)
    print(" [OK] Generated AppxManifest.xml for Microsoft Store / MSIX packaging")

    # 2. Copy procedure definitions
    proc_src = os.path.join(os.path.dirname(__file__), "metrology_app", "procedures")
    proc_dest = os.path.join(DIST_DIR, "procedures")
    if os.path.exists(proc_src):
        shutil.copytree(proc_src, proc_dest, dirs_exist_ok=True)
        print(" [OK] Bundled standard procedures catalog (7 instrument families)")

    # 3. Copy standards concordance documentation
    std_src = os.path.join(os.path.dirname(__file__), "standards")
    std_dest = os.path.join(DIST_DIR, "standards")
    if os.path.exists(std_src):
        shutil.copytree(std_src, std_dest, dirs_exist_ok=True)
        print(" [OK] Bundled standards concordance documentation")

    # 4. Generate package metadata
    metadata = {
        "app_name": "Metrology Workstation",
        "version": "0.9.9",
        "release_tag": "V0.9.9-RC-FINAL",
        "build_date": datetime.utcnow().isoformat(),
        "target_os": "Windows 10 / Windows 11 (x64)",
        "offline_capable": True,
        "math_kernel": "metrology-core (Exact 50-digit context)",
    }
    with open(os.path.join(DIST_DIR, "package_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(" [OK] Generated package_metadata.json")

    print("\n=======================================================")
    print(" METROLOGY WORKSTATION V0.9 (RC) BUILD COMPLETE")
    print("=======================================================")


if __name__ == "__main__":
    build_distribution()
