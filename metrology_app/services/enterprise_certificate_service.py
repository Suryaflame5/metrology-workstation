"""
Enterprise Certificate Generation System for Premium Edition.

Provides professional ISO 17025 compliant certificate generation with digital signatures,
batch processing, custom branding, multi-language support, and high-quality PDF output.
"""

import uuid
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from enum import Enum
import base64
import hashlib

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

from ..db import get_calculation, DB_PATH
from ..config import ensure_app_directories, EVIDENCE_DIR, PROJECT_ROOT


class CertificateTemplate(Enum):
    """Standard certificate templates."""
    ISO_17025_STANDARD = "ISO_17025_STANDARD"
    ANSI_Z540_3 = "ANSI_Z540_3"
    CUSTOM_LABORATORY = "CUSTOM_LABORATORY"
    DIMENSIONAL_CALIBRATION = "DIMENSIONAL_CALIBRATION"
    ELECTRICAL_CALIBRATION = "ELECTRICAL_CALIBRATION"
    TEMPERATURE_CALIBRATION = "TEMPERATURE_CALIBRATION"


class CertificateLanguage(Enum):
    """Supported certificate languages."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"


class CertificateStatus(Enum):
    """Certificate processing status."""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    SIGNED = "SIGNED"
    APPROVED = "APPROVED"
    REVOKED = "REVOKED"


class EnterpriseCertificateService:
    """
    Enterprise-grade certificate generation system with professional templates,
    digital signatures, batch processing, and multi-language support.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._init_certificate_database()
        self._load_templates()
        self._load_branding()
    
    def _init_certificate_database(self):
        """Initialize certificate database schema."""
        ensure_app_directories()
        
        cert_db_path = os.path.join(os.path.dirname(self.db_path), "metrology_certificates.db")
        
        import sqlite3
        conn = sqlite3.connect(cert_db_path)
        cursor = conn.cursor()
        
        # Certificates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id TEXT PRIMARY KEY,
                certificate_number TEXT UNIQUE NOT NULL,
                calculation_id TEXT NOT NULL,
                instrument_id TEXT,
                template_type TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                status TEXT NOT NULL,
                issue_date TEXT NOT NULL,
                valid_until TEXT,
                issued_by TEXT,
                approved_by TEXT,
                digital_signature TEXT,
                signature_algorithm TEXT,
                pdf_path TEXT,
                pdf_hash TEXT,
                customer_name TEXT,
                customer_address TEXT,
                purchase_order TEXT,
                custom_fields TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (calculation_id) REFERENCES calculations(id)
            )
        """)
        
        # Certificate templates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificate_templates (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                template_config TEXT NOT NULL,
                logo_path TEXT,
                is_custom BOOLEAN DEFAULT 0,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Branding configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branding_config (
                id TEXT PRIMARY KEY,
                laboratory_name TEXT NOT NULL,
                laboratory_address TEXT,
                laboratory_phone TEXT,
                laboratory_email TEXT,
                laboratory_website TEXT,
                accreditation_number TEXT,
                logo_path TEXT,
                logo_data TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                font_family TEXT,
                certificate_footer TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Digital certificates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS digital_certificates (
                id TEXT PRIMARY KEY,
                certificate_name TEXT UNIQUE NOT NULL,
                certificate_data TEXT NOT NULL,
                private_key_data TEXT NOT NULL,
                key_algorithm TEXT,
                valid_from TEXT NOT NULL,
                valid_until TEXT NOT NULL,
                issuer TEXT,
                purpose TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_templates(self):
        """Load default certificate templates."""
        self.default_templates = {
            CertificateTemplate.ISO_17025_STANDARD.value: {
                "name": "ISO 17025 Standard Certificate",
                "description": "Standard ISO/IEC 17025 compliant calibration certificate",
                "layout": "standard",
                "sections": ["header", "customer_info", "instrument_info", "calibration_data", "results", "signatures", "footer"],
                "required_fields": ["laboratory_name", "accreditation_body", "certificate_number", "issue_date"]
            },
            CertificateTemplate.ANSI_Z540_3.value: {
                "name": "ANSI Z540.3 Certificate",
                "description": "ANSI/NCSL Z540.3 compliant certificate with Method 6 guardbanding",
                "layout": "standard",
                "sections": ["header", "customer_info", "instrument_info", "calibration_data", "decision_analysis", "signatures", "footer"],
                "required_fields": ["laboratory_name", "decision_rule", "tur_analysis"]
            },
            CertificateTemplate.DIMENSIONAL_CALIBRATION.value: {
                "name": "Dimensional Calibration Certificate",
                "description": "Specialized certificate for dimensional metrology instruments",
                "layout": "dimensional",
                "sections": ["header", "customer_info", "instrument_info", "environmental_conditions", "calibration_points", "uncertainty_budget", "signatures", "footer"],
                "required_fields": ["temperature", "humidity", "environmental_notes"]
            }
        }
    
    def _load_branding(self):
        """Load or create default branding configuration."""
        import sqlite3
        cert_db_path = os.path.join(os.path.dirname(self.db_path), "metrology_certificates.db")
        conn = sqlite3.connect(cert_db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM branding_config LIMIT 1")
        branding = cursor.fetchone()
        
        if branding:
            columns = [desc[0] for desc in cursor.description]
            self.branding = dict(zip(columns, branding))
        else:
            # Create default branding
            default_branding = {
                "id": "BRAND-DEFAULT",
                "laboratory_name": "Precision Metrology Reference Laboratory",
                "laboratory_address": "123 Science Park Drive\nMetropolis, ST 12345",
                "laboratory_phone": "+1 (555) 123-4567",
                "laboratory_email": "calibration@laboratory.com",
                "laboratory_website": "https://www.laboratory.com",
                "accreditation_number": "ISO/IEC 17025:2017 • LAB-001",
                "logo_path": None,
                "logo_data": None,
                "primary_color": "#2C3E50",
                "secondary_color": "#3498DB",
                "font_family": "Helvetica",
                "certificate_footer": "This certificate is based on measurements traceable to the International System of Units (SI).",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            cursor.execute("""
                INSERT INTO branding_config (
                    id, laboratory_name, laboratory_address, laboratory_phone, laboratory_email,
                    laboratory_website, accreditation_number, logo_path, logo_data, primary_color,
                    secondary_color, font_family, certificate_footer, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                default_branding["id"], default_branding["laboratory_name"], 
                default_branding["laboratory_address"], default_branding["laboratory_phone"],
                default_branding["laboratory_email"], default_branding["laboratory_website"],
                default_branding["accreditation_number"], default_branding["logo_path"],
                default_branding["logo_data"], default_branding["primary_color"],
                default_branding["secondary_color"], default_branding["font_family"],
                default_branding["certificate_footer"], default_branding["created_at"],
                default_branding["updated_at"]
            ))
            
            conn.commit()
            self.branding = default_branding
        
        conn.close()
    
    def _get_cert_db_path(self) -> str:
        """Get the certificate database path."""
        return os.path.join(os.path.dirname(self.db_path), "metrology_certificates.db")
    
    def create_certificate(self, calculation_id: str, template_type: str,
                          customer_info: Dict[str, Any], 
                          language: str = "en",
                          custom_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new certificate from a calculation record.
        """
        # Get calculation data
        calculation = get_calculation(calculation_id, db_path=self.db_path)
        if not calculation:
            raise ValueError(f"Calculation {calculation_id} not found")
        
        # Generate certificate number
        cert_number = self._generate_certificate_number()
        certificate_id = f"CERT-{str(uuid.uuid4().int)[:8]}"
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Calculate validity (typically 1 year from issue)
        valid_until = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
        
        # Prepare certificate record
        certificate_record = {
            "id": certificate_id,
            "certificate_number": cert_number,
            "calculation_id": calculation_id,
            "instrument_id": calculation.get("instrument_id"),
            "template_type": template_type,
            "language": language,
            "status": CertificateStatus.DRAFT.value,
            "issue_date": now,
            "valid_until": valid_until,
            "issued_by": self.branding["laboratory_name"],
            "approved_by": None,
            "digital_signature": None,
            "signature_algorithm": None,
            "pdf_path": None,
            "pdf_hash": None,
            "customer_name": customer_info.get("name", ""),
            "customer_address": customer_info.get("address", ""),
            "purchase_order": customer_info.get("purchase_order", ""),
            "custom_fields": json.dumps(custom_fields or {}),
            "created_at": now,
            "updated_at": now
        }
        
        # Save to database
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO certificates (
                id, certificate_number, calculation_id, instrument_id, template_type, language,
                status, issue_date, valid_until, issued_by, approved_by, digital_signature,
                signature_algorithm, pdf_path, pdf_hash, customer_name, customer_address,
                purchase_order, custom_fields, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            certificate_record["id"], certificate_record["certificate_number"],
            certificate_record["calculation_id"], certificate_record["instrument_id"],
            certificate_record["template_type"], certificate_record["language"],
            certificate_record["status"], certificate_record["issue_date"],
            certificate_record["valid_until"], certificate_record["issued_by"],
            certificate_record["approved_by"], certificate_record["digital_signature"],
            certificate_record["signature_algorithm"], certificate_record["pdf_path"],
            certificate_record["pdf_hash"], certificate_record["customer_name"],
            certificate_record["customer_address"], certificate_record["purchase_order"],
            certificate_record["custom_fields"], certificate_record["created_at"],
            certificate_record["updated_at"]
        ))
        
        conn.commit()
        conn.close()
        
        return certificate_record
    
    def _generate_certificate_number(self) -> str:
        """Generate a unique certificate number."""
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        year = datetime.now().year
        cursor.execute("""
            SELECT COUNT(*) FROM certificates 
            WHERE certificate_number LIKE ?
        """, (f"CAL-{year}-%",))
        
        count = cursor.fetchone()[0] + 1
        conn.close()
        
        return f"CAL-{year}-{count:05d}"
    
    def generate_pdf_certificate(self, certificate_id: str) -> Dict[str, Any]:
        """
        Generate PDF certificate using ReportLab.
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab is required for PDF generation. Install with: pip install reportlab")
        
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
        cert_row = cursor.fetchone()
        
        if not cert_row:
            conn.close()
            raise ValueError(f"Certificate {certificate_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        certificate = dict(zip(columns, cert_row))
        conn.close()
        
        # Get calculation data
        calculation = get_calculation(certificate["calculation_id"], db_path=self.db_path)
        
        # Generate PDF
        ensure_app_directories()
        pdf_filename = f"{certificate['certificate_number']}.pdf"
        pdf_path = os.path.join(EVIDENCE_DIR, pdf_filename)
        
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor(self.branding["primary_color"]),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(self.branding["secondary_color"]),
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        # Header section
        story.append(Paragraph(self.branding["laboratory_name"], title_style))
        story.append(Paragraph(self.branding["laboratory_address"], styles["Normal"]))
        story.append(Paragraph(f"{self.branding['laboratory_phone']} | {self.branding['laboratory_email']}", styles["Normal"]))
        story.append(Spacer(1, 0.2*inch))
        
        # Certificate title
        story.append(Paragraph("CALIBRATION CERTIFICATE", title_style))
        story.append(Paragraph(f"Certificate No: {certificate['certificate_number']}", styles["Normal"]))
        story.append(Paragraph(f"Issue Date: {certificate['issue_date'][:10]}", styles["Normal"]))
        story.append(Spacer(1, 0.3*inch))
        
        # Customer information
        story.append(Paragraph("Customer Information", header_style))
        customer_data = [
            ["Customer Name:", certificate["customer_name"] or "N/A"],
            ["Address:", certificate["customer_address"] or "N/A"],
            ["Purchase Order:", certificate["purchase_order"] or "N/A"]
        ]
        customer_table = Table(customer_data, colWidths=[2*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.branding["secondary_color"])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(customer_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Instrument information
        story.append(Paragraph("Instrument Information", header_style))
        instrument_data = [
            ["Instrument Name:", calculation["instrument_name"]],
            ["Model:", calculation.get("instrument_model", "N/A")],
            ["Procedure:", calculation["procedure_name"]],
            ["Procedure Version:", calculation["procedure_version"]]
        ]
        instrument_table = Table(instrument_data, colWidths=[2*inch, 4*inch])
        instrument_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.branding["secondary_color"])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(instrument_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Calibration results
        story.append(Paragraph("Calibration Results", header_style))
        result_data = calculation["result_data"]
        decision_summary = result_data.get("decision_summary", {})
        uncertainty_summary = result_data.get("uncertainty_summary", {})
        
        results_data = [
            ["Nominal Value:", f"{decision_summary.get('nominal_mm', 'N/A')} mm"],
            ["Measured Mean:", f"{decision_summary.get('mean_measured_mm', 'N/A')} mm"],
            ["Error of Indication:", f"{decision_summary.get('error_of_indication_mm', 'N/A')} mm"],
            ["Expanded Uncertainty (k=2):", f"{uncertainty_summary.get('expanded_uncertainty_U95_mm', 'N/A')} mm"],
            ["Decision Rule:", calculation.get("decision_rule", "N/A")],
            ["Conformity Verdict:", calculation.get("conformity_verdict", "N/A")]
        ]
        
        results_table = Table(results_data, colWidths=[2.5*inch, 3.5*inch])
        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(self.branding["secondary_color"])),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(results_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Uncertainty budget
        story.append(Paragraph("Uncertainty Budget", header_style))
        budget_rows = uncertainty_summary.get("budget_rows", [])
        if budget_rows:
            budget_data = [["Component", "Type", "Std Uncertainty", "Sensitivity", "% Contribution"]]
            for row in budget_rows[:10]:  # Limit to top 10 for space
                budget_data.append([
                    row.get("label", ""),
                    row.get("component_type", ""),
                    row.get("standard_uncertainty_mm", ""),
                    row.get("sensitivity_coefficient", ""),
                    row.get("percentage_contribution", "")
                ])
            
            budget_table = Table(budget_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 0.8*inch, 0.9*inch])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.branding["primary_color"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(budget_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        # Accreditation statement
        story.append(Paragraph(self.branding["accreditation_number"], styles["Normal"]))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph(self.branding["certificate_footer"], styles["Normal"]))
        
        # Check if unwatermarked certificates are authorized
        from .license_service import EntitlementService
        is_unwatermarked = EntitlementService.is_feature_authorized(
            "UNWATERMARKED_CERTIFICATES", db_path=self.db_path
        )

        def _draw_evaluation_watermark(canvas, doc_obj):
            canvas.saveState()
            canvas.setFont("Helvetica-Bold", 30)
            canvas.setFillColor(colors.HexColor("#C0392B"), alpha=0.15)
            canvas.translate(A4[0] / 2.0, A4[1] / 2.0)
            canvas.rotate(45)
            canvas.drawCentredString(0, 30, "COMMUNITY EVALUATION COPY")
            canvas.setFont("Helvetica-Bold", 13)
            canvas.drawCentredString(0, 0, "NOT VALID FOR ACCREDITED CALIBRATION USE")
            canvas.setFont("Helvetica", 9)
            canvas.drawCentredString(0, -25, "Licensed for evaluation only. Commercial & accreditation use prohibited.")
            canvas.restoreState()

            # Prominent warning top banner
            canvas.saveState()
            canvas.setFillColor(colors.HexColor("#FDEDEC"))
            canvas.rect(0, A4[1] - 26, A4[0], 26, fill=True, stroke=False)
            canvas.setStrokeColor(colors.HexColor("#E74C3C"))
            canvas.setLineWidth(1)
            canvas.line(0, A4[1] - 26, A4[0], A4[1] - 26)
            canvas.setFont("Helvetica-Bold", 8.5)
            canvas.setFillColor(colors.HexColor("#C0392B"))
            canvas.drawCentredString(A4[0] / 2.0, A4[1] - 17, "COMMUNITY EVALUATION COPY — NOT VALID FOR ACCREDITED CALIBRATION USE")
            canvas.restoreState()

        # Build PDF
        if not is_unwatermarked:
            doc.build(story, onFirstPage=_draw_evaluation_watermark, onLaterPages=_draw_evaluation_watermark)
        else:
            doc.build(story)
        
        # Calculate PDF hash
        with open(pdf_path, 'rb') as f:
            pdf_hash = hashlib.sha256(f.read()).hexdigest()
        
        # Update certificate record
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE certificates 
            SET pdf_path = ?, pdf_hash = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (pdf_path, pdf_hash, CertificateStatus.GENERATED.value, now, certificate_id))
        
        conn.commit()
        conn.close()
        
        return {
            "certificate_id": certificate_id,
            "pdf_path": pdf_path,
            "pdf_hash": pdf_hash,
            "status": CertificateStatus.GENERATED.value
        }

    def generate_pdf_for_calculation(self, calculation_id: str) -> bytes:
        """Generate and return PDF bytes directly for a calculation record."""
        calc = get_calculation(calculation_id, db_path=self.db_path)
        if not calc:
            repo_db = os.path.join(PROJECT_ROOT, "metrology_data.db")
            if os.path.exists(repo_db):
                calc = get_calculation(calculation_id, db_path=repo_db)
                if calc:
                    self.db_path = repo_db
                    self._init_certificate_database()
        else:
            self._init_certificate_database()
        if not calc:
            raise ValueError(f"Calculation record '{calculation_id}' not found")

        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT id, pdf_path FROM certificates WHERE calculation_id = ?", (calculation_id,))
        row = cursor.fetchone()
        conn.close()

        if row and row[1] and os.path.exists(row[1]):
            with open(row[1], "rb") as f:
                return f.read()

        if row:
            cert_id = row[0]
        else:
            cert = self.create_certificate(
                calculation_id=calculation_id,
                template_type=CertificateTemplate.ISO_17025_STANDARD.value,
                customer_info={"name": "Accredited Laboratory Client", "address": "Quality Engineering Facility", "purchase_order": "PO-CAL-2026"},
            )
            cert_id = cert["id"]

        gen_res = self.generate_pdf_certificate(cert_id)
        with open(gen_res["pdf_path"], "rb") as f:
            return f.read()
    
    def sign_certificate(self, certificate_id: str, digital_cert_id: str) -> Dict[str, Any]:
        """
        Digitally sign a certificate using X.509 certificate.
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ImportError("Cryptography library is required for digital signatures. Install with: pip install cryptography")
        
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        # Get certificate record
        cursor.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
        cert_row = cursor.fetchone()
        
        if not cert_row:
            conn.close()
            raise ValueError(f"Certificate {certificate_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        certificate = dict(zip(columns, cert_row))
        
        # Get digital certificate
        cursor.execute("SELECT * FROM digital_certificates WHERE id = ?", (digital_cert_id,))
        cert_row = cursor.fetchone()
        
        if not cert_row:
            conn.close()
            raise ValueError(f"Digital certificate {digital_cert_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        digital_cert = dict(zip(columns, cert_row))
        conn.close()
        
        # Load private key and certificate
        private_key = serialization.load_pem_private_key(
            digital_cert["private_key_data"].encode(),
            password=None,
            backend=default_backend()
        )
        
        cert = x509.load_pem_x509_certificate(
            digital_cert["certificate_data"].encode(),
            default_backend()
        )
        
        # Sign the PDF hash
        if not certificate["pdf_hash"]:
            raise ValueError("Certificate must have PDF generated before signing")
        
        signature = private_key.sign(
            certificate["pdf_hash"].encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Encode signature
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        
        # Update certificate record
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE certificates 
            SET digital_signature = ?, signature_algorithm = ?, status = ?, updated_at = ?
            WHERE id = ?
        """, (signature_b64, "RSA-PSS-SHA256", CertificateStatus.SIGNED.value, now, certificate_id))
        
        conn.commit()
        conn.close()
        
        return {
            "certificate_id": certificate_id,
            "signature_algorithm": "RSA-PSS-SHA256",
            "signed_by": digital_cert["certificate_name"],
            "status": CertificateStatus.SIGNED.value
        }
    
    def batch_generate_certificates(self, calculation_ids: List[str], 
                                   template_type: str,
                                   customer_info: Dict[str, Any],
                                   language: str = "en") -> List[Dict[str, Any]]:
        """
        Batch generate certificates for multiple calculations.
        """
        results = []
        
        for calc_id in calculation_ids:
            try:
                # Create certificate
                cert = self.create_certificate(calc_id, template_type, customer_info, language)
                
                # Generate PDF
                pdf_result = self.generate_pdf_certificate(cert["id"])
                
                results.append({
                    "calculation_id": calc_id,
                    "certificate_id": cert["id"],
                    "certificate_number": cert["certificate_number"],
                    "status": "SUCCESS",
                    "pdf_path": pdf_result["pdf_path"]
                })
            except Exception as e:
                results.append({
                    "calculation_id": calc_id,
                    "status": "FAILED",
                    "error": str(e)
                })
        
        return results
    
    def update_branding(self, branding_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update laboratory branding configuration."""
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Check if branding exists
        cursor.execute("SELECT id FROM branding_config LIMIT 1")
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            update_fields = []
            update_values = []
            
            for key, value in branding_config.items():
                if key in ["laboratory_name", "laboratory_address", "laboratory_phone", 
                          "laboratory_email", "laboratory_website", "accreditation_number",
                          "logo_path", "primary_color", "secondary_color", "font_family",
                          "certificate_footer"]:
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            update_fields.append("updated_at = ?")
            update_values.append(now)
            update_values.append(existing[0])
            
            cursor.execute(f"""
                UPDATE branding_config 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, update_values)
        else:
            # Create new
            branding_id = f"BRAND-{str(uuid.uuid4().int)[:8]}"
            cursor.execute("""
                INSERT INTO branding_config (
                    id, laboratory_name, laboratory_address, laboratory_phone, laboratory_email,
                    laboratory_website, accreditation_number, logo_path, primary_color,
                    secondary_color, font_family, certificate_footer, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                branding_id, branding_config.get("laboratory_name", ""),
                branding_config.get("laboratory_address", ""),
                branding_config.get("laboratory_phone", ""),
                branding_config.get("laboratory_email", ""),
                branding_config.get("laboratory_website", ""),
                branding_config.get("accreditation_number", ""),
                branding_config.get("logo_path", ""),
                branding_config.get("primary_color", "#2C3E50"),
                branding_config.get("secondary_color", "#3498DB"),
                branding_config.get("font_family", "Helvetica"),
                branding_config.get("certificate_footer", ""),
                now, now
            ))
        
        conn.commit()
        conn.close()
        
        # Reload branding
        self._load_branding()
        
        return self.branding
    
    def get_certificate(self, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve certificate details."""
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM certificates WHERE id = ?", (certificate_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            certificate = dict(zip(columns, row))
            
            # Parse JSON fields
            if certificate.get('custom_fields'):
                certificate['custom_fields'] = json.loads(certificate['custom_fields'])
            
            return certificate
        
        return None
    
    def list_certificates(self, status: Optional[str] = None, 
                        instrument_id: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """List certificates with optional filtering."""
        import sqlite3
        conn = sqlite3.connect(self._get_cert_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM certificates WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if instrument_id:
            query += " AND instrument_id = ?"
            params.append(instrument_id)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        certificates = [dict(zip(columns, row)) for row in rows]
        
        # Parse JSON fields
        for certificate in certificates:
            if certificate.get('custom_fields'):
                certificate['custom_fields'] = json.loads(certificate['custom_fields'])
        
        conn.close()
        return certificates


# Singleton instance for service layer
_certificate_service = None

def get_certificate_service(db_path: Optional[str] = None) -> EnterpriseCertificateService:
    """Get or create the certificate service singleton."""
    global _certificate_service
    if _certificate_service is None:
        _certificate_service = EnterpriseCertificateService(db_path)
    return _certificate_service

# Convenience functions for common operations
def create_certificate(calculation_id: str, template_type: str, customer_info: Dict[str, Any],
                      language: str = "en", custom_fields: Optional[Dict[str, Any]] = None,
                      db_path: Optional[str] = None) -> Dict[str, Any]:
    """Create a new certificate."""
    service = get_certificate_service(db_path)
    return service.create_certificate(calculation_id, template_type, customer_info, language, custom_fields)

def generate_pdf_certificate(certificate_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Generate PDF for a certificate."""
    service = get_certificate_service(db_path)
    return service.generate_pdf_certificate(certificate_id)

def batch_generate_certificates(calculation_ids: List[str], template_type: str,
                               customer_info: Dict[str, Any], language: str = "en",
                               db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Batch generate certificates."""
    service = get_certificate_service(db_path)
    return service.batch_generate_certificates(calculation_ids, template_type, customer_info, language)

def update_branding(branding_config: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """Update laboratory branding."""
    service = get_certificate_service(db_path)
    return service.update_branding(branding_config)

def generate_pdf_for_calculation(calculation_id: str, db_path: Optional[str] = None) -> bytes:
    """Generate and return PDF bytes directly for a given calculation ID."""
    service = get_certificate_service(db_path)
    return service.generate_pdf_for_calculation(calculation_id)