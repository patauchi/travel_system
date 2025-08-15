"""
Database configuration for Communication Service
Handles multi-tenant database connections and session management
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)

# Create base engine for shared schema
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory for shared schema
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cache for tenant engines
_tenant_engines = {}


def get_db():
    """
    Get database session for shared schema

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
        Engine: SQLAlchemy engine configured for the tenant schema
    """
    if schema_name not in _tenant_engines:
        _tenant_engines[schema_name] = create_engine(
            DATABASE_URL,
            connect_args={
                "options": f"-csearch_path={schema_name},public"
            },
            poolclass=NullPool,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )

    return _tenant_engines[schema_name]


@contextmanager
def get_tenant_session(schema_name: str):
    """
    Context manager for tenant-specific database session

    Args:
        schema_name: Name of the tenant schema

    Yields:
        Session: Database session for the tenant

    Raises:
        ValueError: If the schema does not exist
    """
    # First check if the schema exists
    if not schema_exists(schema_name):
        raise ValueError(f"Tenant schema '{schema_name}' does not exist")

    engine = get_tenant_engine(schema_name)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error in tenant {schema_name}: {str(e)}")
        raise
    finally:
        session.close()


def get_tenant_db(tenant_slug: str):
    """
    Dependency for FastAPI to get tenant database session

    Args:
        tenant_slug: Tenant identifier

    Yields:
        Session: Database session for the tenant
    """
    schema_name = f"tenant_{tenant_slug}"
    with get_tenant_session(schema_name) as session:
        yield session


def verify_connection() -> bool:
    """
    Verify database connection

    Returns:
        bool: True if connection successful
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def list_tenant_schemas() -> list:
    """
    List all tenant schemas in the database

    Returns:
        list: List of tenant schema names
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'tenant_%'
                ORDER BY schema_name
            """))
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Failed to list tenant schemas: {str(e)}")
        return []


def get_db():
    """
    Get main database session (shared schema)

    Yields:
        Session: Database session for shared schema
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_schema_from_tenant_id(tenant_id: str, db) -> str:
    """
    Get schema name from tenant ID

    Args:
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        str: Schema name or None if not found
    """
    try:
        # Query the shared schema to get tenant info
        result = db.execute(text("""
            SELECT schema_name
            FROM shared.tenants
            WHERE id = :tenant_id
        """), {"tenant_id": tenant_id})

        row = result.fetchone()
        if row:
            return row[0]
        return None
    except Exception as e:
        logger.error(f"Failed to get schema for tenant {tenant_id}: {str(e)}")
        return None


def schema_exists(schema_name: str) -> bool:
    """
    Check if a schema exists

    Args:
        schema_name: Name of the schema to check

    Returns:
        bool: True if schema exists
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = :schema
                )
            """), {"schema": schema_name})
            return result.scalar()
    except Exception as e:
        logger.error(f"Failed to check schema existence: {str(e)}")
        return False


def cleanup_engines():
    """
    Cleanup all cached tenant engines
    Called during shutdown
    """
    global engine

    for tenant_engine in _tenant_engines.values():
        tenant_engine.dispose()
    _tenant_engines.clear()

    # Also dispose main engine
    engine.dispose()

    logger.info("All database connections closed")
