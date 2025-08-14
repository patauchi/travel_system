"""
Database configuration for Financial Service
"""

import os
import logging
from typing import Generator, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/multitenant_db"
)

# Create base engine for shared database
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False
)

# Session factory for shared database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Store tenant-specific engines
tenant_engines: Dict[str, Any] = {}


def get_db() -> Generator[Session, None, None]:
    """
    Get database session for shared database

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tenant_engine(schema_name: str):
    """
    Get or create engine for a specific tenant schema

    Args:
        schema_name: Name of the tenant schema

    Returns:
        Engine instance for the tenant
    """
    if schema_name not in tenant_engines:
        tenant_engines[schema_name] = create_engine(
            DATABASE_URL,
            connect_args={
                "options": f"-csearch_path={schema_name}"
            },
            pool_pre_ping=True,
            pool_size=3,
            max_overflow=5,
            echo=False
        )
    return tenant_engines[schema_name]


def get_tenant_db(schema_name: str) -> Generator[Session, None, None]:
    """
    Get database session for a specific tenant schema

    Args:
        schema_name: Name of the tenant schema

    Yields:
        Session: Database session for the tenant
    """
    engine = get_tenant_engine(schema_name)
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TenantSessionLocal()

    try:
        # Set the search path for this session
        db.execute(text(f"SET search_path TO {schema_name}"))
        yield db
    finally:
        db.close()


@contextmanager
def get_tenant_session(schema_name: str) -> Session:
    """
    Context manager for tenant database session

    Args:
        schema_name: Name of the tenant schema

    Yields:
        Session: Database session for the tenant
    """
    engine = get_tenant_engine(schema_name)
    TenantSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TenantSessionLocal()

    try:
        session.execute(text(f"SET search_path TO {schema_name}"))
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def cleanup_engines():
    """
    Cleanup all tenant engines
    """
    global tenant_engines
    for engine in tenant_engines.values():
        engine.dispose()
    tenant_engines = {}


def get_tenant_from_header(headers: dict) -> Optional[str]:
    """
    Extract tenant ID from request headers

    Args:
        headers: Request headers dictionary

    Returns:
        Tenant ID if found, None otherwise
    """
    return headers.get("X-Tenant-ID")


def get_schema_from_tenant_id(tenant_id: str, db: Session) -> Optional[str]:
    """
    Get schema name for a tenant ID

    Args:
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        Schema name if found, None otherwise
    """
    try:
        result = db.execute(
            text("SELECT schema_name FROM shared.tenants WHERE id = :tenant_id AND status = 'active'"),
            {"tenant_id": tenant_id}
        )
        row = result.first()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Error getting schema for tenant {tenant_id}: {str(e)}")
        return None


def verify_tenant_access(tenant_id: str, user_id: str, db: Session) -> bool:
    """
    Verify if a user has access to a tenant

    Args:
        tenant_id: UUID of the tenant
        user_id: UUID of the user
        db: Database session

    Returns:
        True if user has access, False otherwise
    """
    try:
        # For now, we'll assume users authenticated through the gateway have access
        # In production, implement proper access control
        schema_name = get_schema_from_tenant_id(tenant_id, db)
        if not schema_name:
            return False

        # Check if user exists in tenant schema
        with get_tenant_session(schema_name) as tenant_db:
            result = tenant_db.execute(
                text("SELECT 1 FROM users WHERE id = :user_id AND is_active = true"),
                {"user_id": user_id}
            )
            return result.first() is not None

    except Exception as e:
        logger.error(f"Error verifying tenant access: {str(e)}")
        return False


def get_database_stats() -> Dict[str, Any]:
    """
    Get database statistics

    Returns:
        Dictionary with database statistics
    """
    try:
        with engine.connect() as conn:
            # Get database size
            result = conn.execute(text("""
                SELECT pg_database_size(current_database()) as size,
                       pg_size_pretty(pg_database_size(current_database())) as size_pretty
            """))
            row = result.first()

            # Get connection count
            conn_result = conn.execute(text("""
                SELECT count(*) as connections
                FROM pg_stat_activity
                WHERE datname = current_database()
            """))
            conn_row = conn_result.first()

            return {
                "database_size": row[0] if row else 0,
                "database_size_pretty": row[1] if row else "0 bytes",
                "active_connections": conn_row[0] if conn_row else 0,
                "tenant_engines_loaded": len(tenant_engines)
            }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {
            "error": str(e)
        }
