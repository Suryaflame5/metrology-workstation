"""
Enterprise Hardening and Security Audit Test Suite.
Verifies path traversal protection, SQL injection resilience, and HTTP security headers.
"""

import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.services.backup_service import restore_database_backup
from metrology_app.services.evidence_service import (
    export_evidence_package_directory,
    export_evidence_package_zip_bytes,
)
from metrology_app.db import list_jobs, get_job, list_calculations, get_calculation


@pytest.fixture
def client():
    return TestClient(app)


def test_http_security_headers(client):
    """Verify enterprise HTTP security headers are injected into responses."""
    response = client.get("/api/health")
    if response.status_code == 404:
        response = client.get("/api/license")

    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_backup_restore_path_traversal_prevention():
    """Verify path traversal attempts in backup restoration are rejected immediately."""
    malicious_paths = [
        "../../etc/passwd",
        r"..\..\windows\win.ini",
        "../secret_data.db",
        "sub/../../db.sqlite",
        "/root/secret.db",
    ]
    for path in malicious_paths:
        with pytest.raises(ValueError, match="path traversal"):
            restore_database_backup(path)


def test_evidence_service_path_traversal_prevention():
    """Verify path traversal in evidence export is blocked."""
    malicious_ids = [
        "../../secret_calc",
        r"..\..\calc_id",
        "sub/../../traversal",
        "/etc/calc",
    ]
    for cid in malicious_ids:
        with pytest.raises(ValueError, match="path traversal"):
            export_evidence_package_directory(cid)

        with pytest.raises(ValueError, match="path traversal"):
            export_evidence_package_zip_bytes(cid)


def test_sql_injection_resilience():
    """Verify SQL injection payloads in search and query parameters do not corrupt DB or error."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE measurement_jobs; --",
        "' UNION SELECT * FROM calculations --",
        "1'; EXEC xp_cmdshell('dir'); --",
        '" OR ""=""',
    ]
    for payload in sqli_payloads:
        # Search jobs
        jobs = list_jobs(search=payload)
        assert isinstance(jobs, list)

        # Get job with SQLi ID
        job = get_job(payload)
        assert job is None

        # Calculations
        calc = get_calculation(payload)
        assert calc is None

        calcs = list_calculations()
        assert isinstance(calcs, list)
