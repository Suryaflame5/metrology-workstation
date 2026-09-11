# Laboratory Metrology Workstation — REST API Reference

**API Version:** v1 / v8  
**Base URL:** `http://localhost:8000`  
**Compliance Standard:** OpenAPI 3.1 / RFC 7807  
**Content-Type:** `application/json` (unless multipart upload specified)

---

## 1. Overview & Security Headers

All HTTP responses emitted by the Metrology Workstation FastAPI service include enterprise security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

## 2. Jobs API

### `GET /api/jobs`
List all calibration jobs.
- **Query Parameters:**
  - `status` (optional, string): Filter by status (`SCHEDULED`, `RUNNING`, `COMPLETED`, `APPROVED`, `REJECTED`).
  - `limit` (optional, integer): Maximum records to return (default 50).
- **Response `200 OK`:**
  ```json
  [
    {
      "id": "JOB-2026-0910-01",
      "asset_id": "AST-5522A",
      "procedure_id": "PROC-ELEC-001",
      "technician_id": "TECH-001",
      "status": "COMPLETED",
      "created_at": "2026-09-10T08:00:00Z",
      "due_date": "2026-09-15T00:00:00Z",
      "measurements_count": 12
    }
  ]
  ```

### `POST /api/jobs`
Create a new calibration job.
- **Request Body:**
  ```json
  {
    "asset_id": "AST-5522A",
    "procedure_id": "PROC-ELEC-001",
    "technician_id": "TECH-001",
    "due_date": "2026-09-15T00:00:00Z",
    "notes": "Annual routine verification"
  }
  ```
- **Response `201 Created`:** Returns created Job object.

### `GET /api/jobs/{job_id}`
Retrieve full state of a specific calibration job, including embedded measurements, uncertainty budget, and conformity decision.

### `POST /api/jobs/{job_id}/sign`
Apply 21 CFR Part 11 compliant electronic signature.
- **Request Body:**
  ```json
  {
    "signer_name": "Dr. Jane Doe",
    "signer_role": "LEAD_METROLOGIST",
    "reason": "Approved for Calibration Certificate Release",
    "credential_token": "<auth_token>"
  }
  ```
- **Response `200 OK`:**
  ```json
  {
    "job_id": "JOB-2026-0910-01",
    "signature_id": "SIG-984210",
    "signed_at": "2026-09-10T14:30:00Z",
    "signature_hash": "a6f4e19d...",
    "status": "APPROVED"
  }
  ```

### `GET /api/v1/jobs/{job_id}/advanced-certificate-pdf`
Download the publication-ready 4-page ISO/IEC 17025 PDF Calibration Certificate with dynamic "Page X of Y" pagination, full measurement tables, GUM budget breakdown, and dual signature blocks.
- **Response `200 OK`:** Binary stream `application/pdf`.

### `GET /api/jobs/{job_id}/dcc`
Download machine-readable PTB Digital Calibration Certificate (DCC v3.3.0) XML.
- **Response `200 OK`:** `application/xml`.

---

## 3. Universal Importer & Excel Ingestion API

### `POST /api/v1/import/upload-file`
Multipart upload endpoint for `.xlsx`, `.xls`, and `.csv` files.
- **Content-Type:** `multipart/form-data`
- **Form Data:**
  - `file`: UploadFile binary stream
- **Response `200 OK`:**
  ```json
  {
    "status": "success",
    "filename": "gauge_run.xlsx",
    "sheets": ["Sheet1", "Data_Raw"],
    "sheet_count": 2,
    "sample_rows": [
      {"Nominal": 10.0, "Observed": 10.002, "Tolerance": 0.005}
    ],
    "columns": ["Nominal", "Observed", "Tolerance"],
    "detected_roles": {
      "nominal": "Nominal",
      "reading": "Observed",
      "tolerance": "Tolerance"
    }
  }
  ```

### `POST /api/v1/import/parse`
Parse specific sheets or custom re-mapped columns into standardized metrology measurement records.

---

## 4. Projects Lifecycle API

### `GET /api/v1/projects`
List metrology projects.
- **Query Parameters:** `status` (optional: `DRAFT`, `PLANNING`, `IN_PROGRESS`, `REVIEW`, `COMPLETED`, `ARCHIVED`).

### `POST /api/v1/projects`
Create a new metrology project container.
- **Request Body:**
  ```json
  {
    "name": "Q3 Transducer Batch Qualification",
    "client": "AeroSpace Defense Corp",
    "description": "Full calibration campaign for 20 pressure sensors",
    "due_date": "2026-10-31T23:59:59Z",
    "target_jobs": 20
  }
  ```

### `GET /api/v1/projects/{project_id}`
Retrieve project metrics, completion percentage, linked jobs, and milestone progress.

### `PATCH /api/v1/projects/{project_id}/status`
Update project lifecycle state.
- **Request Body:** `{"status": "IN_PROGRESS"}`

### `POST /api/v1/projects/{project_id}/link-job/{job_id}`
Associate an existing calibration job with the project.

---

## 5. Instruments & Hardware Bus API

### `GET /api/v8/instruments`
List all registered instruments (GPIB, VISA, USB, Serial, LXI, Simulated).

### `POST /api/v8/instruments/{instrument_id}/connect`
Establish session with target instrument via VISA or native socket.

### `POST /api/v8/instruments/{instrument_id}/query`
Execute a raw SCPI command and retrieve response.
- **Request Body:** `{"command": "*IDN?"}`
- **Response `200 OK`:**
  ```json
  {
    "command": "*IDN?",
    "response": "HEWLETT-PACKARD,3458A,0,9.2",
    "latency_ms": 14.2,
    "timestamp": "2026-09-10T14:45:00Z"
  }
  ```

---

## 6. Exception Center API

### `GET /api/v8/exceptions`
Retrieve all open, triaged, and resolved laboratory incidents.
- **Query Parameters:** `status` (`OPEN`, `TRIAGED`, `RESOLVED`), `severity` (`CRITICAL`, `WARNING`, `INFO`).

### `POST /api/v8/exceptions/{exception_id}/resolve`
Resolve an exception with technical justification.
- **Request Body:**
  ```json
  {
    "disposition": "ADJUST_AND_REMEASURE",
    "notes": "Re-zeroed pre-amplifier. Verification points re-run within specification."
  }
  ```

---

## 7. Security & Backup API

### `POST /api/backups/create`
Generate a full database snapshot archive with SHA-256 integrity verification.

### `POST /api/backups/restore`
Restore system database from verified backup. Protected against path traversal.
- **Request Body:** `{"filename": "backup_2026_09_10.db"}`
