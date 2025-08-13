from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import os
import logging
import redis
import json
import uuid
import re
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database and models
from database import get_db, engine, Base, db_manager
from models import Tenant, TenantUser, User, SubscriptionHistory, TenantFeature, FeatureFlag
from auth_middleware import verify_token, get_current_user, require_super_admin, require_tenant_admin
from tasks import provision_tenant_resources, cleanup_tenant_resources
from create_tenant_v2 import TenantCreateV2, create_tenant_v2, initialize_tenant_schema
import httpx

# Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Tenant Service...")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    logger.info("Shutting down Tenant Service...")

app = FastAPI(
    title="Multi-Tenant Management Service",
    description="Service for managing tenants in the multi-tenant platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models
class TenantCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    subdomain: Optional[str] = None
    domain: Optional[str] = None
    owner_email: EmailStr
    owner_username: str
    owner_password: str
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

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    subdomain: Optional[str] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    tenant_metadata: Optional[Dict[str, Any]] = None

class TenantResponse(BaseModel):
    id: str
    slug: str
    name: str
    domain: Optional[str]
    subdomain: Optional[str]
    status: str
    subscription_plan: str
    max_users: int
    max_storage_gb: int
    created_at: datetime
    trial_ends_at: Optional[datetime]
    user_count: Optional[int] = 0
    storage_used_gb: Optional[float] = 0

class SubscriptionUpdate(BaseModel):
    plan: str
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None

class FeatureToggle(BaseModel):
    feature_name: str
    enabled: bool
    configuration: Optional[Dict[str, Any]] = {}

class TenantUserInvite(BaseModel):
    email: EmailStr
    role: str = "tenant_user"
    send_email: bool = True

class TenantStats(BaseModel):
    total_users: int
    active_users: int
    storage_used_gb: float
    storage_limit_gb: int
    api_calls_today: int
    api_calls_limit: int
    last_activity: Optional[datetime]

# Utility functions
def generate_schema_name(slug: str) -> str:
    """Generate a valid PostgreSQL schema name from tenant slug"""
    # PostgreSQL schema names must be <= 63 characters
    schema_name = f"tenant_{slug.lower().replace('-', '_')}"
    return schema_name[:63]

def check_tenant_limits(tenant: Tenant, db: Session) -> Dict[str, bool]:
    """Check if tenant has reached any limits"""
    user_count = db.query(TenantUser).filter(TenantUser.tenant_id == tenant.id).count()

    return {
        "users_limit_reached": user_count >= tenant.max_users,
        "trial_expired": tenant.trial_ends_at and tenant.trial_ends_at < datetime.utcnow() if tenant.status == "trial" else False,
        "subscription_expired": tenant.subscription_ends_at and tenant.subscription_ends_at < datetime.utcnow() if tenant.subscription_ends_at else False
    }

# Routes
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "tenant-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/tenants/v2", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_tenant_endpoint_v2(
    tenant_data: TenantCreateV2,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new tenant with proper architecture (V2)"""
    return await create_tenant_v2(tenant_data, background_tasks, db)

@app.post("/api/v1/tenants", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new tenant with owner user (DEPRECATED - Use /v2)"""

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

    # Check if owner user already exists
    existing_user = db.query(User).filter(
        (User.email == tenant_data.owner_email) |
        (User.username == tenant_data.owner_username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Generate schema name
    schema_name = generate_schema_name(tenant_data.slug)

    # Check if schema already exists
    if db_manager.check_schema_exists(schema_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database schema for this tenant already exists"
        )

    # Create tenant
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
        created_at=datetime.utcnow()
    )

    # Create owner user
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    owner_user = User(
        id=str(uuid.uuid4()),
        email=tenant_data.owner_email,
        username=tenant_data.owner_username,
        password_hash=pwd_context.hash(tenant_data.owner_password),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_verified=True,
        email_verified_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )

    try:
        # Create database schema
        if not db_manager.create_tenant_schema(schema_name):
            raise Exception("Failed to create tenant schema")

        # Save tenant first
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        # Initialize schema with tables using system-service
        tenant_id = str(new_tenant.id)
        if not initialize_tenant_schema(tenant_id, schema_name):
            logger.warning(f"Failed to initialize schema with system-service for tenant {tenant_id}")
            # Continue anyway as the schema was created

        # Initialize communication-service tables
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"http://communication-service:8005/api/v1/tenants/{tenant_id}/initialize",
                    json={"schema_name": schema_name},
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Successfully initialized communication-service for tenant {tenant_id}")
                else:
                    logger.warning(f"Failed to initialize communication-service for tenant {tenant_id}: {response.text}")
        except Exception as e:
            logger.warning(f"Error calling communication-service for tenant {tenant_id}: {str(e)}")

        # Initialize CRM service tables
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"http://crm-service:8006/api/v1/tenants/{tenant_id}/initialize",
                    json={"schema_name": schema_name},
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Successfully initialized CRM service for tenant {tenant_id}")
                else:
                    logger.warning(f"Failed to initialize CRM service for tenant {tenant_id}: {response.text}")
        except Exception as e:
            logger.warning(f"Error calling CRM service for tenant {tenant_id}: {str(e)}")

        # Initialize Financial service tables
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"http://financial-service:8007/api/v1/tenants/{tenant_id}/initialize",
                    json={"schema_name": schema_name},
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Successfully initialized Financial service for tenant {tenant_id}")
                else:
                    logger.warning(f"Failed to initialize Financial service for tenant {tenant_id}: {response.text}")
        except Exception as e:
            logger.warning(f"Error calling Financial service for tenant {tenant_id}: {str(e)}")

        # Initialize Booking Operations service tables
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"http://booking-operations-service:8004/api/v1/tenants/{tenant_id}/initialize",
                    json={"schema_name": schema_name},
                    timeout=30
                )
                if response.status_code == 200:
                    logger.info(f"Successfully initialized Booking Operations service for tenant {tenant_id}")
                else:
                    logger.warning(f"Failed to initialize Booking Operations service for tenant {tenant_id}: {response.text}")
        except Exception as e:
            logger.warning(f"Error calling Booking Operations service for tenant {tenant_id}: {str(e)}")

        # Save user
        db.add(owner_user)
        db.commit()
        db.refresh(owner_user)

        # Create tenant-user relationship
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            tenant_id=str(new_tenant.id),
            user_id=owner_user.id,
            role="tenant_admin",
            is_owner=True,
            joined_at=datetime.utcnow()
        )
        db.add(tenant_user)

        # Create subscription history
        subscription_history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            tenant_id=str(new_tenant.id),
            plan_to=tenant_data.subscription_plan.lower(),
            change_type="initial",
            changed_at=datetime.utcnow(),
            changed_by=owner_user.id
        )
        db.add(subscription_history)
        db.commit()

        # Schedule background tasks for tenant provisioning
        # Temporarily disabled due to Redis serialization issue
        # background_tasks.add_task(provision_tenant_resources, new_tenant.id, schema_name)

        # Cache tenant info in Redis
        redis_client.setex(
            f"tenant:{new_tenant.slug}",
            3600,
            json.dumps({
                "id": str(new_tenant.id),
                "schema_name": schema_name,
                "status": new_tenant.status
            })
        )

        return TenantResponse(
            id=str(new_tenant.id),
            slug=new_tenant.slug,
            name=new_tenant.name,
            domain=new_tenant.domain,
            subdomain=new_tenant.subdomain,
            status=new_tenant.status,
            subscription_plan=new_tenant.subscription_plan,
            max_users=new_tenant.max_users,
            max_storage_gb=new_tenant.max_storage_gb,
            created_at=new_tenant.created_at,
            trial_ends_at=new_tenant.trial_ends_at,
            user_count=1
        )

    except Exception as e:
        # Rollback on error
        db.rollback()
        # Try to clean up schema if created
        db_manager.drop_tenant_schema(schema_name)
        logger.error(f"Error creating tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating tenant: {str(e)}"
        )

