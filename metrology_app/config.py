"""
Application Configuration and Environment Directory Management.
"""

import os
import sys
import json
import platform
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(relative_path: str) -> str:
    """Resolve bundled resource path for both development and PyInstaller runtime."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(PROJECT_ROOT, relative_path)


# Determine standard OS application data directory
if platform.system() == "Windows":
    LOCAL_APP_DATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    APP_DIR = os.path.join(LOCAL_APP_DATA, "MetrologyWorkstation")
else:
    APP_DIR = os.path.expanduser("~/.metrology_workstation")

DATA_DIR = os.path.join(APP_DIR, "data")
BACKUP_DIR = os.path.join(APP_DIR, "backups")
LOGS_DIR = os.path.join(APP_DIR, "logs")
EVIDENCE_DIR = os.path.join(APP_DIR, "evidence")
CONFIG_FILE = os.path.join(APP_DIR, "settings.json")
DB_PATH = os.path.join(DATA_DIR, "metrology_workstation.db")

# Fallback / Local mode override if explicitly requested
if os.environ.get("METROLOGY_LOCAL_DEV") == "1":
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = APP_DIR
    BACKUP_DIR = os.path.join(APP_DIR, "backups")
    LOGS_DIR = os.path.join(APP_DIR, "logs")
    EVIDENCE_DIR = os.path.join(APP_DIR, "evidence_packages")
    CONFIG_FILE = os.path.join(APP_DIR, "settings.json")
    DB_PATH = os.path.join(DATA_DIR, "metrology_data.db")


def ensure_app_directories() -> None:
    """Ensure all required application directories exist."""
    for d in [APP_DIR, DATA_DIR, BACKUP_DIR, LOGS_DIR, EVIDENCE_DIR]:
        os.makedirs(d, exist_ok=True)


DEFAULT_SETTINGS: Dict[str, Any] = {
    "laboratory_name": "Precision Metrology Reference Laboratory",
    "laboratory_code": "LAB-01",
    "accreditation_body": "ISO/IEC 17025 Conformant Laboratory",
    "certificate_prefix": "CERT-",
    "default_technician": "Lead Metrologist",
    "auto_backup_enabled": True,
    "auto_backup_interval_calibrations": 5,
    "rounding_significant_digits": 2,
    "temperature_nominal_c": 20.0,
    "first_run_completed": False,
}


def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file or return defaults."""
    ensure_app_directories()
    if not os.path.exists(CONFIG_FILE):
        save_settings(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge missing keys
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return dict(DEFAULT_SETTINGS)


def save_settings(settings_dict: Dict[str, Any]) -> None:
    """Persist settings to settings.json."""
    ensure_app_directories()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(settings_dict, f, indent=2)
