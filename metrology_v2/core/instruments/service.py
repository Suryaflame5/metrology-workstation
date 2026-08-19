"""
Instrument Domain Service

Business logic for instrument lifecycle management including:
- Instrument creation and validation
- Calibration scheduling
- Lifecycle management
- Status transitions
- Traceability management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import secrets

from ..infrastructure.database.schema import Instrument, InstrumentStatus, Organization, Location, User
from ..infrastructure.database.repositories import InstrumentRepository
from ..infrastructure.security.rbac import Permission, Role, SecurityManager, AuthorizationDecision


logger = logging.getLogger(__name__)


@dataclass
class InstrumentCreateRequest:
    """Request to create a new instrument."""
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


@dataclass
class InstrumentUpdateRequest:
    """Request to update an instrument."""
    location_id: Optional[str] = None
    custodian_id: Optional[str] = None
    calibration_interval_months: Optional[int] = None
    description: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    photo_url: Optional[str] = None


class InstrumentService:
    """
    Service for instrument domain business logic.
    
    Handles instrument lifecycle, calibration scheduling, and traceability
    while enforcing business rules and security policies.
    """
    
    def __init__(self, repository: InstrumentRepository, security_manager: SecurityManager):
        """
        Initialize instrument service.
        
        Args:
            repository: Instrument repository
            security_manager: Security manager for authorization
        """
        self.repository = repository
        self.security_manager = security_manager
    
    def create_instrument(self, request: InstrumentCreateRequest, 
                        created_by_id: str, user_role: Role) -> Instrument:
        """
        Create a new instrument with validation and authorization.
        
        Args:
            request: Instrument creation request
            created_by_id: User ID creating the instrument
            user_role: User role for authorization
            
        Returns:
            Created instrument
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=created_by_id,
            user_role=user_role,
            permission=Permission.INSTRUMENT_CREATE,
            resource="instrument",
            context={"request": request.__dict__}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Validate asset number uniqueness
        if self.repository.get_by_asset_number(request.asset_number):
            raise ValueError(f"Instrument with asset number {request.asset_number} already exists")
        
        # Validate serial number uniqueness
        if self.repository.get_by_serial_number(request.serial_number):
            raise ValueError(f"Instrument with serial number {request.serial_number} already exists")
        
        # Validate calibration interval
        if request.calibration_interval_months < 1 or request.calibration_interval_months > 60:
            raise ValueError("Calibration interval must be between 1 and 60 months")
        
        # Create instrument
        instrument = Instrument(
            id=secrets.token_hex(16),
            organization_id=request.organization_id,
            location_id=request.location_id,
            custodian_id=request.custodian_id,
            asset_number=request.asset_number,
            serial_number=request.serial_number,
            manufacturer=request.manufacturer,
            model=request.model,
            instrument_type=request.instrument_type,
            range_min=request.range_min,
            range_max=request.range_max,
            range_unit=request.range_unit,
            resolution=request.resolution,
            resolution_unit=request.resolution_unit,
            accuracy=request.accuracy,
            accuracy_unit=request.accuracy_unit,
            calibration_interval_months=request.calibration_interval_months,
            status=InstrumentStatus.ACTIVE,
            description=request.description,
            specifications=request.specifications,
            photo_url=request.photo_url,
            created_by_id=created_by_id
        )
        
        return self.repository.create(instrument, created_by_id)
    
    def update_instrument(self, instrument_id: str, request: InstrumentUpdateRequest,
                        updated_by_id: str, user_role: Role) -> Instrument:
        """
        Update an instrument with validation and authorization.
        
        Args:
            instrument_id: Instrument ID to update
            request: Instrument update request
            updated_by_id: User ID updating the instrument
            user_role: User role for authorization
            
        Returns:
            Updated instrument
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=updated_by_id,
            user_role=user_role,
            permission=Permission.INSTRUMENT_UPDATE,
            resource=f"instrument/{instrument_id}",
            context={"request": request.__dict__}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Get existing instrument
        instrument = self.repository.get_by_id(instrument_id)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        # Update fields
        if request.location_id is not None:
            old_location = instrument.location_id
            instrument.location_id = request.location_id
            
            # Record location change as lifecycle event
            if old_location != request.location_id:
                self._record_lifecycle_event(
                    instrument_id, "LOCATION_CHANGE",
                    old_location, request.location_id, updated_by_id,
                    "Instrument location updated"
                )
        
        if request.custodian_id is not None:
            old_custodian = instrument.custodian_id
            instrument.custodian_id = request.custodian_id
            
            # Record custodian change as lifecycle event
            if old_custodian != request.custodian_id:
                self._record_lifecycle_event(
                    instrument_id, "CUSTODIAN_CHANGE",
                    old_custodian, request.custodian_id, updated_by_id,
                    "Instrument custodian updated"
                )
        
        if request.calibration_interval_months is not None:
            if request.calibration_interval_months < 1 or request.calibration_interval_months > 60:
                raise ValueError("Calibration interval must be between 1 and 60 months")
            instrument.calibration_interval_months = request.calibration_interval_months
        
        if request.description is not None:
            instrument.description = request.description
        
        if request.specifications is not None:
            instrument.specifications = request.specifications
        
        if request.photo_url is not None:
            instrument.photo_url = request.photo_url
        
        return self.repository.update(instrument, updated_by_id, "Instrument updated")
    
    def transfer_instrument(self, instrument_id: str, new_location_id: str,
                          new_custodian_id: Optional[str], transferred_by_id: str,
                          user_role: Role, reason: str) -> Instrument:
        """
        Transfer an instrument to a new location and/or custodian.
        
        Args:
            instrument_id: Instrument ID to transfer
            new_location_id: New location ID
            new_custodian_id: New custodian ID (optional)
            transferred_by_id: User ID performing the transfer
            user_role: User role for authorization
            reason: Reason for transfer
            
        Returns:
            Updated instrument
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=transferred_by_id,
            user_role=user_role,
            permission=Permission.INSTRUMENT_TRANSFER,
            resource=f"instrument/{instrument_id}",
            context={"new_location": new_location_id, "new_custodian": new_custodian_id}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Get existing instrument
        instrument = self.repository.get_by_id(instrument_id)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        # Record transfer
        old_location = instrument.location_id
        old_custodian = instrument.custodian_id
        
        instrument.location_id = new_location_id
        instrument.custodian_id = new_custodian_id
        
        # Update instrument
        updated = self.repository.update(instrument, transferred_by_id, reason)
        
        # Record lifecycle event
        self._record_lifecycle_event(
            instrument_id, "TRANSFER",
            {"location": old_location, "custodian": old_custodian},
            {"location": new_location_id, "custodian": new_custodian_id},
            transferred_by_id, reason
        )
        
        return updated
    
    def update_calibration_status(self, instrument_id: str, last_calibration_date: datetime,
                                 updated_by_id: str, user_role: Role) -> Instrument:
        """
        Update instrument calibration status after calibration.
        
        Args:
            instrument_id: Instrument ID
            last_calibration_date: Date of last calibration
            updated_by_id: User ID updating the status
            user_role: User role for authorization
            
        Returns:
            Updated instrument
        """
        # Get instrument
        instrument = self.repository.get_by_id(instrument_id)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        # Update calibration dates
        instrument.last_calibration_date = last_calibration_date
        instrument.next_calibration_date = last_calibration_date + timedelta(
            days=instrument.calibration_interval_months * 30
        )
        
        # Update status if needed
        if instrument.status == InstrumentStatus.CALIBRATION_DUE:
            instrument.status = InstrumentStatus.ACTIVE
        
        return self.repository.update(instrument, updated_by_id, "Calibration status updated")
    
    def get_calibration_due_instruments(self, days_ahead: int = 30,
                                       organization_id: Optional[str] = None,
                                       user_role: Role = Role.VIEWER) -> List[Instrument]:
        """
        Get instruments due for calibration within specified timeframe.
        
        Args:
            days_ahead: Number of days ahead to check
            organization_id: Filter by organization (optional)
            user_role: User role for authorization
            
        Returns:
            List of instruments due for calibration
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id="system",
            user_role=user_role,
            permission=Permission.INSTRUMENT_READ,
            resource="instruments",
            context={"query": "calibration_due"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        instruments = self.repository.get_calibration_due(days_ahead)
        
        # Filter by organization if specified
        if organization_id:
            instruments = [i for i in instruments if i.organization_id == organization_id]
        
        return instruments
    
    def retire_instrument(self, instrument_id: str, retired_by_id: str,
                        user_role: Role, reason: str) -> Instrument:
        """
        Retire an instrument from service.
        
        Args:
            instrument_id: Instrument ID to retire
            retired_by_id: User ID retiring the instrument
            user_role: User role for authorization
            reason: Reason for retirement
            
        Returns:
            Updated instrument
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=retired_by_id,
            user_role=user_role,
            permission=Permission.INSTRUMENT_UPDATE,
            resource=f"instrument/{instrument_id}",
            context={"action": "retire"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Get instrument
        instrument = self.repository.get_by_id(instrument_id)
        if not instrument:
            raise ValueError(f"Instrument {instrument_id} not found")
        
        # Update status and retirement date
        old_status = instrument.status
        instrument.status = InstrumentStatus.RETIRED
        instrument.retirement_date = datetime.now()
        
        # Update instrument
        updated = self.repository.update(instrument, retired_by_id, reason)
        
        # Record lifecycle event
        self._record_lifecycle_event(
            instrument_id, "RETIREMENT",
            old_status.value, InstrumentStatus.RETIRED.value,
            retired_by_id, reason
        )
        
        return updated
    
    def _record_lifecycle_event(self, instrument_id: str, event_type: str,
                               previous_value: Any, new_value: Any,
                               performed_by_id: str, reason: str):
        """Record instrument lifecycle event through repository."""
        self.repository._record_lifecycle_event(
            instrument_id, event_type,
            str(previous_value), str(new_value),
            performed_by_id, reason
        )


# Import PermissionDenied from security module
from ..infrastructure.security.rbac import PermissionDenied