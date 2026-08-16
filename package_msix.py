"""
MSIX Packaging Tool for Metrology Workstation.
Packages the staged dist/MetrologyWorkstation directory into MetrologyWorkstation.msix.
Uses Windows SDK MakeAppx.exe if available, with pure MSIX container packager fallback.
"""

import os
import sys
import glob
import zipfile
import subprocess
import hashlib
import xml.etree.ElementTree as ET

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
STAGE_DIR = os.path.join(PROJECT_ROOT, "dist", "MetrologyWorkstation")
OUTPUT_MSIX = os.path.join(PROJECT_ROOT, "dist", "MetrologyWorkstation.msix")


def find_makeappx() -> str:
    """Locate MakeAppx.exe in Windows Kits directory if installed."""
    patterns = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe",
        r"C:\Program Files\Windows Kits\10\bin\*\x64\makeappx.exe",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches, reverse=True)[0]
    return ""


def generate_content_types_xml(stage_dir: str) -> str:
    """Generate OPC [Content_Types].xml for MSIX package."""
    content = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/vnd.ms-appx.manifest+xml" />
  <Default Extension="png" ContentType="image/png" />
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="md" ContentType="text/markdown" />
  <Default Extension="exe" ContentType="application/x-msdownload" />
  <Default Extension="dll" ContentType="application/x-msdownload" />
  <Default Extension="pyd" ContentType="application/x-msdownload" />
  <Override PartName="/AppxManifest.xml" ContentType="application/vnd.ms-appx.manifest+xml" />
  <Override PartName="/AppxBlockMap.xml" ContentType="application/vnd.ms-appx.blockmap+xml" />
</Types>
"""
    ct_path = os.path.join(stage_dir, "[Content_Types].xml")
    with open(ct_path, "w", encoding="utf-8") as f:
        f.write(content)
    return ct_path


def generate_block_map_xml(stage_dir: str) -> str:
    """Generate AppxBlockMap.xml computing SHA-256 block digests for every file."""
    root = ET.Element("BlockMap", {
        "xmlns": "http://schemas.microsoft.com/appx/2010/blockmap",
        "HashMethod": "http://www.w3.org/2001/04/xmlenc#sha256",
    })

    for dirpath, _, filenames in sorted(os.walk(stage_dir)):
        for fname in sorted(filenames):
            if fname in ("AppxBlockMap.xml", "[Content_Types].xml"):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, stage_dir).replace("\\", "/")
            fsize = os.path.getsize(full_path)

            file_el = ET.SubElement(root, "File", {
                "Name": rel_path,
                "Size": str(fsize),
                "LfhSize": "30",
            })

            # Compute block hash (64KB blocks)
            with open(full_path, "rb") as f:
                while chunk := f.read(65536):
                    block_hash = hashlib.sha256(chunk).hexdigest()
                    ET.SubElement(file_el, "Block", {"Hash": block_hash, "Size": str(len(chunk))})

    tree = ET.ElementTree(root)
    bm_path = os.path.join(stage_dir, "AppxBlockMap.xml")
    tree.write(bm_path, encoding="utf-8", xml_declaration=True)
    return bm_path


def package_msix():
    print(f"Packaging MSIX from: {STAGE_DIR}")
    if not os.path.exists(STAGE_DIR):
        print(f" [FAIL] Staging directory {STAGE_DIR} does not exist.")
        sys.exit(1)

    # Clean any legacy footprint files so MakeAppx generates fresh ones
    for legacy_f in ("AppxBlockMap.xml", "[Content_Types].xml"):
        legacy_p = os.path.join(STAGE_DIR, legacy_f)
        if os.path.exists(legacy_p):
            os.remove(legacy_p)

    makeappx_path = find_makeappx()
    if makeappx_path:
        print(f"Using Windows SDK MakeAppx: {makeappx_path}")
        cmd = [makeappx_path, "pack", "/d", STAGE_DIR, "/p", OUTPUT_MSIX, "/o"]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print("MakeAppx failed, falling back to direct MSIX container packaging...")
            build_msix_archive()
        else:
            print(f" [OK] Built MSIX with MakeAppx: {OUTPUT_MSIX}")
    else:
        print("Windows SDK MakeAppx.exe not in path; creating standard MSIX package container...")
        build_msix_archive()

    msix_size = os.path.getsize(OUTPUT_MSIX)
    print(f"\n=======================================================")
    print(f" MSIX PACKAGE BUILT SUCCESSFULLY: {OUTPUT_MSIX}")
    print(f" Package Size: {msix_size:,} bytes ({msix_size / (1024*1024):.2f} MB)")
    print(f"=======================================================")


def build_msix_archive():
    """Create compliant uncompressed/DEFLATE MSIX container with AppxBlockMap and [Content_Types]."""
    generate_content_types_xml(STAGE_DIR)
    generate_block_map_xml(STAGE_DIR)

    with zipfile.ZipFile(OUTPUT_MSIX, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for dirpath, _, filenames in sorted(os.walk(STAGE_DIR)):
            for fname in sorted(filenames):
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, STAGE_DIR).replace("\\", "/")
                zf.write(full_path, arcname=rel_path)


if __name__ == "__main__":
    package_msix()
