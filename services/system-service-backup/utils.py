"""
Utility functions for system-service
Includes authentication, password hashing, token generation, and other helpers
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import secrets
import string
import hashlib
import re
from sqlalchemy.orm import Session
import logging
import uuid

# Configure logging
logger = logging.getLogger(__name__)

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


# ============================================
# Password Functions
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password

    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: The plain text password to hash

    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def is_password_strong(password: str) -> tuple[bool, str]:
    """
    Check if a password meets strength requirements

    Args:
        password: The password to check

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


# ============================================
# Token Functions
# ============================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token

    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token

    Args:
        token: The JWT token to verify

    Returns:
        The decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without verification (for debugging)

    Args:
        token: The JWT token to decode

    Returns:
        The decoded token payload or None if invalid
    """
    try:
        # Decode without verification
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        logger.error(f"Token decoding failed: {str(e)}")
        return None


# ============================================
# Random Generation Functions
# ============================================

def generate_random_token(length: int = 32) -> str:
    """
    Generate a random token string

    Args:
        length: The length of the token

    Returns:
        A random token string
    """
    return secrets.token_urlsafe(length)


def generate_random_password(length: int = 12) -> str:
    """
    Generate a random password with mixed characters

    Args:
        length: The length of the password

    Returns:
        A random password string
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))

    # Ensure it has at least one of each required character type
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in "!@#$%^&*()" for c in password):
        password = password[:-1] + secrets.choice("!@#$%^&*()")

    return password


def generate_api_key() -> tuple[str, str]:
    """
    Generate an API key with prefix

    Returns:
        Tuple of (full_key, key_hash)
    """
    prefix = "sk_" if os.getenv("ENVIRONMENT") == "production" else "sk_test_"
    key = prefix + secrets.token_urlsafe(48)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


# ============================================
# Permission Functions
# ============================================

def check_user_permission(user: Dict[str, Any], permission: str) -> bool:
    """
    Check if a user has a specific permission

    Args:
        user: The user dict from token
        permission: The permission to check

    Returns:
        True if user has permission, False otherwise
    """
    # Check if user is system admin (always has all permissions)
    if user.get("type") == "system" and user.get("role") == "super_admin":
        return True

    # Check if user has the permission in their permissions list
    permissions = user.get("permissions", [])
    if permission in permissions:
        return True

    # Check wildcard permissions (e.g., "users.*" matches "users.read")
    resource = permission.split(".")[0] if "." in permission else permission
    if f"{resource}.*" in permissions:
        return True

    # Check if user has admin role (for tenant users)
    roles = user.get("roles", [])
    if "admin" in roles:
        return True

    return False


def has_any_permission(user: Dict[str, Any], permissions: List[str]) -> bool:
    """
    Check if a user has any of the specified permissions

    Args:
        user: The user dict from token
        permissions: List of permissions to check

    Returns:
        True if user has any of the permissions
    """
    return any(check_user_permission(user, perm) for perm in permissions)


def has_all_permissions(user: Dict[str, Any], permissions: List[str]) -> bool:
    """
    Check if a user has all of the specified permissions

    Args:
        user: The user dict from token
        permissions: List of permissions to check

    Returns:
        True if user has all of the permissions
    """
    return all(check_user_permission(user, perm) for perm in permissions)


# ============================================
# Audit Logging Functions
# ============================================

def log_audit(
    db: Session,
    user_id: uuid.UUID,
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    result: str = "success",
    error_message: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    session_id: Optional[uuid.UUID] = None,
    request_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an audit event to the database

    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: The action being performed
        resource_type: Type of resource being acted upon
        resource_id: ID of the resource
        resource_name: Name of the resource
        changes: Dictionary of changes made
        result: Result of the action (success, failure, partial)
        error_message: Error message if action failed
        ip_address: IP address of the request
        user_agent: User agent string
        session_id: Session ID
        request_id: Request ID for tracing
        duration_ms: Duration of the operation in milliseconds
        metadata: Additional metadata
    """
    try:
        from models import AuditLog

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            changes=changes,
            result=result,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            duration_ms=duration_ms,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        db.add(audit_log)
        db.commit()

        logger.info(f"Audit log created: {action} by user {user_id} on {resource_type}/{resource_id}")

    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        # Don't fail the main operation if audit logging fails
        db.rollback()


# ============================================
# Validation Functions
# ============================================

def is_valid_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: The email to validate

    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_username(username: str) -> bool:
    """
    Validate username format

    Args:
        username: The username to validate

    Returns:
        True if valid username format
    """
    pattern = r'^[a-zA-Z0-9_.-]{3,100}$'
    return bool(re.match(pattern, username))


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format

    Args:
        phone: The phone number to validate

    Returns:
        True if valid phone format
    """
    pattern = r'^[\+\d\s\-\(\)]+$'
    return bool(re.match(pattern, phone))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal

    Args:
        filename: The filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Remove or replace problematic characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    return filename


def verify_tenant_access(tenant_slug: str, current_user: dict) -> bool:
    """
    Verify that the current user has access to the specified tenant

    Args:
        tenant_slug: The tenant slug to verify access for
        current_user: The current user's information from JWT

    Returns:
        True if user has access

    Raises:
        HTTPException if user doesn't have access
    """
    # For now, we'll just check if the user belongs to the tenant
    # In a real implementation, this would check the database
    user_tenant = current_user.get("tenant_slug")

    if user_tenant != tenant_slug and current_user.get("role") != "super_admin":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="You don't have access to this tenant"
        )

    return True


def get_current_user(request: Any) -> dict:
    """
    Get the current user from the request
    This is a placeholder that should be replaced with actual JWT validation

    Args:
        request: The FastAPI request object

    Returns:
        Dictionary with user information
    """
    # This is a simplified version - in production, extract from JWT token
    return {
        "user_id": str(uuid.uuid4()),
        "email": "user@example.com",
        "tenant_slug": "default",
        "role": "tenant_user"
    }

    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext

    return filename


# ============================================
# String Manipulation Functions
# ============================================

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug

    Args:
        text: The text to slugify

    Returns:
        URL-friendly slug
    """
    # Convert to lowercase
    text = text.lower()

    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)

    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)

    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Remove leading and trailing hyphens
    text = text.strip('-')

    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length

    Args:
        text: The text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


# ============================================
# Date/Time Functions
# ============================================

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object to string

    Args:
        dt: The datetime to format
        format: The format string

    Returns:
        Formatted datetime string
    """
    if dt is None:
        return ""

    return dt.strftime(format)


def parse_datetime(dt_str: str, format: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse a datetime string to datetime object

    Args:
        dt_str: The datetime string to parse
        format: The format string

    Returns:
        Parsed datetime object or None if invalid
    """
    try:
        return datetime.strptime(dt_str, format)
    except (ValueError, TypeError):
        return None


def time_ago(dt: datetime) -> str:
    """
    Get human-readable time ago string

    Args:
        dt: The datetime to compare

    Returns:
        Human-readable time ago string
    """
    if dt is None:
        return "never"

    now = datetime.utcnow()
    diff = now - dt

    if diff.days > 365:
        return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
    elif diff.days > 30:
        return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
    else:
        return "just now"
