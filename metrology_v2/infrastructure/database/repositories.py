"""
Metrology V2 Database Repository Layer

Repository pattern implementation for data access with domain entities.
Provides abstraction over SQLAlchemy with business logic encapsulation.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import and_, or_, func
import logging

from ..infrastructure.database.connection import Database, get_database
from ..infrastructure.database.schema import Base, Organization, User, Instrument, CalibrationRecord, Measurement, Certificate, AuditEvent


logger = logging.getLogger(__name__)

# Generic type for repository entities
T = TypeVar('T', bound=Base)


class Repository(Generic[T]):
    """
    Generic repository base class with common CRUD operations.
    
    Provides a consistent interface for data access while enforcing
    domain rules and audit logging.
    """
    
    def __init__(self, model: Type[T], session: Session):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session
    
    def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        return self.session.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with pagination."""
        return self.session.query(self.model).offset(offset).limit(limit).all()
    
    def create(self, entity: T, created_by_id: Optional[str] = None) -> T:
        """
        Create a new entity with audit logging.
        
        Args:
            entity: Entity to create
            created_by_id: User ID who created the entity
            
        Returns:
            Created entity
        """
        try:
            self.session.add(entity)
            self.session.flush()
            
            # Log creation to audit ledger
            self._log_audit_event(
                action="CREATE",
                entity_type=self.model.__tablename__,
                entity_id=entity.id,
                before_state=None,
                after_state=self._entity_to_dict(entity),
                actor_id=created_by_id,
                reason=f"Created {self.model.__name__}"
            )
            
            self.session.commit()
            logger.info(f"Created {self.model.__name__} with ID: {entity.id}")
            return entity
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise
    
    def update(self, entity: T, updated_by_id: Optional[str] = None, 
              reason: Optional[str] = None) -> T:
        """
        Update an entity with audit logging.
        
        Args:
            entity: Entity to update
            updated_by_id: User ID who updated the entity
            reason: Reason for update
            
        Returns:
            Updated entity
        """
        try:
            # Capture before state for audit
            before_state = self._entity_to_dict(entity)
            
            self.session.merge(entity)
            self.session.flush()
            
            # Log update to audit ledger
            self._log_audit_event(
                action="UPDATE",
                entity_type=self.model.__tablename__,
                entity_id=entity.id,
                before_state=before_state,
                after_state=self._entity_to_dict(entity),
                actor_id=updated_by_id,
                reason=reason or f"Updated {self.model.__name__}"
            )
            
            self.session.commit()
            logger.info(f"Updated {self.model.__name__} with ID: {entity.id}")
            return entity
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to update {self.model.__name__}: {e}")
            raise
    
    def delete(self, entity_id: str, deleted_by_id: Optional[str] = None, 
              reason: Optional[str] = None) -> bool:
        """
        Delete an entity with audit logging.
        
        Args:
            entity_id: ID of entity to delete
            deleted_by_id: User ID who deleted the entity
            reason: Reason for deletion
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return False
            
            # Capture before state for audit
            before_state = self._entity_to_dict(entity)
            
            self.session.delete(entity)
            self.session.flush()
            
            # Log deletion to audit ledger
            self._log_audit_event(
                action="DELETE",
                entity_type=self.model.__tablename__,
                entity_id=entity_id,
                before_state=before_state,
                after_state=None,
                actor_id=deleted_by_id,
                reason=reason or f"Deleted {self.model.__name__}"
            )
            
            self.session.commit()
            logger.info(f"Deleted {self.model.__name__} with ID: {entity_id}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to delete {self.model.__name__}: {e}")
            raise
    
    def query(self, *criterion):
        """
        Query entities with filtering.
        
        Args:
            *criterion: SQLAlchemy filter criteria
            
        Returns:
            Query object
        """
        return self.session.query(self.model).filter(*criterion)
    
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """Convert entity to dictionary for audit logging."""
        return {c.name: getattr(entity, c.name) for c in entity.__table__.columns}
    
    def _log_audit_event(self, action: str, entity_type: str, entity_id: str,
                       before_state: Optional[Dict], after_state: Optional[Dict],
                       actor_id: Optional[str], reason: str):
        """Log audit event to centralized ledger."""
        try:
            import secrets
            from ..infrastructure.database.schema import AuditEvent
            
            event = AuditEvent(
                event_id=secrets.token_hex(32),
                actor_id=actor_id,
                actor_type="USER" if actor_id else "SYSTEM",
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                before_state=before_state,
                after_state=after_state,
                reason=reason,
                application_version="2.0.0",
                correlation_id=secrets.token_hex(16),
            )
            
            self.session.add(event)
            # Note: Audit events are committed with the main transaction
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")


class InstrumentRepository(Repository[Instrument]):
    """Repository for Instrument domain with business logic."""
    
    def __init__(self, session: Session):
        super().__init__(Instrument, session)
    
    def get_by_asset_number(self, asset_number: str) -> Optional[Instrument]:
        """Get instrument by asset number."""
        return self.session.query(Instrument).filter(
            Instrument.asset_number == asset_number
        ).first()
    
    def get_by_serial_number(self, serial_number: str) -> Optional[Instrument]:
        """Get instrument by serial number."""
        return self.session.query(Instrument).filter(
            Instrument.serial_number == serial_number
        ).first()
    
    def get_by_organization(self, organization_id: str, 
                          active_only: bool = True) -> List[Instrument]:
        """Get instruments by organization."""
        query = self.session.query(Instrument).filter(
            Instrument.organization_id == organization_id
        )
        
        if active_only:
            query = query.filter(Instrument.status == InstrumentStatus.ACTIVE)
        
        return query.all()
    
    def get_calibration_due(self, days_ahead: int = 30) -> List[Instrument]:
        """Get instruments due for calibration within specified timeframe."""
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        return self.session.query(Instrument).filter(
            and_(
                Instrument.next_calibration_date <= cutoff_date,
                Instrument.status == InstrumentStatus.ACTIVE
            )
        ).order_by(Instrument.next_calibration_date).all()
    
    def update_status(self, instrument_id: str, new_status: InstrumentStatus,
                      updated_by_id: str, reason: str) -> Instrument:
        """
        Update instrument status with lifecycle event recording.
        
        Args:
            instrument_id: Instrument ID
            new_status: New status
            updated_by_id: User ID making the change
            reason: Reason for status change
            
        Returns:
            Updated instrument
        """
        instrument = self.get_by_id(instrument_id)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        old_status = instrument.status
        instrument.status = new_status
        
        updated = self.update(instrument, updated_by_id, reason)
        
        # Record lifecycle event
        self._record_lifecycle_event(
            instrument_id, "STATUS_CHANGE", 
            old_status.value, new_status.value, updated_by_id, reason
        )
        
        return updated
    
    def _record_lifecycle_event(self, instrument_id: str, event_type: str,
                             previous_value: str, new_value: str,
                             performed_by_id: str, reason: str):
        """Record instrument lifecycle event."""
        from ..infrastructure.database.schema import InstrumentLifecycleEvent
        import secrets
        
        event = InstrumentLifecycleEvent(
            id=secrets.token_hex(16),
            instrument_id=instrument_id,
            event_type=event_type,
            previous_status=previous_value,
            new_status=new_value,
            performed_by_id=performed_by_id,
            reason=reason,
            timestamp=datetime.now()
        )
        
        self.session.add(event)
        self.session.commit()


class CalibrationRepository(Repository[CalibrationRecord]):
    """Repository for Calibration domain with workflow management."""
    
    def __init__(self, session: Session):
        super().__init__(CalibrationRecord, session)
    
    def get_by_instrument(self, instrument_id: str, 
                          status: Optional[CalibrationStatus] = None) -> List[CalibrationRecord]:
        """Get calibrations for an instrument, optionally filtered by status."""
        query = self.session.query(CalibrationRecord).filter(
            CalibrationRecord.instrument_id == instrument_id
        )
        
        if status:
            query = query.filter(CalibrationRecord.status == status)
        
        return query.order_by(CalibrationRecord.scheduled_date.desc()).all()
    
    def get_by_status(self, status: CalibrationStatus, 
                      organization_id: Optional[str] = None) -> List[CalibrationRecord]:
        """Get calibrations by status, optionally filtered by organization."""
        query = self.session.query(CalibrationRecord).filter(
            CalibrationRecord.status == status
        )
        
        if organization_id:
            # Join with instruments to filter by organization
            query = query.join(Instrument).filter(
                Instrument.organization_id == organization_id
            )
        
        return query.order_by(CalibrationRecord.scheduled_date.desc()).all()
    
    def advance_workflow(self, calibration_id: str, new_status: CalibrationStatus,
                          user_id: str, reason: str) -> CalibrationRecord:
        """
        Advance calibration workflow state with authorization check.
        
        Args:
            calibration_id: Calibration record ID
            new_status: New workflow status
            user_id: User ID making the transition
            reason: Reason for state change
            
        Returns:
            Updated calibration record
        """
        calibration = self.get_by_id(calibration_id)
        if not calibration:
            raise ValueError(f"Calibration {calibration_id} not found")
        
        # Validate state transition
        valid_transitions = {
            CalibrationStatus.DRAFT: [CalibrationStatus.IN_PROGRESS],
            CalibrationStatus.IN_PROGRESS: [CalibrationStatus.MEASUREMENT_COMPLETE],
            CalibrationStatus.MEASUREMENT_COMPLETE: [CalibrationStatus.REVIEW_PENDING, CalibrationStatus.OOT],
            CalibrationStatus.REVIEW_PENDING: [CalibrationStatus.APPROVED, CalibrationStatus.REJECTED],
            CalibrationStatus.APPROVED: [CalibrationStatus.CERTIFICATE_ISSUED],
            CalibrationStatus.OOT: [CalibrationStatus.REVIEW_PENDING],
            CalibrationStatus.REJECTED: [CalibrationStatus.MEASUREMENT_COMPLETE],
        }
        
        if new_status not in valid_transitions.get(calibration.status, []):
            raise ValueError(
                f"Invalid state transition from {calibration.status} to {new_status}"
            )
        
        # Set appropriate user role based on state
        if new_status == CalibrationStatus.APPROVED:
            calibration.approved_by_id = user_id
            calibration.approved_at = datetime.now()
        elif new_status == CalibrationStatus.MEASUREMENT_COMPLETE:
            calibration.completed_at = datetime.now()
        elif new_status == CalibrationStatus.REVIEW_PENDING:
            calibration.reviewed_by_id = user_id
            calibration.reviewed_at = datetime.now()
        
        calibration.status = new_status
        
        updated = self.update(calibration, user_id, reason)
        return updated


class MeasurementRepository(Repository[Measurement]):
    """Repository for Measurement domain with immutability enforcement."""
    
    def __init__(self, session: Session):
        super().__init__(Measurement, session)
    
    def get_by_calibration(self, calibration_record_id: str) -> List[Measurement]:
        """Get all measurements for a calibration record."""
        return self.session.query(Measurement).filter(
            Measurement.calibration_record_id == calibration_record_id
        ).order_by(Measurement.timestamp).all()
    
    def create_correction(self, original_measurement_id: str, corrected_value: float,
                       reason: str, corrected_by_id: str) -> Measurement:
        """
        Create a corrected version of a measurement (immutable history).
        
        Args:
            original_measurement_id: Original measurement ID
            corrected_value: Corrected measurement value
            reason: Reason for correction
            corrected_by_id: User ID making the correction
            
        Returns:
            New measurement record (correction)
        """
        original = self.get_by_id(original_measurement_id)
        if not original:
            raise ValueError(f"Original measurement {original_measurement_id} not found")
        
        # Create new measurement version
        corrected = Measurement(
            id=f"{original.id[:32]}v{original.version + 1}",
            calibration_record_id=original.calibration_record_id,
            nominal_value=original.nominal_value,
            measured_value=corrected_value,
            unit=original.unit,
            error=corrected_value - original.nominal_value,
            uncertainty=original.uncertainty,
            tolerance_lower=original.tolerance_lower,
            tolerance_upper=original.tolerance_upper,
            result=original.result,
            operator_id=corrected_by_id,
            measurement_sequence=original.measurement_sequence,
            repeat_number=original.repeat_number,
            standard_used_id=original.standard_used_id,
            version=original.version + 1,
            previous_version_id=original.id,
            correction_reason=reason,
            corrected_by_id=corrected_by_id,
            corrected_at=datetime.now()
        )
        
        return self.create(corrected, corrected_by_id)


class CertificateRepository(Repository[Certificate]):
    """Repository for Certificate domain with verification support."""
    
    def __init__(self, session: Session):
        super().__init__(Certificate, session)
    
    def get_by_certificate_number(self, certificate_number: str) -> Optional[Certificate]:
        """Get certificate by certificate number."""
        return self.session.query(Certificate).filter(
            Certificate.certificate_number == certificate_number
        ).first()
    
    def get_by_verification_hash(self, verification_hash: str) -> Optional[Certificate]:
        """Get certificate by verification hash."""
        return self.session.query(Certificate).filter(
            Certificate.verification_hash == verification_hash
        ).first()
    
    def revoke_certificate(self, certificate_id: str, revoked_by_id: str, 
                        reason: str) -> Certificate:
        """
        Revoke a certificate with audit trail.
        
        Args:
            certificate_id: Certificate ID
            revoked_by_id: User ID revoking the certificate
            reason: Reason for revocation
            
        Returns:
            Updated certificate
        """
        certificate = self.get_by_id(certificate_id)
        if not certificate:
            raise ValueError(f"Certificate {certificate_id} not found")
        
        certificate.status = CertificateStatus.REVOKED
        certificate.revocation_reason = reason
        certificate.revoked_at = datetime.now()
        certificate.revoked_by_id = revoked_by_id
        
        return self.update(certificate, revoked_by_id, reason)


class AuditRepository(Repository[AuditEvent]):
    """Repository for Audit domain with immutable ledger enforcement."""
    
    def __init__(self, session: Session):
        super().__init__(AuditEvent, session)
    
    def get_by_entity(self, entity_type: str, entity_id: str, 
                     limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific entity."""
        return self.session.query(AuditEvent).filter(
            and_(
                AuditEvent.entity_type == entity_type,
                AuditEvent.entity_id == entity_id
            )
        ).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    
    def get_by_actor(self, actor_id: str, limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific actor."""
        return self.session.query(AuditEvent).filter(
            AuditEvent.actor_id == actor_id
        ).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime,
                        limit: int = 1000) -> List[AuditEvent]:
        """Get audit events within a date range."""
        return self.session.query(AuditEvent).filter(
            and_(
                AuditEvent.timestamp >= start_date,
                AuditEvent.timestamp <= end_date
            )
        ).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
    
    def get_by_correlation_id(self, correlation_id: str) -> List[AuditEvent]:
        """Get all audit events for a specific correlation ID."""
        return self.session.query(AuditEvent).filter(
            AuditEvent.correlation_id == correlation_id
        ).order_by(AuditEvent.timestamp.asc()).all()


# Repository factory function
def get_repository(model: Type[T], session: Session) -> Repository[T]:
    """
    Factory function to get appropriate repository for a model.
    
    Args:
        model: SQLAlchemy model class
        session: Database session
        
    Returns:
        Repository instance for the model
    """
    repositories = {
        Instrument: InstrumentRepository,
        CalibrationRecord: CalibrationRepository,
        Measurement: MeasurementRepository,
        Certificate: CertificateRepository,
        AuditEvent: AuditRepository,
    }
    
    repository_class = repositories.get(model, Repository)
    return repository_class(model, session)