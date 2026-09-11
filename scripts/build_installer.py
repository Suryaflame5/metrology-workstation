"""
Build Standalone Windows Setup Installer Executable (v7.0.0).
Uses PyInstaller to compile scripts/installer_runtime.py into Metrology-Workstation-v7.0.0-Windows-x64-Setup.exe.
"""

import os
import sys
import shutil
import hashlib
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
STAGE_DIR = os.path.join(DIST_DIR, "MetrologyWorkstation")
TARGET_EXE = os.path.join(STAGE_DIR, "MetrologyWorkstation.exe")
INSTALLER_EXE_NAME = "Metrology-Workstation-v7.0.0-Windows-x64-Setup.exe"
FINAL_INSTALLER_PATH = os.path.join(DIST_DIR, INSTALLER_EXE_NAME)


def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_installer():
    print("=" * 70)
    print(" BUILDING METROLOGY WORKSTATION WINDOWS INSTALLER (v7.0.0)")
    print("=" * 70)

    if not os.path.exists(TARGET_EXE):
        print(f" [FAIL] Standalone binary {TARGET_EXE} not found. Compile it first.")
        sys.exit(1)

    installer_script = os.path.join(PROJECT_ROOT, "scripts", "installer_runtime.py")
    proc_src = os.path.join(PROJECT_ROOT, "metrology_app", "procedures")
    std_src = os.path.join(PROJECT_ROOT, "standards")
    icon_path = os.path.join(PROJECT_ROOT, "assets", "app.ico")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name=Metrology-Workstation-v7.0.0-Windows-x64-Setup",
        "--onefile",
        "--noconfirm",
        "--clean",
        f"--icon={icon_path}",
        f"--add-data={TARGET_EXE};.",
        f"--add-data={proc_src};procedures",
        f"--add-data={std_src};standards",
        installer_script,
    ]

    print("Compiling standalone installer executable via PyInstaller...")
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(" [FAIL] Installer compilation failed!")
        sys.exit(res.returncode)

    built_installer = os.path.join(DIST_DIR, INSTALLER_EXE_NAME)
    if os.path.exists(built_installer):
        size = os.path.getsize(built_installer)
        sha256_digest = compute_file_sha256(built_installer)
        print("\n" + "=" * 70)
        print(f" INSTALLER BUILT SUCCESSFULLY: {built_installer}")
        print(f" File Size: {size:,} bytes ({size / (1024*1024):.2f} MB)")
        print(f" SHA-256:   {sha256_digest}")
        print("=" * 70)

        # Write SHA256 checksums file
        checksum_file = os.path.join(DIST_DIR, "SHA256SUMS.txt")
        with open(checksum_file, "a", encoding="utf-8") as f:
            f.write(f"{sha256_digest}  {INSTALLER_EXE_NAME}\n")
        print(f" [OK] Updated checksum manifest: {checksum_file}")
    else:
        print(f" [FAIL] Expected installer artifact not found at: {built_installer}")
        sys.exit(1)


if __name__ == "__main__":
    build_installer()
