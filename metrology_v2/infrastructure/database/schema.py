"""
Metrology V2 Database Schema

Production-grade PostgreSQL schema following the architectural principle:
Organizations → Instruments → Calibrations → Measurements → Standards → Certificates

Key architectural decisions:
- Immutable measurement history (never silently update historical data)
- Centralized audit event ledger
- Proper foreign key relationships for traceability chain
- Separation of metadata and large objects
- Comprehensive indexing for performance
"""

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, Enum as SQLEnum, Numeric, CheckConstraint,
    Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
import enum


Base = declarative_base()


class OrganizationStatus(enum.Enum):
    """Organization status."""
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class InstrumentStatus(enum.Enum):
    """Instrument lifecycle status."""
    ACTIVE = "ACTIVE"
    CALIBRATION_DUE = "CALIBRATION_DUE"
    MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    RETIRED = "RETIRED"
    LOST = "LOST"


class CalibrationStatus(enum.Enum):
    """Calibration workflow status."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    MEASUREMENT_COMPLETE = "MEASUREMENT_COMPLETE"
    REVIEW_PENDING = "REVIEW_PENDING"
    APPROVED = "APPROVED"
    CERTIFICATE_ISSUED = "CERTIFICATE_ISSUED"
    REJECTED = "REJECTED"
    OOT = "OUT_OF_TOLERANCE"


class CertificateStatus(enum.Enum):
    """Certificate status."""
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class UserRole(enum.Enum):
    """User roles with RBAC."""
    SYSTEM_ADMINISTRATOR = "SYSTEM_ADMINISTRATOR"
    METROLOGIST = "METROLOGIST"
    TECHNICIAN = "TECHNICIAN"
    QUALITY_MANAGER = "QUALITY_MANAGER"
    LABORATORY_MANAGER = "LABORATORY_MANAGER"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


# ============================================
# ORGANIZATION & IDENTITY DOMAIN
# ============================================

class Organization(Base):
    """Organization/tenant information."""
    __tablename__ = 'organizations'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    status = Column(SQLEnum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)
    accreditation_number = Column(String(100))
    accreditation_body = Column(String(255))
    address = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    logo_url = Column(String(500))
    settings = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    locations = relationship("Location", back_populates="organization")
    instruments = relationship("Instrument", back_populates="organization")


class User(Base):
    """User accounts with RBAC."""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    mfa_secret = Column(String(255))
    mfa_enabled = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    permissions = relationship("UserPermission", back_populates="user")
    performed_calibrations = relationship("CalibrationRecord", foreign_keys="['performed_by_id']")
    reviewed_calibrations = relationship("CalibrationRecord", foreign_keys="['reviewed_by_id']")


class Location(Base):
    """Physical locations for instrument tracking."""
    __tablename__ = 'locations'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    department = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="locations")
    instruments = relationship("Instrument", back_populates="location")


class Permission(Base):
    """System permissions for RBAC."""
    __tablename__ = 'permissions'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserPermission(Base):
    """User permission assignments."""
    __tablename__ = 'user_permissions'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    permission_id = Column(String(36), ForeignKey('permissions.id'), nullable=False)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    granted_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Relationships
    user = relationship("User", back_populates="permissions", foreign_keys=[user_id])
    permission = relationship("Permission")


# ============================================
# INSTRUMENT DOMAIN
# ============================================

class Instrument(Base):
    """Instrument master records."""
    __tablename__ = 'instruments'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'), nullable=False)
    location_id = Column(String(36), ForeignKey('locations.id'))
    custodian_id = Column(String(36), ForeignKey('users.id'))
    
    # Identification
    asset_number = Column(String(50), unique=True, nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    manufacturer = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    instrument_type = Column(String(100), nullable=False)
    
    # Technical specifications
    range_min = Column(Float)
    range_max = Column(Float)
    range_unit = Column(String(20))
    resolution = Column(Float)
    resolution_unit = Column(String(20))
    accuracy = Column(Float)
    accuracy_unit = Column(String(20))
    
    # Calibration requirements
    calibration_interval_months = Column(Integer, default=12)
    last_calibration_date = Column(DateTime(timezone=True))
    next_calibration_date = Column(DateTime(timezone=True))
    
    # Status and lifecycle
    status = Column(SQLEnum(InstrumentStatus), default=InstrumentStatus.ACTIVE, nullable=False)
    purchase_date = Column(DateTime(timezone=True))
    purchase_cost = Column(Numeric(10, 2))
    retirement_date = Column(DateTime(timezone=True))
    
    # Additional information
    description = Column(Text)
    specifications = Column(JSON)
    photo_url = Column(String(500))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Relationships
    organization = relationship("Organization", back_populates="instruments")
    location = relationship("Location", back_populates="instruments")
    calibration_records = relationship("CalibrationRecord", back_populates="instrument")
    maintenance_records = relationship("MaintenanceRecord", back_populates="instrument")
    lifecycle_events = relationship("InstrumentLifecycleEvent", back_populates="instrument")
    
    # Indexes
    __table_args__ = (
        Index('idx_instrument_asset_number', 'asset_number'),
        Index('idx_instrument_serial_number', 'serial_number'),
        Index('idx_instrument_status', 'status'),
        Index('idx_instrument_next_calibration', 'next_calibration_date'),
    )


class InstrumentLifecycleEvent(Base):
    """Instrument lifecycle events for audit trail."""
    __tablename__ = 'instrument_lifecycle_events'
    
    id = Column(String(36), primary_key=True)
    instrument_id = Column(String(36), ForeignKey('instruments.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # PURCHASE, TRANSFER, CALIBRATION, MAINTENANCE, RETIREMENT
    previous_status = Column(SQLEnum(InstrumentStatus))
    new_status = Column(SQLEnum(InstrumentStatus))
    previous_location_id = Column(String(36), ForeignKey('locations.id'))
    new_location_id = Column(String(36), ForeignKey('locations.id'))
    previous_custodian_id = Column(String(36), ForeignKey('users.id'))
    new_custodian_id = Column(String(36), ForeignKey('users.id'))
    reason = Column(Text)
    performed_by_id = Column(String(36), ForeignKey('users.id'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata = Column(JSON)


# ============================================
# CALIBRATION DOMAIN
# ============================================

class CalibrationProcedure(Base):
    """Calibration procedure definitions."""
    __tablename__ = 'calibration_procedures'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    procedure_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text)
    instrument_type = Column(String(100))
    steps = Column(JSON)  # Procedure steps as structured JSON
    requirements = Column(JSON)  # Environmental conditions, equipment needed
    approval_status = Column(String(20), default='DRAFT')
    approved_by_id = Column(String(36), ForeignKey('users.id'))
    approved_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CalibrationRecord(Base):
    """Calibration records - the core of the metrology system."""
    __tablename__ = 'calibration_records'
    
    id = Column(String(36), primary_key=True)
    instrument_id = Column(String(36), ForeignKey('instruments.id'), nullable=False)
    procedure_id = Column(String(36), ForeignKey('calibration_procedures.id'))
    
    # Workflow information
    status = Column(SQLEnum(CalibrationStatus), default=CalibrationStatus.DRAFT, nullable=False)
    performed_by_id = Column(String(36), ForeignKey('users.id'))
    reviewed_by_id = Column(String(36), ForeignKey('users.id'))
    approved_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Timing
    scheduled_date = Column(DateTime(timezone=True))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    approved_at = Column(DateTime(timezone=True))
    
    # Environmental conditions
    environmental_condition_id = Column(String(36), ForeignKey('environmental_conditions.id'))
    
    # Calibration method and results
    calibration_method = Column(String(100))
    overall_result = Column(String(20))  # PASS, FAIL, OOT
    uncertainty_budget_id = Column(String(36), ForeignKey('uncertainty_budgets.id'))
    certificate_id = Column(String(36), ForeignKey('certificates.id'))
    
    # Notes and documentation
    notes = Column(Text)
    deviation_notes = Column(Text)
    corrective_actions = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="calibration_records")
    procedure = relationship("CalibrationProcedure")
    environmental_condition = relationship("EnvironmentalCondition")
    uncertainty_budget = relationship("UncertaintyBudget")
    certificate = relationship("Certificate")
    measurements = relationship("Measurement", back_populates="calibration_record")
    standards_used = relationship("CalibrationStandard", back_populates="calibration_record")
    
    # Indexes
    __table_args__ = (
        Index('idx_calibration_instrument', 'instrument_id'),
        Index('idx_calibration_status', 'status'),
        Index('idx_calibration_date', 'scheduled_date'),
    )


class EnvironmentalCondition(Base):
    """Environmental conditions during calibration."""
    __tablename__ = 'environmental_conditions'
    
    id = Column(String(36), primary_key=True)
    temperature_celsius = Column(Float, nullable=False)
    temperature_tolerance = Column(Float)
    humidity_percent = Column(Float)
    humidity_tolerance = Column(Float)
    atmospheric_pressure_hpa = Column(Float)
    notes = Column(Text)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    recorded_by_id = Column(String(36), ForeignKey('users.id'))


class Measurement(Base):
    """Individual measurements - IMMUTABLE RECORDS."""
    __tablename__ = 'measurements'
    
    id = Column(String(36), primary_key=True)
    calibration_record_id = Column(String(36), ForeignKey('calibration_records.id'), nullable=False)
    
    # Measurement data
    nominal_value = Column(Float, nullable=False)
    measured_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    error = Column(Float, nullable=False)
    uncertainty = Column(Float)
    tolerance_lower = Column(Float, nullable=False)
    tolerance_upper = Column(Float, nullable=False)
    
    # Result
    result = Column(String(20), nullable=False)  # PASS, FAIL, GUARD_BAND
    
    # Operator and timing
    operator_id = Column(String(36), ForeignKey('users.id'))
    measurement_sequence = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional data
    repeat_number = Column(Integer)  # For repeated measurements
    standard_used_id = Column(String(36), ForeignKey('reference_standards.id'))
    notes = Column(Text)
    
    # Version control for immutability
    version = Column(Integer, default=1)
    previous_version_id = Column(String(36), ForeignKey('measurements.id'))
    correction_reason = Column(Text)
    corrected_by_id = Column(String(36), ForeignKey('users.id'))
    corrected_at = Column(DateTime(timezone=True))
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    calibration_record = relationship("CalibrationRecord", back_populates="measurements")
    standard_used = relationship("ReferenceStandard")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('tolerance_lower < tolerance_upper', name='check_tolerance_order'),
        Index('idx_measurement_calibration', 'calibration_record_id'),
        Index('idx_measurement_timestamp', 'timestamp'),
    )


class CalibrationStandard(Base):
    """Reference standards used in calibration."""
    __tablename__ = 'calibration_standards'
    
    id = Column(String(36), primary_key=True)
    calibration_record_id = Column(String(36), ForeignKey('calibration_records.id'), nullable=False)
    standard_id = Column(String(36), ForeignKey('reference_standards.id'), nullable=False)
    usage_notes = Column(Text)


class ReferenceStandard(Base):
    """Reference standard master records."""
    __tablename__ = 'reference_standards'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    
    # Identification
    asset_number = Column(String(50), unique=True, nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    standard_type = Column(String(100), nullable=False)  # GAUGE_BLOCK, WEIGHT, ELECTRICAL_STANDARD, etc.
    
    # Technical specifications
    accuracy = Column(Float)
    accuracy_unit = Column(String(20)
    
    # Traceability
    traceability_number = Column(String(100), nullable=False)
    traceability_chain = Column(JSON)  # Chain of traceability information
    calibration_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))
    certificate_id = Column(String(36), ForeignKey('certificates.id'))
    
    # Status
    status = Column(String(20), default='ACTIVE')
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    certificate = relationship("Certificate")


class UncertaintyBudget(Base):
    """Uncertainty budget calculations."""
    __tablename__ = 'uncertainty_budgets'
    
    id = Column(String(36), primary_key=True)
    calibration_record_id = Column(String(36), ForeignKey('calibration_records.id'))
    
    # Final results
    combined_standard_uncertainty = Column(Float, nullable=False)
    effective_degrees_of_freedom = Column(Float)
    coverage_factor_k = Column(Float, nullable=False)
    expanded_uncertainty = Column(Float, nullable=False)
    confidence_level = Column(Float, default=0.95)
    
    # Detailed budget components
    components = Column(JSON)  # Structured uncertainty components
    
    # Calculation metadata
    calculation_method = Column(String(50), default='GUM')
    calculation_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    calculated_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Relationships
    calibration_record = relationship("CalibrationRecord")


# ============================================
# CERTIFICATE DOMAIN
# ============================================

class Certificate(Base):
    """Calibration certificates."""
    __tablename__ = 'certificates'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    calibration_record_id = Column(String(36), ForeignKey('calibration_records.id'))
    
    # Certificate identification
    certificate_number = Column(String(50), unique=True, nullable=False)
    template_id = Column(String(36))
    language = Column(String(10), default='en')
    
    # Workflow
    status = Column(SQLEnum(CertificateStatus), default=CertificateStatus.DRAFT)
    draft_created_by_id = Column(String(36), ForeignKey('users.id'))
    technical_review_by_id = Column(String(36), ForeignKey('users.id'))
    approved_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Content
    issue_date = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))
    customer_name = Column(String(255))
    customer_address = Column(Text)
    purchase_order = Column(String(100))
    
    # Digital signature
    digital_signature = Column(Text)
    signature_algorithm = Column(String(50))
    signed_at = Column(DateTime(timezone=True))
    signed_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Verification
    verification_hash = Column(String(64))  # SHA-256
    verification_qr_url = Column(String(500))
    revocation_reason = Column(Text)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by_id = Column(String(36), ForeignKey('users.id'))
    
    # Storage
    pdf_path = Column(String(500))
    pdf_size_bytes = Column(Integer)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    calibration_record = relationship("CalibrationRecord")
    
    # Indexes
    __table_args__ = (
        Index('idx_certificate_number', 'certificate_number'),
        Index('idx_certificate_status', 'status'),
        Index('idx_certificate_verification', 'verification_hash'),
    )


# ============================================
# QUALITY DOMAIN
# ============================================

class DeviationRecord(Base):
    """Quality deviation records."""
    __tablename__ = 'deviation_records'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    calibration_record_id = Column(String(36), ForeignKey('calibration_records.id'))
    
    deviation_type = Column(String(50), nullable=False)  # OOT, PROCEDURE, EQUIPMENT, ENVIRONMENT
    severity = Column(String(20), nullable=False)  # CRITICAL, MAJOR, MINOR
    description = Column(Text, nullable=False)
    root_cause = Column(Text)
    immediate_action = Column(Text)
    
    # Workflow
    status = Column(String(20), default='OPEN')
    reported_by_id = Column(String(36), ForeignKey('users.id'))
    assigned_to_id = Column(String(36), ForeignKey('users.id'))
    due_date = Column(DateTime(timezone=True))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_id = Column(String(36), ForeignKey('users.id'))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CorrectiveAction(Base):
    """Corrective action records."""
    __tablename__ = 'corrective_actions'
    
    id = Column(String(36), primary_key=True)
    deviation_id = Column(String(36), ForeignKey('deviation_records.id'))
    
    action_description = Column(Text, nullable=False)
    responsible_person_id = Column(String(36), ForeignKey('users.id'))
    target_date = Column(DateTime(timezone=True))
    completion_date = Column(DateTime(timezone=True))
    effectiveness_verification = Column(Text)
    status = Column(String(20), default='PENDING')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ============================================
# MAINTENANCE DOMAIN
# ============================================

class MaintenanceRecord(Base):
    """Instrument maintenance records."""
    __tablename__ = 'maintenance_records'
    
    id = Column(String(36), primary_key=True)
    instrument_id = Column(String(36), ForeignKey('instruments.id'), nullable=False)
    
    maintenance_type = Column(String(50), nullable=False)  # PREVENTIVE, CORRECTIVE, UPGRADE
    priority = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, ROUTINE
    description = Column(Text, nullable=False)
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    performed_date = Column(DateTime(timezone=True))
    technician_id = Column(String(36), ForeignKey('users.id'))
    
    # Results
    status = Column(String(20), default='SCHEDULED')
    cost = Column(Numeric(10, 2))
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    instrument = relationship("Instrument", back_populates="maintenance_records")


# ============================================
# AUDIT DOMAIN
# ============================================

class AuditEvent(Base):
    """Centralized audit event ledger - IMMUTABLE."""
    __tablename__ = 'audit_events'
    
    id = Column(String(36), primary_key=True)
    event_id = Column(String(64), unique=True, nullable=False)  # Correlation ID
    
    # Actor information
    actor_id = Column(String(36), ForeignKey('users.id'))
    actor_type = Column(String(20))  # USER, SYSTEM, API
    actor_ip_address = Column(String(50))
    
    # Organization context
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    
    # Event details
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(36), nullable=False)
    
    # State changes
    before_state = Column(JSON)
    after_state = Column(JSON)
    reason = Column(Text)
    
    # Technical details
    application_version = Column(String(20))
    correlation_id = Column(String(64))
    request_id = Column(String(64))
    
    # Timing
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes for audit queries
    __table_args__ = (
        Index('idx_audit_actor', 'actor_id'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_organization', 'organization_id'),
        Index('idx_audit_event_id', 'event_id'),
    )


# ============================================
# STORAGE & ATTACHMENTS
# ============================================

class Attachment(Base):
    """File attachments (metadata only, files in object storage)."""
    __tablename__ = 'attachments'
    
    id = Column(String(36), primary_key=True)
    organization_id = Column(String(36), ForeignKey('organizations.id'))
    
    # File information
    entity_type = Column(String(50), nullable=False)  # INSTRUMENT, CALIBRATION, CERTIFICATE
    entity_id = Column(String(36), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size_bytes = Column(Integer)
    
    # Storage location
    storage_path = Column(String(500), nullable=False)
    storage_type = Column(String(20), default='local')  # local, s3, azure
    checksum = Column(String(64))  # SHA-256
    
    # Upload information
    uploaded_by_id = Column(String(36), ForeignKey('users.id'))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Status
    status = Column(String(20), default='ACTIVE')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


def create_database_schema(engine):
    """Create all database tables with proper ordering."""
    Base.metadata.create_all(engine)


def drop_database_schema(engine):
    """Drop all database tables (use with caution)."""
    Base.metadata.drop_all(engine)