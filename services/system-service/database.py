"""
Database configuration and connection management for system-service
Handles connections to both shared schema and tenant-specific schemas
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
import logging
from typing import Optional, Dict
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)

# Create base class for models
Base = declarative_base()

# Create engine for shared schema (default connection)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory for shared schema
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cache for tenant engines to avoid recreating connections
_tenant_engines: Dict[str, any] = {}
_tenant_sessions: Dict[str, any] = {}


def get_db():
    """
    Dependency to get shared database session
    Used for accessing shared schema tables
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tenant_engine(schema_name: str):
    """
    Get or create an engine for a specific tenant schema

    Args:
        schema_name: The name of the tenant's schema

    Returns:
        SQLAlchemy engine configured for the tenant schema
    """
    if schema_name not in _tenant_engines:
        # Create engine with schema-specific configuration
        tenant_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,  # Smaller pool per tenant
            max_overflow=10,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            connect_args={
                "options": f"-csearch_path={schema_name},public"
            }
        )
        _tenant_engines[schema_name] = tenant_engine

        # Create session factory for this tenant
        _tenant_sessions[schema_name] = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=tenant_engine
        )

    return _tenant_engines[schema_name]


def get_tenant_session_factory(schema_name: str):
    """
    Get session factory for a specific tenant schema

    Args:
        schema_name: The name of the tenant's schema

    Returns:
        SessionMaker configured for the tenant schema
    """
    if schema_name not in _tenant_sessions:
        get_tenant_engine(schema_name)  # This will create both engine and session factory

    return _tenant_sessions[schema_name]


def get_tenant_db(tenant_slug: str) -> Session:
    """
    Get database session for a specific tenant

    Args:
        tenant_slug: The slug of the tenant

    Returns:
        Database session for the tenant's schema
    """
    # Convert tenant slug to schema name
    schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

    # Get session factory for this tenant
    TenantSession = get_tenant_session_factory(schema_name)

    # Return new session
    return TenantSession()


@contextmanager
def tenant_db_context(tenant_slug: str):
    """
    Context manager for tenant database sessions

    Args:
        tenant_slug: The slug of the tenant

    Yields:
        Database session for the tenant's schema
    """
    db = get_tenant_db(tenant_slug)
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_schema_name_from_slug(tenant_slug: str) -> str:
    """
    Convert tenant slug to schema name

    Args:
        tenant_slug: The slug of the tenant

    Returns:
        Schema name for the tenant
    """
    return f"tenant_{tenant_slug.replace('-', '_')}"


def verify_tenant_schema_exists(schema_name: str) -> bool:
    """
    Check if a tenant schema exists in the database

    Args:
        schema_name: The name of the schema to check

    Returns:
        True if schema exists, False otherwise
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = :schema_name"
                ),
                {"schema_name": schema_name}
            )
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking schema existence: {str(e)}")
        return False


def create_tenant_schema(schema_name: str) -> bool:
    """
    Create a new schema for a tenant

    Args:
        schema_name: The name of the schema to create

    Returns:
        True if successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Create schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            conn.commit()

            logger.info(f"Created schema: {schema_name}")
            return True
    except Exception as e:
        logger.error(f"Error creating schema {schema_name}: {str(e)}")
        return False


def drop_tenant_schema(schema_name: str) -> bool:
    """
    Drop a tenant's schema (use with caution!)

    Args:
        schema_name: The name of the schema to drop

    Returns:
        True if successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            # Drop schema cascade
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.commit()

            # Remove from cache
            if schema_name in _tenant_engines:
                _tenant_engines[schema_name].dispose()
                del _tenant_engines[schema_name]

            if schema_name in _tenant_sessions:
                del _tenant_sessions[schema_name]

            logger.info(f"Dropped schema: {schema_name}")
            return True
    except Exception as e:
        logger.error(f"Error dropping schema {schema_name}: {str(e)}")
        return False


def get_all_tenant_schemas() -> list:
    """
    Get list of all tenant schemas in the database

    Returns:
        List of schema names that start with 'tenant_'
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name LIKE 'tenant_%' "
                    "ORDER BY schema_name"
                )
            )
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error getting tenant schemas: {str(e)}")
        return []


def execute_in_tenant_schema(schema_name: str, sql: str, params: dict = None) -> any:
    """
    Execute SQL in a specific tenant schema

    Args:
        schema_name: The name of the tenant schema
        sql: SQL query to execute
        params: Parameters for the SQL query

    Returns:
        Query result
    """
    try:
        engine = get_tenant_engine(schema_name)
        with engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            conn.commit()
            return result
    except Exception as e:
        logger.error(f"Error executing SQL in schema {schema_name}: {str(e)}")
        raise


def init_db():
    """
    Initialize database (create tables if needed)
    This is typically handled by migrations, but included for completeness
    """
    try:
        # Import all models to ensure they're registered
        from models import (
            User, Role, Permission, Team, Setting,
            UserSession, AuditLog, PasswordResetToken,
            EmailVerificationToken, ApiKey
        )

        logger.info("Database models loaded successfully")
    except Exception as e:
        logger.error(f"Error loading database models: {str(e)}")
        raise


# Initialize database on module load
init_db()
