"""
Hardware Acquisition & Command Audit Logger Service.
Orchestrates live instrument communication through the unified InstrumentDriver interface,
captures raw signals with millisecond timestamps, and preserves raw command/response
logs for the cryptographic Evidence Vault.
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ..industrial.instrument_driver import (
    InstrumentDriver,
    create_instrument_driver,
    HardwareCommunicationError,
)
from ..db import DB_PATH

# Global active execution trace buffer (keyed by job_id or device_id)
_HARDWARE_AUDIT_BUFFER: List[Dict[str, Any]] = []


def execute_instrument_acquisition(
    device_config: Dict[str, Any],
    count: int = 1,
    configure_params: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute standard hardware communication loop:
      1. Connect
      2. Identify (*IDN?)
      3. Configure (ranges, units, test points)
      4. Measure (capture readings + latency + raw strings)
      5. Disconnect

    Records every command and response into the hardware audit log.
    """
    driver = create_instrument_driver(device_config)
    log_entries: List[Dict[str, Any]] = []
    readings: List[Dict[str, Any]] = []
    start_time = datetime.now(timezone.utc).isoformat()
    errors: List[str] = []

    try:
        # 1. Connect
        conn_meta = driver.connect()
        _record_event(log_entries, job_id, "CONNECT", device_config.get("id", "DEV-01"), str(conn_meta))

        # 2. Identify
        idn = driver.identify()
        _record_event(log_entries, job_id, "*IDN?", device_config.get("id", "DEV-01"), idn)

        # 3. Configure
        if configure_params:
            driver.configure(configure_params)
            _record_event(log_entries, job_id, "CONFIGURE", device_config.get("id", "DEV-01"), json.dumps(configure_params))

        # 4. Measure
        for i in range(count):
            reading = driver.measure()
            readings.append(reading)
            _record_event(log_entries, job_id, "MEASURE", device_config.get("id", "DEV-01"), str(reading["raw_response"]), reading.get("latency_ms", 0.0))
            if count > 1 and i < count - 1:
                time.sleep(0.01)

        # Check errors
        errs = driver.get_errors()
        if errs and errs != ['+0,"No error"']:
            errors.extend(errs)
            _record_event(log_entries, job_id, "SYST:ERR?", device_config.get("id", "DEV-01"), "; ".join(errs))

    except Exception as e:
        err_msg = str(e)
        errors.append(err_msg)
        _record_event(log_entries, job_id, "ERROR", device_config.get("id", "DEV-01"), err_msg)
        raise HardwareCommunicationError(f"Acquisition aborted: {err_msg}")
    finally:
        # 5. Disconnect
        try:
            driver.disconnect()
            _record_event(log_entries, job_id, "DISCONNECT", device_config.get("id", "DEV-01"), "OK")
        except Exception:
            pass

    # Append to global hardware audit buffer
    _HARDWARE_AUDIT_BUFFER.extend(log_entries)

    # Compute digest of raw communications
    log_blob = json.dumps(log_entries, sort_keys=True).encode("utf-8")
    raw_hash = hashlib.sha256(log_blob).hexdigest()

    return {
        "status": "SUCCESS" if not errors else "PARTIAL_ERROR",
        "instrument_id": device_config.get("id", "DEV-UNKNOWN"),
        "instrument_identity": idn if 'idn' in locals() else "UNKNOWN",
        "readings_count": len(readings),
        "readings": readings,
        "raw_values": [r["value"] for r in readings],
        "unit": readings[0]["unit"] if readings else "V",
        "started_at": start_time,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "audit_log": log_entries,
        "hardware_evidence_sha256": raw_hash,
        "errors": errors,
    }


def get_hardware_audit_log(job_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve filtered hardware communication logs."""
    if not job_id:
        return list(_HARDWARE_AUDIT_BUFFER)
    return [e for e in _HARDWARE_AUDIT_BUFFER if e.get("job_id") == job_id]


def clear_hardware_audit_log() -> None:
    """Clear memory buffer for testing."""
    _HARDWARE_AUDIT_BUFFER.clear()


def _record_event(
    target_list: List[Dict[str, Any]],
    job_id: Optional[str],
    command: str,
    device_id: str,
    response: str,
    latency_ms: float = 0.0,
) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "job_id": job_id or "UNASSIGNED",
        "device_id": device_id,
        "command_sent": command,
        "response_received": response,
        "latency_ms": latency_ms,
    }
    target_list.append(entry)
