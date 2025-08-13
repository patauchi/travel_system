"""
System Service - Manages tenant-specific users, roles, permissions, and settings
This service handles all tenant-level user management and configuration
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import logging
import redis
import json
import uuid
from pydantic import BaseModel, EmailStr, Field, validator

from database import get_db, engine, Base
from dependencies import get_tenant_db_session, verify_tenant_schema
from models import User, Role, Permission, Setting, Team, UserSession, AuditLog
from schemas import (
    UserCreate, UserUpdate, UserResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionResponse,
    SettingUpdate, SettingResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    LoginRequest, TokenResponse,
    PasswordReset, PasswordChange
)
from utils import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    verify_token, generate_random_token,
    check_user_permission, log_audit
)
from schema_manager import SchemaManager
from extended_endpoints import include_extended_routers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client for caching and sessions
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Schema manager for creating tables from SQLAlchemy models
schema_manager = SchemaManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application"""
    # Startup
    logger.info("Starting System Service...")

    # Initialize database connections
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

    # Test Redis connection
    try:
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")

    yield

    # Shutdown
    logger.info("Shutting down System Service...")
    redis_client.close()

app = FastAPI(
    title="System Service",
    description="Manages tenant-specific users, roles, permissions, and settings",
    version="1.0.0",
    lifespan=lifespan
)

