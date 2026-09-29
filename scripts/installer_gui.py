"""
CALIBRA Metrology Workstation — Professional Windows Setup Wizard (v7.0.0)
Native Windows GUI Installer with full CALIBRA Pro branding.
"""

import sys
import os
import shutil
import winreg
import json
import subprocess
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Stream safety in windowless GUI mode
# ─────────────────────────────────────────────────────────────────────────────
class _NullWriter:
    encoding = "utf-8"
    errors = "ignore"
    def write(self, s): pass
    def flush(self): pass
    def reconfigure(self, *a, **kw): pass
    def isatty(self): return False
    def readable(self): return False
    def writable(self): return True
    def seekable(self): return False

if sys.stdout is None:
    sys.stdout = _NullWriter()
if sys.stderr is None:
    sys.stderr = _NullWriter()


# ─────────────────────────────────────────────────────────────────────────────
# Edition resolution
# ─────────────────────────────────────────────────────────────────────────────
def resolve_installer_edition() -> str:
    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
    edition_file = bundle_dir / "edition.json"
    if edition_file.exists():
        try:
            data = json.loads(edition_file.read_text("utf-8"))
            if "edition" in data:
                return data["edition"].lower()
        except Exception:
            pass
    if "--demo" in sys.argv:
        return "demo"
    if "--pro" in sys.argv or "--commercial" in sys.argv:
        return "pro"
    if "METROLOGY_EDITION" in os.environ:
        return os.environ["METROLOGY_EDITION"].lower()
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
EDITION_NAME   = "Demo Evaluation" if IS_DEMO else "Professional Edition"
EDITION_TAG    = "Demo" if IS_DEMO else "Pro"
APP_NAME       = f"CALIBRA Metrology Workstation 7 ({EDITION_NAME})"
APP_SHORT_NAME = f"CALIBRA Metrology Workstation ({EDITION_TAG})"
APP_VERSION    = "7.0.0"
PUBLISHER      = "NOVYRAX Engineering Intelligence"
EXE_NAME       = "MetrologyWorkstation.exe"
REG_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstationDemo"
    if IS_DEMO else
    r"Software\Microsoft\Windows\CurrentVersion\Uninstall\MetrologyWorkstationPro"
)

EULA_TEXT = """\
CALIBRA METROLOGY WORKSTATION — SOFTWARE LICENSE AGREEMENT
Version 7.0.0 | NOVYRAX Engineering Intelligence

IMPORTANT — READ CAREFULLY: This End-User License Agreement ("EULA") is a
legal agreement between you (either an individual or a single entity) and
NOVYRAX Engineering Intelligence for the CALIBRA Metrology Workstation
software product, which includes computer software, associated media, and
documentation ("Software").

1. GRANT OF LICENSE
NOVYRAX grants you a non-exclusive, non-transferable license to install and
use CALIBRA Metrology Workstation in accordance with ISO/IEC 17025:2017 and
ANSI/NCSL Z540.3 standards for metrological measurement, calibration
uncertainty budgets, and quality operations.

2. EDITION TERMS
  · Demo Evaluation:   Provided for evaluation, testing, and academic review.
                       Calibration certificates carry evaluation watermarks.
  · Professional:      Fully licensed for commercial, industrial, and
                       accredited laboratory use. All 7 instrument families,
                       Method 5 & 6 guardbanding, and compliance self-tests
                       are enabled with unwatermarked output.

3. DATA INTEGRITY & PRIVACY
CALIBRA is an air-gap safe, 100% offline application. It transmits zero
telemetry, zero analytics, and zero measurement records to external servers.
All data remains inside your local encrypted SQLite vault.

4. ACCREDITATION DISCLAIMER
While CALIBRA implements JCGM 100:2008 (GUM) and ISO 14253 algorithms, the
operating laboratory remains responsible for method validation, reference
standard traceability, and accredited scope compliance.

5. INTELLECTUAL PROPERTY
All algorithms, documentation, and compiled binaries are the exclusive
property of NOVYRAX Engineering Intelligence and are protected by
international copyright law.

6. LIMITATION OF LIABILITY
IN NO EVENT SHALL NOVYRAX BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE
SOFTWARE, EVEN IF NOVYRAX HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGES.

By proceeding with installation you agree to be bound by all terms above.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Installer logic (unchanged)
# ─────────────────────────────────────────────────────────────────────────────
def get_default_install_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    return Path(local) / "Programs" / "MetrologyWorkstation"


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
            winreg.SetValueEx(key, "DisplayName",     0, winreg.REG_SZ,    APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion",  0, winreg.REG_SZ,    APP_VERSION)
            winreg.SetValueEx(key, "Publisher",       0, winreg.REG_SZ,    PUBLISHER)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ,    str(install_dir))
            winreg.SetValueEx(key, "DisplayIcon",     0, winreg.REG_SZ,    str(target_exe))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,    f'"{uninstaller}"')
            winreg.SetValueEx(key, "NoModify",        0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair",        0, winreg.REG_DWORD, 1)
    except Exception:
        pass


def write_uninstaller_script(install_dir: Path) -> Path:
    path = install_dir / "uninstall.bat"
    content = f"""@echo off
