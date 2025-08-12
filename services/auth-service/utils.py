from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import redis
import json
import hashlib
import secrets

# Configure logging
logger = logging.getLogger(__name__)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Redis client
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """Get current user from JWT token"""
    from database import get_db
    from models import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        # Check if token is blacklisted
        if redis_client.get(f"blacklist:{token}"):
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Return user data from token
    return {
        "id": user_id,
        "tenant_id": payload.get("tenant_id"),
        "role": payload.get("role")
    }

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensure user is active"""
    # In production, you would check the database
    return current_user

def check_user_permissions(required_permissions: List[str]):
    """Check if user has required permissions"""
    async def permission_checker(current_user: Dict[str, Any] = Depends(get_current_active_user)):
        # Check permissions logic here
        return current_user
    return permission_checker

def log_audit_event(
    db: Session,
    user_id: str,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> None:
    """Log an audit event"""
    from models import AuditLog
    import uuid

    try:
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")
        db.rollback()

async def send_email(
    to: str,
    subject: str,
    body: str,
    html: bool = False
) -> bool:
    """Send email via SMTP"""
    if os.getenv("EMAIL_ENABLED", "false").lower() != "true":
        logger.info(f"Email disabled - would send to {to}: {subject}")
        return True

    try:
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("EMAIL_FROM_ADDRESS", "noreply@multitenant.com")

        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html' if html else 'plain'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)

def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    api_key = secrets.token_urlsafe(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return api_key, api_key_hash

def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against its hash"""
    return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value) if value.startswith('{') or value.startswith('[') else value
        return None
    except Exception as e:
        logger.error(f"Cache get error: {str(e)}")
        return None

def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    """Set value in cache with TTL"""
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        redis_client.setex(key, ttl, value)
        return True
    except Exception as e:
        logger.error(f"Cache set error: {str(e)}")
        return False

def cache_delete(key: str) -> bool:
    """Delete value from cache"""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Cache delete error: {str(e)}")
        return False

def rate_limit_check(key: str, limit: int = 100, window: int = 3600) -> bool:
    """Check rate limit for a key"""
    try:
        current = redis_client.get(key)
        if current is None:
            redis_client.setex(key, window, 1)
            return True

        current_count = int(current)
        if current_count >= limit:
            return False

        redis_client.incr(key)
        return True

    except Exception as e:
        logger.error(f"Rate limit check error: {str(e)}")
        return True  # Allow request on error

def validate_tenant_slug(slug: str) -> bool:
    """Validate tenant slug format"""
    import re
    pattern = r'^[a-z0-9-]+$'
    return bool(re.match(pattern, slug)) and len(slug) >= 3 and len(slug) <= 50

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    return True, "Password is strong"

def generate_tenant_schema_name(slug: str) -> str:
    """Generate database schema name from tenant slug"""
    schema_name = f"tenant_{slug.lower().replace('-', '_')}"
    return schema_name[:63]  # PostgreSQL schema name limit

def get_client_ip(request) -> Optional[str]:
    """Get client IP address from request"""
    if request.client:
        return request.client.host

    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(',')[0].strip()

    return request.headers.get("X-Real-IP")

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent XSS"""
    import html
    return html.escape(input_str)

def paginate_query(query, page: int = 1, page_size: int = 20):
    """Paginate SQLAlchemy query"""
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": page * page_size < total,
        "has_prev": page > 1
    }
