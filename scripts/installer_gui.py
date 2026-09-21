"""
CALIBRA Metrology Workstation — Professional Windows Setup Wizard (v7.0.0).
Native Windows GUI Installer with CALIBRA Branding & Zero Console Windows.
"""

import sys
import os
import shutil
import winreg
import json
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

# Stream safety in GUI mode
class _NullWriter:
    encoding = "utf-8"
    errors = "ignore"

    def write(self, s):
        pass

    def flush(self):
        pass

    def reconfigure(self, *args, **kwargs):
        pass

    def isatty(self):
        return False

    def readable(self):
        return False

    def writable(self):
        return True

    def seekable(self):
        return False


if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()


def resolve_installer_edition() -> str:
    """Determine whether this setup wizard is for Demo or Pro."""
    # 1. Check embedded edition.json inside PyInstaller bundle (_MEIPASS)
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
    bundled_edition_file = bundle_dir / "edition.json"
    if bundled_edition_file.exists():
        try:
            with open(bundled_edition_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "edition" in data:
                    return data["edition"].lower()
        except Exception:
            pass

    # 2. Check CLI flags
    if "--demo" in sys.argv:
        return "demo"
    if "--pro" in sys.argv or "--commercial" in sys.argv:
        return "pro"

    # 3. Check environment variable
    if "METROLOGY_EDITION" in os.environ:
        return os.environ["METROLOGY_EDITION"].lower()

    # 4. Check executable filename (e.g. Metrology-Workstation-Demo-v7.0.0-Setup.exe)
    try:
        exe_name = Path(sys.executable).name.lower()
        if "demo" in exe_name:
            return "demo"
        if "pro" in exe_name:
            return "pro"
    except Exception:
        pass

    return "demo"


INSTALLER_EDITION = resolve_installer_edition()
IS_DEMO = (INSTALLER_EDITION == "demo")
EDITION_NAME = "Demo Evaluation" if IS_DEMO else "Professional Edition"
APP_NAME = f"CALIBRA Metrology Workstation 7 ({EDITION_NAME})"
APP_SHORT_NAME = f"CALIBRA Metrology Workstation ({'Demo' if IS_DEMO else 'Pro'})"
APP_VERSION = "7.0.0"
PUBLISHER = "NOVYRAX Engineering Intelligence"
EXE_NAME = "MetrologyWorkstation.exe"
REG_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstationDemo"
    if IS_DEMO else
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstationPro"
)

EULA_TEXT = """CALIBRA METROLOGY WORKSTATION — SOFTWARE LICENSE AGREEMENT

IMPORTANT — READ CAREFULLY: This End-User License Agreement ("EULA") is a legal agreement between you (either an individual or a single entity) and NOVYRAX Engineering Intelligence for the CALIBRA Metrology Workstation software.

1. GRANT OF LICENSE
NOVYRAX grants you a non-exclusive, non-transferable license to install and use CALIBRA Metrology Workstation in accordance with ISO/IEC 17025:2017 and ANSI/NCSL Z540.3 standards for metrological measurement, calibration uncertainty budgets, and quality operations.

2. EDITION TERMS
- Demo Evaluation: Provided for evaluation, testing, and academic review. Reports carry evaluation watermarks.
- Professional Edition: Fully licensed for commercial, industrial, and accredited laboratory use. All 7 instrument catalogs, guardbanding methods, and compliance self-tests are enabled.

3. DATA INTEGRITY & PRIVACY
CALIBRA is an air-gap safe, 100% offline application. It transmits zero telemetry, zero analytics, and zero measurement records to external servers. All data remains inside your local encrypted SQLite vault.

4. ACCREDITATION DISCLAIMER
While CALIBRA implements JCGM 100:2008 (GUM) and ISO 14253 algorithms, the operating laboratory remains responsible for method validation, reference standards traceability, and accredited scope compliance.
"""

def get_default_install_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    return Path(local_app_data) / "Programs" / "MetrologyWorkstation"

def create_shortcut(target: Path, shortcut_path: Path, description: str = "", arguments: str = ""):
    ps_cmd = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.Arguments = "{arguments}"
$Shortcut.WorkingDirectory = "{target.parent}"
$Shortcut.IconLocation = "{target},0"
$Shortcut.Description = "{description}"
$Shortcut.Save()
"""
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], creationflags=0x08000000)

def register_uninstall(install_dir: Path, target_exe: Path, uninstaller: Path):
    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(target_exe))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass

def write_uninstaller_script(install_dir: Path) -> Path:
    uninstaller_path = install_dir / "uninstall.bat"
    content = f"""@echo off
