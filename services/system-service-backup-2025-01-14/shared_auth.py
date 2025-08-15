"""
Shared authentication utilities for system-service
JWT-based authentication compatible with auth-service
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import base64
import json
import hashlib

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
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

    return verify_token(credentials.credentials)

# Mock user class for compatibility
class MockUser:
    def __init__(self, user_data: dict):
        self.id = user_data.get('sub', 'mock-user-id')
        self.username = user_data.get('username', 'mock-user')
        self.email = user_data.get('email', 'mock@example.com')
        self.is_active = True

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active
        }

async def get_current_user(
    token_data: Dict[str, Any] = Depends(get_current_user_from_token)
) -> MockUser:
    """Get current user from token data"""
    return MockUser(token_data)

async def get_current_tenant() -> str:
    """Get current tenant ID - simplified implementation"""
    return "default_tenant"

def require_permission(permission: str):
    """Decorator for permission checking - simplified implementation"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # For now, just pass through - implement actual permission checking later
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def verify_simple_token(token: str) -> Dict[str, Any]:
    """Verify token - alias for backward compatibility"""
    return verify_token(token)

def check_tenant_slug_access(user: Dict[str, Any], tenant_slug: str) -> bool:
    """Check if user has access to a tenant by slug"""
    # Super admins have access to all tenants
    if user.get("role") == "super_admin":
        return True

    # Check if user belongs to the tenant
    user_tenant_slug = user.get("tenant_slug")
    if user_tenant_slug and user_tenant_slug == tenant_slug:
        return True

    return False

def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check if user has a specific permission"""
    # Super admins have all permissions
    if user.get("role") == "super_admin":
        return True

    # Admin role has all permissions within their tenant
    if user.get("role") == "admin":
        return True

    # Manager role has most permissions
    if user.get("role") == "manager" and not permission.startswith("admin."):
        return True

    # Check specific permissions list if available
    permissions = user.get("permissions", [])
    if permission in permissions:
        return True

    return False

async def require_super_admin(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Require super admin role"""
    if current_user.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

async def require_tenant_admin(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Require tenant admin role or higher"""
    allowed_roles = ["super_admin", "admin", "tenant_admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Password utilities
def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return hash_password(plain_password) == hashed_password
