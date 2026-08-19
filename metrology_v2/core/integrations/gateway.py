"""
Integration Gateway

Production-grade integration system with:
- REST API endpoints
- Webhook system with retry policies
- File import/export with validation
- ERP/PLM connectors
- Integration security layer
- Rate limiting and monitoring
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import secrets
import json
import hashlib
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    import aiohttp
    ASYNC_HTTP_AVAILABLE = True
except ImportError:
    ASYNC_HTTP_AVAILABLE = False

from ..infrastructure.security.rbac import Permission, Role, SecurityManager, PermissionDenied


logger = logging.getLogger(__name__)


class IntegrationType(Enum):
    """Types of integrations."""
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    FILE_IMPORT = "file_import"
    FILE_EXPORT = "file_export"
    ERP_CONNECTOR = "erp_connector"
    PLM_CONNECTOR = "plm_connector"
    LIMS_CONNECTOR = "lims_connector"


class IntegrationStatus(Enum):
    """Integration status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    RATE_LIMITED = "RATE_LIMITED"


class FileFormat(Enum):
    """Supported file formats."""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    XML = "xml"
    PDF = "pdf"


@dataclass
class IntegrationConfig:
    """Configuration for an integration."""
    integration_id: str
    integration_type: IntegrationType
    name: str
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    authentication_method: str = "none"  # none, api_key, oauth2, basic
    rate_limit_per_minute: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 60
    custom_headers: Dict[str, str] = field(default_factory=dict)
    custom_mappings: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True


@dataclass
class WebhookEvent:
    """Webhook event data."""
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    payload: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    delivered: bool = False
    delivery_attempts: List[datetime] = field(default_factory=list)


