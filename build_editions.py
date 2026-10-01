"""
CALIBRA Metrology Workstation — Master Dual-Edition Release Build Pipeline.
Produces:
1. dist/MetrologyWorkstation/MetrologyWorkstation.exe (Native Windowed Desktop App)
2. dist/Metrology-Workstation-Demo-v7.0.0-Setup.exe (Free Community Demo Wizard)
3. dist/Metrology-Workstation-Pro-v7.0.0-Setup.exe (Professional Commercial Wizard)

All binaries compiled as native Windows GUI applications (console=False, --windowed)
with ZERO visible command prompt or backend terminal windows.
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build" / "editions_build"
ICON_PATH = PROJECT_ROOT / "assets" / "calibra_icon.ico"
if not ICON_PATH.exists():
    ICON_PATH = PROJECT_ROOT / "assets" / "app.ico"

def calculate_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_main_workstation():
    print("=" * 75)
    print(" STEP 1: COMPILING NATIVE WINDOWED CALIBRA WORKSTATION EXECUTABLE")
    print(" (Zero Console Windows -- Windowed GUI Subsystem)")
    print("=" * 75)

    static_src = PROJECT_ROOT / "metrology_app" / "static"
    ui_src = PROJECT_ROOT / "ui" / "workstation"
    proc_src = PROJECT_ROOT / "metrology_app" / "procedures"
    std_src = PROJECT_ROOT / "standards"
    manifest_path = PROJECT_ROOT / "app.manifest"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=MetrologyWorkstation",
        "--onefile",
        "--windowed",            # CRITICAL: Ensures /SUBSYSTEM:WINDOWS (NO CONSOLE WINDOW)
        "--noconsole",           # Explicitly suppress any console window
        "--noconfirm",
        f"--workpath={BUILD_DIR / 'workstation'}",
        f"--icon={ICON_PATH}",
        f"--add-data={static_src};ui/workstation",
        f"--add-data={static_src};metrology_app/static",
        f"--add-data={proc_src};metrology_app/procedures",
        f"--add-data={std_src};standards",
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=fastapi",
        "--hidden-import=fastapi.staticfiles",
        "--hidden-import=fastapi.middleware.cors",
        "--hidden-import=starlette",
        "--hidden-import=starlette.staticfiles",
        "--hidden-import=starlette.responses",
        "--hidden-import=starlette.routing",
        "--hidden-import=pydantic",
        "--hidden-import=sqlite3",
        "--hidden-import=reportlab",
        "--hidden-import=reportlab.lib",
        "--hidden-import=reportlab.lib.colors",
        "--hidden-import=reportlab.lib.pagesizes",
        "--hidden-import=reportlab.platypus",
        "--hidden-import=metrology_core",
        "--hidden-import=metrology_core.engine",
        "--hidden-import=metrology_core.uncertainty",
        "--hidden-import=metrology_core.decision",
        "--hidden-import=metrology_core.ledger",
        "--hidden-import=metrology_core.models",
        "--hidden-import=metrology_app",
        "--hidden-import=metrology_app.config",
        "--hidden-import=metrology_app.db",
        "--hidden-import=metrology_app.server",
        "--hidden-import=metrology_app.services.universal_importer",
        "--hidden-import=metrology_app.services.job_pipeline_engine",
        "--hidden-import=metrology_app.services.procedure_template_service",
        "--hidden-import=metrology_app.services.batch_pipeline_engine",
        "--hidden-import=metrology_app.services.exception_center_service",
        "--hidden-import=metrology_app.services.review_cockpit_service",
        "--hidden-import=metrology_app.services.job_revision_engine",
        "--hidden-import=metrology_app.services.hardware_device_adapter",
        "--hidden-import=metrology_app.services.evidence_service",
        "--hidden-import=metrology_app.services.advanced_analytics_service",
        "--hidden-import=metrology_app.services.license_service",
        "--hidden-import=metrology_app.services.demo_loader_service",
        "--hidden-import=metrology_app.services.demo_factory_data",
        "--hidden-import=metrology_app.services.workbench_service",
        "--hidden-import=metrology_app.services.acquisition_service",
        "--hidden-import=metrology_app.services.verifier_service",
        "--collect-submodules=metrology_app",
        "--collect-submodules=metrology_core",
        "--hidden-import=webview",
        "--hidden-import=webview.platforms",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=clr",
        "--hidden-import=clr_loader",
        "--hidden-import=pythonnet",
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=transformers",
        "--exclude-module=cv2",
        "--exclude-module=nltk",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=pytest",
        str(PROJECT_ROOT / "desktop_app.py"),
    ]

    print("Executing PyInstaller compilation...")
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(" [FAIL] Compilation of MetrologyWorkstation.exe failed!")
        sys.exit(res.returncode)

    built_exe = DIST_DIR / "MetrologyWorkstation.exe"
    target_dir = DIST_DIR / "MetrologyWorkstation"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_exe = target_dir / "MetrologyWorkstation.exe"
    shutil.copy2(built_exe, target_exe)
    print(f" [OK] Built {target_exe} ({os.path.getsize(target_exe):,} bytes)")
    return target_exe


def build_installer_wizard(edition: str, output_name: str, folder_name: str):
    print("\n" + "=" * 75)
    print(f" STEP: COMPILING {edition.upper()} GUI SETUP WIZARD")
    print(f" Output Artifact: dist/{output_name} -> dist/{folder_name}/{output_name}")
    print("=" * 75)

    installer_script = PROJECT_ROOT / "scripts" / "installer_gui.py"
    target_workstation_exe = DIST_DIR / "MetrologyWorkstation" / "MetrologyWorkstation.exe"
    if not target_workstation_exe.exists():
        if (DIST_DIR / "MetrologyWorkstation.exe").exists():
            (DIST_DIR / "MetrologyWorkstation").mkdir(parents=True, exist_ok=True)
            shutil.copy2(DIST_DIR / "MetrologyWorkstation.exe", target_workstation_exe)

    # Use edition-specific procedures & standards if available in products/<folder_name>/
    product_dir = PROJECT_ROOT / "products" / folder_name
    proc_src = product_dir / "procedures" if (product_dir / "procedures").exists() else PROJECT_ROOT / "metrology_app" / "procedures"
    std_src = product_dir / "standards" if (product_dir / "standards").exists() else PROJECT_ROOT / "standards"

    edition_dir = BUILD_DIR / edition
    edition_dir.mkdir(parents=True, exist_ok=True)
    edition_manifest = edition_dir / "edition.json"
    with open(edition_manifest, "w", encoding="utf-8") as f:
        json.dump({"edition": edition, "version": "7.0.0"}, f, indent=2)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name={output_name.replace('.exe', '')}",
        "--onefile",
        "--windowed",            # GUI Setup Wizard: NO CONSOLE
        "--noconsole",
        "--noconfirm",
        f"--workpath={edition_dir}",
        f"--icon={ICON_PATH}",
        f"--add-data={target_workstation_exe};.",
        f"--add-data={edition_manifest};.",
        f"--add-data={proc_src};procedures",
        f"--add-data={std_src};standards",
        str(installer_script),
    ]

    env = os.environ.copy()
    env["METROLOGY_EDITION"] = edition

    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), env=env)
    if res.returncode != 0:
        print(f" [FAIL] Setup Wizard build failed for {edition}!")
        sys.exit(res.returncode)

    out_file = DIST_DIR / output_name
    edition_dist_dir = DIST_DIR / folder_name
    edition_dist_dir.mkdir(parents=True, exist_ok=True)
    edition_out_file = edition_dist_dir / output_name
    shutil.copy2(out_file, edition_out_file)

    print(f" [OK] Setup Wizard Ready: {out_file} ({os.path.getsize(out_file):,} bytes)")
    print(f" [OK] Copied to edition distribution directory: {edition_out_file}")
    return out_file, edition_out_file


def main():
    print("=" * 75)
    print(" CALIBRA METROLOGY WORKSTATION v7.0.0 — 4-EDITION RELEASE BUILD PIPELINE")
    print("=" * 75)

    target_workstation_exe = DIST_DIR / "MetrologyWorkstation" / "MetrologyWorkstation.exe"
    if target_workstation_exe.exists():
        print(f"Found existing compiled workstation executable: {target_workstation_exe}")
        main_exe = target_workstation_exe
    else:
        # 1. Main executable
        main_exe = build_main_workstation()

    # 2. Demo edition setup wizard ($0)
    demo_inst, demo_edition_inst = build_installer_wizard("demo", "Metrology-Workstation-Demo-v7.0.0-Setup.exe", "demo")

    # 3. Professional edition setup wizard ($590 / $1,490)
    pro_inst, pro_edition_inst = build_installer_wizard("pro", "Metrology-Workstation-Pro-v7.0.0-Setup.exe", "professional")

    # 4. Team Fleet edition setup wizard ($1,890 / $2,990)
    team_inst, team_edition_inst = build_installer_wizard("team", "Metrology-Workstation-Team-v7.0.0-Setup.exe", "team")

    # 5. Enterprise Platform edition setup wizard ($4,900 / $4,990)
    enterprise_inst, enterprise_edition_inst = build_installer_wizard("enterprise", "Metrology-Workstation-Enterprise-v7.0.0-Setup.exe", "enterprise")

    all_installers = [demo_inst, pro_inst, team_inst, enterprise_inst]
    all_edition_installers = [demo_edition_inst, pro_edition_inst, team_edition_inst, enterprise_edition_inst]

    # 6. Sign with local Authenticode test certificate
    print("\n" + "=" * 75)
    print(" STEP: SIGNING ARTIFACTS WITH AUTHENTICODE CERTIFICATE")
    print("=" * 75)
    cert_script = PROJECT_ROOT / "scripts" / "create_self_signed_cert.ps1"
    for inst in all_installers + all_edition_installers + [main_exe]:
        if inst.exists():
            subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cert_script), "-TargetFile", str(inst)])

    # 7. Checksums
    print("\n" + "=" * 75)
    print(" RELEASE INTEGRITY CHECKSUMS (SHA-256)")
    print("=" * 75)
    sums_file = DIST_DIR / "SHA256SUMS.txt"
    lines = []
    for inst in all_installers + [main_exe]:
        if inst.exists():
            sha = calculate_sha256(inst)
            line = f"{sha}  {inst.name}"
            print(line)
            lines.append(line)
    
    with open(sums_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nWrote master checksums to {sums_file}")

    for inst in all_edition_installers:
        if inst.exists():
            ed_sums_file = inst.parent / "SHA256SUMS.txt"
            sha = calculate_sha256(inst)
            with open(ed_sums_file, "w", encoding="utf-8") as f:
                f.write(f"{sha}  {inst.name}\n")
            print(f"Wrote edition checksum to {ed_sums_file}")

if __name__ == "__main__":
    main()
