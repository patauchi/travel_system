"""
System Service - Manages tenant-specific users, roles, permissions, and settings
This service handles all tenant-level user management and configuration using modular architecture
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import logging
from pydantic import BaseModel, EmailStr, Field, validator

# Import modular components
from database import get_db, engine
from dependencies import get_tenant_db_session
from shared_auth import get_current_user, verify_token

# Import all modular routers
from users import users_router, User, UserSession
from users.models import Role  # Import Role at the top to avoid duplicate registration
from settings import settings_router, AuditLog
from tools import tools_router
from common.enums import UserStatus

# Import shared base for creating all tables
from shared_models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client for caching - optional
redis_client = None
try:
    import redis
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Connected to Redis")
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}")
    redis_client = None

# Authentication schemas
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(default=False)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

# Password hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    logger.warning("passlib not available, using simple password hashing")
    import hashlib
    pwd_context = None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # Simple fallback hash verification
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password"""
    if pwd_context:
        return pwd_context.hash(password)
    else:
        # Simple fallback hashing
        return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    try:
        from jose import jwt
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, os.getenv('SECRET_KEY', 'your-secret-key'), algorithm="HS256")
        return encoded_jwt
    except ImportError:
        # Simple token fallback
        import base64
        import json
        token_data = {**data, "exp": (datetime.utcnow() + (expires_delta or timedelta(hours=24))).timestamp()}
        return base64.b64encode(json.dumps(token_data).encode()).decode()

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting System Service...")

    # Create all tables from all modules
    try:
        # Import all models to ensure they're registered with shared Base
        from users.models import User, Role, Permission, Team, UserSession
        from settings.models import Setting, AuditLog
        from tools.models import Note, Task, LogCall, Attachment, Event

        # Create all tables using shared Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down System Service...")
    if redis_client:
        redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="System Service",
    description="Manages tenant-specific users, roles, permissions, and settings",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include modular routers
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(settings_router, prefix="/api/v1", tags=["settings"])
app.include_router(tools_router, prefix="/api/v1", tags=["tools"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "system-service",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "users": "User management, roles, permissions, teams",
            "settings": "System settings and audit logs",
            "tools": "Notes, tasks, calls, attachments, events"
        }
    }

# Health check endpoints
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    # Test Redis connection
    redis_status = "healthy" if redis_client else "unavailable"
    if redis_client:
        try:
            redis_client.ping()
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = "unhealthy"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "redis": redis_status
        }
    }

