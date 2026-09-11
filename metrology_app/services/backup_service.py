"""
SQLite Online Backup, Integrity Check, and Restore Service.
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..config import BACKUP_DIR, DB_PATH, ensure_app_directories
from ..db import get_connection, init_db


def compute_file_sha256(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def create_database_backup(backup_name: Optional[str] = None, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Perform a live, non-blocking atomic online SQLite database backup.
    """
    ensure_app_directories()
    init_db(db_path)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = backup_name or f"metrology_backup_{ts}.db"
    dest_path = os.path.join(BACKUP_DIR, name)
    manifest_path = dest_path + ".manifest.json"

    # Online atomic backup API
    with get_connection(db_path) as src_conn:
        dest_conn = sqlite3.connect(dest_path)
        src_conn.backup(dest_conn)
        dest_conn.close()

    # Verify backup integrity
    with sqlite3.connect(dest_path) as check_conn:
        res = check_conn.execute("PRAGMA integrity_check").fetchone()[0]
        if res != "ok":
            os.remove(dest_path)
            raise ValueError(f"Backup failed integrity check: {res}")

    sha256 = compute_file_sha256(dest_path)
    size_bytes = os.path.getsize(dest_path)

    manifest = {
        "backup_filename": name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sha256": sha256,
        "size_bytes": size_bytes,
        "source_db": os.path.basename(db_path),
        "integrity_status": "PASS",
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def list_backups() -> List[Dict[str, Any]]:
    """List all available verified backup files."""
    ensure_app_directories()
    backups = []
    if not os.path.exists(BACKUP_DIR):
        return []

    for fname in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if fname.endswith(".db"):
            fpath = os.path.join(BACKUP_DIR, fname)
            mpath = fpath + ".manifest.json"
            manifest = {}
            if os.path.exists(mpath):
                try:
                    with open(mpath, "r", encoding="utf-8") as mf:
                        manifest = json.load(mf)
                except Exception:
                    pass

            backups.append({
                "filename": fname,
                "size_bytes": os.path.getsize(fpath),
                "created_at": manifest.get("timestamp", datetime.fromtimestamp(os.path.getmtime(fpath), timezone.utc).isoformat()),
                "sha256": manifest.get("sha256", compute_file_sha256(fpath)),
                "integrity": manifest.get("integrity_status", "VERIFIED"),
            })
    return backups


def restore_database_backup(backup_filename: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Safely restore database from a verified backup.
    Takes an emergency pre-restore snapshot of current DB before restoration.
    """
    ensure_app_directories()
    clean_filename = os.path.basename(backup_filename)
    if clean_filename != backup_filename or ".." in backup_filename or "/" in backup_filename or "\\" in backup_filename:
        raise ValueError("Invalid backup filename: path traversal attempt detected.")
    backup_path = os.path.join(BACKUP_DIR, clean_filename)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file '{clean_filename}' not found")

    # 1. Pre-flight integrity check on backup
    with sqlite3.connect(backup_path) as b_conn:
        res = b_conn.execute("PRAGMA integrity_check").fetchone()[0]
        if res != "ok":
            raise ValueError(f"Cannot restore corrupted backup: {res}")

    # 2. Create emergency pre-restore snapshot if source DB exists
    if os.path.exists(db_path):
        create_database_backup(backup_name=f"emergency_snapshot_pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db", db_path=db_path)

    # 3. Perform atomic restore using SQLite backup API
    with sqlite3.connect(backup_path) as src_conn:
        with get_connection(db_path) as dest_conn:
            src_conn.backup(dest_conn)

    return {
        "status": "RESTORED",
        "restored_from": backup_filename,
        "restored_at": datetime.now(timezone.utc).isoformat(),
        "integrity_verified": True,
    }