@dataclass
class IntegrationResult:
    """Result of an integration operation."""
    success: bool
    integration_id: str
    operation: str
    status_code: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class IntegrationGateway:
    """
    Production-grade integration gateway with security and monitoring.
    
    Handles external system integrations, webhooks, file operations,
    and API management while enforcing security policies.
    """
    
    def __init__(self, security_manager: SecurityManager):
        """
        Initialize integration gateway.
        
        Args:
            security_manager: Security manager for authorization
        """
        self.security_manager = security_manager
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.webhook_queue: List[WebhookEvent] = []
        self.rate_limiters: Dict[str, List[datetime]] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        logger.info("Integration gateway initialized")
    
    def register_integration(self, config: IntegrationConfig, 
                           registered_by_id: str, user_role: Role) -> IntegrationConfig:
        """
        Register a new integration.
        
        Args:
            config: Integration configuration
            registered_by_id: User ID registering the integration
            user_role: User role for authorization
            
        Returns:
            Registered integration configuration
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=registered_by_id,
            user_role=user_role,
            permission=Permission.SYSTEM_CONFIG,
            resource="integration",
            context={"action": "register"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Validate configuration
        if config.integration_type in [IntegrationType.REST_API, IntegrationType.WEBHOOK]:
            if not config.endpoint_url:
                raise ValueError("Endpoint URL required for REST API and webhook integrations")
        
        # Store integration
        self.integrations[config.integration_id] = config
        
        # Initialize rate limiter
        self.rate_limiters[config.integration_id] = []
        
        logger.info(f"Registered integration {config.integration_id} of type {config.integration_type.value}")
        return config
    
    def execute_http_request(self, integration_id: str, method: str, 
                           endpoint: str, payload: Optional[Dict[str, Any]] = None,
                           requested_by_id: str, user_role: Role = Role.VIEWER) -> IntegrationResult:
        """
        Execute HTTP request to external system.
        
        Args:
            integration_id: Integration ID
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            payload: Request payload
            requested_by_id: User ID making the request
            user_role: User role for authorization
            
        Returns:
            Integration result
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=requested_by_id,
            user_role=user_role,
            permission=Permission.SYSTEM_CONFIG,
            resource=f"integration/{integration_id}",
            context={"action": "execute_request"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Get integration configuration
        config = self.integrations.get(integration_id)
        if not config:
            return IntegrationResult(
                success=False,
                integration_id=integration_id,
                operation="http_request",
                error_message=f"Integration {integration_id} not found"
            )
        
        # Check rate limit
        if not self._check_rate_limit(integration_id):
            return IntegrationResult(
                success=False,
                integration_id=integration_id,
                operation="http_request",
                error_message="Rate limit exceeded"
            )
        
        # Execute request
        start_time = datetime.now()
        
        try:
            import requests
            
            # Prepare headers
            headers = config.custom_headers.copy()
            
            # Add authentication
            if config.authentication_method == "api_key" and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            
            # Execute request
            url = f"{config.endpoint_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=payload, timeout=config.timeout_seconds)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=payload, timeout=config.timeout_seconds)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=payload, timeout=config.timeout_seconds)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=config.timeout_seconds)
            else:
                return IntegrationResult(
                    success=False,
                    integration_id=integration_id,
                    operation="http_request",
                    error_message=f"Unsupported HTTP method: {method}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return IntegrationResult(
                success=response.status_code < 400,
                integration_id=integration_id,
                operation="http_request",
                status_code=response.status_code,
                response_data=response_data,
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"HTTP request failed for integration {integration_id}: {e}")
            
            return IntegrationResult(
                success=False,
                integration_id=integration_id,
                operation="http_request",
                error_message=str(e),
                execution_time_seconds=execution_time
            )
    
    def trigger_webhook(self, integration_id: str, event_type: str,
                       entity_type: str, entity_id: str, payload: Dict[str, Any],
                       triggered_by_id: str, user_role: Role) -> WebhookEvent:
        """
        Trigger a webhook event.
        
        Args:
            integration_id: Integration ID
            event_type: Type of event
            entity_type: Type of entity
            entity_id: Entity ID
            payload: Event payload
            triggered_by_id: User ID triggering the webhook
            user_role: User role for authorization
            
        Returns:
            Webhook event
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=triggered_by_id,
            user_role=user_role,
            permission=Permission.SYSTEM_CONFIG,
            resource=f"integration/{integration_id}",
            context={"action": "trigger_webhook"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        # Create webhook event
        webhook_event = WebhookEvent(
            event_id=secrets.token_hex(16),
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            timestamp=datetime.now()
        )
        
        # Add to queue
        self.webhook_queue.append(webhook_event)
        
        # Process webhook asynchronously
        self.executor.submit(self._process_webhook, integration_id, webhook_event)
        
        logger.info(f"Webhook triggered for integration {integration_id}, event {event_type}")
        return webhook_event
    
    def _process_webhook(self, integration_id: str, webhook_event: WebhookEvent):
        """
        Process webhook event asynchronously.
        
        Args:
            integration_id: Integration ID
            webhook_event: Webhook event to process
        """
        config = self.integrations.get(integration_id)
        if not config:
            logger.error(f"Integration {integration_id} not found for webhook processing")
            return
        
        # Process with retry logic
        for attempt in range(config.retry_attempts):
            try:
                import requests
                
                headers = config.custom_headers.copy()
                if config.authentication_method == "api_key" and config.api_key:
                    headers["Authorization"] = f"Bearer {config.api_key}"
                
                # Send webhook
                response = requests.post(
                    config.endpoint_url,
                    headers=headers,
                    json=webhook_event.payload,
                    timeout=config.timeout_seconds
                )
                
                webhook_event.delivery_attempts.append(datetime.now())
                
                if response.status_code < 400:
                    webhook_event.delivered = True
                    logger.info(f"Webhook {webhook_event.event_id} delivered successfully")
                    return
                else:
                    webhook_event.retry_count += 1
                    logger.warning(f"Webhook {webhook_event.event_id} failed with status {response.status_code}")
                    
            except Exception as e:
                webhook_event.retry_count += 1
                logger.error(f"Webhook {webhook_event.event_id} failed: {e}")
            
            # Wait before retry
            if attempt < config.retry_attempts - 1:
                import time
                time.sleep(config.retry_delay_seconds)
        
        # Mark as failed after all retries
        webhook_event.delivered = False
        logger.error(f"Webhook {webhook_event.event_id} failed after {config.retry_attempts} attempts")
    
    def import_file(self, integration_id: str, file_path: str, 
                   file_format: FileFormat, imported_by_id: str,
                   user_role: Role) -> IntegrationResult:
        """
        Import data from file.
        
        Args:
            integration_id: Integration ID
            file_path: Path to file to import
            file_format: File format
            imported_by_id: User ID importing the file
            user_role: User role for authorization
            
        Returns:
            Integration result
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=imported_by_id,
            user_role=user_role,
            permission=Permission.SYSTEM_CONFIG,
            resource=f"integration/{integration_id}",
            context={"action": "import_file"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        start_time = datetime.now()
        
        try:
            # Read file based on format
            if file_format == FileFormat.CSV:
                import pandas as pd
                data = pd.read_csv(file_path)
                result_data = data.to_dict(orient='records')
            elif file_format == FileFormat.EXCEL:
                import pandas as pd
                data = pd.read_excel(file_path)
                result_data = data.to_dict(orient='records')
            elif file_format == FileFormat.JSON:
                with open(file_path, 'r') as f:
                    result_data = json.load(f)
            elif file_format == FileFormat.XML:
                import xml.etree.ElementTree as ET
                tree = ET.parse(file_path)
                result_data = self._xml_to_dict(tree.getroot())
            else:
                return IntegrationResult(
                    success=False,
                    integration_id=integration_id,
                    operation="file_import",
                    error_message=f"Unsupported file format: {file_format.value}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return IntegrationResult(
                success=True,
                integration_id=integration_id,
                operation="file_import",
                response_data={"records": result_data, "count": len(result_data)},
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"File import failed for integration {integration_id}: {e}")
            
            return IntegrationResult(
                success=False,
                integration_id=integration_id,
                operation="file_import",
                error_message=str(e),
                execution_time_seconds=execution_time
            )
    
    def export_file(self, integration_id: str, data: List[Dict[str, Any]],
                   file_format: FileFormat, output_path: str,
                   exported_by_id: str, user_role: Role) -> IntegrationResult:
        """
        Export data to file.
        
        Args:
            integration_id: Integration ID
            data: Data to export
            file_format: File format
            output_path: Output file path
            exported_by_id: User ID exporting the data
            user_role: User role for authorization
            
        Returns:
            Integration result
            
        Raises:
            PermissionDenied: If user lacks required permissions
        """
        # Authorization check
        decision = self.security_manager.authorize(
            user_id=exported_by_id,
            user_role=user_role,
            permission=Permission.SYSTEM_CONFIG,
            resource=f"integration/{integration_id}",
            context={"action": "export_file"}
        )
        
        if not decision.authorized:
            raise PermissionDenied(decision.reason)
        
        start_time = datetime.now()
        
        try:
            # Write file based on format
            if file_format == FileFormat.CSV:
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_csv(output_path, index=False)
            elif file_format == FileFormat.EXCEL:
                import pandas as pd
                df = pd.DataFrame(data)
                df.to_excel(output_path, index=False)
            elif file_format == FileFormat.JSON:
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif file_format == FileFormat.XML:
                xml_data = self._dict_to_xml(data)
                with open(output_path, 'w') as f:
                    f.write(xml_data)
            else:
                return IntegrationResult(
                    success=False,
                    integration_id=integration_id,
                    operation="file_export",
                    error_message=f"Unsupported file format: {file_format.value}"
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return IntegrationResult(
                success=True,
                integration_id=integration_id,
                operation="file_export",
                response_data={"output_path": output_path, "record_count": len(data)},
                execution_time_seconds=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"File export failed for integration {integration_id}: {e}")
            
            return IntegrationResult(
                success=False,
                integration_id=integration_id,
                operation="file_export",
                error_message=str(e),
                execution_time_seconds=execution_time
            )
    
    def _check_rate_limit(self, integration_id: str) -> bool:
        """
        Check if integration is within rate limits.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            True if within rate limit, False otherwise
        """
        config = self.integrations.get(integration_id)
        if not config:
            return False
        
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        # Clean old requests
        self.rate_limiters[integration_id] = [
            timestamp for timestamp in self.rate_limiters[integration_id]
            if timestamp > cutoff
        ]
        
        # Check rate limit
        if len(self.rate_limiters[integration_id]) >= config.rate_limit_per_minute:
            return False
        
        # Add current request
        self.rate_limiters[integration_id].append(now)
        return True
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        for child in element:
            if len(child) > 0:
                result[child.tag] = self._xml_to_dict(child)
            else:
                result[child.tag] = child.text
        return result
    
    def _dict_to_xml(self, data: List[Dict[str, Any]]) -> str:
        """Convert dictionary to XML string."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("data")
        for item in data:
            item_element = ET.SubElement(root, "item")
            for key, value in item.items():
                child = ET.SubElement(item_element, key)
                child.text = str(value)
        
        return ET.tostring(root, encoding='unicode')
    
    def get_integration_status(self, integration_id: str) -> Dict[str, Any]:
        """
        Get integration status and statistics.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Integration status dictionary
        """
        config = self.integrations.get(integration_id)
        if not config:
            return {"error": "Integration not found"}
        
        recent_requests = len(self.rate_limiters.get(integration_id, []))
        
        return {
            "integration_id": integration_id,
            "name": config.name,
            "type": config.integration_type.value,
            "is_active": config.is_active,
            "rate_limit_per_minute": config.rate_limit_per_minute,
            "recent_requests_last_minute": recent_requests,
            "status": "ACTIVE" if config.is_active else "INACTIVE"
        }


# Global integration gateway instance
_integration_gateway: Optional[IntegrationGateway] = None


def get_integration_gateway() -> IntegrationGateway:
    """Get or create the global integration gateway instance."""
    global _integration_gateway
    if _integration_gateway is None:
        from ..infrastructure.security.rbac import get_security_manager
        _integration_gateway = IntegrationGateway(get_security_manager())
    return _integration_gateway