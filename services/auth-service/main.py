from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, validator
import os
import logging
import redis
import json
import uuid
from contextlib import asynccontextmanager

from database import get_db, engine, Base
from models import User, Tenant, AuditLog
from schemas import (
    UserCreate, UserResponse, UserLogin, TokenResponse,
    PasswordReset, PasswordChange, TenantContext,
    UserUpdate, TokenData, RefreshTokenRequest
)
from utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, send_email,
    get_current_user, get_current_active_user,
    check_user_permissions, log_audit_event
)
from exceptions import (
    InvalidCredentialsException, UserNotFoundException,
    TenantNotFoundException, PermissionDeniedException,
    TokenExpiredException, InvalidTokenException
)
from tenant_context import AuthContext, is_system_admin_context, extract_tenant_from_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Auth Service...")
    Base.metadata.create_all(bind=engine)

    # Initialize super_admin on first startup
    try:
        from services.shared.init_super_admin import SuperAdminInitializer
        initializer = SuperAdminInitializer()
        if initializer.initialize():
            logger.info("Super admin initialization completed")
        else:
            logger.warning("Super admin initialization failed or skipped")
    except ImportError:
        # If the module is not available, try inline initialization
        logger.info("Checking for super_admin user...")
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM shared.central_users
                    WHERE username = 'superadmin' OR email = 'admin@system.local'
                """))
                if result.scalar() == 0:
                    # Create super_admin
                    import uuid
                    from passlib.context import CryptContext
                    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
                    user_id = str(uuid.uuid4())
                    password_hash = pwd_ctx.hash("SuperAdmin123!")

                    conn.execute(text("""
                        INSERT INTO shared.central_users (
                            id, email, username, password_hash,
                            first_name, last_name,
                            is_active, is_verified, email_verified_at,
                            created_at, updated_at
                        ) VALUES (
                            :id, 'admin@system.local', 'superadmin', :password_hash,
                            'System', 'Administrator',
                            true, true, CURRENT_TIMESTAMP,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                        )
                    """), {'id': user_id, 'password_hash': password_hash})
                    conn.commit()
                    logger.info("Super admin created: username=superadmin, password=SuperAdmin123!")
                    logger.warning("⚠️ IMPORTANT: Change the super_admin password immediately!")
                else:
                    logger.info("Super admin already exists")
        except Exception as e:
            logger.error(f"Failed to initialize super_admin: {str(e)}")

    yield
    # Shutdown
    logger.info("Shutting down Auth Service...")

app = FastAPI(
    title="Multi-Tenant Auth Service",
    description="Authentication and Authorization Service for Multi-Tenant Platform",
    version="2.0.0",
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

# Models
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant: Optional[Dict[str, Any]] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    # Don't override the type if it's already set (system, tenant, user)
    if "type" not in to_encode:
        to_encode["type"] = "access"
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/auth/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user - works for both tenant and system contexts"""

    with AuthContext(request, db) as auth_ctx:
        if auth_ctx.is_tenant_context:
            # Tenant registration
            tenant_db = auth_ctx.get_db_session()

            # Check if user exists in tenant
            result = tenant_db.execute(
                text(f"""
                    SELECT id FROM {auth_ctx.schema_name}.users
                    WHERE email = :email OR username = :username
                    LIMIT 1
                """),
                {"email": user_data.email, "username": user_data.username}
            )

            if result.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists in this tenant"
                )

            # Create user in tenant schema
            user_id = str(uuid.uuid4())
            hashed_password = get_password_hash(user_data.password)

            tenant_db.execute(
                text(f"""
                    INSERT INTO {auth_ctx.schema_name}.users (
                        id, email, username, password_hash,
                        first_name, last_name, phone,
                        status, is_active, is_verified,
                        created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :password_hash,
                        :first_name, :last_name, :phone,
                        'active', true, false,
                        NOW(), NOW()
                    )
                """),
                {
                    "id": user_id,
                    "email": user_data.email,
                    "username": user_data.username,
                    "password_hash": hashed_password,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "phone": user_data.phone
                }
            )

            # Assign default role
            tenant_db.execute(
                text(f"""
                    INSERT INTO {auth_ctx.schema_name}.user_roles (user_id, role_id)
                    SELECT :user_id, id FROM {auth_ctx.schema_name}.roles
                    WHERE name = 'user'
                    LIMIT 1
                """),
                {"user_id": user_id}
            )

            tenant_db.commit()

            # Create tokens with tenant context
            token_data = {
                "sub": user_id,
                "email": user_data.email,
                "username": user_data.username,
                "role": "user",
                "tenant_id": auth_ctx.tenant_info["id"],
                "tenant_slug": auth_ctx.tenant_info["slug"],
                "tenant_schema": auth_ctx.schema_name
            }

            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": user_id,
                    "email": user_data.email,
                    "username": user_data.username,
                    "first_name": user_data.first_name,
                    "last_name": user_data.last_name,
                    "is_active": True,
                    "is_verified": False,
                    "role": "user"
                },
                "tenant": auth_ctx.tenant_info
            }
        else:
            # System admin registration (main domain only)
            # Check if user exists in shared.central_users
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email or username already exists"
                )

            # Create system user
            hashed_password = get_password_hash(user_data.password)
            new_user = User(
                id=str(uuid.uuid4()),
                email=user_data.email,
                username=user_data.username,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone,
                is_active=True,
                is_verified=False,
                created_at=datetime.utcnow()
            )

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Create tokens for system admin
            token_data = {
                "sub": str(new_user.id),
                "email": new_user.email,
                "username": new_user.username,
                "role": "super_admin"
            }

            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "user": {
                    "id": str(new_user.id),
                    "email": new_user.email,
                    "username": new_user.username,
                    "first_name": new_user.first_name,
                    "last_name": new_user.last_name,
                    "is_active": True,
                    "is_verified": False,
                    "role": "super_admin"
                },
                "tenant": None
            }

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login endpoint - works for both tenant users and system admins"""

    with AuthContext(request, db) as auth_ctx:
        user_data = None
        user_role = None
        tenant_info = None

        if auth_ctx.is_tenant_context:
            # Tenant login - query tenant's users table
            tenant_db = auth_ctx.get_db_session()

            result = tenant_db.execute(
                text(f"""
                    SELECT
                        u.id, u.email, u.username, u.password_hash,
                        u.first_name, u.last_name, u.is_active, u.is_verified,
                        u.failed_login_attempts, u.locked_until,
                        r.name as role_name
                    FROM {auth_ctx.schema_name}.users u
                    LEFT JOIN {auth_ctx.schema_name}.user_roles ur ON u.id = ur.user_id
                    LEFT JOIN {auth_ctx.schema_name}.roles r ON ur.role_id = r.id
                    WHERE u.username = :username
                    ORDER BY r.priority DESC
                    LIMIT 1
                """),
                {"username": form_data.username}
            )

            row = result.fetchone()
            if row:
                user_data = row._asdict() if hasattr(row, '_asdict') else dict(row)
                user_role = user_data.get('role_name', 'user')
                tenant_info = auth_ctx.tenant_info

                # Check if account is locked
                if user_data.get('locked_until'):
                    locked_until = user_data['locked_until']
                    if isinstance(locked_until, str):
                        locked_until = datetime.fromisoformat(locked_until)
                    if locked_until > datetime.utcnow():
                        raise HTTPException(
                            status_code=status.HTTP_423_LOCKED,
                            detail=f"Account locked until {locked_until.isoformat()}"
                        )

                # Verify password
                if not verify_password(form_data.password, user_data['password_hash']):
                    # Update failed login attempts
                    failed_attempts = (user_data.get('failed_login_attempts') or 0) + 1

                    tenant_db.execute(
                        text(f"""
                            UPDATE {auth_ctx.schema_name}.users
                            SET failed_login_attempts = :attempts,
                                locked_until = CASE
                                    WHEN :attempts >= 5 THEN NOW() + INTERVAL '15 minutes'
                                    ELSE NULL
                                END
                            WHERE id = :user_id
                        """),
                        {"attempts": failed_attempts, "user_id": user_data['id']}
                    )
                    tenant_db.commit()

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid username or password"
                    )

                # Reset failed login attempts on successful login
                tenant_db.execute(
                    text(f"""
                        UPDATE {auth_ctx.schema_name}.users
                        SET failed_login_attempts = 0,
                            locked_until = NULL,
                            last_login_at = NOW()
                        WHERE id = :user_id
                    """),
                    {"user_id": user_data['id']}
                )
                tenant_db.commit()

        else:
            # System login - query shared.central_users table
            user = db.query(User).filter(User.username == form_data.username).first()

            if user:
                # Verify password
                if not verify_password(form_data.password, user.password_hash):
                    # Update failed login attempts
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    if user.failed_login_attempts >= 5:
                        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    db.commit()

                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid username or password"
                    )

                # Check if account is locked
                if user.locked_until and user.locked_until > datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_423_LOCKED,
                        detail=f"Account locked until {user.locked_until.isoformat()}"
                    )

                # Reset failed login attempts
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login_at = datetime.utcnow()
                db.commit()

                user_data = {
                    'id': str(user.id),
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_active': user.is_active,
                    'is_verified': user.is_verified
                }
                user_role = "super_admin"

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Check if user is active
        if not user_data.get('is_active'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active"
            )

        # Create tokens
        token_data = {
            "sub": str(user_data['id']),
            "email": user_data['email'],
            "username": user_data['username'],
            "role": user_role
        }

        # Add type field based on role
        if user_role == "super_admin":
            token_data["type"] = "system"
        elif user_role in ["tenant_admin", "tenant_user"]:
            token_data["type"] = "tenant"
        else:
            token_data["type"] = "user"

        if tenant_info:
            token_data.update({
                "tenant_id": tenant_info["id"],
                "tenant_slug": tenant_info["slug"],
                "tenant_schema": auth_ctx.schema_name
            })

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Cache session in Redis
        session_key = f"session:{user_data['id']}"
        session_data = {
            "user_id": str(user_data['id']),
            "username": user_data['username'],
            "role": user_role,
            "tenant_id": tenant_info["id"] if tenant_info else None,
            "login_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(session_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, json.dumps(session_data))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user_data['id']),
                "email": user_data['email'],
                "username": user_data['username'],
                "first_name": user_data.get('first_name'),
                "last_name": user_data.get('last_name'),
                "is_active": user_data.get('is_active', True),
                "is_verified": user_data.get('is_verified', False),
                "role": user_role
            },
            "tenant": tenant_info
        }

@app.post("/api/v1/auth/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user and invalidate session"""

    # Remove session from Redis
    session_key = f"session:{current_user['sub']}"
    redis_client.delete(session_key)

    # Add token to blacklist
    token_blacklist_key = f"blacklist:{current_user['sub']}"
    redis_client.setex(token_blacklist_key, ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")

    return {"message": "Successfully logged out"}

@app.post("/api/v1/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Create new access token
        token_data = {
            "sub": payload["sub"],
            "email": payload["email"],
            "username": payload["username"],
            "role": payload["role"]
        }

        # Preserve the type from the original token
        if "type" in payload:
            token_data["type"] = payload["type"]
        elif payload["role"] == "super_admin":
            token_data["type"] = "system"
        elif payload["role"] in ["tenant_admin", "tenant_user"]:
            token_data["type"] = "tenant"
        else:
            token_data["type"] = "user"

        if "tenant_id" in payload:
            token_data.update({
                "tenant_id": payload["tenant_id"],
                "tenant_slug": payload["tenant_slug"],
                "tenant_schema": payload["tenant_schema"]
            })

        new_access_token = create_access_token(token_data)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": payload["sub"],
                "email": payload.get("email"),
                "username": payload.get("username"),
                "role": payload.get("role")
            },
            "tenant": {
                "id": payload.get("tenant_id"),
                "slug": payload.get("tenant_slug")
            } if payload.get("tenant_id") else None
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@app.get("/api/v1/auth/me")
async def get_current_user_info(
    token: str = Depends(oauth2_scheme),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Get current user information"""

    # Decode token to get user info
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        current_user = payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with AuthContext(request, db) as auth_ctx:
        if auth_ctx.is_tenant_context:
            # Get user from tenant schema
            tenant_db = auth_ctx.get_db_session()
            result = tenant_db.execute(
                text(f"""
                    SELECT
                        u.*, r.name as role_name, r.display_name as role_display
                    FROM {auth_ctx.schema_name}.users u
                    LEFT JOIN {auth_ctx.schema_name}.user_roles ur ON u.id = ur.user_id
                    LEFT JOIN {auth_ctx.schema_name}.roles r ON ur.role_id = r.id
                    WHERE u.id = :user_id
                    LIMIT 1
                """),
                {"user_id": current_user["sub"]}
            )

            user = result.fetchone()
            if user:
                user_dict = user._asdict() if hasattr(user, '_asdict') else dict(user)
                return {
                    "id": str(user_dict['id']),
                    "email": user_dict['email'],
                    "username": user_dict['username'],
                    "first_name": user_dict.get('first_name'),
                    "last_name": user_dict.get('last_name'),
                    "role": user_dict.get('role_name', 'user'),
                    "role_display": user_dict.get('role_display'),
                    "is_active": user_dict.get('is_active', True),
                    "is_verified": user_dict.get('is_verified', False),
                    "tenant": auth_ctx.tenant_info
                }
        else:
            # Get user from shared.central_users
            user = db.query(User).filter(User.id == current_user["sub"]).first()
            if user:
                return {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": "super_admin",
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "tenant": None
                }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
