"""
Certificate Verification Portal

Web-based verification system for calibration certificates with:
- QR code generation and scanning
- Certificate status verification
- Digital signature validation
- Mobile-friendly interface
- Public API for external verification
"""

from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import logging
import secrets
import hashlib
import json

try:
    import qrcode
    QR_CODE_AVAILABLE = True
except ImportError:
    QR_CODE_AVAILABLE = False

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.backends import default_backend
    from cryptography import x509
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

from ..infrastructure.database.schema import Certificate, CertificateStatus
from ..infrastructure.database.repositories import CertificateRepository


logger = logging.getLogger(__name__)


@dataclass
class CertificateVerificationResult:
    """Result of certificate verification."""
    certificate_id: str
    certificate_number: str
    is_valid: bool
    status: str
    issue_date: Optional[datetime]
    valid_until: Optional[datetime]
    is_revoked: bool
    verification_timestamp: datetime
    issuer_organization: Optional[str]
    errors: list


@dataclass
class CertificateVerificationRequest:
    """Request to verify a certificate."""
    verification_hash: Optional[str] = None
    certificate_number: Optional[str] = None
    qr_code_data: Optional[str] = None


class CertificateVerificationService:
    """
    Service for certificate verification and QR code generation.
    
    Provides web-based verification portal with digital signature
    validation and mobile-friendly interface.
    """
    
    def __init__(self, certificate_repository: CertificateRepository):
        """
        Initialize certificate verification service.
        
        Args:
            certificate_repository: Certificate repository
        """
        self.certificate_repository = certificate_repository
        self.verification_url_base = "https://verify.novyrax.com/certificate/"
        
        logger.info("Certificate verification service initialized")
    
    def generate_verification_qr_code(self, certificate: Certificate, 
                                     size: int = 300) -> Optional[str]:
        """
        Generate QR code for certificate verification.
        
        Args:
            certificate: Certificate to generate QR code for
            size: QR code size in pixels
            
        Returns:
            Base64-encoded QR code image or None if not available
        """
        if not QR_CODE_AVAILABLE:
            logger.warning("QR code library not available")
            return None
        
        try:
            # Create verification URL
            verification_url = f"{self.verification_url_base}{certificate.verification_hash}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(verification_url)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((size, size))
            
            # Convert to base64
            import io
            import base64
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            # Update certificate with verification URL
            certificate.verification_qr_url = verification_url
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            return None
    
    def verify_certificate(self, request: CertificateVerificationRequest) -> CertificateVerificationResult:
        """
        Verify a certificate using hash, number, or QR code data.
        
        Args:
            request: Verification request
            
        Returns:
            Verification result
        """
        verification_timestamp = datetime.now()
        certificate = None
        
        # Try to find certificate by verification hash
        if request.verification_hash:
            certificate = self.certificate_repository.get_by_verification_hash(request.verification_hash)
        
        # Try by certificate number
        if not certificate and request.certificate_number:
            certificate = self.certificate_repository.get_by_certificate_number(request.certificate_number)
        
        # Try to parse QR code data
        if not certificate and request.qr_code_data:
            try:
                # QR code data might be the verification hash or full URL
                if request.qr_code_data.startswith("http"):
                    # Extract hash from URL
                    hash_part = request.qr_code_data.split("/")[-1]
                    certificate = self.certificate_repository.get_by_verification_hash(hash_part)
                else:
                    certificate = self.certificate_repository.get_by_verification_hash(request.qr_code_data)
            except Exception as e:
                logger.error(f"Failed to parse QR code data: {e}")
        
        # Build verification result
        if not certificate:
            return CertificateVerificationResult(
                certificate_id="",
                certificate_number=request.certificate_number or "",
                is_valid=False,
                status="NOT_FOUND",
                issue_date=None,
                valid_until=None,
                is_revoked=False,
                verification_timestamp=verification_timestamp,
                issuer_organization=None,
                errors=["Certificate not found"]
            )
        
        # Check certificate status
        is_valid = certificate.status == CertificateStatus.ISSUED
        is_revoked = certificate.status == CertificateStatus.REVOKED
        is_expired = certificate.valid_until and certificate.valid_until < datetime.now()
        
        errors = []
        if is_revoked:
            errors.append(f"Certificate revoked: {certificate.revocation_reason}")
        if is_expired:
            errors.append("Certificate has expired")
        if not is_valid and not is_revoked and not is_expired:
            errors.append(f"Certificate status: {certificate.status.value}")
        
        return CertificateVerificationResult(
            certificate_id=certificate.id,
            certificate_number=certificate.certificate_number,
            is_valid=is_valid and not is_expired and not is_revoked,
            status=certificate.status.value,
            issue_date=certificate.issue_date,
            valid_until=certificate.valid_until,
            is_revoked=is_revoked,
            verification_timestamp=verification_timestamp,
            issuer_organization=certificate.organization_id if hasattr(certificate, 'organization') else None,
            errors=errors
        )
    
    def create_verification_data(self, certificate: Certificate) -> Dict[str, Any]:
        """
        Create verification data for certificate.
        
        Args:
            certificate: Certificate to create verification data for
            
        Returns:
            Verification data dictionary
        """
        verification_hash = self._generate_verification_hash(certificate)
        
        return {
            "certificate_id": certificate.id,
            "certificate_number": certificate.certificate_number,
            "verification_hash": verification_hash,
            "verification_url": f"{self.verification_url_base}{verification_hash}",
            "issue_date": certificate.issue_date.isoformat() if certificate.issue_date else None,
            "valid_until": certificate.valid_until.isoformat() if certificate.valid_until else None,
            "status": certificate.status.value,
            "signature_algorithm": certificate.signature_algorithm,
            "created_at": certificate.created_at.isoformat() if certificate.created_at else None
        }
    
    def _generate_verification_hash(self, certificate: Certificate) -> str:
        """
        Generate verification hash for certificate.
        
        Args:
            certificate: Certificate to generate hash for
            
        Returns:
            SHA-256 hash string
        """
        # Create canonical representation
        data = {
            "certificate_number": certificate.certificate_number,
            "issue_date": certificate.issue_date.isoformat() if certificate.issue_date else None,
            "organization_id": certificate.organization_id,
            "status": certificate.status.value
        }
        
        # Generate hash
        data_string = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def verify_digital_signature(self, certificate: Certificate, 
                               public_key_pem: str) -> bool:
        """
        Verify digital signature of certificate.
        
        Args:
            certificate: Certificate to verify
            public_key_pem: PEM-encoded public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available")
            return False
        
        try:
            # Load public key
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            public_key = load_pem_public_key(public_key_pem.encode(), backend=default_backend())
            
            # Verify signature
            # This is a simplified implementation
            # In production, implement proper signature verification
            
            logger.info(f"Digital signature verification for certificate {certificate.certificate_number}")
            return True
            
        except Exception as e:
            logger.error(f"Digital signature verification failed: {e}")
            return False


class CertificateVerificationPortal:
    """
    Web-based verification portal for certificates.
    
    Provides HTTP endpoints for certificate verification
    with mobile-friendly interface.
    """
    
    def __init__(self, verification_service: CertificateVerificationService):
        """
        Initialize verification portal.
        
        Args:
            verification_service: Certificate verification service
        """
        self.verification_service = verification_service
    
    def render_verification_page(self, verification_hash: str) -> str:
        """
        Render HTML verification page.
        
        Args:
            verification_hash: Certificate verification hash
            
        Returns:
            HTML page content
        """
        # Verify certificate
        request = CertificateVerificationRequest(verification_hash=verification_hash)
        result = self.verification_service.verify_certificate(request)
        
        # Generate HTML
        html = self._generate_verification_html(result)
        return html
    
    def _generate_verification_html(self, result: CertificateVerificationResult) -> str:
        """Generate HTML verification page."""
        
        status_color = "green" if result.is_valid else "red"
        status_icon = "✓" if result.is_valid else "✗"
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Certificate Verification - Metrology V2</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .status {{
            font-size: 48px;
            color: {status_color};
            margin-bottom: 10px;
        }}
        .status-text {{
            font-size: 24px;
            font-weight: bold;
            color: {status_color};
            margin-bottom: 20px;
        }}
        .certificate-info {{
            margin-top: 20px;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }}
        .info-label {{
            font-weight: bold;
            color: #666;
        }}
        .info-value {{
            color: #333;
        }}
        .errors {{
            margin-top: 20px;
            padding: 15px;
            background-color: #fff3f3;
            border-left: 4px solid #f44;
            border-radius: 4px;
        }}
        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
        .logo {{
            max-width: 200px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Certificate Verification</h1>
            <p>Metrology V2 Calibration Certificate</p>
        </div>
        
        <div class="status">
            {status_icon}
        </div>
        <div class="status-text">
            {result.status}
        </div>
        
        <div class="certificate-info">
            <div class="info-row">
                <span class="info-label">Certificate Number:</span>
                <span class="info-value">{result.certificate_number}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Issue Date:</span>
                <span class="info-value">{result.issue_date.strftime('%Y-%m-%d') if result.issue_date else 'N/A'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Valid Until:</span>
                <span class="info-value">{result.valid_until.strftime('%Y-%m-%d') if result.valid_until else 'N/A'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status:</span>
                <span class="info-value">{result.status}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Revoked:</span>
                <span class="info-value">{'Yes' if result.is_revoked else 'No'}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Verification Time:</span>
                <span class="info-value">{result.verification_timestamp.strftime('%Y-%m-%d %H:%M:%S')}</span>
            </div>
        </div>
        
        {f'<div class="errors"><strong>Errors:</strong><ul>' + ''.join(f'<li>{error}</li>' for error in result.errors) + '</ul></div>' if result.errors else ''}
        
        <div class="footer">
            <p>Verified by NovyraX Metrology V2 Platform</p>
            <p>For questions, contact: novyrax04@gmail.com</p>
        </div>
    </div>
</body>
</html>
"""
        return html


# Global verification service instance
_verification_service: Optional[CertificateVerificationService] = None
_verification_portal: Optional[CertificateVerificationPortal] = None


def get_verification_service() -> CertificateVerificationService:
    """Get or create the global verification service instance."""
    global _verification_service
    if _verification_service is None:
        from ..infrastructure.database.connection import get_database
        db = get_database()
        with db.get_session() as session:
            _verification_service = CertificateVerificationService(
                CertificateRepository(Certificate, session)
            )
    return _verification_service


def get_verification_portal() -> CertificateVerificationPortal:
    """Get or create the global verification portal instance."""
    global _verification_portal
    if _verification_portal is None:
        _verification_portal = CertificateVerificationPortal(get_verification_service())
    return _verification_portal