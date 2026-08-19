"""
Calibration Domain Service

Business logic for calibration workflow management including:
- Calibration scheduling and execution
- Measurement recording with immutability
- Uncertainty budget calculation
- Workflow state management
- Quality assurance integration
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
import secrets
from decimal import Decimal, getcontext

getcontext().prec = 50  # Set high precision for metrology calculations

from ..infrastructure.database.schema import (
    CalibrationRecord, CalibrationStatus, Instrument, Measurement,
    EnvironmentalCondition, UncertaintyBudget, ReferenceStandard
)
from ..infrastructure.database.repositories import CalibrationRepository, MeasurementRepository
from ..infrastructure.security.rbac import Permission, Role, SecurityManager, PermissionDenied


logger = logging.getLogger(__name__)


@dataclass
class CalibrationCreateRequest:
    """Request to create a new calibration."""
    instrument_id: str
    procedure_id: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    calibration_method: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class MeasurementCreateRequest:
    """Request to create a measurement."""
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


@dataclass
class UncertaintyComponent:
    """Component of uncertainty budget."""
    source: str
    value: float
    unit: str
    distribution: str  # normal, rectangular, triangular, etc.
    degrees_of_freedom: Optional[int] = None
    sensitivity_coefficient: float = 1.0


class CalibrationService:
    """
    Service for calibration domain business logic.
    
    Handles calibration workflow, measurement recording, and uncertainty
    calculation while enforcing business rules and security policies.
    """
    
    def __init__(self, calibration_repository: CalibrationRepository,
                 measurement_repository: MeasurementRepository,
                 security_manager: SecurityManager):
        """
        Initialize calibration service.
        
        Args:
            calibration_repository: Calibration repository
            measurement_repository: Measurement repository
            security_manager: Security manager for authorization
        """
        self.calibration_repository = calibration_repository
        self.measurement_repository = measurement_repository
        self.security_manager = security_manager
    
    def create_calibration(self, request: CalibrationCreateRequest,
                          created_by_id: str, user_role: Role) -> CalibrationRecord:
        """
        Create a new calibration record with validation and authorization.
        
        Args:
            request: Calibration creation request
            created_by_id: User ID creating the calibration
            user_role: User role for authorization
            
        Returns:
            Created calibration record
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=created_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_CREATE,
            resource="calibration",
            context={"request": request.__dict__}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Create calibration record
        calibration = CalibrationRecord(
            id=secrets.token_hex(16),
            instrument_id=request.instrument_id,
            procedure_id=request.procedure_id,
            status=CalibrationStatus.DRAFT,
            performed_by_id=created_by_id,
            scheduled_date=request.scheduled_date or datetime.now(),
            calibration_method=request.calibration_method,
            notes=request.notes
        )
        
        return self.calibration_repository.create(calibration, created_by_id)
    
    def start_calibration(self, calibration_id: str, started_by_id: str,
                        user_role: Role) -> CalibrationRecord:
        """
        Start calibration execution.
        
        Args:
            calibration_id: Calibration record ID
            started_by_id: User ID starting the calibration
            user_role: User role for authorization
            
        Returns:
            Updated calibration record
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=started_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_EXECUTE,
            resource=f"calibration/{calibration_id}",
            context={"action": "start"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Advance workflow state
        return self.calibration_repository.advance_workflow(
            calibration_id, CalibrationStatus.IN_PROGRESS,
            started_by_id, "Calibration started"
        )
    
    def add_measurement(self, request: MeasurementCreateRequest,
                      added_by_id: str, user_role: Role) -> Measurement:
        """
        Add a measurement to a calibration record with immutable recording.
        
        Args:
            request: Measurement creation request
            added_by_id: User ID adding the measurement
            user_role: User role for authorization
            
        Returns:
            Created measurement
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If validation fails
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=added_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_EXECUTE,
            resource=f"calibration/{request.calibration_record_id}",
            context={"action": "add_measurement"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Validate tolerance order
        if request.tolerance_lower >= request.tolerance_upper:
            raise ValueError("Tolerance lower must be less than tolerance upper")
        
        # Calculate error
        error = request.measured_value - request.nominal_value
        
        # Determine result
        result = self._determine_measurement_result(
            request.measured_value, request.tolerance_lower, request.tolerance_upper
        )
        
        # Create measurement (immutable)
        measurement = Measurement(
            id=secrets.token_hex(16),
            calibration_record_id=request.calibration_record_id,
            nominal_value=request.nominal_value,
            measured_value=request.measured_value,
            unit=request.unit,
            error=error,
            uncertainty=request.uncertainty,
            tolerance_lower=request.tolerance_lower,
            tolerance_upper=request.tolerance_upper,
            result=result,
            operator_id=added_by_id,
            measurement_sequence=request.measurement_sequence,
            repeat_number=request.repeat_number,
            standard_used_id=request.standard_used_id,
            notes=request.notes,
            version=1
        )
        
        return self.measurement_repository.create(measurement, added_by_id)
    
    def _determine_measurement_result(self, measured_value: float,
                                    tolerance_lower: float,
                                    tolerance_upper: float) -> str:
        """
        Determine measurement result based on tolerance.
        
        Args:
            measured_value: Measured value
            tolerance_lower: Lower tolerance limit
            tolerance_upper: Upper tolerance limit
            
        Returns:
            Result string (PASS, FAIL, or GUARD_BAND)
        """
        if tolerance_lower <= measured_value <= tolerance_upper:
            return "PASS"
        else:
            return "FAIL"
    
    def complete_measurements(self, calibration_id: str, completed_by_id: str,
                            user_role: Role) -> CalibrationRecord:
        """
        Mark measurement phase as complete.
        
        Args:
            calibration_id: Calibration record ID
            completed_by_id: User ID completing measurements
            user_role: User role for authorization
            
        Returns:
            Updated calibration record
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=completed_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_EXECUTE,
            resource=f"calibration/{calibration_id}",
            context={"action": "complete_measurements"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Advance workflow state
        return self.calibration_repository.advance_workflow(
            calibration_id, CalibrationStatus.MEASUREMENT_COMPLETE,
            completed_by_id, "Measurements completed"
        )
    
    def submit_for_review(self, calibration_id: str, submitted_by_id: str,
                        user_role: Role) -> CalibrationRecord:
        """
        Submit calibration for technical review.
        
        Args:
            calibration_id: Calibration record ID
            submitted_by_id: User ID submitting for review
            user_role: User role for authorization
            
        Returns:
            Updated calibration record
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=submitted_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_EXECUTE,
            resource=f"calibration/{calibration_id}",
            context={"action": "submit_review"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Advance workflow state
        return self.calibration_repository.advance_workflow(
            calibration_id, CalibrationStatus.REVIEW_PENDING,
            submitted_by_id, "Submitted for review"
        )
    
    def approve_calibration(self, calibration_id: str, approved_by_id: str,
                          user_role: Role, notes: Optional[str] = None) -> CalibrationRecord:
        """
        Approve calibration for certificate generation.
        
        Args:
            calibration_id: Calibration record ID
            approved_by_id: User ID approving the calibration
            user_role: User role for authorization
            notes: Approval notes
            
        Returns:
            Updated calibration record
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=approved_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_APPROVE,
            resource=f"calibration/{calibration_id}",
            context={"action": "approve"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Add notes if provided
        calibration = self.calibration_repository.get_by_id(calibration_id)
        if calibration and notes:
            calibration.notes = (calibration.notes or "") + f"\nApproval notes: {notes}"
        
        # Advance workflow state
        return self.calibration_repository.advance_workflow(
            calibration_id, CalibrationStatus.APPROVED,
            approved_by_id, "Calibration approved"
        )
    
    def reject_calibration(self, calibration_id: str, rejected_by_id: str,
                         user_role: Role, reason: str) -> CalibrationRecord:
        """
        Reject calibration and return for correction.
        
        Args:
            calibration_id: Calibration record ID
            rejected_by_id: User ID rejecting the calibration
            user_role: User role for authorization
            reason: Reason for rejection
            
        Returns:
            Updated calibration record
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=rejected_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_REVIEW,
            resource=f"calibration/{calibration_id}",
            context={"action": "reject"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Add rejection reason
        calibration = self.calibration_repository.get_by_id(calibration_id)
        if calibration:
            calibration.deviation_notes = (calibration.deviation_notes or "") + f"\nRejection: {reason}"
        
        # Advance workflow state
        return self.calibration_repository.advance_workflow(
            calibration_id, CalibrationStatus.REJECTED,
            rejected_by_id, f"Rejected: {reason}"
        )
    
    def calculate_uncertainty_budget(self, calibration_id: str,
                                    components: List[UncertaintyComponent],
                                    calculated_by_id: str, user_role: Role) -> UncertaintyBudget:
        """
        Calculate uncertainty budget using GUM methodology.
        
        Args:
            calibration_id: Calibration record ID
            components: List of uncertainty components
            calculated_by_id: User ID performing calculation
            user_role: User role for authorization
            
        Returns:
            Calculated uncertainty budget
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=calculated_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_EXECUTE,
            resource=f"calibration/{calibration_id}",
            context={"action": "calculate_uncertainty"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Calculate combined standard uncertainty using GUM method
        combined_standard_uncertainty = self._calculate_combined_uncertainty(components)
        
        # Calculate effective degrees of freedom (Welch-Satterthwaite)
        effective_degrees_of_freedom = self._calculate_effective_degrees_of_freedom(components)
        
        # Determine coverage factor based on degrees of freedom
        coverage_factor_k = self._determine_coverage_factor(effective_degrees_of_freedom)
        
        # Calculate expanded uncertainty
        expanded_uncertainty = combined_standard_uncertainty * coverage_factor_k
        
        # Create uncertainty budget record
        uncertainty_budget = UncertaintyBudget(
            id=secrets.token_hex(16),
            calibration_record_id=calibration_id,
            combined_standard_uncertainty=float(combined_standard_uncertainty),
            effective_degrees_of_freedom=float(effective_degrees_of_freedom),
            coverage_factor_k=float(coverage_factor_k),
            expanded_uncertainty=float(expanded_uncertainty),
            confidence_level=0.95,
            components=[{
                "source": comp.source,
                "value": comp.value,
                "unit": comp.unit,
                "distribution": comp.distribution,
                "degrees_of_freedom": comp.degrees_of_freedom,
                "sensitivity_coefficient": comp.sensitivity_coefficient
            } for comp in components],
            calculated_by_id=calculated_by_id
        )
        
        return uncertainty_budget
    
    def _calculate_combined_uncertainty(self, components: List[UncertaintyComponent]) -> Decimal:
        """
        Calculate combined standard uncertainty using GUM method.
        
        Args:
            components: List of uncertainty components
            
        Returns:
            Combined standard uncertainty
        """
        # Use Decimal for high-precision calculation
        combined = Decimal('0')
        
        for component in components:
            # Convert component to standard uncertainty based on distribution
            standard_uncertainty = self._convert_to_standard_uncertainty(component)
            
            # Apply sensitivity coefficient
            standard_uncertainty *= Decimal(str(component.sensitivity_coefficient))
            
            # Add in quadrature (root sum of squares)
            combined += standard_uncertainty ** 2
        
        # Take square root
        return combined.sqrt()
    
    def _convert_to_standard_uncertainty(self, component: UncertaintyComponent) -> Decimal:
        """
        Convert component to standard uncertainty based on distribution.
        
        Args:
            component: Uncertainty component
            
        Returns:
            Standard uncertainty
        """
        value = Decimal(str(component.value))
        
        if component.distribution == "normal":
            return value
        elif component.distribution == "rectangular":
            return value / Decimal('3').sqrt()  # Divide by sqrt(3)
        elif component.distribution == "triangular":
            return value / Decimal('6').sqrt()  # Divide by sqrt(6)
        else:
            # Default to normal distribution
            return value
    
    def _calculate_effective_degrees_of_freedom(self, components: List[UncertaintyComponent]) -> Decimal:
        """
        Calculate effective degrees of freedom using Welch-Satterthwaite formula.
        
        Args:
            components: List of uncertainty components
            
        Returns:
            Effective degrees of freedom
        """
        numerator = Decimal('0')
        denominator = Decimal('0')
        
        for component in components:
            if component.degrees_of_freedom is None:
                continue
            
            standard_uncertainty = self._convert_to_standard_uncertainty(component)
            standard_uncertainty *= Decimal(str(component.sensitivity_coefficient))
            
            component_variance = standard_uncertainty ** 4
            dof = Decimal(str(component.degrees_of_freedom))
            
            numerator += component_variance
            denominator += component_variance / dof
        
        if denominator == 0:
            return Decimal('1')  # Minimum degrees of freedom
        
        return numerator / denominator
    
    def _determine_coverage_factor(self, effective_degrees_of_freedom: Decimal) -> Decimal:
        """
        Determine coverage factor k based on effective degrees of freedom.
        
        For 95% confidence level, uses t-distribution.
        
        Args:
            effective_degrees_of_freedom: Effective degrees of freedom
            
        Returns:
            Coverage factor k
        """
        # Simplified approximation for common cases
        dof = float(effective_degrees_of_freedom)
        
        if dof >= 30:
            return Decimal('2.0')  # Normal distribution approximation
        elif dof >= 10:
            return Decimal('2.2')
        elif dof >= 5:
            return Decimal('2.5')
        else:
            return Decimal('3.0')  # Conservative for small dof
    
    def get_calibration_summary(self, calibration_id: str,
                              requested_by_id: str, user_role: Role) -> Dict[str, Any]:
        """
        Get comprehensive calibration summary with measurements and uncertainty.
        
        Args:
            calibration_id: Calibration record ID
            requested_by_id: User ID requesting summary
            user_role: User role for authorization
            
        Returns:
            Calibration summary dictionary
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=requested_by_id,
            user_role=user_role,
            permission=Permission.CALIBRATION_READ,
            resource=f"calibration/{calibration_id}",
            context={"action": "get_summary"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Get calibration record
        calibration = self.calibration_repository.get_by_id(calibration_id)
        if not calibration:
            raise ValueError(f"Calibration {calibration_id} not found")
        
        # Get measurements
        measurements = self.measurement_repository.get_by_calibration(calibration_id)
        
        # Calculate summary statistics
        if measurements:
            measured_values = [m.measured_value for m in measurements]
            mean_value = sum(measured_values) / len(measured_values)
            std_dev = (sum((x - mean_value) ** 2 for x in measured_values) / len(measured_values)) ** 0.5
        else:
            mean_value = None
            std_dev = None
        
        return {
            "calibration": {
                "id": calibration.id,
                "instrument_id": calibration.instrument_id,
                "status": calibration.status.value,
                "performed_by_id": calibration.performed_by_id,
                "scheduled_date": calibration.scheduled_date.isoformat() if calibration.scheduled_date else None,
                "completed_at": calibration.completed_at.isoformat() if calibration.completed_at else None,
                "overall_result": calibration.overall_result,
                "notes": calibration.notes
            },
            "measurements": {
                "count": len(measurements),
                "mean_value": mean_value,
                "standard_deviation": std_dev,
                "details": [
                    {
                        "id": m.id,
                        "nominal_value": m.nominal_value,
                        "measured_value": m.measured_value,
                        "error": m.error,
                        "uncertainty": m.uncertainty,
                        "result": m.result,
                        "timestamp": m.timestamp.isoformat()
                    }
                    for m in measurements
                ]
            }
        }