"""
Tenant Context Helper for Auth Service
Handles tenant detection and database routing
"""

from typing import Optional, Dict, Any, Tuple
from fastapi import Request, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
import logging
import re

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/multitenant_db"
)

# Cache for tenant database sessions
_tenant_sessions = {}


def extract_tenant_from_request(request: Request) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract tenant information from request
    Returns: (tenant_slug, schema_name) or (None, None) for main domain
    """
    host = request.headers.get("host", "")

    # Remove port if present
    if ":" in host:
        host = host.split(":")[0]

    # Check if it's a subdomain request
    parts = host.split(".")

    # For subdomain like tenant1.localhost or tenant1.example.com
    if len(parts) >= 2 and parts[0] not in ['www', 'app', 'api']:
        tenant_slug = parts[0]

        # Validate tenant slug format
        if re.match(r'^[a-z0-9-]+$', tenant_slug):
            # Convert slug to schema name (replace hyphens with underscores)
            schema_name = f"tenant_{tenant_slug.replace('-', '_')}"
            logger.info(f"Detected tenant context: {tenant_slug} -> {schema_name}")
            return tenant_slug, schema_name

    # Check for tenant header (useful for API calls)
    tenant_header = request.headers.get("X-Tenant-Slug")
    if tenant_header:
        tenant_slug = tenant_header
        if re.match(r'^[a-z0-9-]+$', tenant_slug):
            schema_name = f"tenant_{tenant_slug.replace('-', '_')}"
            logger.info(f"Detected tenant from header: {tenant_slug} -> {schema_name}")
            return tenant_slug, schema_name

    # Check query parameter as fallback
    if hasattr(request, 'query_params'):
        tenant_param = request.query_params.get("tenant")
        if tenant_param:
            tenant_slug = tenant_param
            if re.match(r'^[a-z0-9-]+$', tenant_slug):
                schema_name = f"tenant_{tenant_slug.replace('-', '_')}"
                logger.info(f"Detected tenant from query: {tenant_slug} -> {schema_name}")
                return tenant_slug, schema_name

    # No tenant detected - main domain context
    logger.info("No tenant detected - using main domain context")
    return None, None


def get_tenant_db_session(schema_name: str) -> Session:
    """
    Get a database session for a specific tenant schema
    """
    if schema_name not in _tenant_sessions:
        # Create engine with specific schema
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,  # Don't pool connections for tenant schemas
            connect_args={
                "options": f"-csearch_path={schema_name},public"
            }
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _tenant_sessions[schema_name] = SessionLocal

    return _tenant_sessions[schema_name]()


def verify_tenant_schema_exists(schema_name: str) -> bool:
    """
    Verify that a tenant schema exists in the database
    """
    engine = create_engine(DATABASE_URL, poolclass=NullPool)

    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = :schema_name
                )
            """),
            {"schema_name": schema_name}
        )
        exists = result.scalar()

    engine.dispose()
    return exists


def get_tenant_info(tenant_slug: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get tenant information from shared.tenants table
    """
    from models import Tenant

    tenant = db.query(Tenant).filter(
        Tenant.slug == tenant_slug
    ).first()

    if tenant:
        return {
            "id": str(tenant.id),
            "slug": tenant.slug,
            "name": tenant.name,
            "schema_name": tenant.schema_name,
            "status": tenant.status.value if hasattr(tenant.status, 'value') else tenant.status,
            "subdomain": tenant.subdomain,
            "subscription_plan": tenant.subscription_plan.value if hasattr(tenant.subscription_plan, 'value') else tenant.subscription_plan
        }

    return None


class AuthContext:
    """
    Context manager for handling authentication in multi-tenant environment
    """

    def __init__(self, request: Request, shared_db: Session):
        self.request = request
        self.shared_db = shared_db
        self.tenant_slug, self.schema_name = extract_tenant_from_request(request)
        self.is_tenant_context = self.tenant_slug is not None
        self.tenant_info = None
        self.tenant_db = None

        if self.is_tenant_context:
            # Verify tenant exists and is active
            self.tenant_info = get_tenant_info(self.tenant_slug, shared_db)
            if not self.tenant_info:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant '{self.tenant_slug}' not found"
                )

            if self.tenant_info["status"] not in ["active", "trial"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Tenant '{self.tenant_slug}' is not active"
                )

            # Verify schema exists
            if not verify_tenant_schema_exists(self.schema_name):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Tenant schema not properly initialized"
                )

            # Get tenant database session
            self.tenant_db = get_tenant_db_session(self.schema_name)

    def get_user_table(self):
        """
        Get the appropriate user table based on context
        """
        if self.is_tenant_context:
            # Use dynamic SQL for tenant users table
            return f"{self.schema_name}.users"
        else:
            # Use shared.users for system admins
            return "shared.users"

    def get_db_session(self) -> Session:
        """
        Get the appropriate database session based on context
        """
        if self.is_tenant_context:
            return self.tenant_db
        else:
            return self.shared_db

    def close(self):
        """
        Close tenant database session if opened
        """
        if self.tenant_db:
            self.tenant_db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def is_system_admin_context(request: Request) -> bool:
    """
    Check if the current request is in system admin context (main domain)
    """
    tenant_slug, _ = extract_tenant_from_request(request)
    return tenant_slug is None


def validate_system_admin_access(request: Request):
    """
    Validate that the request is from the main domain for system admin operations
    """
    if not is_system_admin_context(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This operation is only available from the main domain"
        )
