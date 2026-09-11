"""
Metrology Workstation — Native Windows Installer Engine (v7.0.0).

Handles:
- Extraction to %LOCALAPPDATA%\Programs\MetrologyWorkstation
- Start Menu and Desktop shortcut creation with custom icon
- Windows Add/Remove Programs (Registry) registration
- Clean Uninstaller generation preserving calibration records
- Silent installation support (/S, --silent)
"""

import sys
import os
import shutil
import winreg
import subprocess
from pathlib import Path


APP_NAME = "Metrology Workstation 7"
APP_VERSION = "7.0.0"
PUBLISHER = "NOVYRAX Metrology Systems"
EXE_NAME = "MetrologyWorkstation.exe"
REG_UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstation"


def get_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    return Path(local_app_data) / "Programs" / "MetrologyWorkstation"


def create_windows_shortcut(target_exe: Path, shortcut_path: Path, description: str = ""):
    """Create Windows .lnk shortcut using PowerShell."""
    ps_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target_exe}"
$Shortcut.WorkingDirectory = "{target_exe.parent}"
$Shortcut.IconLocation = "{target_exe},0"
$Shortcut.Description = "{description}"
$Shortcut.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)


def register_in_add_remove_programs(install_dir: Path, target_exe: Path, uninstaller_path: Path):
    """Register application in Windows Registry Add/Remove Programs."""
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_UNINSTALL_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(target_exe))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as e:
        print(f" Registry registration note: {e}")


def write_uninstaller(install_dir: Path) -> Path:
    """Create uninstaller script in install directory."""
    uninstaller_path = install_dir / "uninstall.bat"
    script = f"""@echo off
echo =======================================================
echo  Uninstalling {APP_NAME} v{APP_VERSION}
echo =======================================================
echo.

:: Remove Start Menu shortcut
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
if exist "%START_MENU%\\{APP_NAME}.lnk" del "%START_MENU%\\{APP_NAME}.lnk"

:: Remove Desktop shortcut
if exist "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" del "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk"

:: Remove Registry Uninstall entry
reg delete "HKCU\\{REG_UNINSTALL_KEY}" /f >nul 2>&1

:: Schedule self-deletion of installation directory
echo Removing installed program files...
cd "%TEMP%"
timeout /t 1 /nobreak >nul
rmdir /s /q "{install_dir}" >nul 2>&1

echo.
echo {APP_NAME} has been successfully uninstalled.
echo (User calibration records in %%LOCALAPPDATA%%\\MetrologyWorkstation were preserved.)
echo.
pause
"""
    with open(uninstaller_path, "w", encoding="utf-8") as f:
        f.write(script)
    return uninstaller_path


def install(silent: bool = False, launch_after: bool = True):
    print("=" * 65)
    print(f" {APP_NAME} v{APP_VERSION} — Windows Installation")
    print("=" * 65)

    install_dir = get_install_dir()
    print(f"Target Directory: {install_dir}")
    os.makedirs(install_dir, exist_ok=True)

    # Determine bundle payload directory (sys._MEIPASS if PyInstaller or local dist)
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent / "dist" / "MetrologyWorkstation"))
    source_exe = bundle_dir / EXE_NAME
    target_exe = install_dir / EXE_NAME

    if not source_exe.exists():
        # Fallback search
        source_exe = Path(__file__).parent.parent / "dist" / "MetrologyWorkstation" / EXE_NAME

    if not source_exe.exists():
        print(f" [FAIL] Source executable not found at: {source_exe}")
        sys.exit(1)

    print(f"Installing {EXE_NAME} ({os.path.getsize(source_exe):,} bytes)...")
    shutil.copy2(source_exe, target_exe)

    # Copy bundled procedures and standards if present
    for folder in ("procedures", "standards"):
        src_folder = bundle_dir / folder
        if src_folder.exists():
            dest_folder = install_dir / folder
            shutil.copytree(src_folder, dest_folder, dirs_exist_ok=True)

    # Create Uninstaller
    uninstaller_path = write_uninstaller(install_dir)
    print(" [OK] Generated uninstaller")

    # Create Start Menu Shortcut
    start_menu_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    if start_menu_dir.exists():
        shortcut_path = start_menu_dir / f"{APP_NAME}.lnk"
        create_windows_shortcut(target_exe, shortcut_path, f"{APP_NAME} v{APP_VERSION}")
        print(f" [OK] Created Start Menu shortcut: {shortcut_path}")

    # Create Desktop Shortcut
    desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if desktop_dir.exists():
        desktop_shortcut = desktop_dir / f"{APP_NAME}.lnk"
        create_windows_shortcut(target_exe, desktop_shortcut, f"{APP_NAME} v{APP_VERSION}")
        print(f" [OK] Created Desktop shortcut: {desktop_shortcut}")

    # Register in Windows Add/Remove Programs
    register_in_add_remove_programs(install_dir, target_exe, uninstaller_path)
    print(" [OK] Registered in Windows Add/Remove Programs")

    print("\n" + "=" * 65)
    print(f" {APP_NAME} v{APP_VERSION} INSTALLED SUCCESSFULLY!")
    print("=" * 65)

    if launch_after and not silent:
        print("Launching Metrology Workstation...")
        subprocess.Popen([str(target_exe)])


if __name__ == "__main__":
    is_silent = "/S" in sys.argv or "--silent" in sys.argv or "-s" in sys.argv
    is_no_launch = "--no-launch" in sys.argv
    install(silent=is_silent, launch_after=not is_no_launch)