echo ===============================================================
echo  Uninstalling {APP_NAME}
echo ===============================================================
echo.
set "START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs"
if exist "%START_MENU%\\{APP_NAME}.lnk" del "%START_MENU%\\{APP_NAME}.lnk"
if exist "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" del "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk"
reg delete "HKCU\\{REG_KEY}" /f >nul 2>&1
echo Removing program files...
cd "%TEMP%"
timeout /t 1 /nobreak >nul
rmdir /s /q "{install_dir}" >nul 2>&1
echo {APP_NAME} uninstalled successfully.
echo (User calibration records in %%LOCALAPPDATA%%\\MetrologyWorkstation were preserved.)
pause
"""
    with open(uninstaller_path, "w", encoding="utf-8") as f:
        f.write(content)
    return uninstaller_path

def perform_install(target_dir: Path, desktop_shortcut: bool, start_shortcut: bool, progress_callback=None):
    os.makedirs(target_dir, exist_ok=True)
    if progress_callback: progress_callback(10, "Locating installation payload...")

    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent / "dist" / "MetrologyWorkstation"))
    source_exe = bundle_dir / EXE_NAME
    if not source_exe.exists():
        source_exe = Path(__file__).parent.parent / "dist" / "MetrologyWorkstation" / EXE_NAME
    if not source_exe.exists():
        source_exe = Path(__file__).parent.parent / "dist" / EXE_NAME

    target_exe = target_dir / EXE_NAME

    if progress_callback: progress_callback(30, f"Extracting {EXE_NAME}...")
    if source_exe.exists():
        shutil.copy2(source_exe, target_exe)

    # Write edition manifest to installation directory
    edition_payload = {
        "edition": INSTALLER_EDITION,
        "version": APP_VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(target_dir / "edition.json", "w", encoding="utf-8") as f:
        json.dump(edition_payload, f, indent=2)

    # Also register edition manifest in user AppData so runtime always recognizes installed edition
    try:
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        app_data_dir = Path(local_app_data) / "MetrologyWorkstation"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        with open(app_data_dir / "edition.json", "w", encoding="utf-8") as f:
            json.dump(edition_payload, f, indent=2)
    except Exception:
        pass

    if progress_callback: progress_callback(60, "Copying procedures and standards...")
    for folder in ("procedures", "standards", "static"):
        src = bundle_dir / folder
        if not src.exists():
            src = Path(__file__).parent.parent / "metrology_app" / folder if folder != "standards" else Path(__file__).parent.parent / folder
        if src.exists():
            shutil.copytree(src, target_dir / folder, dirs_exist_ok=True)

    if progress_callback: progress_callback(80, "Configuring uninstaller & registry...")
    uninstaller = write_uninstaller_script(target_dir)
    register_uninstall(target_dir, target_exe, uninstaller)

    if progress_callback: progress_callback(90, "Creating Windows shortcuts...")
    shortcut_args = "--demo" if IS_DEMO else "--pro"
    shortcut_name = f"{APP_NAME}.lnk"
    if start_shortcut:
        sm = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        if sm.exists():
            create_shortcut(target_exe, sm / shortcut_name, APP_NAME, arguments=shortcut_args)

    if desktop_shortcut:
        dt = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if dt.exists():
            create_shortcut(target_exe, dt / shortcut_name, APP_NAME, arguments=shortcut_args)

    if progress_callback: progress_callback(100, "Installation complete.")
    return target_exe

# ── GUI SETUP WIZARD (Tkinter) ──
def run_gui_wizard():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    root = tk.Tk()
    root.title(f"{APP_NAME} — Setup")
    root.geometry("620x450")
    root.resizable(False, False)

    # Styling colors: CALIBRA Teal & Slate
    BG_DARK = "#00435F"
    BG_LIGHT = "#FFFFFF"
    TEXT_DARK = "#17191C"
    TEXT_MUTED = "#64748B"
    TEAL = "#007A9B"

    root.configure(bg=BG_LIGHT)

    # Top Banner
    banner = tk.Frame(root, bg=BG_DARK, height=72)
    banner.pack(fill=tk.X, side=tk.TOP)
    banner.pack_propagate(False)

    lbl_title = tk.Label(banner, text=APP_NAME, font=("Segoe UI", 13, "bold"), fg="#FFFFFF", bg=BG_DARK)
    lbl_title.pack(anchor="w", padx=20, pady=(12, 2))
    lbl_sub = tk.Label(banner, text="ISO/IEC 17025:2017 & ANSI/NCSL Z540.3 Accredited Engineering Setup", font=("Segoe UI", 9), fg="#94D2E3", bg=BG_DARK)
    lbl_sub.pack(anchor="w", padx=20)

    # Content Container
    content = tk.Frame(root, bg=BG_LIGHT)
    content.pack(fill=tk.BOTH, expand=True, padx=24, pady=16)

    # Bottom Button Bar
    btn_bar = tk.Frame(root, bg="#F1F5F9", height=50, bd=1, relief=tk.SOLID)
    btn_bar.pack(fill=tk.X, side=tk.BOTTOM)
    btn_bar.pack_propagate(False)

    current_step = tk.IntVar(value=0)
    install_path_var = tk.StringVar(value=str(get_default_install_dir()))
    eula_accepted = tk.BooleanVar(value=False)
    shortcut_desktop = tk.BooleanVar(value=True)
    shortcut_start = tk.BooleanVar(value=True)
    launch_app_var = tk.BooleanVar(value=True)

    installed_exe = None

    def clear_content():
        for widget in content.winfo_children():
            widget.destroy()

    # Step 0: Welcome
    def show_welcome():
        clear_content()
        tk.Label(content, text=f"Welcome to the {APP_NAME} Setup", font=("Segoe UI", 12, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(8, 12))
        msg = f"""This setup wizard will install {APP_NAME} v{APP_VERSION} on your computer.

