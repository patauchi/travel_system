"""
System Service Main Application
FastAPI application for handling user management, settings, and administrative tools
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import os
from pydantic import BaseModel, validator
import bcrypt
import jwt
from uuid import uuid4

# Import shared authentication
from shared_auth import (
    get_current_user,
    require_super_admin,
    require_tenant_admin,
    check_tenant_slug_access,
    check_permission,
    safe_tenant_session,
    validate_tenant_access
)

# Import database
from database import engine, get_db, SessionLocal, verify_connection

# Import routers from modules
from users.endpoints import (
    router as users_router,
    create_role,
    list_roles,
    get_role,
    create_team,
    list_teams
)
from settings.endpoints import (
    router as settings_router,
    list_audit_logs,
    get_audit_log
)
from tools.endpoints import router as tools_router

# Import models to register them with their respective Base
from users.models import Base as UsersBase
from settings.models import Base as SettingsBase
from tools.models import Base as ToolsBase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Pydantic models for authentication
class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str
    tenant_id: Optional[str] = None

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: Optional[str] = None

class PasswordReset(BaseModel):
    """Password reset request model"""
    email: str

class PasswordChange(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ============================================================================
# Lifespan Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle - startup and shutdown
    """
    # Startup
    logger.info("🚀 Starting System Service...")

    try:
        # Create database tables
        logger.info("📊 Initializing database...")
        with engine.begin() as conn:
            # Create tables for all modules
            UsersBase.metadata.create_all(conn)
            SettingsBase.metadata.create_all(conn)
            ToolsBase.metadata.create_all(conn)

        # Verify database connection
        if verify_connection():
            logger.info("✅ Database connection verified")
        else:
            raise Exception("Database connection failed")

        # Log module registration
        logger.info("📦 Modules registered:")
        logger.info("  - Users module: /api/v1/users")
        logger.info("  - Settings module: /api/v1/settings")
        logger.info("  - Tools module: /api/v1/tools")

        logger.info("✅ System Service started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start System Service: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("👋 Shutting down System Service...")
    engine.dispose()
    logger.info("✅ System Service shut down complete")


# ============================================================================
# Application Setup
# ============================================================================

app = FastAPI(
    title="System Service",
    description="User management, settings, and administrative tools for the Travel System",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with service information"""
    return {
        "service": "System Service",
        "version": "2.0.0",
        "status": "operational",
        "description": "User management, settings, and administrative tools",
        "modules": {
            "users": "User and role management",
            "settings": "System settings and audit logs",
            "tools": "Administrative tools (notes, tasks, calls)"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "users": "/api/v1/users",
            "settings": "/api/v1/settings",
            "tools": "/api/v1/tools"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "System Service",
        "version": "2.0.0",
        "checks": {}
    }

    # Database check
    try:
        result = db.execute(text("SELECT 1"))
        db.commit()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }

    # Module checks
    health_status["checks"]["modules"] = {
        "users": "loaded",
        "settings": "loaded",
        "tools": "loaded"
    }

    return health_status


@app.get("/readiness", tags=["Health"])
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes
    """
    try:
        # Check database
        result = db.execute(text("SELECT 1"))
        db.commit()

        # Check critical tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        required_tables = ['users', 'roles', 'settings', 'audit_logs', 'tasks', 'notes']

        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "missing_tables": missing_tables}
            )

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/v1/auth/initialize-tenant", tags=["Authentication"])
async def initialize_tenant_schema(
    tenant_id: str,
    schema_name: str,
    db: Session = Depends(get_db)
):
    """
    Initialize database schema for a new tenant
    Creates all necessary tables and initial data
    """
    try:
        logger.info(f"Initializing schema for tenant: {tenant_id} with schema name: {schema_name}")

        # Create schema if not exists
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

        # Set search path to tenant schema
        db.execute(text(f"SET search_path TO {schema_name}, public"))

        # Create tables in tenant schema
        # Use a transaction to ensure all tables are created with the correct schema context
        with engine.begin() as conn:
            # Set the schema search path for the connection
            conn.execute(text(f"SET search_path TO {schema_name}, public"))

            # Create metadata with the schema set
            from sqlalchemy import MetaData
            tenant_metadata = MetaData(schema=schema_name)

            # Create tables in correct order to respect foreign key dependencies
            # 1. First create Users module tables (no dependencies)
            users_metadata = MetaData(schema=schema_name)
            for table in UsersBase.metadata.tables.values():
                table.to_metadata(users_metadata)
            users_metadata.create_all(conn)

            # 2. Then create Settings module tables (may depend on users)
            settings_metadata = MetaData(schema=schema_name)
            for table in SettingsBase.metadata.tables.values():
                table.to_metadata(settings_metadata)
            settings_metadata.create_all(conn)

            # 3. Finally create Tools module tables (depends on users)
            tools_metadata = MetaData(schema=schema_name)
            for table in ToolsBase.metadata.tables.values():
                table.to_metadata(tools_metadata)
            tools_metadata.create_all(conn)

        # Create default roles and admin user
        from users.models import User, Role, Permission
        from common.enums import UserStatus, PermissionAction, ResourceType

        # Define all required roles
        roles_to_create = [
            {
                "id": str(uuid4()),
                "name": "admin",
                "display_name": "Administrator",
                "description": "Full system access",
                "is_system": True,
                "priority": 100
            },
            {
                "id": str(uuid4()),
                "name": "manager",
                "display_name": "Manager",
                "description": "Management level access",
                "is_system": True,
                "priority": 80
            },
            {
                "id": str(uuid4()),
                "name": "agent",
                "display_name": "Agent",
                "description": "Sales and booking agent access",
                "is_system": True,
                "priority": 60
            },
            {
                "id": str(uuid4()),
                "name": "accountant",
                "display_name": "Accountant",
                "description": "Financial and accounting access",
                "is_system": True,
                "priority": 70
            },
            {
                "id": str(uuid4()),
                "name": "support",
                "display_name": "Support",
                "description": "Customer support access",
                "is_system": True,
                "priority": 50
            },
            {
                "id": str(uuid4()),
                "name": "user",
                "display_name": "User",
                "description": "Basic user access",
                "is_system": True,
                "priority": 30
            }
        ]

        # Create all roles
        admin_role_id = None
        for role_data in roles_to_create:
            # Check if role exists
            result = db.execute(
                text(f"SELECT id FROM roles WHERE name = :name LIMIT 1"),
                {"name": role_data["name"]}
            )
            existing_role = result.first()

            if not existing_role:
                db.execute(
                    text("""
                        INSERT INTO roles (id, name, display_name, description, is_system, priority)
                        VALUES (:id, :name, :display_name, :description, :is_system, :priority)
                    """),
                    role_data
                )
                if role_data["name"] == "admin":
                    admin_role_id = role_data["id"]
            else:
                if role_data["name"] == "admin":
                    admin_role_id = existing_role.id

        # Ensure we have admin_role_id
        if not admin_role_id:
            result = db.execute(
                text("SELECT id FROM roles WHERE name = 'admin' LIMIT 1")
            )
            admin_role_result = result.first()
            if admin_role_result:
                admin_role_id = str(admin_role_result.id)
            else:
                raise Exception("Admin role not found after creation")

        # Create admin user
        admin_user_id = str(uuid4())
        password_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        db.execute(
            text("""
                INSERT INTO users (id, email, username, password_hash, first_name, last_name, status, is_active, is_verified)
                VALUES (:id, :email, :username, :password_hash, :first_name, :last_name, 'ACTIVE'::userstatus, :is_active, :is_verified)
            """),
            {
                "id": admin_user_id,
                "email": f"admin@tenant{tenant_id}.com",
                "username": f"admin_{tenant_id}",
                "password_hash": password_hash,
                "first_name": "Admin",
                "last_name": "User",
                "is_active": True,
                "is_verified": True
            }
        )

        # Assign admin role to user
        db.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
            """),
            {
                "user_id": admin_user_id,
                "role_id": admin_role_id
            }
        )

        db.commit()

        return {
            "success": True,
            "message": f"Schema initialized for tenant {tenant_id}",
            "tenant_id": tenant_id,
            "admin_user": f"admin_{tenant_id}",
            "default_password": "admin123 (please change immediately)"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize tenant schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize tenant schema: {str(e)}"
        )





@app.post("/api/v1/auth/verify-tenant", tags=["Authentication"])
async def verify_tenant_schema_endpoint(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Verify that a tenant's schema exists and is properly configured
    """
    try:
        # Check if schema exists
        result = db.execute(
            text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name = :schema_name
            """),
            {"schema_name": f"tenant_{tenant_id}"}
        )

        schema = result.first()
        if not schema:
            return {
                "exists": False,
                "message": f"Schema for tenant {tenant_id} does not exist"
            }

        # Set search path and check tables
        db.execute(text(f"SET search_path TO tenant_{tenant_id}, public"))

        result = db.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema_name
                ORDER BY table_name
            """),
            {"schema_name": f"tenant_{tenant_id}"}
        )

        tables = [row[0] for row in result]

        required_tables = ['users', 'roles', 'permissions', 'settings', 'audit_logs', 'tasks', 'notes', 'log_calls']
        missing_tables = [t for t in required_tables if t not in tables]

        return {
            "exists": True,
            "schema": f"tenant_{tenant_id}",
            "tables": tables,
            "missing_tables": missing_tables,
            "is_complete": len(missing_tables) == 0,
            "message": "Schema is properly configured" if len(missing_tables) == 0 else f"Missing tables: {missing_tables}"
        }

    except Exception as e:
        logger.error(f"Failed to verify tenant schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify tenant schema: {str(e)}"
        )


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def tenant_login(
    request: LoginRequest,
    tenant_request: Request,
    db: Session = Depends(get_db)
):
    """
    Authenticate user within a specific tenant context
    """
    try:
        # Get tenant from header or request
        tenant_id = tenant_request.headers.get("X-Tenant-ID") or request.tenant_id

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant ID is required"
            )

        # Set search path to tenant schema
        db.execute(text(f"SET search_path TO tenant_{tenant_id}, public"))

        # Find user by email
        result = db.execute(
            text("""
                SELECT id, email, username, password_hash, status, is_active, is_verified
                FROM users
                WHERE email = :email
                LIMIT 1
            """),
            {"email": request.email}
        )

        user = result.first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password
        if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
            # Update failed login attempts
            db.execute(
                text("""
                    UPDATE users
                    SET failed_login_attempts = failed_login_attempts + 1
                    WHERE id = :user_id
                """),
                {"user_id": user.id}
            )
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user.is_active or user.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "username": user.username,
                "tenant_id": tenant_id
            },
            expires_delta=access_token_expires
        )

        refresh_token = create_access_token(
            data={
                "sub": str(user.id),
                "tenant_id": tenant_id,
                "type": "refresh"
            },
            expires_delta=refresh_token_expires
        )

        # Update last login
        db.execute(
            text("""
                UPDATE users
                SET last_login_at = :now,
                    failed_login_attempts = 0
                WHERE id = :user_id
            """),
            {"now": datetime.utcnow(), "user_id": user.id}
        )
        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id),
            tenant_id=tenant_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@app.post("/api/v1/auth/logout", tags=["Authentication"])