# Include extended endpoints for notes, tasks, events, etc.
include_extended_routers(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ============================================
# Health Check Endpoints
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "system-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check database
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        # Check Redis
        redis_client.ping()

        return {
            "status": "ready",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )

# ============================================
# Tenant Schema Management
# ============================================

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant_schema(
    tenant_id: str,
    schema_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Initialize a new tenant schema with all required tables"""
    try:
        # Initialize schema with all tables from SQLAlchemy models
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] != "success":
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize schema: {result.get('errors', ['Unknown error'])}"
            )

        # Log the action
        logger.info(f"Initialized schema for tenant {tenant_id}: {schema_name}")

        # Schedule background task to verify schema
        background_tasks.add_task(verify_tenant_schema, tenant_id, schema_name)

        return {
            "status": "success",
            "message": f"Schema {schema_name} initialized successfully",
            "tenant_id": tenant_id
        }
    except Exception as e:
        logger.error(f"Failed to initialize tenant schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize tenant schema: {str(e)}"
        )

async def verify_tenant_schema(tenant_id: str, schema_name: str):
    """Background task to verify tenant schema creation"""
    try:
        with engine.connect() as conn:
            # Check if all tables exist
            result = conn.execute(text(f"""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
            """))
            table_count = result.scalar()

            logger.info(f"Tenant {tenant_id} schema {schema_name} has {table_count} tables")

            # Update cache
            redis_client.setex(
                f"tenant:{tenant_id}:schema_verified",
                3600,
                json.dumps({"verified": True, "table_count": table_count})
            )
    except Exception as e:
        logger.error(f"Schema verification failed for tenant {tenant_id}: {str(e)}")

# ============================================
# Authentication Endpoints (Tenant-specific)
# ============================================

@app.post("/api/v1/tenants/{tenant_slug}/auth/login", response_model=TokenResponse)
async def tenant_login(
    tenant_slug: str,
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login for tenant users"""
    # Get tenant database connection
    tenant_db = get_tenant_db(tenant_slug)

    # Find user in tenant's schema
    user = tenant_db.query(User).filter(
        (User.email == credentials.username) |
        (User.username == credentials.username)
    ).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        # Log failed attempt
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            tenant_db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked until {user.locked_until}"
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Reset failed login attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()

    # Get user roles and permissions
    roles = [role.name for role in user.roles]
    permissions = []
    for role in user.roles:
        permissions.extend([perm.name for perm in role.permissions])

    # Create tokens
    token_data = {
        "sub": str(user.id),
        "type": "tenant",
        "tenant_slug": tenant_slug,
        "email": user.email,
        "username": user.username,
        "roles": roles,
        "permissions": list(set(permissions))  # Remove duplicates
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Create session
    session = UserSession(
        user_id=user.id,
        token_hash=get_password_hash(access_token),
        refresh_token_hash=get_password_hash(refresh_token),
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent"),
        expires_at=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        refresh_expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    tenant_db.add(session)

    # Log audit
    log_audit(
        tenant_db,
        user_id=user.id,
        action="user_login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent")
    )

    tenant_db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user.to_dict()
    }

# ============================================
# User Management Endpoints
# ============================================

@app.post("/api/v1/tenants/{tenant_slug}/users", response_model=UserResponse)
async def create_user(
    tenant_slug: str,
    user_data: UserCreate,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Create a new user in the tenant"""
    # Check permission
    if not check_user_permission(current_user, "users.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Check if user already exists
    existing_user = tenant_db.query(User).filter(
        (User.email == user_data.email) |
        (User.username == user_data.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        full_name=f"{user_data.first_name} {user_data.last_name}",
        department=user_data.department,
        title=user_data.title,
        created_by=uuid.UUID(current_user["sub"])
    )

    # Assign default role
    default_role = tenant_db.query(Role).filter(Role.name == "user").first()
    if default_role:
        new_user.roles.append(default_role)

    tenant_db.add(new_user)

    # Log audit
    log_audit(
        tenant_db,
        user_id=uuid.UUID(current_user["sub"]),
        action="user_created",
        resource_type="user",
        resource_id=str(new_user.id),
        resource_name=new_user.username
    )

    tenant_db.commit()
    tenant_db.refresh(new_user)

    return UserResponse.from_orm(new_user)

@app.get("/api/v1/tenants/{tenant_slug}/users", response_model=List[UserResponse])
async def list_users(
    tenant_slug: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """List all users in the tenant"""
    # Check permission
    if not check_user_permission(current_user, "users.view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Query users
    users = tenant_db.query(User).filter(
        User.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()

    return [UserResponse.from_orm(user) for user in users]

@app.get("/api/v1/tenants/{tenant_slug}/users/{user_id}", response_model=UserResponse)
async def get_user(
    tenant_slug: str,
    user_id: uuid.UUID,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Get a specific user by ID"""
    # Check permission
    if not check_user_permission(current_user, "users.view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get user
    user = tenant_db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)

@app.put("/api/v1/tenants/{tenant_slug}/users/{user_id}", response_model=UserResponse)
async def update_user(
    tenant_slug: str,
    user_id: uuid.UUID,
    user_update: UserUpdate,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Update user information"""
    # Check permission
    if not check_user_permission(current_user, "users.update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get user
    user = tenant_db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    for field, value in user_data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    user.updated_by = uuid.UUID(current_user["sub"])
    user.updated_at = datetime.utcnow()

    # Log audit
    log_audit(
        tenant_db,
        user_id=uuid.UUID(current_user["sub"]),
        action="user_updated",
        resource_type="user",
        resource_id=str(user.id),
        resource_name=user.username
    )

    tenant_db.commit()
    tenant_db.refresh(user)

    return UserResponse.from_orm(user)

@app.delete("/api/v1/tenants/{tenant_slug}/users/{user_id}")
async def delete_user(
    tenant_slug: str,
    user_id: uuid.UUID,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Delete a user"""
    # Check permission
    if not check_user_permission(current_user, "users.delete"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get user
    user = tenant_db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.deleted_by = uuid.UUID(current_user["sub"])
    user.is_active = False

    # Log audit
    log_audit(
        tenant_db,
        user_id=uuid.UUID(current_user["sub"]),
        action="user_deleted",
        resource_type="user",
        resource_id=str(user.id),
        resource_name=user.username
    )

    tenant_db.commit()

    return {"message": "User deleted successfully"}

# ============================================
# Role Management Endpoints
# ============================================

@app.get("/api/v1/tenants/{tenant_slug}/roles", response_model=List[RoleResponse])
async def list_roles(
    tenant_slug: str,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """List all roles in the tenant"""
    # Check permission
    if not check_user_permission(current_user, "roles.view"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Query roles
    roles = tenant_db.query(Role).filter(Role.is_active == True).all()

    return [RoleResponse.from_orm(role) for role in roles]

@app.post("/api/v1/tenants/{tenant_slug}/roles", response_model=RoleResponse)
async def create_role(
    tenant_slug: str,
    role_data: RoleCreate,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Create a new role"""
    # Check permission
    if not check_user_permission(current_user, "roles.create"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Check if role already exists
    existing_role = tenant_db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )

    # Create new role
    new_role = Role(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        priority=role_data.priority,
        created_by=uuid.UUID(current_user["sub"])
    )

    # Assign permissions
    if role_data.permission_ids:
        permissions = tenant_db.query(Permission).filter(
            Permission.id.in_(role_data.permission_ids)
        ).all()
        new_role.permissions.extend(permissions)

    tenant_db.add(new_role)

    # Log audit
    log_audit(
        tenant_db,
        user_id=uuid.UUID(current_user["sub"]),
        action="role_created",
        resource_type="role",
        resource_id=str(new_role.id),
        resource_name=new_role.name
    )

    tenant_db.commit()
    tenant_db.refresh(new_role)

    return RoleResponse.from_orm(new_role)

# ============================================
# Settings Management Endpoints
# ============================================

@app.get("/api/v1/tenants/{tenant_slug}/settings", response_model=List[SettingResponse])
async def list_settings(
    tenant_slug: str,
    category: Optional[str] = None,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """List all settings or settings in a specific category"""
    # Query settings
    query = tenant_db.query(Setting)

    if category:
        query = query.filter(Setting.category == category)

    # Filter based on permissions
    if not check_user_permission(current_user, "settings.view"):
        # Only show public settings
        query = query.filter(Setting.is_public == True)

    settings = query.all()

    return [SettingResponse.from_orm(setting) for setting in settings]

@app.put("/api/v1/tenants/{tenant_slug}/settings/{setting_id}", response_model=SettingResponse)
async def update_setting(
    tenant_slug: str,
    setting_id: uuid.UUID,
    setting_data: SettingUpdate,
    current_user: dict = Depends(verify_token),
    tenant_db: Session = Depends(get_tenant_db_session)
):
    """Update a tenant setting"""
    # Check permission
    if not check_user_permission(current_user, "settings.update"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Get setting
    setting = tenant_db.query(Setting).filter(Setting.id == setting_id).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )

    # Check if system setting
    if setting.is_system and not check_user_permission(current_user, "settings.update_system"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system settings"
        )

    # Update setting
    setting.value = setting_data.value
    setting.updated_by = uuid.UUID(current_user["sub"])
    setting.updated_at = datetime.utcnow()

    # Log audit
    log_audit(
        tenant_db,
        user_id=uuid.UUID(current_user["sub"]),
        action="setting_updated",
        resource_type="setting",
        resource_id=str(setting.id),
        resource_name=f"{setting.category}.{setting.key}",
        changes={"old_value": setting.value, "new_value": setting_data.value}
    )

    tenant_db.commit()
    tenant_db.refresh(setting)

    return SettingResponse.from_orm(setting)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004, reload=True)
