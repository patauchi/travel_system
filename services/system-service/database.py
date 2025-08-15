"""
Database configuration and connection management for system-service
Handles connections to both shared schema and tenant-specific schemas
Using async SQLAlchemy for better performance
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
import os
import logging
from typing import Optional, Dict, AsyncGenerator
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine for shared schema
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create async session factory
SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Cache for tenant sessions
_tenant_sessions: Dict[str, async_sessionmaker] = {}


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get shared database session
    Used for accessing shared schema tables
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_schema_name(tenant_id: str) -> str:
    """
    Convert tenant ID to schema name

    Args:
        tenant_id: The tenant identifier

    Returns:
        Schema name for the tenant
    """
    # Replace any characters that aren't valid in PostgreSQL schema names
    safe_tenant_id = tenant_id.replace('-', '_').replace(' ', '_').lower()
    return f"tenant_{safe_tenant_id}"


async def get_tenant_session(tenant_id: str) -> AsyncSession:
    """
    Get an async session for a specific tenant

    Args:
        tenant_id: The tenant identifier

    Returns:
        AsyncSession configured for the tenant's schema
    """
    schema_name = get_schema_name(tenant_id)

    if schema_name not in _tenant_sessions:
        # Create a new engine for this tenant with schema in search path
        tenant_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            pool_size=5,  # Smaller pool per tenant
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "search_path": f"{schema_name},public"
                }
            }
        )

        # Create session factory for this tenant
        _tenant_sessions[schema_name] = async_sessionmaker(
            tenant_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )

    # Create and return a new session
    session = _tenant_sessions[schema_name]()

    # Set search path explicitly
    await session.execute(text(f"SET search_path TO {schema_name}, public"))

    return session


async def get_tenant_db(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get tenant-specific database session

    Args:
        tenant_id: The tenant identifier

    Yields:
        AsyncSession for the tenant's schema
    """
    session = await get_tenant_session(tenant_id)
    try:
        yield session
    finally:
        await session.close()


@asynccontextmanager
async def tenant_session_context(tenant_id: str):
    """
    Context manager for tenant database sessions

    Args:
        tenant_id: The tenant identifier

    Yields:
        AsyncSession for the tenant's schema
    """
    session = await get_tenant_session(tenant_id)
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def verify_tenant_schema_exists(tenant_id: str) -> bool:
    """
    Check if a tenant schema exists in the database

    Args:
        tenant_id: The tenant identifier

    Returns:
        True if schema exists, False otherwise
    """
    schema_name = get_schema_name(tenant_id)

    try:
        async with SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = :schema_name
                """),
                {"schema_name": schema_name}
            )
            return result.first() is not None
    except Exception as e:
        logger.error(f"Error checking schema existence: {str(e)}")
        return False


async def create_tenant_schema(tenant_id: str) -> bool:
    """
    Create a new schema for a tenant

    Args:
        tenant_id: The tenant identifier

    Returns:
        True if successful, False otherwise
    """
    schema_name = get_schema_name(tenant_id)

    try:
        async with SessionLocal() as session:
            # Create schema
            await session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            await session.commit()

            logger.info(f"Created schema: {schema_name}")
            return True
    except Exception as e:
        logger.error(f"Error creating schema {schema_name}: {str(e)}")
        return False


async def drop_tenant_schema(tenant_id: str) -> bool:
    """
    Drop a tenant's schema (use with caution!)

    Args:
        tenant_id: The tenant identifier

    Returns:
        True if successful, False otherwise
    """
    schema_name = get_schema_name(tenant_id)

    try:
        async with SessionLocal() as session:
            # Drop schema cascade
            await session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            await session.commit()

            # Remove from cache
            if schema_name in _tenant_sessions:
                del _tenant_sessions[schema_name]

            logger.info(f"Dropped schema: {schema_name}")
            return True
    except Exception as e:
        logger.error(f"Error dropping schema {schema_name}: {str(e)}")
        return False


async def get_all_tenant_schemas() -> list:
    """
    Get list of all tenant schemas in the database

    Returns:
        List of tenant schema names
    """
    try:
        async with SessionLocal() as session:
            result = await session.execute(
                text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name LIKE 'tenant_%'
                    ORDER BY schema_name
                """)
            )
            return [row[0] for row in result]
    except Exception as e:
        logger.error(f"Error getting tenant schemas: {str(e)}")
        return []


async def execute_in_tenant_schema(tenant_id: str, sql: str, params: dict = None):
    """
    Execute SQL in a specific tenant schema

    Args:
        tenant_id: The tenant identifier
        sql: SQL query to execute
        params: Parameters for the SQL query

    Returns:
        Query result
    """
    schema_name = get_schema_name(tenant_id)

    try:
        async with await get_tenant_session(tenant_id) as session:
            result = await session.execute(text(sql), params or {})
            await session.commit()
            return result
    except Exception as e:
        logger.error(f"Error executing SQL in schema {schema_name}: {str(e)}")
        raise


async def init_tenant_tables(tenant_id: str):
    """
    Initialize all tables for a tenant schema

    Args:
        tenant_id: The tenant identifier
    """
    from shared_models import Base

    schema_name = get_schema_name(tenant_id)

    try:
        # Create schema if it doesn't exist
        await create_tenant_schema(tenant_id)

        # Create all tables in the tenant schema
        async with engine.begin() as conn:
            # Set the schema search path
            await conn.execute(text(f"SET search_path TO {schema_name}, public"))

            # Create all tables
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"Initialized tables for tenant {tenant_id}")

    except Exception as e:
        logger.error(f"Error initializing tables for tenant {tenant_id}: {str(e)}")
        raise


async def get_db_stats() -> dict:
    """
    Get database statistics and health information

    Returns:
        Dictionary with database statistics
    """
    try:
        async with SessionLocal() as session:
            # Get database size
            size_result = await session.execute(
                text("""
                    SELECT pg_database_size(current_database()) as size,
                           current_database() as name
                """)
            )
            size_data = size_result.first()

            # Get connection count
            conn_result = await session.execute(
                text("""
                    SELECT count(*) as connections
                    FROM pg_stat_activity
                    WHERE datname = current_database()
                """)
            )
            conn_data = conn_result.first()

            # Get tenant count
            tenant_schemas = await get_all_tenant_schemas()

            return {
                "database_name": size_data.name if size_data else "unknown",
                "database_size_bytes": size_data.size if size_data else 0,
                "active_connections": conn_data.connections if conn_data else 0,
                "tenant_count": len(tenant_schemas),
                "tenant_schemas": tenant_schemas
            }

    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {
            "error": str(e),
            "database_name": "unknown",
            "database_size_bytes": 0,
            "active_connections": 0,
            "tenant_count": 0,
            "tenant_schemas": []
        }


# Sync engine for specific operations that require it
sync_engine = None
if ASYNC_DATABASE_URL.startswith("postgresql+asyncpg://"):
    sync_url = ASYNC_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    from sqlalchemy import create_engine
    sync_engine = create_engine(sync_url)
