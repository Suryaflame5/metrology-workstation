"""
Metrology V2 Configuration

Centralized configuration management with environment-specific settings.
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Application deployment environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentMode(Enum):
    """Deployment modes for the application."""
    LOCAL = "local"           # Single-user desktop with local database
    PROFESSIONAL = "professional"  # Desktop/web client with application server
    ENTERPRISE = "enterprise"  # Multi-server deployment with load balancing


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "metrology_v2"
    username: str = "metrology_user"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    session_timeout: int = 3600
    mfa_enabled: bool = True
    mfa_secret_length: int = 32
    password_min_length: int = 12
    password_require_special: bool = True
    password_require_number: bool = True
    max_login_attempts: int = 5
    lockout_duration: int = 900
    audit_log_retention_days: int = 365


@dataclass
class StorageConfig:
    """Storage configuration."""
    local_storage_path: str = ""
    use_encryption: bool = True
    encryption_key: str = ""
    max_file_size_mb: int = 100
    allowed_extensions: list = field(default_factory=lambda: [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", 
        ".csv", ".json", ".xml", ".jpg", ".png"
    ])


@dataclass
class AnalyticsConfig:
    """Analytics and ML configuration."""
    enable_ml_analytics: bool = True
    model_registry_path: str = ""
    max_training_samples: int = 100000
    anomaly_detection_threshold: float = 0.1
    drift_detection_window_days: int = 90
    spc_sample_size_min: int = 30


@dataclass
class IntegrationConfig:
    """Integration configuration."""
    api_rate_limit_per_minute: int = 1000
    webhook_timeout_seconds: int = 30
    webhook_max_retries: int = 3
    webhook_retry_delay_seconds: int = 60
    enable_external_erp: bool = False
    enable_external_plm: bool = False


@dataclass
class UIConfig:
    """UI and animation configuration."""
    enable_animations: bool = True
    animation_duration_ms: int = 300
    enable_agentic_ui: bool = True
    theme: str = "professional"
    font_size: int = 14
    high_contrast_mode: bool = False


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    deployment_mode: DeploymentMode = DeploymentMode.LOCAL
    version: str = "2.0.0"
    debug: bool = False
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    # Paths
    base_path: Path = field(default_factory=lambda: Path.cwd())
    data_path: Path = field(default_factory=lambda: Path.cwd() / "data")
    logs_path: Path = field(default_factory=lambda: Path.cwd() / "logs")
    plugins_path: Path = field(default_factory=lambda: Path.cwd() / "plugins")
    temp_path: Path = field(default_factory=lambda: Path.cwd() / "temp")


def load_config(env: Optional[str] = None) -> ApplicationConfig:
    """
    Load configuration from environment variables and config files.
    
    Args:
        env: Environment name (development, testing, staging, production)
    
    Returns:
        ApplicationConfig instance with loaded settings
    """
    env_name = env or os.environ.get("METROLOGY_ENV", "development")
    
    try:
        environment = Environment(env_name.lower())
    except ValueError:
        environment = Environment.DEVELOPMENT
    
    # Determine deployment mode
    deployment_mode_str = os.environ.get("METROLOGY_DEPLOYMENT", "local")
    try:
        deployment_mode = DeploymentMode(deployment_mode_str.lower())
    except ValueError:
        deployment_mode = DeploymentMode.LOCAL
    
    # Set paths based on OS
    if os.name == 'nt':  # Windows
        base_path = Path(os.environ.get("LOCALAPPDATA", Path.cwd())) / "MetrologyV2"
    else:  # Mac/Linux
        base_path = Path.home() / ".metrology_v2"
    
    config = ApplicationConfig(
        environment=environment,
        deployment_mode=deployment_mode,
        debug=(environment == Environment.DEVELOPMENT),
        base_path=base_path,
        data_path=base_path / "data",
        logs_path=base_path / "logs",
        plugins_path=base_path / "plugins",
        temp_path=base_path / "temp",
    )
    
    # Override with environment variables if present
    config.database.host = os.environ.get("DB_HOST", config.database.host)
    config.database.port = int(os.environ.get("DB_PORT", str(config.database.port)))
    config.database.database = os.environ.get("DB_NAME", config.database.database)
    config.database.username = os.environ.get("DB_USER", config.database.username)
    config.database.password = os.environ.get("DB_PASSWORD", config.database.password)
    
    config.security.secret_key = os.environ.get("SECRET_KEY", config.security.secret_key)
    config.security.mfa_enabled = os.environ.get("MFA_ENABLED", "true").lower() == "true"
    
    config.storage.local_storage_path = os.environ.get("STORAGE_PATH", str(config.storage.local_storage_path))
    
    config.analytics.enable_ml_analytics = os.environ.get("ENABLE_ML", "true").lower() == "true"
    
    config.ui.enable_animations = os.environ.get("ENABLE_ANIMATIONS", "true").lower() == "true"
    config.ui.enable_agentic_ui = os.environ.get("ENABLE_AGENTIC_UI", "true").lower() == "true"
    
    # Create directories
    config.data_path.mkdir(parents=True, exist_ok=True)
    config.logs_path.mkdir(parents=True, exist_ok=True)
    config.plugins_path.mkdir(parents=True, exist_ok=True)
    config.temp_path.mkdir(parents=True, exist_ok=True)
    
    return config


# Global settings instance
settings = load_config()