echo ================================================================
echo  Uninstalling {APP_NAME}
echo ================================================================
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
    path.write_text(content, encoding="utf-8")
    return path


def perform_install(target_dir: Path, desktop_shortcut: bool, start_shortcut: bool, progress_callback=None):
    os.makedirs(target_dir, exist_ok=True)
    if progress_callback: progress_callback(10, "Locating installation payload…")

    bundle_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent / "dist" / "MetrologyWorkstation"))
    source_exe = bundle_dir / EXE_NAME
    if not source_exe.exists():
        source_exe = Path(__file__).parent.parent / "dist" / "MetrologyWorkstation" / EXE_NAME
    if not source_exe.exists():
        source_exe = Path(__file__).parent.parent / "dist" / EXE_NAME

    target_exe = target_dir / EXE_NAME

    if progress_callback: progress_callback(30, f"Extracting {EXE_NAME}…")
    if source_exe.exists():
        shutil.copy2(source_exe, target_exe)

    edition_payload = {
        "edition": INSTALLER_EDITION,
        "version": APP_VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
    }
    (target_dir / "edition.json").write_text(json.dumps(edition_payload, indent=2), encoding="utf-8")

    try:
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        app_data_dir = Path(local) / "MetrologyWorkstation"
        app_data_dir.mkdir(parents=True, exist_ok=True)
        (app_data_dir / "edition.json").write_text(json.dumps(edition_payload, indent=2), encoding="utf-8")

        lic_file = app_data_dir / "license.json"
        if IS_DEMO:
            if lic_file.exists():
                try:
                    lic_file.unlink()
                except Exception:
                    pass
        else:
            if not lic_file.exists():
                try:
                    import hmac
                    import hashlib
                    now_utc     = datetime.now(timezone.utc)
                    expires_utc = now_utc + timedelta(days=365)
                    token_payload = {
                        "entitlement_id":   f"CALIBRA-PRO-{int(now_utc.timestamp())}",
                        "customer_id":      "CUST-LICENSED-PRO",
                        "customer_name":    "Licensed Commercial Organization",
                        "organization_id":  "commercial@calibra.metrology",
                        "product_id":       "MetrologyWorkstation.Commercial",
                        "plan_id":          "PROFESSIONAL",
                        "status":           "ACTIVE",
                        "seat_limit":       1,
                        "issued_at":        now_utc.isoformat(),
                        "expires_at":       expires_utc.isoformat(),
                        "grace_period_days": 30,
                        "features": [
                            "SINGLE_POINT_MICROMETER", "EXACT_50_DIGIT_GUM",
                            "DECISION_Z5403_METHOD6", "12_STAGE_REPLAY",
                            "ALL_7_INSTRUMENT_FAMILIES", "MULTI_POINT_STUDIO",
                            "UNLIMITED_RECORDS", "MACHINE_VERIFIABLE_EVIDENCE_ZIP",
                            "UNWATERMARKED_CERTIFICATES", "HASH_CHAINED_AUDIT_VAULT",
                            "SQLITE_ATOMIC_BACKUPS", "OFFLINE_OPERATION",
                        ],
                    }
                    raw = json.dumps(token_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    verify_key = b"MW_PUB_VERIFY_KEY_2026_PRECISION_METROLOGY_981247"
                    token_payload["signature"] = hmac.new(verify_key, raw, hashlib.sha256).hexdigest()
                    lic_file.write_text(json.dumps(token_payload, indent=2), encoding="utf-8")
                except Exception:
                    pass
    except Exception:
        pass

    if progress_callback: progress_callback(60, "Copying procedures and standards…")
    for folder in ("procedures", "standards", "static"):
        src = bundle_dir / folder
        if not src.exists():
            if folder == "standards":
                src = Path(__file__).parent.parent / folder
            else:
                src = Path(__file__).parent.parent / "metrology_app" / folder
        if src.exists():
            shutil.copytree(src, target_dir / folder, dirs_exist_ok=True)

    if progress_callback: progress_callback(80, "Configuring uninstaller & registry…")
    uninstaller = write_uninstaller_script(target_dir)
    register_uninstall(target_dir, target_exe, uninstaller)

    if progress_callback: progress_callback(90, "Creating Windows shortcuts…")
    args = "--demo" if IS_DEMO else "--pro"
    shortcut_name = f"{APP_NAME}.lnk"
    if start_shortcut:
        sm = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        if sm.exists():
            create_shortcut(target_exe, sm / shortcut_name, APP_NAME, arguments=args)
    if desktop_shortcut:
        dt = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if dt.exists():
            create_shortcut(target_exe, dt / shortcut_name, APP_NAME, arguments=args)

    if progress_callback: progress_callback(100, "Installation complete.")
    return target_exe


# ─────────────────────────────────────────────────────────────────────────────
# GUI SETUP WIZARD — Premium CALIBRA Design
# ─────────────────────────────────────────────────────────────────────────────
def run_gui_wizard():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    # ── Palette ──────────────────────────────────────────────────────────────
    # Pro edition: deep navy + gold accent
    # Demo edition: teal + silver accent (still professional, but differentiated)
    if IS_DEMO:
        ACCENT       = "#00B4D8"   # teal
        ACCENT_DARK  = "#0096B4"
        ACCENT_TEXT  = "#E0F7FF"
        SIDEBAR_BG   = "#051926"
        HEADER_BG    = "#062030"
    else:
        ACCENT       = "#C5A856"   # gold
        ACCENT_DARK  = "#A88F3E"
        ACCENT_TEXT  = "#FFF8E7"
        SIDEBAR_BG   = "#06090F"
        HEADER_BG    = "#0A0E18"

    BODY_BG      = "#FFFFFF"
    CARD_BG      = "#F8FAFC"
    BORDER_CLR   = "#E2E8F0"
    TEXT_DARK    = "#0F172A"
    TEXT_MID     = "#334155"
    TEXT_MUTED   = "#64748B"
    DISABLED_BG  = "#CBD5E1"
    BTN_TEXT     = "#FFFFFF"
    SUCCESS_CLR  = "#16A34A"

    WIN_W, WIN_H = 760, 520
    SIDEBAR_W    = 190

    # ── Steps definition ─────────────────────────────────────────────────────
    STEPS = ["Welcome", "License", "Location", "Installing", "Complete"]

    # ── Root window ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title(f"{APP_NAME} — Setup Wizard")
    root.geometry(f"{WIN_W}x{WIN_H}")
    root.resizable(False, False)
    root.configure(bg=BODY_BG)

    # Centre on screen
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{WIN_W}x{WIN_H}+{(sw - WIN_W)//2}+{(sh - WIN_H)//2}")

    # ── ttk style ─────────────────────────────────────────────────────────────
    style = ttk.Style()
    style.theme_use("clam")

    # Progress bar — accent colour fill
    style.configure("Calibra.Horizontal.TProgressbar",
                    troughcolor=BORDER_CLR,
                    background=ACCENT,
                    bordercolor=BORDER_CLR,
                    lightcolor=ACCENT,
                    darkcolor=ACCENT,
                    thickness=8)

    # Scrollbar
    style.configure("Calibra.Vertical.TScrollbar",
                    troughcolor=CARD_BG,
                    background=BORDER_CLR,
                    arrowcolor=TEXT_MUTED,
                    borderwidth=0,
                    relief="flat")

    # ── Layout frames ─────────────────────────────────────────────────────────
    # Left sidebar
    sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=SIDEBAR_W)
    sidebar.pack(side=tk.LEFT, fill=tk.Y)
    sidebar.pack_propagate(False)

    # Right area (header + content + footer)
    right = tk.Frame(root, bg=BODY_BG)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Header strip
    header = tk.Frame(right, bg=HEADER_BG, height=68)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)

    # Content area
    content = tk.Frame(right, bg=BODY_BG)
    content.pack(fill=tk.BOTH, expand=True, padx=28, pady=16)

    # Footer bar
    footer = tk.Frame(right, bg=CARD_BG, height=52)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    footer.pack_propagate(False)

    # Divider line above footer
    tk.Frame(right, bg=BORDER_CLR, height=1).pack(fill=tk.X, side=tk.BOTTOM)

    # ── Sidebar — product identity ─────────────────────────────────────────────
    sb_top = tk.Frame(sidebar, bg=SIDEBAR_BG, pady=24)
    sb_top.pack(fill=tk.X)

    tk.Label(
        sb_top, text="CALIBRA", font=("Segoe UI", 15, "bold"),
        fg=ACCENT, bg=SIDEBAR_BG
    ).pack(pady=(0, 2))

    tk.Label(
        sb_top, text="Metrology Workstation", font=("Segoe UI", 8),
        fg=ACCENT_TEXT, bg=SIDEBAR_BG
    ).pack()

    tk.Label(
        sb_top, text=f"v{APP_VERSION}", font=("Segoe UI", 7),
        fg=TEXT_MUTED, bg=SIDEBAR_BG
    ).pack(pady=(2, 0))

    # Horizontal rule
    tk.Frame(sidebar, bg=ACCENT, height=1).pack(fill=tk.X, padx=20, pady=(0, 18))

    # Edition badge
    badge_text = "DEMO EVALUATION" if IS_DEMO else "PROFESSIONAL EDITION"
    badge_fg   = "#94D2E3" if IS_DEMO else "#D4AF5C"
    tk.Label(
        sidebar, text=badge_text, font=("Segoe UI", 6, "bold"),
        fg=badge_fg, bg=SIDEBAR_BG, letterSpacing=2
    ).pack(pady=(0, 22))

    # Step indicators — stored as list of label references
    step_labels = []
    step_frames  = []
    for i, name in enumerate(STEPS):
        sf = tk.Frame(sidebar, bg=SIDEBAR_BG, padx=18, pady=6)
        sf.pack(fill=tk.X)

        # Bullet circle (canvas)
        c = tk.Canvas(sf, width=20, height=20, bg=SIDEBAR_BG, highlightthickness=0)
        c.pack(side=tk.LEFT, padx=(0, 10))

        lbl = tk.Label(sf, text=name, font=("Segoe UI", 8), fg=TEXT_MUTED, bg=SIDEBAR_BG)
        lbl.pack(side=tk.LEFT)

        step_labels.append((c, lbl))
        step_frames.append(sf)

    # Vertical connector line between bullets (purely decorative)
    tk.Frame(sidebar, bg=SIDEBAR_BG).pack(expand=True)

    # Publisher tag at bottom
    tk.Label(
        sidebar, text="NOVYRAX", font=("Segoe UI", 7, "bold"),
        fg=TEXT_MUTED, bg=SIDEBAR_BG
    ).pack(pady=(0, 4))
    tk.Label(
        sidebar, text="Engineering Intelligence", font=("Segoe UI", 6),
        fg="#374151", bg=SIDEBAR_BG
    ).pack(pady=(0, 12))

    # ── Header — step title + subtitle ────────────────────────────────────────
    header_title = tk.Label(
        header, text="", font=("Segoe UI", 12, "bold"),
        fg="#FFFFFF", bg=HEADER_BG, anchor="w"
    )
    header_title.pack(side=tk.LEFT, padx=24, pady=(14, 2), anchor="nw")

    header_sub = tk.Label(
        header, text="", font=("Segoe UI", 8),
        fg=ACCENT_TEXT, bg=HEADER_BG, anchor="w"
    )
    header_sub.pack(side=tk.LEFT, padx=24, anchor="sw")

    # Pack header children vertically instead
    for w in header.winfo_children():
        w.pack_forget()

    header_title.pack(anchor="w", padx=24, pady=(14, 1))
    header_sub.pack(anchor="w", padx=24, pady=(0, 10))

    # ── Footer buttons ─────────────────────────────────────────────────────────
    btn_cancel = tk.Button(
        footer, text="Cancel", command=root.destroy,
        font=("Segoe UI", 8), width=9,
        bg=BODY_BG, fg=TEXT_MID,
        relief="flat", bd=0, cursor="hand2",
        activebackground=BORDER_CLR, activeforeground=TEXT_DARK
    )
    btn_cancel.pack(side=tk.RIGHT, padx=(4, 20), pady=12)

    btn_next = tk.Button(
        footer, text="Next  →", width=11,
        font=("Segoe UI", 9, "bold"),
        bg=ACCENT, fg=BTN_TEXT,
        relief="flat", bd=0, cursor="hand2",
        activebackground=ACCENT_DARK, activeforeground=BTN_TEXT,
        padx=10, pady=4
    )
    btn_next.pack(side=tk.RIGHT, padx=4, pady=12)

    btn_back = tk.Button(
        footer, text="←  Back", width=9,
        font=("Segoe UI", 8),
        bg=BODY_BG, fg=TEXT_MID,
        relief="flat", bd=0, cursor="hand2",
        activebackground=BORDER_CLR, activeforeground=TEXT_DARK,
        padx=8, pady=4
    )
    btn_back.pack(side=tk.RIGHT, padx=4, pady=12)

    # ── State ─────────────────────────────────────────────────────────────────
    current_step       = tk.IntVar(value=0)
    install_path_var   = tk.StringVar(value=str(get_default_install_dir()))
    eula_accepted      = tk.BooleanVar(value=False)
    shortcut_desktop   = tk.BooleanVar(value=True)
    shortcut_start     = tk.BooleanVar(value=True)
    launch_app_var     = tk.BooleanVar(value=True)
    installed_exe      = None

    # ── Sidebar step updater ──────────────────────────────────────────────────
    def update_steps(active):
        for i, (c, lbl) in enumerate(step_labels):
            c.delete("all")
            if i < active:
                # Completed
                c.create_oval(2, 2, 18, 18, fill=ACCENT, outline="")
                c.create_text(10, 10, text="✓", fill=SIDEBAR_BG, font=("Segoe UI", 7, "bold"))
                lbl.config(fg=ACCENT)
            elif i == active:
                # Active
                c.create_oval(2, 2, 18, 18, fill=ACCENT, outline="")
                c.create_text(10, 10, text=str(i + 1), fill=SIDEBAR_BG, font=("Segoe UI", 7, "bold"))
                lbl.config(fg="#FFFFFF", font=("Segoe UI", 8, "bold"))
            else:
                # Pending
                c.create_oval(2, 2, 18, 18, fill="", outline=TEXT_MUTED, width=1.5)
                c.create_text(10, 10, text=str(i + 1), fill=TEXT_MUTED, font=("Segoe UI", 7))
                lbl.config(fg=TEXT_MUTED, font=("Segoe UI", 8))

    def set_header(title, sub=""):
        header_title.config(text=title)
        header_sub.config(text=sub)

    def clear_content():
        for w in content.winfo_children():
            w.destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def section_label(parent, text):
        tk.Label(
            parent, text=text, font=("Segoe UI", 9, "bold"),
            fg=TEXT_DARK, bg=BODY_BG
        ).pack(anchor="w", pady=(0, 6))

    def body_label(parent, text, muted=False, wrap=460):
        tk.Label(
            parent, text=text,
            font=("Segoe UI", 8 if muted else 9),
            fg=TEXT_MUTED if muted else TEXT_MID,
            bg=BODY_BG, justify="left", wraplength=wrap
        ).pack(anchor="w", pady=(0, 4))

    def info_row(parent, key, value):
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill=tk.X, pady=1)
        tk.Label(row, text=key, font=("Segoe UI", 8, "bold"),
                 fg=TEXT_MID, bg=CARD_BG, width=22, anchor="w").pack(side=tk.LEFT, padx=(10, 0), pady=4)
        tk.Label(row, text=value, font=("Segoe UI", 8),
                 fg=TEXT_DARK, bg=CARD_BG, anchor="w").pack(side=tk.LEFT, padx=4, pady=4)

    def card_frame(parent):
        f = tk.Frame(parent, bg=CARD_BG, bd=1, relief="solid")
        f.pack(fill=tk.X, pady=(0, 12))
        return f

    def styled_check(parent, text, var):
        tk.Checkbutton(
            parent, text=text, variable=var,
            font=("Segoe UI", 9), fg=TEXT_DARK, bg=BODY_BG,
            activebackground=BODY_BG, selectcolor=BODY_BG,
            cursor="hand2"
        ).pack(anchor="w", pady=2)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 0 — Welcome
    # ─────────────────────────────────────────────────────────────────────────
    def show_welcome():
        clear_content()
        update_steps(0)
        set_header(
            f"Welcome to {APP_NAME} Setup",
            "The installation wizard will guide you through setup in a few steps."
        )

        body_label(content,
            f"This wizard installs CALIBRA Metrology Workstation v{APP_VERSION} "
            f"({EDITION_NAME}) on your Windows system.",
            wrap=480)

        tk.Frame(content, bg=BORDER_CLR, height=1).pack(fill=tk.X, pady=(6, 12))

        # Info card
        cf = card_frame(content)
        info_row(cf, "Edition",       EDITION_NAME)
        info_row(cf, "Version",       f"v{APP_VERSION}")
        info_row(cf, "Platform",      "Windows 10 / 11 (64-bit)")
        info_row(cf, "Architecture",  "Local-First · 100% Offline · Air-Gap Safe")
        info_row(cf, "Compliance",    "ISO/IEC 17025:2017 · ANSI/NCSL Z540.3")
        info_row(cf, "Publisher",     PUBLISHER)

        tk.Frame(content, bg=BORDER_CLR, height=1).pack(fill=tk.X, pady=(8, 8))
        body_label(content, "Click  Next  to continue, or  Cancel  to exit Setup.", muted=True)

        btn_back.config(state=tk.DISABLED)
        btn_next.config(text="Next  →", state=tk.NORMAL, command=lambda: go_to(1))

    # ─────────────────────────────────────────────────────────────────────────
    # Step 1 — License Agreement
    # ─────────────────────────────────────────────────────────────────────────
    def show_eula():
        clear_content()
        update_steps(1)
        set_header(
            "License Agreement",
            "Read the agreement carefully. You must accept to proceed."
        )

        body_label(content, "Please read the following End-User License Agreement:", muted=True)

        txt_frame = tk.Frame(content, bg=CARD_BG, bd=1, relief="solid")
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        txt = tk.Text(
            txt_frame, wrap=tk.WORD, font=("Consolas", 8),
            bg=CARD_BG, fg=TEXT_MID,
            bd=0, highlightthickness=0, padx=12, pady=10
        )
        txt.insert("1.0", EULA_TEXT)
        txt.config(state=tk.DISABLED)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = ttk.Scrollbar(txt_frame, orient="vertical",
                            command=txt.yview, style="Calibra.Vertical.TScrollbar")
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=sb.set)

        sep = tk.Frame(content, bg=BORDER_CLR, height=1)
        sep.pack(fill=tk.X, pady=(0, 8))

        styled_check(content,
            "I accept the terms of this agreement and laboratory compliance requirements.",
            eula_accepted)

        btn_back.config(state=tk.NORMAL, command=lambda: go_to(0))
        btn_next.config(text="Next  →", state=tk.NORMAL, command=validate_eula)

    def validate_eula():
        if not eula_accepted.get():
            messagebox.showwarning(
                "License Agreement",
                "You must accept the license agreement to continue installation."
            )
            return
        go_to(2)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 2 — Destination & Options
    # ─────────────────────────────────────────────────────────────────────────
    def show_destination():
        clear_content()
        update_steps(2)
        set_header(
            "Select Destination Location",
            "Choose where CALIBRA Metrology Workstation will be installed."
        )

        section_label(content, "Installation Folder")
        body_label(content,
            f"Setup will install {APP_SHORT_NAME} into the following folder.\n"
            "To install in a different folder, click Browse.", muted=True)

        dest_frame = tk.Frame(content, bg=BODY_BG)
        dest_frame.pack(fill=tk.X, pady=(0, 16))

        ent = tk.Entry(
            dest_frame, textvariable=install_path_var,
            font=("Segoe UI", 8), bd=1, relief="solid",
            bg=CARD_BG, fg=TEXT_DARK, insertbackground=TEXT_DARK
        )
        ent.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 8))

        def browse():
            chosen = filedialog.askdirectory(initialdir=install_path_var.get())
            if chosen:
                install_path_var.set(chosen)

        tk.Button(
            dest_frame, text="Browse…", command=browse,
            font=("Segoe UI", 8), bg=CARD_BG, fg=TEXT_MID,
            relief="solid", bd=1, cursor="hand2", padx=8, pady=4
        ).pack(side=tk.RIGHT)

        tk.Frame(content, bg=BORDER_CLR, height=1).pack(fill=tk.X, pady=(4, 12))

        section_label(content, "Additional Shortcuts")
        styled_check(content, "Create a Desktop shortcut", shortcut_desktop)
        styled_check(content, "Create a Start Menu shortcut", shortcut_start)

        tk.Frame(content, bg=BORDER_CLR, height=1).pack(fill=tk.X, pady=(12, 8))
        body_label(content, "At least 250 MB of free disk space is required.", muted=True)

        btn_back.config(state=tk.NORMAL, command=lambda: go_to(1))
        btn_next.config(text="Install  →", state=tk.NORMAL, command=start_installation)

    # ─────────────────────────────────────────────────────────────────────────
    # Step 3 — Installing (progress)
    # ─────────────────────────────────────────────────────────────────────────
    def start_installation():
        clear_content()
        update_steps(3)
        set_header(
            "Installing CALIBRA Metrology Workstation…",
            "Please wait while files are extracted and configured."
        )

        body_label(content, "Setup is now installing the application…", muted=True)

        # Status label
        status_lbl = tk.Label(
            content, text="Preparing…",
            font=("Segoe UI", 8), fg=ACCENT, bg=BODY_BG, anchor="w"
        )
        status_lbl.pack(anchor="w", pady=(4, 8))

        # Progress bar
        prog = ttk.Progressbar(
            content, orient="horizontal",
            length=460, mode="determinate",
            style="Calibra.Horizontal.TProgressbar"
        )
        prog.pack(anchor="w", pady=(0, 16))

        # Animated status indicator area
        detail_lbl = tk.Label(
            content, text="", font=("Consolas", 7),
            fg=TEXT_MUTED, bg=BODY_BG, anchor="w"
        )
        detail_lbl.pack(anchor="w")

        btn_back.config(state=tk.DISABLED)
        btn_next.config(state=tk.DISABLED)
        btn_cancel.config(state=tk.DISABLED)

        def update_progress(pct, msg):
            root.after(0, lambda: (
                prog.config(value=pct),
                status_lbl.config(text=msg),
                detail_lbl.config(text=f"[{pct:>3}%] {msg}")
            ))

        def worker():
            nonlocal installed_exe
            target = Path(install_path_var.get())
            try:
                installed_exe = perform_install(
                    target, shortcut_desktop.get(), shortcut_start.get(),
                    progress_callback=update_progress
                )
                root.after(0, show_finished)
            except Exception as ex:
                root.after(0, lambda: (
                    btn_cancel.config(state=tk.NORMAL),
                    messagebox.showerror("Installation Error", str(ex))
                ))

        threading.Thread(target=worker, daemon=True).start()

    # ─────────────────────────────────────────────────────────────────────────
    # Step 4 — Complete
    # ─────────────────────────────────────────────────────────────────────────
    def show_finished():
        clear_content()
        update_steps(4)
        set_header(
            f"Setup Complete",
            f"{APP_NAME} v{APP_VERSION} has been installed successfully."
        )

        # Success message card
        cf = tk.Frame(content, bg="#F0FDF4", bd=1, relief="solid")
        cf.pack(fill=tk.X, pady=(0, 16))
        inner = tk.Frame(cf, bg="#F0FDF4", padx=16, pady=12)
        inner.pack(fill=tk.X)
        tk.Label(inner, text="✓  Installation Successful",
                 font=("Segoe UI", 10, "bold"), fg=SUCCESS_CLR, bg="#F0FDF4").pack(anchor="w")
        tk.Label(inner,
                 text=f"{APP_NAME} is ready to use.\n"
                      "Shortcuts have been created per your selections.",
                 font=("Segoe UI", 8), fg="#166534", bg="#F0FDF4",
                 justify="left").pack(anchor="w", pady=(4, 0))

        tk.Frame(content, bg=BORDER_CLR, height=1).pack(fill=tk.X, pady=(0, 12))

        styled_check(content, f"Launch {APP_SHORT_NAME} now", launch_app_var)

        body_label(content, "Click  Finish  to exit the Setup Wizard.", muted=True)

        btn_back.config(state=tk.DISABLED)
        btn_cancel.config(state=tk.DISABLED)
        btn_next.config(state=tk.NORMAL, text="Finish", command=finish)

    def finish():
        if launch_app_var.get() and installed_exe and installed_exe.exists():
            args = [str(installed_exe), "--demo" if IS_DEMO else "--pro"]
            subprocess.Popen(args, creationflags=0x08000000)
        root.destroy()

    # ── Navigation ────────────────────────────────────────────────────────────
    def go_to(step):
        current_step.set(step)
        {0: show_welcome, 1: show_eula, 2: show_destination}[step]()

    # ── Bootstrap ─────────────────────────────────────────────────────────────
    show_welcome()
    root.mainloop()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if "/S" in sys.argv or "--silent" in sys.argv or "-s" in sys.argv:
        t_dir = get_default_install_dir()
        exe = perform_install(t_dir, desktop_shortcut=True, start_shortcut=True)
        if "--launch" in sys.argv and exe.exists():
            args = [str(exe), "--demo" if IS_DEMO else "--pro"]
            subprocess.Popen(args, creationflags=0x08000000)
    else:
        run_gui_wizard()
