"""
Create Tenant V2 - Updated tenant creation with proper architecture
Creates tenant in shared.tenants and initializes tenant schema with admin user
"""

from fastapi import HTTPException, status, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, create_engine
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import uuid
import re
import httpx
import logging
import os

from database import get_db
from models import Tenant, SubscriptionHistory

logger = logging.getLogger(__name__)

# Database URL for direct schema operations
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@postgres:5432/multitenant_db"
)

class TenantCreateV2(BaseModel):
    """Updated tenant creation model"""
    name: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    subdomain: Optional[str] = None
    domain: Optional[str] = None
    owner_email: EmailStr
    owner_username: str
    owner_password: str
    owner_first_name: Optional[str] = "Admin"
    owner_last_name: Optional[str] = "User"
    subscription_plan: str = "free"

    @validator('slug')
    def validate_slug(cls, v):
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
        return v

    @validator('subdomain')
    def validate_subdomain(cls, v):
        if v and not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError('Subdomain must contain only lowercase letters, numbers, and hyphens')
        return v


def generate_schema_name(slug: str) -> str:
    """Generate schema name from slug"""
    return f"tenant_{slug.replace('-', '_')}"


def create_tenant_schema(schema_name: str) -> bool:
    """Create the tenant schema in database"""
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Create schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            conn.commit()

        logger.info(f"Created schema: {schema_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create schema {schema_name}: {str(e)}")
        return False
    finally:
        engine.dispose()


def initialize_tenant_schema(tenant_id: str, schema_name: str) -> bool:
    """Initialize tenant schema using system-service"""
    try:
        # Call system-service to initialize the tenant schema
        with httpx.Client() as client:
            response = client.post(
                f"http://system-service:8004/api/v1/tenants/{tenant_id}/initialize",
                params={"schema_name": schema_name},
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"Successfully initialized schema for tenant {tenant_id}")
                return True
            else:
                logger.error(f"Failed to initialize schema: {response.text}")
                return False

    except Exception as e:
        logger.error(f"Error calling system-service: {str(e)}")
        return False

