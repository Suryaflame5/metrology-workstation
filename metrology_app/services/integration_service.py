"""
Integration Service for Premium Edition.

Provides comprehensive API endpoints, database connectors, file import/export,
ERP/PLM integration, webhook systems, and external system authentication.
"""

import json
import os
import uuid
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from enum import Enum
import hashlib
import hmac
import base64

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from ..db import DB_PATH, list_calculations, get_calculation
from ..config import ensure_app_directories
import sqlite3


class IntegrationType(Enum):
    """Integration type enumeration."""
    REST_API = "REST_API"
    DATABASE = "DATABASE"
    FILE_IMPORT = "FILE_IMPORT"
    FILE_EXPORT = "FILE_EXPORT"
    WEBHOOK = "WEBHOOK"
    ERP_SYSTEM = "ERP_SYSTEM"
    PLM_SYSTEM = "PLM_SYSTEM"
    CUSTOM = "CUSTOM"


class DatabaseType(Enum):
    """Supported database types."""
    SQLITE = "SQLITE"
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    SQL_SERVER = "SQL_SERVER"
    ORACLE = "ORACLE"


class FileFormat(Enum):
    """Supported file formats."""
    CSV = "CSV"
    EXCEL = "EXCEL"
    JSON = "JSON"
    XML = "XML"
    PDF = "PDF"


class AuthenticationType(Enum):
    """Authentication types for external systems."""
    NONE = "NONE"
    BASIC_AUTH = "BASIC_AUTH"
    API_KEY = "API_KEY"
    OAUTH2 = "OAUTH2"
    JWT = "JWT"
    CUSTOM_HEADER = "CUSTOM_HEADER"