@app.get("/api/v1/tenants", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tenants (admin only) or user's tenants"""

    query = db.query(Tenant)

    # Temporarily show all tenants for testing
    # TODO: Re-enable role-based filtering
    show_all = True  # Set to False to enable filtering

    if not show_all:
        # If not super admin, only show user's tenants
        if current_user.get("role") != "super_admin":
            user_tenant_ids = db.query(TenantUser.tenant_id).filter(
                TenantUser.user_id == current_user["id"]
            ).subquery()
            query = query.filter(Tenant.id.in_(user_tenant_ids))

    if status:
        query = query.filter(Tenant.status == status)

    tenants = query.offset(skip).limit(limit).all()

    results = []
    for tenant in tenants:
        user_count = db.query(TenantUser).filter(TenantUser.tenant_id == tenant.id).count()
        results.append(TenantResponse(
            id=str(tenant.id),
            slug=tenant.slug,
            name=tenant.name,
            domain=tenant.domain,
            subdomain=tenant.subdomain,
            status=tenant.status,
            subscription_plan=tenant.subscription_plan,
            max_users=tenant.max_users,
            max_storage_gb=tenant.max_storage_gb,
            created_at=tenant.created_at,
            trial_ends_at=tenant.trial_ends_at,
            user_count=user_count
        ))

    return results

@app.get("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tenant details"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if user has access to this tenant
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"]
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

    user_count = db.query(TenantUser).filter(TenantUser.tenant_id == tenant.id).count()

    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        domain=tenant.domain,
        subdomain=tenant.subdomain,
        status=tenant.status,
        subscription_plan=tenant.subscription_plan,
        max_users=tenant.max_users,
        max_storage_gb=tenant.max_storage_gb,
        created_at=tenant.created_at,
        trial_ends_at=tenant.trial_ends_at,
        user_count=user_count
    )

@app.patch("/api/v1/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tenant details"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if user has admin access to this tenant
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"],
            TenantUser.role.in_(["tenant_admin", "tenant_owner"])
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can update tenant"
            )

    # Update fields
    update_data = tenant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(tenant, field):
            setattr(tenant, field, value)

    tenant.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(tenant)

    # Update cache
    redis_client.setex(
        f"tenant:{tenant.slug}",
        3600,
        json.dumps({
            "id": tenant.id,
            "schema_name": tenant.schema_name,
            "status": tenant.status
        })
    )

    user_count = db.query(TenantUser).filter(TenantUser.tenant_id == tenant.id).count()

    return TenantResponse(
        id=str(tenant.id),
        slug=tenant.slug,
        name=tenant.name,
        domain=tenant.domain,
        subdomain=tenant.subdomain,
        status=tenant.status,
        subscription_plan=tenant.subscription_plan,
        max_users=tenant.max_users,
        max_storage_gb=tenant.max_storage_gb,
        created_at=tenant.created_at,
        trial_ends_at=tenant.trial_ends_at,
        user_count=user_count
    )

@app.delete("/api/v1/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db)
):
    """Delete a tenant (super admin only)"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    try:
        # Drop schema
        if not db_manager.drop_tenant_schema(tenant.schema_name):
            logger.warning(f"Failed to drop schema {tenant.schema_name}")

        # Delete from database (cascade will handle related records)
        db.delete(tenant)
        db.commit()

        # Clear cache
        redis_client.delete(f"tenant:{tenant.slug}")

        # Schedule cleanup tasks
        background_tasks.add_task(cleanup_tenant_resources, tenant_id)

        return {"message": f"Tenant {tenant.name} deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting tenant: {str(e)}"
        )

@app.post("/api/v1/tenants/{tenant_id}/subscription", response_model=Dict[str, Any])
async def update_subscription(
    tenant_id: str,
    subscription: SubscriptionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tenant subscription plan"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check permissions
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"],
            TenantUser.is_owner == True
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant owner can update subscription"
            )

    # Determine change type
    old_plan = tenant.subscription_plan
    new_plan = subscription.plan

    if old_plan == new_plan:
        change_type = "renewal"
    elif ["free", "starter", "professional", "enterprise"].index(new_plan) > ["free", "starter", "professional", "enterprise"].index(old_plan):
        change_type = "upgrade"
    else:
        change_type = "downgrade"

    # Update tenant subscription
    tenant.subscription_plan = new_plan
    tenant.status = "active"

    # Update limits based on plan
    plan_limits = {
        "free": {"max_users": 5, "max_storage_gb": 10},
        "starter": {"max_users": 50, "max_storage_gb": 100},
        "professional": {"max_users": 200, "max_storage_gb": 500},
        "enterprise": {"max_users": 99999, "max_storage_gb": 99999}
    }

    limits = plan_limits.get(new_plan, plan_limits["free"])
    tenant.max_users = limits["max_users"]
    tenant.max_storage_gb = limits["max_storage_gb"]

    # Set subscription end date
    tenant.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
    tenant.updated_at = datetime.utcnow()

    # Create subscription history
    history = SubscriptionHistory(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        plan_from=old_plan,
        plan_to=new_plan,
        change_type=change_type,
        payment_method=subscription.payment_method,
        transaction_id=subscription.transaction_id,
        changed_at=datetime.utcnow(),
        changed_by=current_user["id"]
    )

    db.add(history)
    db.commit()

    return {
        "message": f"Subscription updated to {new_plan}",
        "tenant_id": tenant_id,
        "old_plan": old_plan,
        "new_plan": new_plan,
        "change_type": change_type,
        "subscription_ends_at": tenant.subscription_ends_at.isoformat()
    }

@app.get("/api/v1/tenants/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tenant statistics"""

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check permissions
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"]
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

    # Get statistics
    total_users = db.query(TenantUser).filter(TenantUser.tenant_id == tenant_id).count()

    active_users = db.query(TenantUser).join(User).filter(
        TenantUser.tenant_id == tenant_id,
        User.is_active == True,
        TenantUser.last_active_at >= datetime.utcnow() - timedelta(days=30)
    ).count()

    # Get storage usage (mock for now)
    storage_used_gb = 2.5  # This would come from actual file storage service

    # Get API usage from Redis
    api_calls_today = int(redis_client.get(f"api_calls:{tenant_id}:{datetime.utcnow().date()}") or 0)
    api_calls_limit = 10000 if tenant.subscription_plan != "free" else 1000

    # Get last activity
    last_activity = db.query(TenantUser.last_active_at).filter(
        TenantUser.tenant_id == tenant_id
    ).order_by(TenantUser.last_active_at.desc()).first()

    return TenantStats(
        total_users=total_users,
        active_users=active_users,
        storage_used_gb=storage_used_gb,
        storage_limit_gb=tenant.max_storage_gb,
        api_calls_today=api_calls_today,
        api_calls_limit=api_calls_limit,
        last_activity=last_activity[0] if last_activity else None
    )

@app.post("/api/v1/tenants/{tenant_id}/features", response_model=Dict[str, Any])
async def toggle_tenant_feature(
    tenant_id: str,
    feature: FeatureToggle,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable or disable a feature for a tenant"""

    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check permissions
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"],
            TenantUser.role == "tenant_admin"
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can manage features"
            )

    # Check if feature exists
    feature_flag = db.query(FeatureFlag).filter(FeatureFlag.name == feature.feature_name).first()
    if not feature_flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )

    # Check or create tenant feature
    tenant_feature = db.query(TenantFeature).filter(
        TenantFeature.tenant_id == tenant_id,
        TenantFeature.feature_id == feature_flag.id
    ).first()

    if tenant_feature:
        tenant_feature.is_enabled = feature.enabled
        tenant_feature.configuration = feature.configuration
    else:
        tenant_feature = TenantFeature(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            feature_id=feature_flag.id,
            is_enabled=feature.enabled,
            configuration=feature.configuration,
            enabled_at=datetime.utcnow(),
            enabled_by=current_user["id"]
        )
        db.add(tenant_feature)

    db.commit()

    # Cache feature state
    redis_client.setex(
        f"feature:{tenant_id}:{feature.feature_name}",
        3600,
        json.dumps({"enabled": feature.enabled, "config": feature.configuration})
    )

    return {
        "message": f"Feature {feature.feature_name} {'enabled' if feature.enabled else 'disabled'}",
        "tenant_id": tenant_id,
        "feature": feature.feature_name,
        "enabled": feature.enabled
    }

@app.post("/api/v1/tenants/{tenant_id}/users/invite", response_model=Dict[str, Any])
async def invite_user_to_tenant(
    tenant_id: str,
    invite: TenantUserInvite,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invite a user to join a tenant"""

    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check permissions
    if current_user.get("role") != "super_admin":
        tenant_user = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == current_user["id"],
            TenantUser.role.in_(["tenant_admin", "tenant_owner"])
        ).first()

        if not tenant_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only tenant admins can invite users"
            )

    # Check tenant limits
    limits = check_tenant_limits(tenant, db)
    if limits["users_limit_reached"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant has reached the maximum number of users ({tenant.max_users})"
        )

    # Check if user exists
    user = db.query(User).filter(User.email == invite.email).first()

    if user:
        # Check if user is already in tenant
        existing = db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.user_id == user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this tenant"
            )

    # Generate invitation token
    invitation_token = str(uuid.uuid4())

    # Create tenant user invitation
    if user:
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user.id,
            role=invite.role,
            invited_by=current_user["id"],
            invitation_token=invitation_token,
            joined_at=datetime.utcnow()
        )
        db.add(tenant_user)
    else:
        # Store invitation in Redis for new users
        redis_client.setex(
            f"invitation:{invitation_token}",
            7 * 24 * 3600,  # 7 days expiry
            json.dumps({
                "tenant_id": tenant_id,
                "email": invite.email,
                "role": invite.role,
                "invited_by": current_user["id"]
            })
        )

    db.commit()

    # Send invitation email (mock)
    if invite.send_email:
        # This would integrate with email service
        logger.info(f"Sending invitation email to {invite.email}")

    return {
        "message": f"Invitation sent to {invite.email}",
        "tenant_id": tenant_id,
        "invitation_token": invitation_token,
        "user_exists": user is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