def initialize_communication_service(tenant_id: str, schema_name: str) -> bool:
    """Initialize communication service for tenant"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://communication-service:8010/api/v1/tenants/{tenant_id}/initialize",
                json={"schema_name": schema_name},
                timeout=30
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error initializing communication service: {str(e)}")
        return False


def create_tenant_admin(
    schema_name: str,
    email: str,
    username: str,
    password_hash: str,
    first_name: str,
    last_name: str
) -> Optional[str]:
    """Create admin user in tenant schema"""
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Create the admin user
            user_id = str(uuid.uuid4())

            result = conn.execute(
                text(f"""
                    INSERT INTO {schema_name}.users (
                        id, email, username, password_hash,
                        first_name, last_name,
                        status, is_active, is_verified,
                        created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :password_hash,
                        :first_name, :last_name,
                        'active', true, true,
                        NOW(), NOW()
                    ) RETURNING id
                """),
                {
                    "id": user_id,
                    "email": email,
                    "username": username,
                    "password_hash": password_hash,
                    "first_name": first_name,
                    "last_name": last_name
                }
            )

            # Assign admin role to the user
            conn.execute(
                text(f"""
                    INSERT INTO {schema_name}.user_roles (user_id, role_id)
                    SELECT :user_id, id FROM {schema_name}.roles
                    WHERE name = 'admin'
                    LIMIT 1
                """),
                {"user_id": user_id}
            )

            conn.commit()
            logger.info(f"Created admin user {username} in schema {schema_name}")
            return user_id

    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        return None
    finally:
        engine.dispose()


async def create_tenant_v2(
    tenant_data: TenantCreateV2,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new tenant with proper architecture"""

    # Check if tenant slug already exists
    existing_tenant = db.query(Tenant).filter(
        (Tenant.slug == tenant_data.slug) |
        (Tenant.subdomain == tenant_data.subdomain)
    ).first()

    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant with this slug or subdomain already exists"
        )

    # Generate schema name
    schema_name = generate_schema_name(tenant_data.slug)

    # Create tenant record in shared.tenants
    new_tenant = Tenant(
        id=str(uuid.uuid4()),
        slug=tenant_data.slug,
        name=tenant_data.name,
        subdomain=tenant_data.subdomain or tenant_data.slug,
        domain=tenant_data.domain,
        schema_name=schema_name,
        status="trial" if tenant_data.subscription_plan == "free" else "active",
        subscription_plan=tenant_data.subscription_plan.lower(),
        max_users=5 if tenant_data.subscription_plan == "free" else 50,
        max_storage_gb=10 if tenant_data.subscription_plan == "free" else 100,
        trial_ends_at=datetime.utcnow() + timedelta(days=14) if tenant_data.subscription_plan == "free" else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    try:
        # Step 1: Create tenant record
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        tenant_id = str(new_tenant.id)

        # Step 2: Create database schema
        if not create_tenant_schema(schema_name):
            raise Exception("Failed to create tenant schema")

        # Step 3: Initialize schema with tables using system-service
        if not initialize_tenant_schema(tenant_id, schema_name):
            raise Exception("Failed to initialize tenant schema")

        # Step 4: Initialize communication service tables
        if not initialize_communication_service(tenant_id, schema_name):
            logger.warning(f"Failed to initialize communication service for tenant {tenant_id}, but continuing...")
            # Not raising exception as communication service is optional

        # Step 5: Create admin user in tenant schema
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash(tenant_data.owner_password)

        admin_user_id = create_tenant_admin(
            schema_name=schema_name,
            email=tenant_data.owner_email,
            username=tenant_data.owner_username,
            password_hash=password_hash,
            first_name=tenant_data.owner_first_name,
            last_name=tenant_data.owner_last_name
        )

        if not admin_user_id:
            raise Exception("Failed to create admin user")

        # Step 6: Create subscription history (without changed_by since user is in tenant schema, not shared)
        subscription_history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plan_to=tenant_data.subscription_plan.lower(),
            change_type="initial",
            changed_at=datetime.utcnow(),
            changed_by=None  # User is in tenant schema, not in shared.users
        )
        db.add(subscription_history)
        db.commit()

        # Cache tenant info in Redis (optional)
        try:
            import redis
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "redis"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                decode_responses=True
            )
            import json
            redis_client.setex(
                f"tenant:{new_tenant.slug}",
                3600,
                json.dumps({
                    "id": tenant_id,
                    "schema_name": schema_name,
                    "status": new_tenant.status
                })
            )
        except:
            pass  # Redis caching is optional

        logger.info(f"Successfully created tenant {tenant_data.slug} with admin user {tenant_data.owner_username}")

        return {
            "id": tenant_id,
            "slug": new_tenant.slug,
            "name": new_tenant.name,
            "domain": new_tenant.domain,
            "subdomain": new_tenant.subdomain,
            "status": new_tenant.status,
            "subscription_plan": new_tenant.subscription_plan,
            "max_users": new_tenant.max_users,
            "max_storage_gb": new_tenant.max_storage_gb,
            "created_at": new_tenant.created_at.isoformat(),
            "trial_ends_at": new_tenant.trial_ends_at.isoformat() if new_tenant.trial_ends_at else None,
            "admin_user": {
                "id": admin_user_id,
                "username": tenant_data.owner_username,
                "email": tenant_data.owner_email
            },
            "message": f"Tenant created successfully. Login at: http://{new_tenant.subdomain}.localhost:3000"
        }

    except Exception as e:
        # Rollback on error
        db.rollback()

        # Try to clean up schema if created
        try:
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()
            engine.dispose()
        except:
            pass

        logger.error(f"Error creating tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )


# Usage in FastAPI app:
# @app.post("/api/v1/tenants/v2", response_model=Dict[str, Any])
# async def create_tenant_endpoint(
#     tenant_data: TenantCreateV2,
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     return await create_tenant_v2(tenant_data, background_tasks, db)