class IntegrationService:
    """
    Enterprise-grade integration service providing comprehensive external system
    connectivity, data exchange, and automation capabilities.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._init_integration_database()
        self._load_api_endpoints()
    
    def _init_integration_database(self):
        """Initialize integration database schema."""
        ensure_app_directories()
        
        integration_db_path = os.path.join(os.path.dirname(self.db_path), "metrology_integrations.db")
        
        conn = sqlite3.connect(integration_db_path)
        cursor = conn.cursor()
        
        # External connections table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS external_connections (
                id TEXT PRIMARY KEY,
                connection_name TEXT UNIQUE NOT NULL,
                connection_type TEXT NOT NULL,
                database_type TEXT,
                host TEXT,
                port INTEGER,
                database_name TEXT,
                username TEXT,
                password_encrypted TEXT,
                connection_string TEXT,
                authentication_type TEXT,
                api_key_encrypted TEXT,
                oauth_config TEXT,
                custom_headers TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_tested TEXT,
                test_result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Integration logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS integration_logs (
                id TEXT PRIMARY KEY,
                connection_id TEXT,
                integration_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                status TEXT NOT NULL,
                request_data TEXT,
                response_data TEXT,
                error_message TEXT,
                processing_time_ms INTEGER,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (connection_id) REFERENCES external_connections(id)
            )
        """)
        
        # Data mappings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_mappings (
                id TEXT PRIMARY KEY,
                connection_id TEXT NOT NULL,
                mapping_name TEXT NOT NULL,
                source_system TEXT,
                target_system TEXT,
                field_mappings TEXT NOT NULL,
                transformation_rules TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (connection_id) REFERENCES external_connections(id)
            )
        """)
        
        # Webhook subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webhook_subscriptions (
                id TEXT PRIMARY KEY,
                webhook_name TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                endpoint_url TEXT NOT NULL,
                secret_key TEXT,
                authentication_type TEXT,
                auth_config TEXT,
                retry_policy TEXT,
                is_active BOOLEAN DEFAULT 1,
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # File transfer history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_transfers (
                id TEXT PRIMARY KEY,
                transfer_type TEXT NOT NULL,
                file_format TEXT NOT NULL,
                source_path TEXT,
                destination_path TEXT,
                record_count INTEGER,
                status TEXT NOT NULL,
                error_message TEXT,
                transfer_time_ms INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_api_endpoints(self):
        """Load enhanced API endpoint configurations."""
        self.api_endpoints = {
            "calculations": {
                "list": "/api/v2/calculations",
                "get": "/api/v2/calculations/{id}",
                "create": "/api/v2/calculations",
                "update": "/api/v2/calculations/{id}",
                "delete": "/api/v2/calculations/{id}",
                "export": "/api/v2/calculations/export"
            },
            "instruments": {
                "list": "/api/v2/instruments",
                "get": "/api/v2/instruments/{id}",
                "create": "/api/v2/instruments",
                "update": "/api/v2/instruments/{id}",
                "delete": "/api/v2/instruments/{id}",
                "calibration_history": "/api/v2/instruments/{id}/calibration-history"
            },
            "analytics": {
                "spc": "/api/v2/analytics/spc/{instrument_id}",
                "trends": "/api/v2/analytics/trends/{instrument_id}",
                "anomalies": "/api/v2/anomalies/{instrument_id}",
                "control_charts": "/api/v2/control-charts/{instrument_id}",
                "fleet": "/api/v2/analytics/fleet"
            },
            "certificates": {
                "list": "/api/v2/certificates",
                "get": "/api/v2/certificates/{id}",
                "create": "/api/v2/certificates",
                "generate_pdf": "/api/v2/certificates/{id}/generate-pdf",
                "sign": "/api/v2/certificates/{id}/sign",
                "batch": "/api/v2/certificates/batch"
            },
            "fleet": {
                "list": "/api/v2/fleet/instruments",
                "analytics": "/api/v2/fleet/analytics",
                "schedule": "/api/v2/fleet/calibration-schedule",
                "maintenance": "/api/v2/fleet/maintenance"
            },
            "integrations": {
                "connections": "/api/v2/integrations/connections",
                "test": "/api/v2/integrations/connections/{id}/test",
                "sync": "/api/v2/integrations/connections/{id}/sync",
                "mappings": "/api/v2/integrations/mappings",
                "webhooks": "/api/v2/integrations/webhooks"
            }
        }
    
    def _get_integration_db_path(self) -> str:
        """Get the integration database path."""
        return os.path.join(os.path.dirname(self.db_path), "metrology_integrations.db")
    
    def create_database_connection(self, connection_name: str, database_type: str,
                                 host: str, port: int, database_name: str,
                                 username: str, password: str,
                                 authentication_type: str = AuthenticationType.BASIC_AUTH.value) -> Dict[str, Any]:
        """
        Create a database connection configuration.
        """
        connection_id = f"DB-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Encrypt password (simple base64 for demo - use proper encryption in production)
        password_encrypted = base64.b64encode(password.encode()).decode('utf-8')
        
        conn_record = {
            "id": connection_id,
            "connection_name": connection_name,
            "connection_type": IntegrationType.DATABASE.value,
            "database_type": database_type,
            "host": host,
            "port": port,
            "database_name": database_name,
            "username": username,
            "password_encrypted": password_encrypted,
            "connection_string": None,
            "authentication_type": authentication_type,
            "api_key_encrypted": None,
            "oauth_config": None,
            "custom_headers": None,
            "is_active": True,
            "last_tested": None,
            "test_result": None,
            "created_at": now,
            "updated_at": now
        }
        
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO external_connections (
                    id, connection_name, connection_type, database_type, host, port,
                    database_name, username, password_encrypted, connection_string,
                    authentication_type, api_key_encrypted, oauth_config, custom_headers,
                    is_active, last_tested, test_result, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                connection_record["id"], connection_record["connection_name"],
                connection_record["connection_type"], connection_record["database_type"],
                connection_record["host"], connection_record["port"],
                connection_record["database_name"], connection_record["username"],
                connection_record["password_encrypted"], connection_record["connection_string"],
                connection_record["authentication_type"], connection_record["api_key_encrypted"],
                connection_record["oauth_config"], connection_record["custom_headers"],
                connection_record["is_active"], connection_record["last_tested"],
                connection_record["test_result"], connection_record["created_at"],
                connection_record["updated_at"]
            ))
            conn.commit()
            return connection_record
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Connection with name '{connection_name}' already exists")
        finally:
            conn.close()
    
    def test_database_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test a database connection."""
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM external_connections WHERE id = ?", (connection_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Connection {connection_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        connection = dict(zip(columns, row))
        conn.close()
        
        if not SQLALCHEMY_AVAILABLE:
            return {
                "connection_id": connection_id,
                "status": "FAILED",
                "error": "SQLAlchemy not available. Install with: pip install sqlalchemy"
            }
        
        try:
            # Build connection string
            if connection["database_type"] == DatabaseType.POSTGRESQL.value:
                conn_str = f"postgresql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            elif connection["database_type"] == DatabaseType.MYSQL.value:
                conn_str = f"mysql+pymysql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            elif connection["database_type"] == DatabaseType.SQL_SERVER.value:
                conn_str = f"mssql+pyodbc://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            else:
                return {
                    "connection_id": connection_id,
                    "status": "FAILED",
                    "error": f"Database type {connection['database_type']} not supported"
                }
            
            # Test connection
            engine = create_engine(conn_str)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Update connection record
            conn = sqlite3.connect(self._get_integration_db_path())
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE external_connections 
                SET last_tested = ?, test_result = 'SUCCESS', updated_at = ?
                WHERE id = ?
            """, (now, now, connection_id))
            conn.commit()
            conn.close()
            
            return {
                "connection_id": connection_id,
                "status": "SUCCESS",
                "message": "Database connection successful",
                "tested_at": now
            }
            
        except Exception as e:
            # Update connection record with failure
            conn = sqlite3.connect(self._get_integration_db_path())
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE external_connections 
                SET last_tested = ?, test_result = 'FAILED', updated_at = ?
                WHERE id = ?
            """, (now, now, connection_id))
            conn.commit()
            conn.close()
            
            return {
                "connection_id": connection_id,
                "status": "FAILED",
                "error": str(e)
            }
    
    def export_data_to_database(self, connection_id: str, data: List[Dict[str, Any]],
                               table_name: str, operation: str = "INSERT") -> Dict[str, Any]:
        """Export metrology data to external database."""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy is required for database export. Install with: pip install sqlalchemy")
        
        # Get connection details
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM external_connections WHERE id = ?", (connection_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Connection {connection_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        connection = dict(zip(columns, row))
        conn.close()
        
        try:
            # Build connection string
            if connection["database_type"] == DatabaseType.POSTGRESQL.value:
                conn_str = f"postgresql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            elif connection["database_type"] == DatabaseType.MYSQL.value:
                conn_str = f"mysql+pymysql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            else:
                raise ValueError(f"Database type {connection['database_type']} not supported for export")
            
            # Create engine and export data
            engine = create_engine(conn_str)
            df = pd.DataFrame(data)
            
            if operation == "INSERT":
                df.to_sql(table_name, engine, if_exists='append', index=False)
            elif operation == "REPLACE":
                df.to_sql(table_name, engine, if_exists='replace', index=False)
            elif operation == "UPDATE":
                # Implement upsert logic based on primary key
                df.to_sql(table_name, engine, if_exists='append', index=False)
            
            # Log the integration
            self._log_integration(connection_id, IntegrationType.DATABASE.value, "EXPORT",
                                "SUCCESS", len(data), None, None)
            
            return {
                "connection_id": connection_id,
                "table_name": table_name,
                "operation": operation,
                "records_exported": len(data),
                "status": "SUCCESS"
            }
            
        except Exception as e:
            self._log_integration(connection_id, IntegrationType.DATABASE.value, "EXPORT",
                                "FAILED", 0, None, str(e))
            raise
    
    def import_data_from_database(self, connection_id: str, query: str) -> List[Dict[str, Any]]:
        """Import data from external database."""
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy is required for database import. Install with: pip install sqlalchemy")
        
        # Get connection details
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM external_connections WHERE id = ?", (connection_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Connection {connection_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        connection = dict(zip(columns, row))
        conn.close()
        
        try:
            # Build connection string
            if connection["database_type"] == DatabaseType.POSTGRESQL.value:
                conn_str = f"postgresql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            elif connection["database_type"] == DatabaseType.MYSQL.value:
                conn_str = f"mysql+pymysql://{connection['username']}:{base64.b64decode(connection['password_encrypted']).decode()}@{connection['host']}:{connection['port']}/{connection['database_name']}"
            else:
                raise ValueError(f"Database type {connection['database_type']} not supported for import")
            
            # Create engine and import data
            engine = create_engine(conn_str)
            df = pd.read_sql(query, engine)
            
            data = df.to_dict('records')
            
            # Log the integration
            self._log_integration(connection_id, IntegrationType.DATABASE.value, "IMPORT",
                                "SUCCESS", len(data), None, None)
            
            return data
            
        except Exception as e:
            self._log_integration(connection_id, IntegrationType.DATABASE.value, "IMPORT",
                                "FAILED", 0, None, str(e))
            raise
    
    def export_to_file(self, data: List[Dict[str, Any]], file_format: str,
                      file_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Export data to various file formats."""
        start_time = datetime.now()
        
        try:
            if file_format == FileFormat.CSV.value:
                self._export_to_csv(data, file_path, include_metadata)
            elif file_format == FileFormat.EXCEL.value:
                self._export_to_excel(data, file_path, include_metadata)
            elif file_format == FileFormat.JSON.value:
                self._export_to_json(data, file_path, include_metadata)
            elif file_format == FileFormat.XML.value:
                self._export_to_xml(data, file_path, include_metadata)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log file transfer
            self._log_file_transfer(FileFormat.FILE_EXPORT.value, file_format, 
                                   None, file_path, len(data), "SUCCESS", 
                                   None, processing_time)
            
            return {
                "file_path": file_path,
                "file_format": file_format,
                "records_exported": len(data),
                "processing_time_ms": processing_time,
                "status": "SUCCESS"
            }
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_file_transfer(FileFormat.FILE_EXPORT.value, file_format,
                                   None, file_path, 0, "FAILED", str(e), processing_time)
            raise
    
    def _export_to_csv(self, data: List[Dict[str, Any]], file_path: str, include_metadata: bool):
        """Export data to CSV format."""
        if not data:
            raise ValueError("No data to export")
        
        # Flatten nested dictionaries
        flattened_data = []
        for record in data:
            flattened = self._flatten_dict(record)
            if include_metadata:
                flattened['_export_timestamp'] = datetime.now(timezone.utc).isoformat()
                flattened['_export_version'] = '1.0'
            flattened_data.append(flattened)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = set()
            for record in flattened_data:
                fieldnames.update(record.keys())
            
            writer = csv.DictWriter(csvfile, fieldnames=list(fieldnames))
            writer.writeheader()
            writer.writerows(flattened_data)
    
    def _export_to_excel(self, data: List[Dict[str, Any]], file_path: str, include_metadata: bool):
        """Export data to Excel format."""
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel export. Install with: pip install pandas")
        
        # Flatten and prepare data
        flattened_data = []
        for record in data:
            flattened = self._flatten_dict(record)
            if include_metadata:
                flattened['_export_timestamp'] = datetime.now(timezone.utc).isoformat()
                flattened['_export_version'] = '1.0'
            flattened_data.append(flattened)
        
        df = pd.DataFrame(flattened_data)
        df.to_excel(file_path, index=False, engine='openpyxl')
    
    def _export_to_json(self, data: List[Dict[str, Any]], file_path: str, include_metadata: bool):
        """Export data to JSON format."""
        export_data = {
            "data": data,
            "metadata": {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "export_version": "1.0",
                "record_count": len(data)
            } if include_metadata else None
        }
        
        with open(file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, default=str)
    
    def _export_to_xml(self, data: List[Dict[str, Any]], file_path: str, include_metadata: bool):
        """Export data to XML format."""
        root = ET.Element("MetrologyData")
        
        if include_metadata:
            metadata = ET.SubElement(root, "Metadata")
            ET.SubElement(metadata, "ExportTimestamp").text = datetime.now(timezone.utc).isoformat()
            ET.SubElement(metadata, "ExportVersion").text = "1.0"
            ET.SubElement(metadata, "RecordCount").text = str(len(data))
        
        records_element = ET.SubElement(root, "Records")
        
        for record in data:
            record_element = ET.SubElement(records_element, "Record")
            self._dict_to_xml(record, record_element)
        
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def _dict_to_xml(self, data: Dict[str, Any], parent_element):
        """Convert dictionary to XML elements."""
        for key, value in data.items():
            if isinstance(value, dict):
                child_element = ET.SubElement(parent_element, key)
                self._dict_to_xml(value, child_element)
            elif isinstance(value, list):
                list_element = ET.SubElement(parent_element, key)
                for item in value:
                    item_element = ET.SubElement(list_element, "Item")
                    if isinstance(item, dict):
                        self._dict_to_xml(item, item_element)
                    else:
                        item_element.text = str(item)
            else:
                child_element = ET.SubElement(parent_element, key)
                child_element.text = str(value)
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionaries."""
        items = []
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            if isinstance(value, dict):
                items.extend(self._flatten_dict(value, new_key, sep=sep).items())
            elif isinstance(value, list):
                # Handle lists by converting to string representation
                items.append((new_key, json.dumps(value)))
            else:
                items.append((new_key, value))
        return dict(items)
    
    def import_from_file(self, file_path: str, file_format: str) -> List[Dict[str, Any]]:
        """Import data from various file formats."""
        start_time = datetime.now()
        
        try:
            if file_format == FileFormat.CSV.value:
                data = self._import_from_csv(file_path)
            elif file_format == FileFormat.EXCEL.value:
                data = self._import_from_excel(file_path)
            elif file_format == FileFormat.JSON.value:
                data = self._import_from_json(file_path)
            elif file_format == FileFormat.XML.value:
                data = self._import_from_xml(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log file transfer
            self._log_file_transfer(FileFormat.FILE_IMPORT.value, file_format,
                                   file_path, None, len(data), "SUCCESS",
                                   None, processing_time)
            
            return data
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._log_file_transfer(FileFormat.FILE_IMPORT.value, file_format,
                                   file_path, None, 0, "FAILED", str(e), processing_time)
            raise
    
    def _import_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Import data from CSV format."""
        data = []
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Filter out metadata fields
                filtered_row = {k: v for k, v in row.items() if not k.startswith('_')}
                data.append(filtered_row)
        return data
    
    def _import_from_excel(self, file_path: str) -> List[Dict[str, Any]]:
        """Import data from Excel format."""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel import. Install with: pip install pandas")
        
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is required for Excel import. Install with: pip install openpyxl")
        
        df = pd.read_excel(file_path, engine='openpyxl')
        
        # Filter out metadata columns
        df = df[[col for col in df.columns if not col.startswith('_')]]
        
        return df.to_dict('records')
    
    def _import_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Import data from JSON format."""
        with open(file_path, 'r', encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
        
        if isinstance(data, dict) and 'data' in data:
            return data['data']
        elif isinstance(data, list):
            return data
        else:
            return [data]
    
    def _import_from_xml(self, file_path: str) -> List[Dict[str, Any]]:
        """Import data from XML format."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        data = []
        records_element = root.find('Records')
        if records_element is not None:
            for record_element in records_element.findall('Record'):
                record = self._xml_to_dict(record_element)
                data.append(record)
        
        return data
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        for child in element:
            if len(child) > 0:
                # Nested element
                child_data = self._xml_to_dict(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            else:
                # Simple element
                result[child.tag] = child.text
        return result
    
    def create_webhook_subscription(self, webhook_name: str, event_type: str,
                                    endpoint_url: str, secret_key: Optional[str] = None,
                                    authentication_type: str = AuthenticationType.API_KEY.value,
                                    auth_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a webhook subscription for event notifications."""
        webhook_id = f"WEBHOOK-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        webhook_record = {
            "id": webhook_id,
            "webhook_name": webhook_name,
            "event_type": event_type,
            "endpoint_url": endpoint_url,
            "secret_key": secret_key,
            "authentication_type": authentication_type,
            "auth_config": json.dumps(auth_config) if auth_config else None,
            "retry_policy": json.dumps({"max_retries": 3, "retry_delay": 60}),
            "is_active": True,
            "last_triggered": None,
            "trigger_count": 0,
            "created_at": now,
            "updated_at": now
        }
        
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO webhook_subscriptions (
                    id, webhook_name, event_type, endpoint_url, secret_key,
                    authentication_type, auth_config, retry_policy, is_active,
                    last_triggered, trigger_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                webhook_record["id"], webhook_record["webhook_name"],
                webhook_record["event_type"], webhook_record["endpoint_url"],
                webhook_record["secret_key"], webhook_record["authentication_type"],
                webhook_record["auth_config"], webhook_record["retry_policy"],
                webhook_record["is_active"], webhook_record["last_triggered"],
                webhook_record["trigger_count"], webhook_record["created_at"],
                webhook_record["updated_at"]
            ))
            conn.commit()
            return webhook_record
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Webhook with name '{webhook_name}' already exists")
        finally:
            conn.close()
    
    def trigger_webhook(self, webhook_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a webhook with event data."""
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM webhook_subscriptions WHERE id = ?", (webhook_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Webhook {webhook_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        webhook = dict(zip(columns, row))
        conn.close()
        
        if not webhook["is_active"]:
            return {"webhook_id": webhook_id, "status": "SKIPPED", "reason": "Webhook is inactive"}
        
        try:
            # Prepare webhook payload
            payload = {
                "webhook_id": webhook_id,
                "event_type": webhook["event_type"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": event_data
            }
            
            # Add signature if secret key is provided
            headers = {"Content-Type": "application/json"}
            if webhook["secret_key"]:
                signature = self._generate_signature(payload, webhook["secret_key"])
                headers["X-Signature"] = signature
            
            # Simulate webhook call (in production, use requests library)
            # response = requests.post(webhook["endpoint_url"], json=payload, headers=headers)
            
            # Update webhook record
            now = datetime.now(timezone.utc).isoformat()
            conn = sqlite3.connect(self._get_integration_db_path())
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE webhook_subscriptions 
                SET last_triggered = ?, trigger_count = trigger_count + 1, updated_at = ?
                WHERE id = ?
            """, (now, now, webhook_id))
            conn.commit()
            conn.close()
            
            # Log the integration
            self._log_integration(webhook_id, IntegrationType.WEBHOOK.value, "OUTBOUND",
                                "SUCCESS", 1, json.dumps(payload), None)
            
            return {
                "webhook_id": webhook_id,
                "status": "SUCCESS",
                "endpoint_url": webhook["endpoint_url"],
                "triggered_at": now
            }
            
        except Exception as e:
            self._log_integration(webhook_id, IntegrationType.WEBHOOK.value, "OUTBOUND",
                                "FAILED", 0, json.dumps(payload), str(e))
            raise
    
    def _generate_signature(self, payload: Dict[str, Any], secret_key: str) -> str:
        """Generate HMAC signature for webhook verification."""
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _log_integration(self, connection_id: str, integration_type: str,
                        direction: str, status: str, record_count: int,
                        request_data: Optional[str], error_message: Optional[str]):
        """Log integration activity for audit trail."""
        log_id = f"LOG-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO integration_logs (
                id, connection_id, integration_type, direction, status,
                request_data, response_data, error_message, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, connection_id, integration_type, direction, status,
              request_data, None, error_message, now))
        
        conn.commit()
        conn.close()
    
    def _log_file_transfer(self, transfer_type: str, file_format: str,
                          source_path: Optional[str], destination_path: Optional[str],
                          record_count: int, status: str, error_message: Optional[str],
                          processing_time: float):
        """Log file transfer activity."""
        transfer_id = f"TRANSFER-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO file_transfers (
                id, transfer_type, file_format, source_path, destination_path,
                record_count, status, error_message, transfer_time_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (transfer_id, transfer_type, file_format, source_path, destination_path,
              record_count, status, error_message, processing_time, now))
        
        conn.commit()
        conn.close()
    
    def get_api_endpoints(self) -> Dict[str, Any]:
        """Get available API endpoints."""
        return self.api_endpoints
    
    def get_integration_logs(self, connection_id: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """Get integration logs with optional filtering."""
        conn = sqlite3.connect(self._get_integration_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM integration_logs WHERE 1=1"
        params = []
        
        if connection_id:
            query += " AND connection_id = ?"
            params.append(connection_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        logs = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return logs


# Singleton instance for service layer
_integration_service = None

def get_integration_service(db_path: Optional[str] = None) -> IntegrationService:
    """Get or create the integration service singleton."""
    global _integration_service
    if _integration_service is None:
        _integration_service = IntegrationService(db_path)
    return _integration_service

# Convenience functions for common operations
def create_database_connection(connection_name: str, database_type: str, host: str,
                             port: int, database_name: str, username: str, password: str,
                             authentication_type: str = AuthenticationType.BASIC_AUTH.value,
                             db_path: Optional[str] = None) -> Dict[str, Any]:
    """Create a database connection."""
    service = get_integration_service(db_path)
    return service.create_database_connection(connection_name, database_type, host, port,
                                           database_name, username, password, authentication_type)

def export_to_file(data: List[Dict[str, Any]], file_format: str, file_path: str,
                  include_metadata: bool = True, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Export data to file."""
    service = get_integration_service(db_path)
    return service.export_to_file(data, file_format, file_path, include_metadata)

def import_from_file(file_path: str, file_format: str,
                     db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Import data from file."""
    service = get_integration_service(db_path)
    return service.import_from_file(file_path, file_format)

def create_webhook_subscription(webhook_name: str, event_type: str, endpoint_url: str,
                               secret_key: Optional[str] = None,
                               authentication_type: str = AuthenticationType.API_KEY.value,
                               auth_config: Optional[Dict[str, Any]] = None,
                               db_path: Optional[str] = None) -> Dict[str, Any]:
    """Create webhook subscription."""
    service = get_integration_service(db_path)
    return service.create_webhook_subscription(webhook_name, event_type, endpoint_url,
                                             secret_key, authentication_type, auth_config)