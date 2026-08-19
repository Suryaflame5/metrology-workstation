"""
Workflow Engine with State Management

Production-grade workflow orchestration with:
- State machine implementation
- State transition validation
- Authorization checks
- Timeout and escalation handling
- Workflow history and audit trails
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import secrets
import threading
import time

from ..infrastructure.security.rbac import Permission, Role, SecurityManager, PermissionDenied


logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """Workflow states."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ESCALATED = "ESCALATED"


class WorkflowEventType(Enum):
    """Workflow event types."""
    STATE_CHANGE = "STATE_CHANGE"
    TIMEOUT = "TIMEOUT"
    ESCALATION = "ESCALATION"
    COMMENT = "COMMENT"
    ATTACHMENT = "ATTACHMENT"
    APPROVAL = "APPROVAL"
    REJECTION = "REJECTION"


@dataclass
class WorkflowTransition:
    """Workflow transition definition."""
    from_state: WorkflowState
    to_state: WorkflowState
    required_permission: Optional[Permission] = None
    allowed_roles: List[Role] = field(default_factory=list)
    auto_transition: bool = False
    timeout_seconds: Optional[int] = None


@dataclass
class WorkflowEvent:
    """Workflow event record."""
    event_id: str
    workflow_id: str
    event_type: WorkflowEventType
    from_state: Optional[WorkflowState]
    to_state: Optional[WorkflowState]
    actor_id: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Workflow definition with state machine."""
    workflow_type: str
    initial_state: WorkflowState
    transitions: List[WorkflowTransition]
    timeout_handlers: Dict[WorkflowState, Callable] = field(default_factory=dict)
    escalation_handlers: Dict[WorkflowState, Callable] = field(default_factory=dict)


class WorkflowInstance:
    """Running workflow instance."""
    
    def __init__(self, workflow_id: str, workflow_type: str, 
                 initial_state: WorkflowState, entity_id: str,
                 entity_type: str, context: Dict[str, Any]):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.current_state = initial_state
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.context = context
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.events: List[WorkflowEvent] = []
        self.timeout_handle: Optional[threading.Timer] = None
        self.escalation_handle: Optional[threading.Timer] = None
        self.completed = False
    
    def add_event(self, event: WorkflowEvent):
        """Add event to workflow history."""
        self.events.append(event)
        self.updated_at = datetime.now()
    
    def get_state_duration(self) -> timedelta:
        """Get duration in current state."""
        if not self.events:
            return timedelta(0)
        
        last_state_change = next(
            (e.timestamp for e in reversed(self.events) 
             if e.event_type == WorkflowEventType.STATE_CHANGE),
            self.created_at
        )
        
        return datetime.now() - last_state_change


class WorkflowEngine:
    """
    Production-grade workflow engine with state management.
    
    Handles workflow orchestration, state transitions, timeouts,
    and escalation while enforcing security policies.
    """
    
    def __init__(self, security_manager: SecurityManager):
        """
        Initialize workflow engine.
        
        Args:
            security_manager: Security manager for authorization
        """
        self.security_manager = security_manager
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.active_workflows: Dict[str, WorkflowInstance] = {}
        self.workflow_history: Dict[str, List[WorkflowEvent]] = {}
        self._lock = threading.Lock()
        
        # Register standard workflow definitions
        self._register_standard_workflows()
        
        logger.info("Workflow engine initialized")
    
    def _register_standard_workflows(self):
        """Register standard workflow definitions."""
        
        # Calibration workflow
        calibration_workflow = WorkflowDefinition(
            workflow_type="calibration",
            initial_state=WorkflowState.DRAFT,
            transitions=[
                WorkflowTransition(
                    from_state=WorkflowState.DRAFT,
                    to_state=WorkflowState.IN_PROGRESS,
                    required_permission=Permission.CALIBRATION_EXECUTE,
                    allowed_roles=[Role.METROLOGIST, Role.TECHNICIAN]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.IN_PROGRESS,
                    to_state=WorkflowState.REVIEW,
                    required_permission=Permission.CALIBRATION_EXECUTE,
                    allowed_roles=[Role.METROLOGIST, Role.TECHNICIAN]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.REVIEW,
                    to_state=WorkflowState.APPROVED,
                    required_permission=Permission.CALIBRATION_APPROVE,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.REVIEW,
                    to_state=WorkflowState.REJECTED,
                    required_permission=Permission.CALIBRATION_REVIEW,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.APPROVED,
                    to_state=WorkflowState.COMPLETED,
                    required_permission=Permission.CALIBRATION_APPROVE,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER],
                    auto_transition=True
                ),
                WorkflowTransition(
                    from_state=WorkflowState.REJECTED,
                    to_state=WorkflowState.IN_PROGRESS,
                    required_permission=Permission.CALIBRATION_EXECUTE,
                    allowed_roles=[Role.METROLOGIST, Role.TECHNICIAN]
                ),
            ]
        )
        
        self.workflow_definitions["calibration"] = calibration_workflow
        
        # Certificate workflow
        certificate_workflow = WorkflowDefinition(
            workflow_type="certificate",
            initial_state=WorkflowState.DRAFT,
            transitions=[
                WorkflowTransition(
                    from_state=WorkflowState.DRAFT,
                    to_state=WorkflowState.REVIEW,
                    required_permission=Permission.CERTIFICATE_GENERATE,
                    allowed_roles=[Role.METROLOGIST, Role.QUALITY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.REVIEW,
                    to_state=WorkflowState.APPROVED,
                    required_permission=Permission.CERTIFICATE_SIGN,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.APPROVED,
                    to_state=WorkflowState.COMPLETED,
                    required_permission=Permission.CERTIFICATE_SIGN,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER],
                    auto_transition=True
                ),
            ]
        )
        
        self.workflow_definitions["certificate"] = certificate_workflow
        
        # Deviation workflow
        deviation_workflow = WorkflowDefinition(
            workflow_type="deviation",
            initial_state=WorkflowState.DRAFT,
            transitions=[
                WorkflowTransition(
                    from_state=WorkflowState.DRAFT,
                    to_state=WorkflowState.PENDING,
                    required_permission=Permission.DEVIATION_REPORT,
                    allowed_roles=[Role.METROLOGIST, Role.TECHNICIAN]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.PENDING,
                    to_state=WorkflowState.IN_PROGRESS,
                    required_permission=Permission.QUALITY_MANAGE,
                    allowed_roles=[Role.QUALITY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.IN_PROGRESS,
                    to_state=WorkflowState.APPROVED,
                    required_permission=Permission.QUALITY_MANAGE,
                    allowed_roles=[Role.QUALITY_MANAGER, Role.LABORATORY_MANAGER]
                ),
                WorkflowTransition(
                    from_state=WorkflowState.IN_PROGRESS,
                    to_state=WorkflowState.COMPLETED,
                    required_permission=Permission.CORRECTIVE_ACTION,
                    allowed_roles=[Role.QUALITY_MANAGER]
                ),
            ]
        )
        
        self.workflow_definitions["deviation"] = deviation_workflow
    
    def create_workflow(self, workflow_type: str, entity_id: str, entity_type: str,
                       context: Optional[Dict[str, Any]] = None) -> WorkflowInstance:
        """
        Create a new workflow instance.
        
        Args:
            workflow_type: Type of workflow
            entity_id: ID of entity being processed
            entity_type: Type of entity
            context: Additional context for the workflow
            
        Returns:
            Created workflow instance
            
        Raises:
            ValueError: If workflow type is not defined
        """
        with self._lock:
            if workflow_type not in self.workflow_definitions:
                raise ValueError(f"Workflow type {workflow_type} not defined")
            
            definition = self.workflow_definitions[workflow_type]
            workflow_id = secrets.token_hex(16)
            
            workflow = WorkflowInstance(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                initial_state=definition.initial_state,
                entity_id=entity_id,
                entity_type=entity_type,
                context=context or {}
            )
            
            # Record initial state event
            initial_event = WorkflowEvent(
                event_id=secrets.token_hex(16),
                workflow_id=workflow_id,
                event_type=WorkflowEventType.STATE_CHANGE,
                from_state=None,
                to_state=definition.initial_state,
                actor_id="system",
                timestamp=datetime.now(),
                metadata={"reason": "Workflow created"}
            )
            
            workflow.add_event(initial_event)
            self.active_workflows[workflow_id] = workflow
            
            # Start timeout monitoring
            self._start_timeout_monitoring(workflow)
            
            logger.info(f"Created workflow {workflow_id} of type {workflow_type}")
            return workflow
    
    def transition_state(self, workflow_id: str, new_state: WorkflowState,
                       actor_id: str, user_role: Role, reason: str) -> WorkflowInstance:
        """
        Transition workflow to a new state with authorization.
        
        Args:
            workflow_id: Workflow instance ID
            new_state: New state to transition to
            actor_id: User ID making the transition
            user_role: User role for authorization
            reason: Reason for state transition
            
        Returns:
            Updated workflow instance
            
        Raises:
            PermissionDenied: If user lacks required permissions
            ValueError: If transition is invalid
        """
        with self._lock:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Get workflow definition
            definition = self.workflow_definitions.get(workflow.workflow_type)
            if not definition:
                raise ValueError(f"Workflow type {workflow.workflow_type} not defined")
            
            # Find valid transition
            valid_transition = None
            for transition in definition.transitions:
                if transition.from_state == workflow.current_state and transition.to_state == new_state:
                    valid_transition = transition
                    break
            
            if not valid_transition:
                raise ValueError(
                    f"Invalid transition from {workflow.current_state} to {new_state}"
                )
            
            # Authorization check
            if valid_transition.required_permission:
                decision = self.security_manager.authorize(
                    user_id=actor_id,
                    user_role=user_role,
                    permission=valid_transition.required_permission,
                    resource=f"workflow/{workflow_id}",
                    context={
                        "workflow_type": workflow.workflow_type,
                        "entity_id": workflow.entity_id,
                        "entity_type": workflow.entity_type
                    }
                )
                
                if not decision.authorized:
                    raise PermissionDenied(decision.reason)
            
            # Role check
            if valid_transition.allowed_roles and user_role not in valid_transition.allowed_roles:
                raise PermissionDenied(
                    f"User role {user_role.value} not allowed for this transition"
                )
            
            # Perform transition
            old_state = workflow.current_state
            workflow.current_state = new_state
            
            # Record state change event
            state_change_event = WorkflowEvent(
                event_id=secrets.token_hex(16),
                workflow_id=workflow_id,
                event_type=WorkflowEventType.STATE_CHANGE,
                from_state=old_state,
                to_state=new_state,
                actor_id=actor_id,
                timestamp=datetime.now(),
                metadata={"reason": reason}
            )
            
            workflow.add_event(state_change_event)
            
            # Cancel existing timeout
            if workflow.timeout_handle:
                workflow.timeout_handle.cancel()
                workflow.timeout_handle = None
            
            # Start new timeout monitoring
            self._start_timeout_monitoring(workflow)
            
            # Check for auto-transition
            if valid_transition.auto_transition:
                self._schedule_auto_transition(workflow, new_state)
            
            # Check for completion
            if new_state in [WorkflowState.COMPLETED, WorkflowState.CANCELLED]:
                workflow.completed = True
                self._complete_workflow(workflow)
            
            logger.info(f"Workflow {workflow_id} transitioned from {old_state} to {new_state}")
            return workflow
    
    def _start_timeout_monitoring(self, workflow: WorkflowInstance):
        """Start timeout monitoring for current state."""
        definition = self.workflow_definitions.get(workflow.workflow_type)
        if not definition:
            return
        
        # Find transition with timeout for current state
        for transition in definition.transitions:
            if transition.from_state == workflow.current_state and transition.timeout_seconds:
                timeout_seconds = transition.timeout_seconds
                
                def timeout_handler():
                    self._handle_timeout(workflow.workflow_id)
                
                workflow.timeout_handle = threading.Timer(timeout_seconds, timeout_handler)
                workflow.timeout_handle.start()
                
                logger.info(f"Started timeout monitoring for workflow {workflow.workflow_id}")
                break
    
    def _handle_timeout(self, workflow_id: str):
        """Handle workflow timeout."""
        with self._lock:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow or workflow.completed:
                return
            
            # Record timeout event
            timeout_event = WorkflowEvent(
                event_id=secrets.token_hex(16),
                workflow_id=workflow_id,
                event_type=WorkflowEventType.TIMEOUT,
                from_state=workflow.current_state,
                to_state=None,
                actor_id="system",
                timestamp=datetime.now(),
                metadata={"state_duration": workflow.get_state_duration().total_seconds()}
            )
            
            workflow.add_event(timeout_event)
            
            # Call timeout handler if defined
            definition = self.workflow_definitions.get(workflow.workflow_type)
            if definition and workflow.current_state in definition.timeout_handlers:
                handler = definition.timeout_handlers[workflow.current_state]
                try:
                    handler(workflow)
                except Exception as e:
                    logger.error(f"Timeout handler error for workflow {workflow_id}: {e}")
            
            logger.warning(f"Workflow {workflow_id} timed out in state {workflow.current_state}")
    
    def _schedule_auto_transition(self, workflow: WorkflowInstance, current_state: WorkflowState):
        """Schedule automatic transition for auto-transition states."""
        # For auto-transitions, transition immediately
        # In production, this might have a delay or conditions
        definition = self.workflow_definitions.get(workflow.workflow_type)
        if not definition:
            return
        
        # Find next state
        for transition in definition.transitions:
            if transition.from_state == current_state and transition.auto_transition:
                try:
                    self.transition_state(
                        workflow.workflow_id,
                        transition.to_state,
                        "system",
                        Role.SYSTEM_ADMINISTRATOR,
                        "Automatic transition"
                    )
                except Exception as e:
                    logger.error(f"Auto-transition error for workflow {workflow.workflow_id}: {e}")
                break
    
    def _complete_workflow(self, workflow: WorkflowInstance):
        """Complete workflow and move to history."""
        # Cancel any remaining timers
        if workflow.timeout_handle:
            workflow.timeout_handle.cancel()
        if workflow.escalation_handle:
            workflow.escalation_handle.cancel()
        
        # Move to history
        self.workflow_history[workflow.workflow_id] = workflow.events
        del self.active_workflows[workflow.workflow_id]
        
        logger.info(f"Workflow {workflow.workflow_id} completed")
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current workflow status.
        
        Args:
            workflow_id: Workflow instance ID
            
        Returns:
            Workflow status dictionary or None if not found
        """
        with self._lock:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                # Check history
                if workflow_id in self.workflow_history:
                    return {
                        "workflow_id": workflow_id,
                        "status": "completed",
                        "events": len(self.workflow_history[workflow_id])
                    }
                return None
            
            return {
                "workflow_id": workflow.workflow_id,
                "workflow_type": workflow.workflow_type,
                "current_state": workflow.current_state.value,
                "entity_id": workflow.entity_id,
                "entity_type": workflow.entity_type,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "state_duration": workflow.get_state_duration().total_seconds(),
                "event_count": len(workflow.events),
                "completed": workflow.completed
            }
    
    def cancel_workflow(self, workflow_id: str, cancelled_by_id: str,
                      user_role: Role, reason: str) -> WorkflowInstance:
        """
        Cancel a workflow.
        
        Args:
            workflow_id: Workflow instance ID
            cancelled_by_id: User ID cancelling the workflow
            user_role: User role for authorization
            reason: Reason for cancellation
            
        Returns:
            Cancelled workflow instance
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        with self._lock:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Authorization check
            decision = self.security_manager.authorize(
                user_id=cancelled_by_id,
                user_role=user_role,
                permission=Permission.CALIBRATION_APPROVE,  # High-level permission
                resource=f"workflow/{workflow_id}",
                context={"action": "cancel"}
            )
            
            if not decision.authorized:
                raise PermissionDenied(decision.reason)
            
            # Record cancellation event
            cancel_event = WorkflowEvent(
                event_id=secrets.token_hex(16),
                workflow_id=workflow_id,
                event_type=WorkflowEventType.STATE_CHANGE,
                from_state=workflow.current_state,
                to_state=WorkflowState.CANCELLED,
                actor_id=cancelled_by_id,
                timestamp=datetime.now(),
                metadata={"reason": reason}
            )
            
            workflow.add_event(cancel_event)
            workflow.current_state = WorkflowState.CANCELLED
            workflow.completed = True
            
            self._complete_workflow(workflow)
            
            logger.info(f"Workflow {workflow_id} cancelled by {cancelled_by_id}")
            return workflow
    
    def add_workflow_comment(self, workflow_id: str, comment: str,
                           actor_id: str, user_role: Role) -> WorkflowInstance:
        """
        Add a comment to a workflow.
        
        Args:
            workflow_id: Workflow instance ID
            comment: Comment text
            actor_id: User ID adding the comment
            user_role: User role for authorization
            
        Returns:
            Updated workflow instance
        """
        with self._lock:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            # Record comment event
            comment_event = WorkflowEvent(
                event_id=secrets.token_hex(16),
                workflow_id=workflow_id,
                event_type=WorkflowEventType.COMMENT,
                from_state=None,
                to_state=None,
                actor_id=actor_id,
                timestamp=datetime.now(),
                metadata={"comment": comment}
            )
            
            workflow.add_event(comment_event)
            
            logger.info(f"Comment added to workflow {workflow_id} by {actor_id}")
            return workflow


# Global workflow engine instance
_workflow_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get or create the global workflow engine instance."""
    global _workflow_engine
    if _workflow_engine is None:
        from ..infrastructure.security.rbac import get_security_manager
        _workflow_engine = WorkflowEngine(get_security_manager())
    return _workflow_engine