@app.get("/readiness")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check endpoint"""
    try:
        # Verify database is ready
        db.execute(text("SELECT 1"))

        # Verify critical tables exist
        db.execute(text("SELECT count(*) FROM information_schema.tables WHERE table_name = 'users'"))

        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

# Tenant management endpoints
@app.post("/api/v1/tenant/initialize")
async def initialize_tenant_schema(
    tenant_id: str,
    schema_name: str = None,
    db: Session = Depends(get_db)
):
    """Initialize tenant-specific schema"""
    try:
        # Use provided schema_name or generate from tenant_id
        if not schema_name:
            # Fallback: replace hyphens with underscores for valid schema name
            schema_name = f"tenant_{tenant_id.replace('-', '_')}"

        # Create schema if it doesn't exist
        db.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        db.commit()

        # Create all tables in tenant schema using the current connection
        # We need to use the connection from the current session
        connection = db.connection()

        # Set the schema for this connection
        connection.execute(text(f"SET search_path TO {schema_name}"))

        # Create all tables using the connection with the correct search_path
        Base.metadata.create_all(bind=connection)

        # Create default roles for the tenant
        logger.info(f"Creating default roles for tenant: {tenant_id}")

        default_roles = [
            {
                "name": "admin",
                "display_name": "Administrator",
                "description": "Full access to all tenant features and settings",
                "priority": 100
            },
            {
                "name": "manager",
                "display_name": "Manager",
                "description": "Can manage teams, view reports, and oversee operations",
                "priority": 75
            },
            {
                "name": "agent",
                "display_name": "Agent",
                "description": "Can handle customer interactions and day-to-day operations",
                "priority": 50
            },
            {
                "name": "user",
                "display_name": "User",
                "description": "Basic access to assigned features",
                "priority": 25
            }
        ]

        for role_data in default_roles:
            db.execute(text(f"""
                INSERT INTO {schema_name}.roles (id, name, display_name, description, priority, is_active, created_at)
                VALUES (
                    gen_random_uuid(),
                    :name,
                    :display_name,
                    :description,
                    :priority,
                    true,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (name) DO NOTHING
            """), role_data)

        # Commit the transaction
        db.commit()

        logger.info(f"Initialized schema for tenant: {tenant_id} with default roles")

        return {
            "status": "success",
            "message": f"Tenant schema {schema_name} initialized successfully",
            "tenant_id": tenant_id,
            "schema_name": schema_name
        }

    except Exception as e:
        logger.error(f"Failed to initialize tenant schema: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize tenant schema: {str(e)}"
        )

@app.get("/api/v1/tenant/verify")
def get_current_tenant() -> str:
    """Get current tenant ID - placeholder implementation"""
    return "default_tenant"

@app.get("/api/v1/tenant/verify")
async def verify_tenant_schema_endpoint(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Verify tenant schema exists and is properly configured"""
    try:
        schema_name = f"tenant_{tenant_id}"

        # Check if schema exists
        result = db.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = :schema_name
        """), {"schema_name": schema_name})

        if not result.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant schema {schema_name} not found"
            )

        # Set search path and verify tables
        db.execute(text(f"SET search_path TO {schema_name}"))

        # Check critical tables
        required_tables = ['users', 'roles', 'permissions', 'settings', 'audit_logs']
        for table in required_tables:
            result = db.execute(text(f"""
                SELECT tablename
                FROM pg_tables
                WHERE tablename = '{table}'
                AND schemaname = '{schema_name}'
            """))
            if not result.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Required table {table} not found in schema {schema_name}"
                )

        return {
            "status": "verified",
            "tenant_id": tenant_id,
            "schema_name": schema_name,
            "tables_verified": required_tables
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify tenant schema: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify tenant schema: {str(e)}"
        )

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def tenant_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Tenant-specific user login"""
    try:
        # Find user by username or email
        user = db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked"
            )

        # Check if user is active
        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_activity_at = datetime.utcnow()

        # Create tokens
        access_token_expires = timedelta(hours=24)
        refresh_token_expires = timedelta(days=7)

        access_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": "current"},
            expires_delta=access_token_expires
        )

        refresh_token = create_access_token(
            data={"sub": str(user.id), "tenant_id": "current", "type": "refresh"},
            expires_delta=refresh_token_expires
        )

        # Create user session
        session = UserSession(
            user_id=user.id,
            token_hash=get_password_hash(access_token),
            refresh_token_hash=get_password_hash(refresh_token),
            expires_at=datetime.utcnow() + access_token_expires,
            refresh_expires_at=datetime.utcnow() + refresh_token_expires
        )
        db.add(session)

        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="user_login",
            resource_type="authentication",
            result="success"
        )
        db.add(audit_log)

        db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds()),
            user=user.to_dict()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/api/v1/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""
    try:
        # Deactivate all user sessions
        db.query(UserSession).filter(UserSession.user_id == current_user.id).update(
            {"is_active": False}
        )

        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="user_logout",
            resource_type="authentication",
            result="success"
        )
        db.add(audit_log)

        db.commit()

        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@app.get("/api/v1/auth/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user.to_dict()

@app.post("/api/v1/auth/test")
async def auth_test(
    current_user: User = Depends(get_current_user)
):
    """Test authentication"""
    return {
        "message": "Authentication successful",
        "user_id": str(current_user.id),
        "username": current_user.username,
        "tenant_id": get_current_tenant(),
        "timestamp": datetime.utcnow().isoformat()
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
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
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8008")),
            reload=os.getenv("ENVIRONMENT", "production") == "development"
        )
    except ImportError:
        logger.error("uvicorn not available, cannot start server")
        raise
