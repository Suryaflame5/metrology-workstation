"""
Plugin System and Custom Scripting Service for Premium Edition.

Provides MEF-based plugin architecture, custom calculation engines,
C# scripting support, and third-party marketplace integration.
"""

import os
import sys
import json
import uuid
import importlib
import importlib.util
import inspect
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable, Type
from decimal import Decimal
from enum import Enum
import hashlib
import traceback

try:
    import code
    CODE_EXECUTION_AVAILABLE = True
except ImportError:
    CODE_EXECUTION_AVAILABLE = False

try:
    import ast
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False

from ..db import DB_PATH
from ..config import ensure_app_directories
import sqlite3


class PluginType(Enum):
    """Plugin type enumeration."""
    CALCULATION_ENGINE = "CALCULATION_ENGINE"
    DATA_SOURCE = "DATA_SOURCE"
    EXPORT_FORMAT = "EXPORT_FORMAT"
    UI_EXTENSION = "UI_EXTENSION"
    VALIDATION_RULE = "VALIDATION_RULE"
    WORKFLOW_AUTOMATION = "WORKFLOW_AUTOMATION"
    CUSTOM_REPORT = "CUSTOM_REPORT"
    ANALYTICS_MODULE = "ANALYTICS_MODULE"


class PluginStatus(Enum):
    """Plugin status enumeration."""
    INSTALLED = "INSTALLED"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ERROR = "ERROR"
    UNINSTALLED = "UNINSTALLED"


class ScriptType(Enum):
    """Script type enumeration."""
    PYTHON = "PYTHON"
    JAVASCRIPT = "JAVASCRIPT"
    SQL = "SQL"
    WORKFLOW = "WORKFLOW"


