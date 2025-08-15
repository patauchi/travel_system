"""
Shared authentication utilities for system-service
JWT-based authentication compatible with auth-service
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security scheme
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Extract current user from token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(credentials.credentials)

        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting user from token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current authenticated user"""
    return await get_current_user_from_token(credentials)


def get_current_tenant(request: Request) -> Optional[str]:
    """Extract tenant ID from request headers or token"""
    # First try to get from header
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    # Try to get from authorization token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = verify_token(token)
            return payload.get("tenant_id")
        except:
            pass

    return None


async def verify_tenant_access(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> bool:
    """Verify that the current user has access to the specified tenant"""
    user_tenant_id = current_user.get("tenant_id")

    # Check if user's tenant matches requested tenant
    if user_tenant_id and user_tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this tenant"
        )

    # Check if user is a super admin (optional)
    if current_user.get("is_super_admin"):
        return True

    return user_tenant_id == tenant_id


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check permissions
            user_permissions = current_user.get("permissions", [])
            if permission not in user_permissions and not current_user.get("is_super_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check roles
            user_roles = current_user.get("roles", [])
            if role not in user_roles and not current_user.get("is_super_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role}' required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_role(roles: List[str]):
    """Decorator to require any of the specified roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has any of the required roles
            user_roles = current_user.get("roles", [])
            if not any(role in user_roles for role in roles) and not current_user.get("is_super_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these roles required: {', '.join(roles)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """Decorator to require any of the specified permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            # Check if user has any of the required permissions
            user_permissions = current_user.get("permissions", [])
            if not any(perm in user_permissions for perm in permissions) and not current_user.get("is_super_admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of these permissions required: {', '.join(permissions)}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


class TenantContext:
    """Context manager for tenant-specific operations"""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.schema_name = f"tenant_{tenant_id.replace('-', '_').lower()}"

    async def __aenter__(self):
        """Enter tenant context"""
        logger.info(f"Entering tenant context: {self.tenant_id}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit tenant context"""
        logger.info(f"Exiting tenant context: {self.tenant_id}")
        if exc_type:
            logger.error(f"Error in tenant context: {exc_val}")
        return False


def parse_token(token: str) -> Optional[Dict[str, Any]]:
    """Parse a token without verification (for logging/debugging only)"""
    try:
        # Decode without verification for inspection
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode payload
        import base64
        import json

        # Add padding if needed
        payload = parts[1]
        padding = 4 - (len(payload) % 4)
        if padding:
            payload += '=' * padding

        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded)
    except Exception as e:
        logger.error(f"Error parsing token: {str(e)}")
        return None


def generate_api_key() -> str:
    """Generate a new API key"""
    import secrets
    return f"sk_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage"""
    import hashlib
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash"""
    return hash_api_key(api_key) == hashed_key


async def get_user_from_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Get user information from API key"""
    # This would typically query the database
    # For now, return a mock response
    if api_key.startswith("sk_"):
        return {
            "user_id": "api_user",
            "tenant_id": "default",
            "is_api_key": True,
            "permissions": ["read", "write"]
        }
    return None


# Export all functions
__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_user_from_token",
    "get_current_tenant",
    "verify_tenant_access",
    "require_permission",
    "require_role",
    "require_any_role",
    "require_any_permission",
    "TenantContext",
    "parse_token",
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "get_user_from_api_key",
    "security"
]
