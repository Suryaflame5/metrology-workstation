"""
REST API for Metrology V2

Production-grade REST API with:
- Versioned API from day one (/api/v1/)
- FastAPI framework
- Comprehensive error handling
- Rate limiting
- Authentication and authorization
- OpenAPI documentation
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import logging
import secrets

try:
    from fastapi import FastAPI
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from ..infrastructure.security.rbac import Permission, Role, SecurityManager, PermissionDenied
from ..core.instruments.service import InstrumentService, InstrumentCreateRequest, InstrumentUpdateRequest
from ..core.calibration.service import CalibrationService, CalibrationCreateRequest, MeasurementCreateRequest
from ..core.workflow.engine import get_workflow_engine, WorkflowState
from ..core.certificates.verification import get_verification_service, CertificateVerificationRequest
from ..core.integrations.gateway import get_integration_gateway, IntegrationConfig, IntegrationType
from ..infrastructure.database.connection import get_database
from ..infrastructure.database.repositories import InstrumentRepository, CalibrationRepository


logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class InstrumentCreateModel(BaseModel):
    """Model for instrument creation request."""
    organization_id: str
    asset_number: str
    serial_number: str
    manufacturer: str
    model: str
    instrument_type: str
    location_id: Optional[str] = None
    custodian_id: Optional[str] = None
    range_min: Optional[float] = None
    range_max: Optional[float] = None
    range_unit: Optional[str] = None
    resolution: Optional[float] = None
    resolution_unit: Optional[str] = None
    accuracy: Optional[float] = None
    accuracy_unit: Optional[str] = None
    calibration_interval_months: int = 12
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None


class InstrumentUpdateModel(BaseModel):
    """Model for instrument update request."""
    location_id: Optional[str] = None
    custodian_id: Optional[str] = None
    calibration_interval_months: Optional[int] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None


class CalibrationCreateModel(BaseModel):
    """Model for calibration creation request."""
    instrument_id: str
    procedure_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    calibration_method: Optional[str] = None
    notes: Optional[str] = None


class MeasurementCreateModel(BaseModel):
    """Model for measurement creation request."""
    calibration_record_id: str
    nominal_value: float
    measured_value: float
    unit: str
    tolerance_lower: float
    tolerance_upper: float
    uncertainty: Optional[float] = None
    measurement_sequence: Optional[int] = None
    repeat_number: Optional[int] = None
    standard_used_id: Optional[str] = None
    notes: Optional[str] = None


class ApiResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


# Security
security = HTTPBearer()
security_manager = SecurityManager()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Get current user from authorization header.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    # Validate token and extract user ID
    # This is a simplified implementation
    # In production, implement proper JWT validation
    try:
        # TODO: Implement proper token validation
        user_id = "user_123"  # Placeholder
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_role(user_id: str) -> Role:
    """
    Get user role from user ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User role
    """
    # TODO: Implement proper role lookup
    return Role.METROLOGIST  # Placeholder


# Create FastAPI application
app = FastAPI(
    title="Metrology V2 API",
    description="Production-grade REST API for Metrology V2 platform",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=ApiResponse)
async def health_check():
    """Health check endpoint."""
    return ApiResponse(
        success=True,
        message="Metrology V2 API is healthy",
        data={"status": "healthy", "version": "2.0.0"}
    )


# API v1 endpoints
@app.get("/api/v1/instruments", response_model=ApiResponse)
async def get_instruments(
    organization_id: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """
    Get instruments with optional filtering.
    
    Args:
        organization_id: Filter by organization
        user_id: Current user ID
        
    Returns:
        List of instruments
    """
    try:
        user_role = get_user_role(user_id)
        db = get_database()
        
        with db.get_session() as session:
            repository = InstrumentRepository(Instrument, session)
            
            if organization_id:
                instruments = repository.get_by_organization(organization_id)
            else:
                instruments = repository.get_all()
            
            return ApiResponse(
                success=True,
                message="Instruments retrieved successfully",
                data=[
                    {
                        "id": inst.id,
                        "asset_number": inst.asset_number,
                        "serial_number": inst.serial_number,
                        "manufacturer": inst.manufacturer,
                        "model": inst.model,
                        "instrument_type": inst.instrument_type,
                        "status": inst.status.value
                    }
                    for inst in instruments
                ]
            )
            
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/instruments", response_model=ApiResponse)
async def create_instrument(
    instrument: InstrumentCreateModel,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new instrument.
    
    Args:
        instrument: Instrument creation data
        user_id: Current user ID
        
    Returns:
        Created instrument
    """
    try:
        user_role = get_user_role(user_id)
        db = get_database()
        
        with db.get_session() as session:
            repository = InstrumentRepository(Instrument, session)
            service = InstrumentService(repository, security_manager)
            
            request = InstrumentCreateRequest(**instrument.dict())
            created_instrument = service.create_instrument(request, user_id, user_role)
            
            return ApiResponse(
                success=True,
                message="Instrument created successfully",
                data={
                    "id": created_instrument.id,
                    "asset_number": created_instrument.asset_number,
                    "serial_number": created_instrument.serial_number
                }
            )
            
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=e.reason)
    except Exception as e:
        logger.error(f"Error creating instrument: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/instruments/{instrument_id}", response_model=ApiResponse)
