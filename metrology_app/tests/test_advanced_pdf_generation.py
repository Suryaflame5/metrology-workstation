import pytest
from fastapi.testclient import TestClient
from metrology_app.server import app
from metrology_app.db import save_job, DB_PATH
from metrology_app.services.advanced_pdf_service import generate_advanced_multi_page_pdf


def test_advanced_multi_page_pdf_generation():
    client = TestClient(app)

    # 1. Create a calibration job with measurements
    job_id = save_job({
        "title": "Precision DMM 10V DC Calibration",
        "customer_name": "Accredited Metrology Lab",
        "instrument_name": "Digital Multimeter",
        "instrument_model": "Fluke 8846A",
        "instrument_serial": "SN-998822",
        "procedure_name": "EURAMET cg-15 Multimeter Calibration",
        "nominal_value": 10.0,
        "tolerance_upper": 0.001,
        "tolerance_lower": -0.001,
        "unit": "V",
        "raw_measurements": [10.000021, 9.999984, 10.000015, 9.999992, 10.000033],
        "status": "APPROVED",
    })

    # 2. Directly test generator
    pdf_bytes = generate_advanced_multi_page_pdf(job_id)
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF-")

    # 3. Test HTTP Endpoint
    res = client.get(f"/api/v1/jobs/{job_id}/advanced-certificate-pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert len(res.content) == len(pdf_bytes)
