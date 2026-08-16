"""
Standalone Windows Executable Compiler for Metrology Workstation.
Uses PyInstaller to compile desktop_app.py into a self-contained MetrologyWorkstation.exe.
"""

import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_WORKSTATION_DIR = os.path.join(PROJECT_ROOT, "dist", "MetrologyWorkstation")
TARGET_EXE = os.path.join(DIST_WORKSTATION_DIR, "MetrologyWorkstation.exe")


def compile_executable():
    print(f"Compiling standalone executable into: {DIST_WORKSTATION_DIR}")
    os.makedirs(DIST_WORKSTATION_DIR, exist_ok=True)

    static_src = os.path.join(PROJECT_ROOT, "metrology_app", "static")
    proc_src = os.path.join(PROJECT_ROOT, "metrology_app", "procedures")
    std_src = os.path.join(PROJECT_ROOT, "standards")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=MetrologyWorkstation",
        "--onefile",
        "--noconfirm",
        "--clean",
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
        "--hidden-import=pydantic",
        "--hidden-import=sqlite3",
        f"--manifest={os.path.join(PROJECT_ROOT, 'app.manifest')}",
        os.path.join(PROJECT_ROOT, "desktop_app.py"),
    ]

    print("Running PyInstaller command...")
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(" [FAIL] PyInstaller compilation failed!")
        sys.exit(res.returncode)

    built_exe = os.path.join(PROJECT_ROOT, "dist", "MetrologyWorkstation.exe")
    if os.path.exists(built_exe):
        shutil.copy2(built_exe, TARGET_EXE)
        print(f" [OK] Standalone executable installed to: {TARGET_EXE} ({os.path.getsize(TARGET_EXE):,} bytes)")
    else:
        print(f" [FAIL] Expected {built_exe} was not found.")
        sys.exit(1)


if __name__ == "__main__":
    compile_executable()
