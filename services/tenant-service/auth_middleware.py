"""
Authentication middleware for Tenant Service
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Security scheme
security = HTTPBearer(auto_error=False)

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

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from JWT token
    Returns user info or raises HTTPException
    """
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

        # Extract user info from token
        user_info = {
            "id": user_id,
            "tenant_id": payload.get("tenant_id"),
            "tenant_slug": payload.get("tenant_slug"),
            "role": payload.get("role", "user"),
            "email": payload.get("email"),
            "username": payload.get("username"),
        }

        # Check if it's a service token
        if payload.get("type") == "service":
            user_info["role"] = "super_admin"  # Services have full access
            user_info["is_service"] = True
            user_info["service_name"] = payload.get("service")

        return user_info
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token if present
    Returns user info or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def require_super_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require super admin role"""
    if current_user.get("role") != "super_admin" and not current_user.get("is_service"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Super admin access required."
        )
    return current_user

async def require_tenant_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require tenant admin role"""
    allowed_roles = ["super_admin", "tenant_admin"]
    if current_user.get("role") not in allowed_roles and not current_user.get("is_service"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Tenant admin access required."
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
