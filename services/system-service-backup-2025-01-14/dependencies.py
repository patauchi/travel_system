"""
FastAPI Dependencies for System Service
Handles dependency injection for tenant-specific database sessions and authentication
"""

from fastapi import Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, Generator
import logging

from database import get_tenant_session_factory, get_db, verify_tenant_schema_exists

logger = logging.getLogger(__name__)


def get_tenant_db_session(tenant_slug: str = Path(...)) -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session for a specific tenant.

    This dependency:
    1. Converts the tenant slug to a schema name
    2. Creates a session for that tenant's schema
    3. Sets the search_path explicitly for the session
    4. Properly closes the session after use

    Args:
        tenant_slug: The tenant identifier from the URL path

    Yields:
        SQLAlchemy Session configured for the tenant's schema

    Raises:
        HTTPException: If there's an error accessing the tenant schema
    """
    # Convert tenant slug to schema name
    schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

    try:
        # Get session factory for this tenant
        TenantSession = get_tenant_session_factory(schema_name)

        # Create new session
        db = TenantSession()

        try:
            # Set the search path explicitly for this session
            # This ensures all queries use the tenant's schema
            db.execute(text(f"SET search_path TO {schema_name}, public"))
            db.commit()  # Commit the search_path change

            logger.debug(f"Created database session for tenant schema: {schema_name}")

            yield db

        finally:
            # Always close the session
            db.close()
            logger.debug(f"Closed database session for tenant schema: {schema_name}")

    except Exception as e:
        logger.error(f"Error creating tenant database session for {schema_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access tenant database: {str(e)}"
        )


def get_optional_tenant_db(tenant_slug: Optional[str] = None) -> Optional[Session]:
    """
    Get an optional tenant database session.
    Returns None if no tenant_slug is provided.

    Args:
        tenant_slug: Optional tenant identifier

    Returns:
        Session or None
    """
    if not tenant_slug:
        return None

    # Convert to generator and get the session
    gen = get_tenant_db_session(tenant_slug)
    return next(gen)


class TenantDBDependency:
    """
    Class-based dependency for tenant database sessions.
    Can be used when you need more control over the session lifecycle.
    """

    def __init__(self, tenant_slug: str = Path(...)):
        self.tenant_slug = tenant_slug
        self.schema_name = f"tenant_{tenant_slug.replace('-', '_')}"
        self.session = None

    def __enter__(self) -> Session:
        """Create and configure the session"""
        try:
            TenantSession = get_tenant_session_factory(self.schema_name)
            self.session = TenantSession()

            # Set search path
            self.session.execute(text(f"SET search_path TO {self.schema_name}, public"))
            self.session.commit()

            return self.session

        except Exception as e:
            if self.session:
                self.session.close()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to access tenant database: {str(e)}"
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the session"""
        if self.session:
            if exc_type:
                self.session.rollback()
            self.session.close()


def verify_tenant_schema(tenant_slug: str = Path(...)) -> str:
    """
    Dependency to verify that a tenant schema exists before proceeding.

    Args:
        tenant_slug: The tenant identifier from the URL path

    Returns:
        The schema name if it exists

    Raises:
        HTTPException: If the tenant schema doesn't exist
    """
    schema_name = f"tenant_{tenant_slug.replace('-', '_')}"

    if not verify_tenant_schema_exists(schema_name):
        logger.error(f"Tenant schema not found: {schema_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant not found: {tenant_slug}"
        )

    return schema_name


# Alias for backward compatibility
get_tenant_db = get_tenant_db_session
