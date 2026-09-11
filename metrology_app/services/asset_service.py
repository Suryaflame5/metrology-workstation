"""
Asset Registry Service for Metrology Workstation.
Manages physical assets, customer equipment under test (DUT), barcode/QR tracking,
and calibration due lifecycle.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from ..db import (
    save_asset,
    get_asset,
    get_asset_by_tag_or_serial,
    list_assets,
    delete_asset,
    DB_PATH,
)


def register_asset(asset_payload: Dict[str, Any], db_path: str = DB_PATH) -> Dict[str, Any]:
    """Register a new asset or update an existing asset in the registry."""
    if not asset_payload.get("serial_number"):
        raise ValueError("serial_number is required for asset registration.")
    if not asset_payload.get("manufacturer") or not asset_payload.get("model"):
        raise ValueError("manufacturer and model are required for asset registration.")

    # Calculate next_calibration_due if not provided
    interval_days = int(asset_payload.get("calibration_interval_days", 365))
    last_cal = asset_payload.get("last_calibration_date")
    if not last_cal:
        last_cal = datetime.now(timezone.utc).date().isoformat()
        asset_payload["last_calibration_date"] = last_cal

    if not asset_payload.get("next_calibration_due"):
        try:
            last_dt = datetime.fromisoformat(last_cal)
            next_due = (last_dt + timedelta(days=interval_days)).date().isoformat()
            asset_payload["next_calibration_due"] = next_due
        except Exception:
            pass

    return save_asset(asset_payload, db_path=db_path)


def get_asset_details(asset_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Get full asset details including computed calibration status."""
    asset = get_asset(asset_id, db_path=db_path)
    if not asset:
        return None
    return _compute_asset_health(asset)


def scan_and_identify_asset(barcode_or_identifier: str, db_path: str = DB_PATH) -> Dict[str, Any]:
    """
    Lookup an asset by scanned barcode, QR code string, asset tag, or serial number.
    Format examples:
      - Raw serial: 'MY53201482'
      - Asset tag: 'TAG-2026-0042'
      - Metrology QR: 'METRO:ASSET:ASSET-001:SN-1234'
    """
    clean_id = barcode_or_identifier.strip()
    if clean_id.startswith("METRO:ASSET:"):
        parts = clean_id.split(":")
        if len(parts) >= 3:
            clean_id = parts[2]  # asset_id

    asset = get_asset_by_tag_or_serial(clean_id, db_path=db_path)
    if not asset:
        asset = get_asset(clean_id, db_path=db_path)

    if not asset:
        return {
            "found": False,
            "query": barcode_or_identifier,
            "message": f"No asset found matching identifier '{barcode_or_identifier}'.",
        }

    enriched = _compute_asset_health(asset)
    return {
        "found": True,
        "query": barcode_or_identifier,
        "asset": enriched,
    }


def list_all_assets(status: Optional[str] = None, customer_id: Optional[str] = None, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """List assets with health evaluation."""
    raw = list_assets(status=status, customer_id=customer_id, db_path=db_path)
    return [_compute_asset_health(a) for a in raw]


def update_asset_after_calibration(
    asset_id: str,
    calibration_date: str,
    certificate_id: str,
    conformance_status: str,
    db_path: str = DB_PATH,
) -> Dict[str, Any]:
    """Update asset calibration dates and status following a completed calibration job."""
    asset = get_asset(asset_id, db_path=db_path)
    if not asset:
        raise ValueError(f"Asset '{asset_id}' not found.")

    interval_days = int(asset.get("calibration_interval_days", 365))
    clean_date = calibration_date.replace("Z", "+00:00")
    cal_dt = datetime.fromisoformat(clean_date)
    next_due = (cal_dt + timedelta(days=interval_days)).date().isoformat()

    status = "IN_SERVICE" if conformance_status == "PASS" else "QUARANTINED"
    meta = asset.get("metadata", {})
    history = meta.get("calibration_history", [])
    history.append({
        "calibration_date": calibration_date,
        "certificate_id": certificate_id,
        "conformance": conformance_status,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    })
    meta["calibration_history"] = history
    meta["last_certificate_id"] = certificate_id

    asset["last_calibration_date"] = calibration_date[:10]
    asset["next_calibration_due"] = next_due
    asset["status"] = status
    asset["metadata"] = meta

    return save_asset(asset, db_path=db_path)


def _compute_asset_health(asset: Dict[str, Any]) -> Dict[str, Any]:
    """Compute days until calibration due and alert flags."""
    enriched = dict(asset)
    next_due_str = asset.get("next_calibration_due")
    if next_due_str:
        try:
            today = datetime.now(timezone.utc).date()
            due_dt = datetime.fromisoformat(next_due_str[:10]).date()
            days_remaining = (due_dt - today).days
            enriched["days_until_due"] = days_remaining
            if days_remaining < 0:
                enriched["calibration_health"] = "OVERDUE"
            elif days_remaining <= 30:
                enriched["calibration_health"] = "EXPIRING_SOON"
            else:
                enriched["calibration_health"] = "COMPLIANT"
        except Exception:
            enriched["days_until_due"] = 999
            enriched["calibration_health"] = "UNKNOWN"
    else:
        enriched["days_until_due"] = 999
        enriched["calibration_health"] = "NOT_SCHEDULED"
    return enriched