Edition: {EDITION_NAME}
Target Platform: Windows 10/11 (64-bit)
Compliance: ISO/IEC 17025:2017 Section 7.11 & ANSI/NCSL Z540.3
Architecture: Native Local-First Engineering Workstation (100% Offline)

Click Next to continue, or Cancel to exit Setup."""
        tk.Label(content, text=msg, font=("Segoe UI", 9), fg=TEXT_DARK, bg=BG_LIGHT, justify=tk.LEFT).pack(anchor="w")

        btn_back.config(state=tk.DISABLED)
        btn_next.config(text="Next >", command=lambda: next_step(1))

    # Step 1: EULA
    def show_eula():
        clear_content()
        tk.Label(content, text="License Agreement", font=("Segoe UI", 11, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(0, 4))
        tk.Label(content, text="Please read the following terms before proceeding with installation:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_LIGHT).pack(anchor="w", pady=(0, 8))

        txt_frame = tk.Frame(content)
        txt_frame.pack(fill=tk.BOTH, expand=True)

        txt = tk.Text(txt_frame, wrap=tk.WORD, font=("Consolas", 8), height=9, bd=1, relief=tk.SOLID)
        txt.insert("1.0", EULA_TEXT)
        txt.config(state=tk.DISABLED)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(txt_frame, command=txt.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=scrollbar.set)

        chk = tk.Checkbutton(content, text="I accept the agreement and laboratory compliance terms", variable=eula_accepted, bg=BG_LIGHT, font=("Segoe UI", 9))
        chk.pack(anchor="w", pady=(8, 0))

        btn_back.config(state=tk.NORMAL, command=lambda: next_step(0))
        btn_next.config(text="Next >", command=validate_eula)

    def validate_eula():
        if not eula_accepted.get():
            messagebox.showwarning("License Agreement", "You must accept the agreement to continue installation.")
            return
        next_step(2)

    # Step 2: Destination & Shortcuts
    def show_destination():
        clear_content()
        tk.Label(content, text="Select Destination Location", font=("Segoe UI", 11, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(0, 4))
        tk.Label(content, text=f"Setup will install {APP_NAME} into the following folder:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_LIGHT).pack(anchor="w", pady=(0, 8))

        dest_frame = tk.Frame(content, bg=BG_LIGHT)
        dest_frame.pack(fill=tk.X, pady=(0, 16))

        ent = tk.Entry(dest_frame, textvariable=install_path_var, font=("Segoe UI", 9), bd=1, relief=tk.SOLID)
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        def browse():
            chosen = filedialog.askdirectory(initialdir=install_path_var.get())
            if chosen: install_path_var.set(chosen)

        tk.Button(dest_frame, text="Browse...", command=browse, font=("Segoe UI", 8)).pack(side=tk.RIGHT, padx=(8, 0))

        tk.Label(content, text="Additional Shortcuts:", font=("Segoe UI", 10, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(8, 4))
        tk.Checkbutton(content, text="Create Desktop shortcut", variable=shortcut_desktop, bg=BG_LIGHT, font=("Segoe UI", 9)).pack(anchor="w")
        tk.Checkbutton(content, text="Create Start Menu shortcut", variable=shortcut_start, bg=BG_LIGHT, font=("Segoe UI", 9)).pack(anchor="w")

        tk.Label(content, text="At least 250 MB of free disk space is required.", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_LIGHT).pack(anchor="w", pady=(12, 0))

        btn_back.config(state=tk.NORMAL, command=lambda: next_step(1))
        btn_next.config(text="Install", command=start_installation)

    # Step 3: Progress
    def start_installation():
        clear_content()
        tk.Label(content, text="Installing Metrology Workstation...", font=("Segoe UI", 11, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(0, 4))
        status_lbl = tk.Label(content, text="Please wait while files are extracted...", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_LIGHT)
        status_lbl.pack(anchor="w", pady=(0, 12))

        prog = ttk.Progressbar(content, orient="horizontal", length=570, mode="determinate")
        prog.pack(pady=16)

        btn_back.config(state=tk.DISABLED)
        btn_next.config(state=tk.DISABLED)

        def update_progress(pct, msg):
            root.after(0, lambda: (prog.config(value=pct), status_lbl.config(text=msg)))

        def worker():
            nonlocal installed_exe
            target = Path(install_path_var.get())
            try:
                installed_exe = perform_install(target, shortcut_desktop.get(), shortcut_start.get(), progress_callback=update_progress)
                root.after(0, show_finished)
            except Exception as ex:
                root.after(0, lambda: messagebox.showerror("Installation Error", str(ex)))

        threading.Thread(target=worker, daemon=True).start()

    # Step 4: Finished
    def show_finished():
        clear_content()
        tk.Label(content, text=f"Completing {APP_NAME} Setup", font=("Segoe UI", 12, "bold"), fg=TEXT_DARK, bg=BG_LIGHT).pack(anchor="w", pady=(8, 12))
        tk.Label(content, text=f"{APP_NAME} has been installed on your computer.\n\nThe application may be launched by selecting the installed shortcuts.", font=("Segoe UI", 9), fg=TEXT_DARK, bg=BG_LIGHT, justify=tk.LEFT).pack(anchor="w", pady=(0, 16))

        tk.Checkbutton(content, text=f"Launch {APP_SHORT_NAME}", variable=launch_app_var, bg=BG_LIGHT, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 0))

        btn_back.config(state=tk.DISABLED)
        btn_next.config(state=tk.NORMAL, text="Finish", command=finish)

    def finish():
        if launch_app_var.get() and installed_exe and installed_exe.exists():
            # Launch detached windowed executable with CREATE_NO_WINDOW and appropriate edition flag
            launch_args = [str(installed_exe)]
            if IS_DEMO:
                launch_args.append("--demo")
            else:
                launch_args.append("--pro")
            subprocess.Popen(launch_args, creationflags=0x08000000)
        root.destroy()

    def next_step(step):
        current_step.set(step)
        if step == 0: show_welcome()
        elif step == 1: show_eula()
        elif step == 2: show_destination()

    btn_cancel = tk.Button(btn_bar, text="Cancel", command=root.destroy, width=9, font=("Segoe UI", 9))
    btn_cancel.pack(side=tk.RIGHT, padx=(4, 16), pady=10)

    btn_next = tk.Button(btn_bar, text="Next >", width=9, font=("Segoe UI", 9, "bold"), bg="#00435F", fg="#FFFFFF")
    btn_next.pack(side=tk.RIGHT, padx=4, pady=10)

    btn_back = tk.Button(btn_bar, text="< Back", width=9, font=("Segoe UI", 9))
    btn_back.pack(side=tk.RIGHT, padx=4, pady=10)

    show_welcome()
    root.mainloop()


if __name__ == "__main__":
    if "/S" in sys.argv or "--silent" in sys.argv or "-s" in sys.argv:
        t_dir = get_default_install_dir()
        exe = perform_install(t_dir, desktop_shortcut=True, start_shortcut=True)
        if "--launch" in sys.argv and exe.exists():
            launch_args = [str(exe)]
            if IS_DEMO:
                launch_args.append("--demo")
            else:
                launch_args.append("--pro")
            subprocess.Popen(launch_args, creationflags=0x08000000)
    else:
        run_gui_wizard()