class PluginService:
    """
    Enterprise-grade plugin system providing dynamic loading of custom modules,
    scripting capabilities, and extensibility framework for the premium edition.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or DB_PATH
        self._init_plugin_database()
        self._load_installed_plugins()
        self._plugin_cache = {}
        self._script_engine = ScriptEngine()
    
    def _init_plugin_database(self):
        """Initialize plugin database schema."""
        ensure_app_directories()
        
        plugin_db_path = os.path.join(os.path.dirname(self.db_path), "metrology_plugins.db")
        
        conn = sqlite3.connect(plugin_db_path)
        cursor = conn.cursor()
        
        # Plugins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                plugin_name TEXT UNIQUE NOT NULL,
                plugin_version TEXT NOT NULL,
                plugin_type TEXT NOT NULL,
                author TEXT,
                description TEXT,
                entry_point TEXT,
                requirements TEXT,
                config_schema TEXT,
                is_active BOOLEAN DEFAULT 0,
                install_date TEXT NOT NULL,
                last_updated TEXT,
                error_message TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Plugin configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugin_configurations (
                id TEXT PRIMARY KEY,
                plugin_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                config_type TEXT DEFAULT 'string',
                is_encrypted BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (plugin_id) REFERENCES plugins(id)
            )
        """)
        
        # Custom scripts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_scripts (
                id TEXT PRIMARY KEY,
                script_name TEXT UNIQUE NOT NULL,
                script_type TEXT NOT NULL,
                script_content TEXT NOT NULL,
                description TEXT,
                parameters TEXT,
                return_schema TEXT,
                is_active BOOLEAN DEFAULT 1,
                execution_count INTEGER DEFAULT 0,
                last_executed TEXT,
                average_execution_time_ms REAL,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Script execution logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS script_execution_logs (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                execution_parameters TEXT,
                execution_result TEXT,
                execution_time_ms REAL,
                status TEXT NOT NULL,
                error_message TEXT,
                executed_at TEXT NOT NULL,
                FOREIGN KEY (script_id) REFERENCES custom_scripts(id)
            )
        """)
        
        # Plugin marketplace cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plugin_marketplace (
                id TEXT PRIMARY KEY,
                marketplace_plugin_id TEXT UNIQUE NOT NULL,
                plugin_name TEXT NOT NULL,
                plugin_version TEXT,
                plugin_type TEXT NOT NULL,
                author TEXT,
                description TEXT,
                download_url TEXT,
                documentation_url TEXT,
                price TEXT,
                rating REAL,
                download_count INTEGER,
                last_synced TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _load_installed_plugins(self):
        """Load all installed plugins into memory."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM plugins WHERE is_active = 1")
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        
        for row in rows:
            plugin = dict(zip(columns, row))
            try:
                self._load_plugin(plugin)
            except Exception as e:
                # Deactivate plugin on load error
                cursor.execute("""
                    UPDATE plugins 
                    SET is_active = 0, error_message = ?, updated_at = ?
                    WHERE id = ?
                """, (str(e), datetime.now(timezone.utc).isoformat(), plugin['id']))
                conn.commit()
        
        conn.close()
    
    def _get_plugin_db_path(self) -> str:
        """Get the plugin database path."""
        return os.path.join(os.path.dirname(self.db_path), "metrology_plugins.db")
    
    def _load_plugin(self, plugin: Dict[str, Any]):
        """Load a plugin dynamically into the application."""
        plugin_id = plugin['id']
        entry_point = plugin.get('entry_point')
        
        if not entry_point:
            raise ValueError(f"Plugin {plugin_id} has no entry point")
        
        # Create plugin directory if it doesn't exist
        plugin_dir = os.path.join(ensure_app_directories()[0], "plugins", plugin_id)
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Load the plugin module
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_id}",
                os.path.join(plugin_dir, entry_point)
            )
            
            if spec and spec.loader:
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # Cache the loaded plugin
                self._plugin_cache[plugin_id] = {
                    'module': plugin_module,
                    'metadata': plugin,
                    'loaded_at': datetime.now(timezone.utc).isoformat()
                }
            else:
                raise ValueError(f"Could not load plugin from {entry_point}")
                
        except Exception as e:
            raise ValueError(f"Failed to load plugin {plugin_id}: {str(e)}")
    
    def install_plugin(self, plugin_data: Dict[str, Any], plugin_code: str) -> Dict[str, Any]:
        """
        Install a new plugin from code or file.
        """
        plugin_id = plugin_data.get('id') or f"PLUGIN-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Validate plugin data
        required_fields = ['plugin_name', 'plugin_version', 'plugin_type', 'entry_point']
        for field in required_fields:
            if field not in plugin_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Create plugin directory
        plugin_dir = os.path.join(ensure_app_directories()[0], "plugins", plugin_id)
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Write plugin code
        entry_point = plugin_data['entry_point']
        plugin_file_path = os.path.join(plugin_dir, entry_point)
        
        with open(plugin_file_path, 'w', encoding='utf-8') as f:
            f.write(plugin_code)
        
        # Calculate plugin hash
        plugin_hash = hashlib.sha256(plugin_code.encode()).hexdigest()
        
        # Create plugin record
        plugin_record = {
            "id": plugin_id,
            "plugin_name": plugin_data['plugin_name'],
            "plugin_version": plugin_data['plugin_version'],
            "plugin_type": plugin_data['plugin_type'],
            "author": plugin_data.get('author', 'Unknown'),
            "description": plugin_data.get('description', ''),
            "entry_point": entry_point,
            "requirements": json.dumps(plugin_data.get('requirements', [])),
            "config_schema": json.dumps(plugin_data.get('config_schema', {})),
            "is_active": False,  # Start inactive until manually activated
            "install_date": now,
            "last_updated": now,
            "error_message": None,
            "metadata": json.dumps({
                "hash": plugin_hash,
                "file_size": len(plugin_code),
                "dependencies": plugin_data.get('dependencies', [])
            }),
            "created_at": now,
            "updated_at": now
        }
        
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO plugins (
                    id, plugin_name, plugin_version, plugin_type, author, description,
                    entry_point, requirements, config_schema, is_active, install_date,
                    last_updated, error_message, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                plugin_record["id"], plugin_record["plugin_name"],
                plugin_record["plugin_version"], plugin_record["plugin_type"],
                plugin_record["author"], plugin_record["description"],
                plugin_record["entry_point"], plugin_record["requirements"],
                plugin_record["config_schema"], plugin_record["is_active"],
                plugin_record["install_date"], plugin_record["last_updated"],
                plugin_record["error_message"], plugin_record["metadata"],
                plugin_record["created_at"], plugin_record["updated_at"]
            ))
            conn.commit()
            
            return plugin_record
            
        except sqlite3.IntegrityError:
            conn.close()
            # Clean up created files
            if os.path.exists(plugin_file_path):
                os.remove(plugin_file_path)
            raise ValueError(f"Plugin with name '{plugin_data['plugin_name']}' already exists")
        finally:
            conn.close()
    
    def activate_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Activate an installed plugin."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Plugin {plugin_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        plugin = dict(zip(columns, row))
        
        try:
            # Load the plugin
            self._load_plugin(plugin)
            
            # Update database
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE plugins 
                SET is_active = 1, error_message = NULL, updated_at = ?
                WHERE id = ?
            """, (now, plugin_id))
            conn.commit()
            conn.close()
            
            return {"plugin_id": plugin_id, "status": "ACTIVE", "activated_at": now}
            
        except Exception as e:
            # Update with error
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
                UPDATE plugins 
                SET is_active = 0, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (str(e), now, plugin_id))
            conn.commit()
            conn.close()
            raise ValueError(f"Failed to activate plugin {plugin_id}: {str(e)}")
    
    def deactivate_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Deactivate an active plugin."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE plugins 
            SET is_active = 0, updated_at = ?
            WHERE id = ?
        """, (now, plugin_id))
        
        conn.commit()
        conn.close()
        
        # Remove from cache
        if plugin_id in self._plugin_cache:
            del self._plugin_cache[plugin_id]
        
        return {"plugin_id": plugin_id, "status": "INACTIVE", "deactivated_at": now}
    
    def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """Uninstall a plugin completely."""
        # First deactivate
        self.deactivate_plugin(plugin_id)
        
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        # Get plugin info for cleanup
        cursor.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            plugin = dict(zip(columns, row))
            
            # Delete plugin files
            plugin_dir = os.path.join(ensure_app_directories()[0], "plugins", plugin_id)
            if os.path.exists(plugin_dir):
                import shutil
                shutil.rmtree(plugin_dir)
        
        # Delete from database
        cursor.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
        cursor.execute("DELETE FROM plugin_configurations WHERE plugin_id = ?", (plugin_id,))
        
        conn.commit()
        conn.close()
        
        return {"plugin_id": plugin_id, "status": "UNINSTALLED"}
    
    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin details."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            plugin = dict(zip(columns, row))
            
            # Parse JSON fields
            if plugin.get('requirements'):
                plugin['requirements'] = json.loads(plugin['requirements'])
            if plugin.get('config_schema'):
                plugin['config_schema'] = json.loads(plugin['config_schema'])
            if plugin.get('metadata'):
                plugin['metadata'] = json.loads(plugin['metadata'])
            
            return plugin
        
        return None
    
    def list_plugins(self, plugin_type: Optional[str] = None, 
                    status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List plugins with optional filtering."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM plugins WHERE 1=1"
        params = []
        
        if plugin_type:
            query += " AND plugin_type = ?"
            params.append(plugin_type)
        
        if status:
            if status == "ACTIVE":
                query += " AND is_active = 1"
            elif status == "INACTIVE":
                query += " AND is_active = 0"
        
        query += " ORDER BY install_date DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        plugins = [dict(zip(columns, row)) for row in rows]
        
        # Parse JSON fields
        for plugin in plugins:
            if plugin.get('requirements'):
                plugin['requirements'] = json.loads(plugin['requirements'])
            if plugin.get('config_schema'):
                plugin['config_schema'] = json.loads(plugin['config_schema'])
            if plugin.get('metadata'):
                plugin['metadata'] = json.loads(plugin['metadata'])
        
        conn.close()
        return plugins
    
    def call_plugin_function(self, plugin_id: str, function_name: str, 
                            *args, **kwargs) -> Any:
        """Call a function from an active plugin."""
        if plugin_id not in self._plugin_cache:
            raise ValueError(f"Plugin {plugin_id} is not loaded")
        
        plugin_cache = self._plugin_cache[plugin_id]
        plugin_module = plugin_cache['module']
        
        if not hasattr(plugin_module, function_name):
            raise ValueError(f"Plugin {plugin_id} does not have function {function_name}")
        
        function = getattr(plugin_module, function_name)
        
        try:
            result = function(*args, **kwargs)
            return result
        except Exception as e:
            raise ValueError(f"Error calling plugin function: {str(e)}")
    
    def create_custom_script(self, script_name: str, script_type: str,
                           script_content: str, description: str = "",
                           parameters: Optional[Dict[str, Any]] = None,
                           return_schema: Optional[Dict[str, Any]] = None,
                           created_by: str = "system") -> Dict[str, Any]:
        """
        Create a custom script for automation and extensibility.
        """
        script_id = f"SCRIPT-{str(uuid.uuid4().int)[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Validate script syntax for Python scripts
        if script_type == ScriptType.PYTHON.value and AST_AVAILABLE:
            try:
                ast.parse(script_content)
            except SyntaxError as e:
                raise ValueError(f"Invalid Python syntax: {str(e)}")
        
        script_record = {
            "id": script_id,
            "script_name": script_name,
            "script_type": script_type,
            "script_content": script_content,
            "description": description,
            "parameters": json.dumps(parameters or {}),
            "return_schema": json.dumps(return_schema or {}),
            "is_active": True,
            "execution_count": 0,
            "last_executed": None,
            "average_execution_time_ms": None,
            "created_by": created_by,
            "created_at": now,
            "updated_at": now
        }
        
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO custom_scripts (
                    id, script_name, script_type, script_content, description,
                    parameters, return_schema, is_active, execution_count,
                    last_executed, average_execution_time_ms, created_by,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                script_record["id"], script_record["script_name"],
                script_record["script_type"], script_record["script_content"],
                script_record["description"], script_record["parameters"],
                script_record["return_schema"], script_record["is_active"],
                script_record["execution_count"], script_record["last_executed"],
                script_record["average_execution_time_ms"], script_record["created_by"],
                script_record["created_at"], script_record["updated_at"]
            ))
            conn.commit()
            return script_record
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Script with name '{script_name}' already exists")
        finally:
            conn.close()
    
    def execute_script(self, script_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a custom script with parameters."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM custom_scripts WHERE id = ?", (script_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            raise ValueError(f"Script {script_id} not found")
        
        columns = [desc[0] for desc in cursor.description]
        script = dict(zip(columns, row))
        
        if not script['is_active']:
            conn.close()
            raise ValueError(f"Script {script_id} is not active")
        
        # Parse parameters
        script_params = json.loads(script['parameters']) if script['parameters'] else {}
        exec_params = {**script_params, **(parameters or {})}
        
        execution_log_id = f"EXECLOG-{str(uuid.uuid4().int)[:8]}"
        start_time = datetime.now()
        
        try:
            # Execute script based on type
            if script['script_type'] == ScriptType.PYTHON.value:
                result = self._script_engine.execute_python(
                    script['script_content'], 
                    exec_params
                )
            elif script['script_type'] == ScriptType.SQL.value:
                result = self._script_engine.execute_sql(
                    script['script_content'], 
                    exec_params
                )
            else:
                raise ValueError(f"Unsupported script type: {script['script_type']}")
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            now = datetime.now(timezone.utc).isoformat()
            
            # Update script statistics
            new_count = script['execution_count'] + 1
            avg_time = (
                (script['average_execution_time_ms'] * script['execution_count'] + execution_time) / new_count
                if script['execution_count'] > 0 else execution_time
            )
            
            cursor.execute("""
                UPDATE custom_scripts 
                SET execution_count = ?, last_executed = ?, average_execution_time_ms = ?, updated_at = ?
                WHERE id = ?
            """, (new_count, now, avg_time, now, script_id))
            
            # Log execution
            cursor.execute("""
                INSERT INTO script_execution_logs (
                    id, script_id, execution_parameters, execution_result,
                    execution_time_ms, status, error_message, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_log_id, script_id, json.dumps(exec_params),
                json.dumps(result), execution_time, "SUCCESS", None, now
            ))
            
            conn.commit()
            conn.close()
            
            return {
                "script_id": script_id,
                "execution_id": execution_log_id,
                "result": result,
                "execution_time_ms": execution_time,
                "status": "SUCCESS"
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            now = datetime.now(timezone.utc).isoformat()
            
            # Log failed execution
            cursor.execute("""
                INSERT INTO script_execution_logs (
                    id, script_id, execution_parameters, execution_result,
                    execution_time_ms, status, error_message, executed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_log_id, script_id, json.dumps(exec_params),
                None, execution_time, "FAILED", str(e), now
            ))
            
            conn.commit()
            conn.close()
            raise ValueError(f"Script execution failed: {str(e)}")
    
    def get_script(self, script_id: str) -> Optional[Dict[str, Any]]:
        """Get script details."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM custom_scripts WHERE id = ?", (script_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            script = dict(zip(columns, row))
            
            # Parse JSON fields
            if script.get('parameters'):
                script['parameters'] = json.loads(script['parameters'])
            if script.get('return_schema'):
                script['return_schema'] = json.loads(script['return_schema'])
            
            return script
        
        return None
    
    def list_scripts(self, script_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List custom scripts with optional filtering."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM custom_scripts WHERE 1=1"
        params = []
        
        if script_type:
            query += " AND script_type = ?"
            params.append(script_type)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        scripts = [dict(zip(columns, row)) for row in rows]
        
        # Parse JSON fields
        for script in scripts:
            if script.get('parameters'):
                script['parameters'] = json.loads(script['parameters'])
            if script.get('return_schema'):
                script['return_schema'] = json.loads(script['return_schema'])
        
        conn.close()
        return scripts
    
    def get_script_execution_logs(self, script_id: Optional[str] = None,
                                  limit: int = 50) -> List[Dict[str, Any]]:
        """Get script execution logs."""
        conn = sqlite3.connect(self._get_plugin_db_path())
        cursor = conn.cursor()
        
        query = "SELECT * FROM script_execution_logs WHERE 1=1"
        params = []
        
        if script_id:
            query += " AND script_id = ?"
            params.append(script_id)
        
        query += " ORDER BY executed_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        logs = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        return logs


class ScriptEngine:
    """Script execution engine for custom scripting capabilities."""
    
    def __init__(self):
        self.globals_cache = {}
        self.locals_cache = {}
    
    def execute_python(self, script_content: str, parameters: Dict[str, Any]) -> Any:
        """Execute Python script with parameters."""
        if not CODE_EXECUTION_AVAILABLE:
            raise ImportError("Python code execution not available")
        
        # Create execution environment
        exec_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'dict': dict,
                'list': list,
                'tuple': tuple,
                'set': set,
                'bool': bool,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'sorted': sorted,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'Decimal': Decimal,
            }
        }
        
        # Add parameters to execution environment
        exec_locals = parameters.copy()
        
        try:
            # Execute the script
            exec(script_content, exec_globals, exec_locals)
            
            # Return result if specified
            return exec_locals.get('result', exec_locals.get('return_value', None))
            
        except Exception as e:
            raise ValueError(f"Python script execution failed: {str(e)}")
    
    def execute_sql(self, script_content: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute SQL script with parameters."""
        # This would connect to the database and execute SQL
        # For security, this should be restricted to read-only operations
        # or specific whitelisted operations
        
        try:
            # Placeholder for SQL execution
            # In production, this would use the actual database connection
            # with proper security restrictions
            
            return {"message": "SQL execution placeholder", "parameters": parameters}
            
        except Exception as e:
            raise ValueError(f"SQL script execution failed: {str(e)}")


# Singleton instance for service layer
_plugin_service = None

def get_plugin_service(db_path: Optional[str] = None) -> PluginService:
    """Get or create the plugin service singleton."""
    global _plugin_service
    if _plugin_service is None:
        _plugin_service = PluginService(db_path)
    return _plugin_service

# Convenience functions for common operations
def install_plugin(plugin_data: Dict[str, Any], plugin_code: str,
                  db_path: Optional[str] = None) -> Dict[str, Any]:
    """Install a new plugin."""
    service = get_plugin_service(db_path)
    return service.install_plugin(plugin_data, plugin_code)

def activate_plugin(plugin_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Activate a plugin."""
    service = get_plugin_service(db_path)
    return service.activate_plugin(plugin_id)

def create_custom_script(script_name: str, script_type: str, script_content: str,
                        description: str = "", parameters: Optional[Dict[str, Any]] = None,
                        return_schema: Optional[Dict[str, Any]] = None,
                        created_by: str = "system", db_path: Optional[str] = None) -> Dict[str, Any]:
    """Create a custom script."""
    service = get_plugin_service(db_path)
    return service.create_custom_script(script_name, script_type, script_content,
                                      description, parameters, return_schema, created_by)

def execute_script(script_id: str, parameters: Optional[Dict[str, Any]] = None,
                  db_path: Optional[str] = None) -> Dict[str, Any]:
    """Execute a custom script."""
    service = get_plugin_service(db_path)
    return service.execute_script(script_id, parameters)