async def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user and invalidate session
    """
    try:
        # In a production environment, you would:
        # 1. Add the token to a blacklist
        # 2. Delete the session from user_sessions table
        # 3. Clear any cached data

        user_id = current_user.get("sub")
        tenant_id = current_user.get("tenant_id")

        if tenant_id:
            db.execute(text(f"SET search_path TO tenant_{tenant_id}, public"))

            # Update last activity
            db.execute(
                text("""
                    UPDATE users
                    SET last_activity_at = :now
                    WHERE id = :user_id
                """),
                {"now": datetime.utcnow(), "user_id": user_id}
            )
            db.commit()

        return {
            "success": True,
            "message": "Logged out successfully"
        }

    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return {
            "success": False,
            "message": "Logout failed"
        }


@app.get("/api/v1/auth/me", tags=["Authentication"])
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user)
):
    """Get current user information from token"""
    return current_user


@app.get("/api/v1/auth/test", tags=["Authentication"])
async def auth_test(
    current_user: Dict = Depends(get_current_user)
):
    """Test authentication endpoint"""
    return {
        "message": "Authentication successful",
        "user": current_user,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# Utility Functions
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid4())  # JWT ID for tracking
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# Register Module Routers
# ============================================================================

# Users module - all user management endpoints
app.include_router(
    users_router,
    prefix="/api/v1/tenants/{tenant_slug}/users",
    tags=["Users"]
)

# Roles endpoints - accessible directly at /roles (from users module)
from fastapi import APIRouter
roles_router = APIRouter()
roles_router.add_api_route("/", endpoint=create_role, methods=["POST"], status_code=status.HTTP_201_CREATED)
roles_router.add_api_route("/", endpoint=list_roles, methods=["GET"])
roles_router.add_api_route("/{role_id}", endpoint=get_role, methods=["GET"])

app.include_router(
    roles_router,
    prefix="/api/v1/tenants/{tenant_slug}/roles",
    tags=["Roles"]
)

# Teams endpoints - accessible directly at /teams (from users module)
teams_router = APIRouter()
teams_router.add_api_route("/", endpoint=create_team, methods=["POST"], status_code=status.HTTP_201_CREATED)
teams_router.add_api_route("/", endpoint=list_teams, methods=["GET"])

app.include_router(
    teams_router,
    prefix="/api/v1/tenants/{tenant_slug}/teams",
    tags=["Teams"]
)

# Settings module - all settings management endpoints
app.include_router(
    settings_router,
    prefix="/api/v1/tenants/{tenant_slug}/settings",
    tags=["Settings"]
)

# Audit logs endpoints - accessible directly at /audit-logs (from settings module)
audit_logs_router = APIRouter()
audit_logs_router.add_api_route("/", endpoint=list_audit_logs, methods=["GET"])
audit_logs_router.add_api_route("/{log_id}", endpoint=get_audit_log, methods=["GET"])

app.include_router(
    audit_logs_router,
    prefix="/api/v1/tenants/{tenant_slug}/audit-logs",
    tags=["Audit Logs"]
)

# Tools module - notes, tasks, logcalls, events
app.include_router(
    tools_router,
    prefix="/api/v1/tenants/{tenant_slug}/tools",
    tags=["Tools"]
)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8008,
        reload=True
    )
