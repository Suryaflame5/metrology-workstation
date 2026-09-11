"""
Standalone Windows Executable Compiler for Metrology Workstation (v7.0.0).
Uses PyInstaller to compile desktop_app.py into a self-contained MetrologyWorkstation.exe.
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
DIST_WORKSTATION_DIR = os.path.join(DIST_DIR, "MetrologyWorkstation")
TARGET_EXE = os.path.join(DIST_WORKSTATION_DIR, "MetrologyWorkstation.exe")
ROOT_EXE = os.path.join(DIST_DIR, "MetrologyWorkstation.exe")


def compile_executable():
    print("=" * 70)
    print(" COMPILING METROLOGY WORKSTATION STANDALONE EXECUTABLE (v7.0.0)")
    print("=" * 70)
    os.makedirs(DIST_WORKSTATION_DIR, exist_ok=True)

    ui_src = os.path.join(PROJECT_ROOT, "ui", "workstation")
    static_src = ui_src if os.path.exists(ui_src) else os.path.join(PROJECT_ROOT, "metrology_app", "static")
    proc_src = os.path.join(PROJECT_ROOT, "metrology_app", "procedures")
    std_src = os.path.join(PROJECT_ROOT, "standards")
    icon_path = os.path.join(PROJECT_ROOT, "assets", "app.ico")
    manifest_path = os.path.join(PROJECT_ROOT, "app.manifest")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=MetrologyWorkstation",
        "--onefile",
        "--noconfirm",
        "--workpath=build/v7_build",
        f"--icon={icon_path}",
        f"--add-data={static_src};ui/workstation",
        f"--add-data={static_src};metrology_app/static",
        f"--add-data={proc_src};metrology_app/procedures",
        f"--add-data={std_src};standards",
        # Explicit hidden imports for FastAPI, Uvicorn, and Metrology subsystems
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
        "--hidden-import=metrology_app.services.enterprise_certificate_service",
        "--hidden-import=metrology_app.services.evidence_package_service",
        "--hidden-import=metrology_app.services.procedure_service",
        "--hidden-import=metrology_app.services.log_service",
        # Native Desktop GUI (pywebview + pythonnet)
        "--hidden-import=webview",
        "--hidden-import=webview.platforms",
        "--hidden-import=webview.platforms.winforms",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=clr",
        "--hidden-import=clr_loader",
        "--hidden-import=pythonnet",
        # Exclude unrelated heavy ML & dev packages to ensure clean 20s build
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "--exclude-module=transformers",
        "--exclude-module=cv2",
        "--exclude-module=nltk",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=pytest",
        f"--manifest={manifest_path}",
        os.path.join(PROJECT_ROOT, "desktop_app.py"),
    ]

    print("Running PyInstaller compilation command...")
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(" [FAIL] PyInstaller compilation failed!")
        sys.exit(res.returncode)

    built_exe = os.path.join(DIST_DIR, "MetrologyWorkstation.exe")
    if os.path.exists(built_exe):
        shutil.copy2(built_exe, TARGET_EXE)
        size = os.path.getsize(TARGET_EXE)
        print("\n" + "=" * 70)
        print(" STANDALONE EXECUTABLE BUILT SUCCESSFULLY")
        print(f" Output Location: {TARGET_EXE}")
        print(f" File Size:       {size:,} bytes ({size / (1024*1024):.2f} MB)")
        print("=" * 70)
    else:
        print(f" [FAIL] Expected {built_exe} was not found.")
        sys.exit(1)


if __name__ == "__main__":
    compile_executable()
