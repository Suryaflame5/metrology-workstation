"""
Metrology V2 Database Connection and Management

Production-grade database connection handling with connection pooling,
transaction management, and health monitoring.
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager
from typing import Optional, Generator
import logging
from datetime import datetime
import time

from .schema import Base
from ..config import settings


logger = logging.getLogger(__name__)


class DatabaseHealthCheck:
    """Database health monitoring."""
    
    def __init__(self):
        self.last_check = None
        self.is_healthy = True
        self.check_interval = 60  # seconds
        self.connection_timeout = 5
    
    def check_health(self, engine) -> bool:
        """Check database connection health."""
        try:
            start_time = time.time()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            elapsed = time.time() - start_time
            
            if elapsed > self.connection_timeout:
                logger.warning(f"Database health check slow: {elapsed:.2f}s")
                self.is_healthy = False
            else:
                self.is_healthy = True
            
            self.last_check = datetime.now()
            return self.is_healthy
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.is_healthy = False
            self.last_check = datetime.now()
            return False


class Database:
    """
    Production-grade database manager with connection pooling,
    transaction management, and health monitoring.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            connection_string: Database connection string (optional, uses config if not provided)
        """
        self.connection_string = connection_string or self._build_connection_string()
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self.health_check = DatabaseHealthCheck()
        
        self._initialize_engines()
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from configuration."""
        db_config = settings.database
        
        return (
            f"postgresql://{db_config.username}:{db_config.password}"
            f"@{db_config.host}:{db_config.port}/{db_config.database}"
        )
    
    def _initialize_engines(self):
        """Initialize synchronous and asynchronous database engines."""
        # Synchronous engine for most operations
        self.engine = create_engine(
            self.connection_string,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_recycle=settings.database.pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.debug,
            future=True,  # Use SQLAlchemy 2.0 style
        )
        
        # Configure connection pool events
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")
        
        # Create session factory
        self.session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,  # Prevent accidental lazy loading after commit
            autoflush=True,  # Auto-flush before query
        )
        
        # Asynchronous engine for background operations
        async_connection_string = self.connection_string.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        
        self.async_engine = create_async_engine(
            async_connection_string,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            echo=settings.debug,
        )
        
        self.async_session_factory = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        logger.info("Database engines initialized successfully")
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("Database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup.
        
        Yields:
            SQLAlchemy Session object
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error, transaction rolled back: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get a synchronous session (manual management required)."""
        return self.session_factory()
    
    async def get_async_session(self) -> AsyncSession:
        """Get an asynchronous session."""
        return self.async_session_factory()
    
    def check_health(self) -> bool:
        """Check database health."""
        return self.health_check.check_health(self.engine)
    
    def close(self):
        """Close all database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine disposed")
        
        if self.async_engine:
            # Note: async engine needs to be disposed in async context
            logger.info("Async database engine dispose requested")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class TransactionManager:
    """
    Transaction management for complex operations.
    Ensures proper transaction boundaries and rollback handling.
    """
    
    def __init__(self, database: Database):
        self.database = database
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Example:
            with db.transaction():
                # Perform multiple operations
                # All committed if no exception, rolled back otherwise
        """
        session = self.database.get_session_sync()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
        finally:
            session.close()
    
    def run_in_transaction(self, func):
        """
        Run a function within a transaction.
        
        Args:
            func: Function that takes a session argument
            
        Returns:
            Function result
        """
        with self.transaction() as session:
            return func(session)


# Global database instance
_database_instance: Optional[Database] = None


def get_database() -> Database:
    """Get or create the global database instance."""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
    return _database_instance


def init_database():
    """Initialize the database and create tables."""
    db = get_database()
    db.create_tables()
    logger.info("Database initialized successfully")


def close_database():
    """Close the database connection."""
    global _database_instance
    if _database_instance:
        _database_instance.close()
        _database_instance = None