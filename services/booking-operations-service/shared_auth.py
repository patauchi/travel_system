"""
Shared authentication utilities for all microservices
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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
    """Extract current user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Build user info from token
        user_info = {
            "id": user_id,
            "tenant_id": payload.get("tenant_id"),
            "tenant_slug": payload.get("tenant_slug"),
            "role": payload.get("role", "user"),
            "email": payload.get("email"),
            "username": payload.get("username"),
            "permissions": payload.get("permissions", []),
        }

        # Handle service tokens
        if payload.get("type") == "service":
            user_info["role"] = "super_admin"
            user_info["is_service"] = True
            user_info["service_name"] = payload.get("service")

        return user_info
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None

    try:
        return await get_current_user_from_token(credentials)
    except HTTPException:
        return None

# Alias for easier use
get_current_user = get_current_user_from_token

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Ensure user is active"""
    # In a real app, you might check the database here
    # For now, we trust the token
    return current_user

async def require_super_admin(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Require super admin role"""
    if current_user.get("role") != "super_admin" and not current_user.get("is_service"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user

async def require_tenant_admin(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
) -> Dict[str, Any]:
    """Require tenant admin role or higher"""
    allowed_roles = ["super_admin", "tenant_admin"]
    if current_user.get("role") not in allowed_roles and not current_user.get("is_service"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required"
        )
    return current_user

def check_tenant_access(user: Dict[str, Any], tenant_id: str) -> bool:
    """Check if user has access to a specific tenant"""
    # Services and super admins have access to all tenants
    if user.get("is_service") or user.get("role") == "super_admin":
        return True

    # Check if user belongs to the tenant
    return str(user.get("tenant_id")) == str(tenant_id)

def check_tenant_slug_access(user: Dict[str, Any], tenant_slug: str) -> bool:
    """Check if user has access to a tenant by slug"""
    # Services and super admins have access to all tenants
    if user.get("is_service") or user.get("role") == "super_admin":
        return True

    # Check if user belongs to the tenant
    return user.get("tenant_slug") == tenant_slug

def check_permission(user: Dict[str, Any], permission: str) -> bool:
    """Check if a user has a specific permission"""
    # Services and super admins have all permissions
    if user.get("is_service") or user.get("role") == "super_admin":
        return True

    # Check if user has the permission in their permissions list
    permissions = user.get("permissions", [])
    if permission in permissions:
        return True

    # Check wildcard permissions (e.g., "conversations.*" matches "conversations.read")
    if "." in permission:
        resource = permission.split(".")[0]
        if f"{resource}.*" in permissions:
            return True

    # Tenant admins have broad permissions within their tenant
    if user.get("role") == "tenant_admin":
        return True

    return False

# Backward compatibility alias
check_user_permission = check_permission

# Service-to-service authentication
def create_service_token(service_name: str) -> str:
    """Create a token for service-to-service communication"""
    data = {
        "sub": f"service:{service_name}",
        "type": "service",
        "service": service_name,
        "role": "super_admin",
        "iat": datetime.utcnow(),
    }
    return create_access_token(data, expires_delta=timedelta(hours=24))

def verify_service_token(token: str) -> Dict[str, Any]:
    """Verify a service-to-service token"""
    payload = verify_token(token)
    if payload.get("type") != "service":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service token"
        )
    return payload
