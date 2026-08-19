"""
Metrology V2 - Production-Grade Metrology Platform

A controlled, auditable metrology platform following the architectural principle:
Measurement integrity first → traceability → workflow → analytics → integrations → intelligence

Architecture: Modular Monolith with Domain-Driven Design
Database: PostgreSQL (authoritative transactional database)
Platform: Desktop-first with Windows x64 safe downloader
UI: Agentic animations with professional desktop experience
"""

__version__ = "2.0.0"
__edition__ = "PRODUCTION"

from .config import settings
from .infrastructure.database import Database
from .infrastructure.security import SecurityManager
from .infrastructure.observability import ObservabilityManager

__all__ = [
    "settings",
    "Database", 
    "SecurityManager",
    "ObservabilityManager",
]