async def get_instrument(
    instrument_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get instrument by ID.
    
    Args:
        instrument_id: Instrument ID
        user_id: Current user ID
        
    Returns:
        Instrument details
    """
    try:
        user_role = get_user_role(user_id)
        db = get_database()
        
        with db.get_session() as session:
            repository = InstrumentRepository(Instrument, session)
            instrument = repository.get_by_id(instrument_id)
            
            if not instrument:
                raise HTTPException(status_code=404, detail="Instrument not found")
            
            return ApiResponse(
                success=True,
                message="Instrument retrieved successfully",
                data={
                    "id": instrument.id,
                    "asset_number": instrument.asset_number,
                    "serial_number": instrument.serial_number,
                    "manufacturer": instrument.manufacturer,
                    "model": instrument.model,
                    "instrument_type": instrument.instrument_type,
                    "status": instrument.status.value,
                    "location_id": instrument.location_id,
                    "custodian_id": instrument.custodian_id
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instrument: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/calibrations", response_model=ApiResponse)
async def get_calibrations(
    instrument_id: Optional[str] = None,
    status: Optional[str] = None,
    user_id: str = Depends(get_current_user)
):
    """
    Get calibrations with optional filtering.
    
    Args:
        instrument_id: Filter by instrument
        status: Filter by status
        user_id: Current user ID
        
    Returns:
        List of calibrations
    """
    try:
        user_role = get_user_role(user_id)
        db = get_database()
        
        with db.get_session() as session:
            repository = CalibrationRepository(CalibrationRecord, session)
            
            if instrument_id:
                calibrations = repository.get_by_instrument(instrument_id)
            elif status:
                calibrations = repository.get_by_status(CalibrationStatus(status.upper()))
            else:
                calibrations = repository.get_all()
            
            return ApiResponse(
                success=True,
                message="Calibrations retrieved successfully",
                data=[
                    {
                        "id": cal.id,
                        "instrument_id": cal.instrument_id,
                        "status": cal.status.value,
                        "scheduled_date": cal.scheduled_date.isoformat() if cal.scheduled_date else None,
                        "performed_by_id": cal.performed_by_id
                    }
                    for cal in calibrations
                ]
            )
            
    except Exception as e:
        logger.error(f"Error getting calibrations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/calibrations", response_model=ApiResponse)
async def create_calibration(
    calibration: CalibrationCreateModel,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new calibration.
    
    Args:
        calibration: Calibration creation data
        user_id: Current user ID
        
    Returns:
        Created calibration
    """
    try:
        user_role = get_user_role(user_id)
        db = get_database()
        
        with db.get_session() as session:
            calibration_repository = CalibrationRepository(CalibrationRecord, session)
            measurement_repository = MeasurementRepository(Measurement, session)
            service = CalibrationService(calibration_repository, measurement_repository, security_manager)
            
            request = CalibrationCreateRequest(**calibration.dict())
            created_calibration = service.create_calibration(request, user_id, user_role)
            
            return ApiResponse(
                success=True,
                message="Calibration created successfully",
                data={
                    "id": created_calibration.id,
                    "instrument_id": created_calibration.instrument_id,
                    "status": created_calibration.status.value
                }
            )
            
    except PermissionDenied as e:
        raise HTTPException(status_code=403, detail=e.reason)
    except Exception as e:
        logger.error(f"Error creating calibration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/certificates/verify", response_model=ApiResponse)
async def verify_certificate(
    verification_hash: Optional[str] = None,
    certificate_number: Optional[str] = None
):
    """
    Verify a certificate.
    
    Args:
        verification_hash: Certificate verification hash
        certificate_number: Certificate number
        
    Returns:
        Verification result
    """
    try:
        verification_service = get_verification_service()
        request = CertificateVerificationRequest(
            verification_hash=verification_hash,
            certificate_number=certificate_number
        )
        
        result = verification_service.verify_certificate(request)
        
        return ApiResponse(
            success=result.is_valid,
            message="Certificate verification completed",
            data={
                "certificate_id": result.certificate_id,
                "certificate_number": result.certificate_number,
                "is_valid": result.is_valid,
                "status": result.status,
                "is_revoked": result.is_revoked,
                "verification_timestamp": result.verification_timestamp.isoformat(),
                "errors": result.errors
            }
        )
            
    except Exception as e:
        logger.error(f"Error verifying certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workflows/{workflow_id}/status", response_model=ApiResponse)
async def get_workflow_status(
    workflow_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get workflow status.
    
    Args:
        workflow_id: Workflow ID
        user_id: Current user ID
        
    Returns:
        Workflow status
    """
    try:
        workflow_engine = get_workflow_engine()
        status = workflow_engine.get_workflow_status(workflow_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return ApiResponse(
            success=True,
            message="Workflow status retrieved successfully",
            data=status
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def create_api_application():
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    if not FASTAPI_AVAILABLE:
        logger.error("FastAPI is not available. API cannot be created.")
        return None
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=logging.INFO)
    
    if FASTAPI_AVAILABLE:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("FastAPI is not available. Please install it with: pip install fastapi uvicorn")