from fastapi import HTTPException, Request, status
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def extract_tenant_from_request(request: Request) -> Optional[str]:
    """Extract tenant identifier from request (subdomain or header)"""

    # Try to get tenant from subdomain
    host = request.headers.get("host", "")

    # Remove port if present
    if ":" in host:
        host = host.split(":")[0]

    # Check if it's a subdomain request
    parts = host.split(".")
    if len(parts) >= 3:  # e.g., tenant1.localhost.com or tenant1.example.com
        return parts[0]

    # Try to get tenant from custom header (useful for API calls)
    tenant_header = request.headers.get("X-Tenant-Slug")
    if tenant_header:
        return tenant_header

    # Try to get tenant from query parameter (fallback)
    tenant_param = request.query_params.get("tenant")
    if tenant_param:
        return tenant_param

    return None

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_tenant_access(token_payload: Dict[str, Any], requested_tenant: Optional[str]) -> bool:
    """
    Verify if user has access to the requested tenant based on their role

    Rules:
    - super_admin: Can access any tenant or no tenant (global admin)
    - tenant_admin: Can only access their own tenant
    - tenant_user: Can only access their own tenant
    - tenant_viewer: Can only access their own tenant
    """

    user_role = token_payload.get("role", "tenant_user")
    user_tenant_slug = token_payload.get("tenant_slug")
    user_tenant_id = token_payload.get("tenant_id")

    # Super admin can access anything
    if user_role == "super_admin":
        return True

    # If no tenant is requested (e.g., accessing main domain), only super_admin is allowed
    if not requested_tenant:
        return False

    # For tenant-specific roles, check if they're accessing their own tenant
    if user_role in ["tenant_admin", "tenant_user", "tenant_viewer"]:
        # User must have a tenant association
        if not user_tenant_slug and not user_tenant_id:
            return False

        # Check if the requested tenant matches user's tenant
        return user_tenant_slug == requested_tenant

    # Default deny
    return False

async def tenant_access_middleware(request: Request, call_next):
    """
    Middleware to enforce tenant access control based on subdomain and user role
    """

    # Skip middleware for auth endpoints (login, register, etc.)
    path = request.url.path
    skip_paths = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/docs",
        "/openapi.json",
        "/health"
    ]

    if any(path.startswith(skip_path) for skip_path in skip_paths):
        return await call_next(request)

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # For public endpoints or if token is not required, continue
        return await call_next(request)

    token = auth_header.split(" ")[1]

    try:
        # Decode token to get user info
        token_payload = decode_token(token)

        # Extract requested tenant from request
        requested_tenant = extract_tenant_from_request(request)

        # Verify access
        if not verify_tenant_access(token_payload, requested_tenant):
            # Log the access denial for auditing
            user_id = token_payload.get("sub")
            user_role = token_payload.get("role")
            user_tenant = token_payload.get("tenant_slug", "none")

            error_detail = (
                f"Access denied. User role '{user_role}' from tenant '{user_tenant}' "
                f"attempted to access tenant '{requested_tenant or 'main'}'"
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_detail
            )

        # Add user info to request state for downstream use
        request.state.user = {
            "id": token_payload.get("sub"),
            "email": token_payload.get("email"),
            "username": token_payload.get("username"),
            "role": token_payload.get("role"),
            "tenant_id": token_payload.get("tenant_id"),
            "tenant_slug": token_payload.get("tenant_slug")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

    # Continue with the request
    response = await call_next(request)
    return response

def get_current_tenant_from_request(request: Request) -> Optional[str]:
    """
    Helper function to get the current tenant from request
    Used by endpoints that need to know which tenant context they're in
    """
    return extract_tenant_from_request(request)

def get_user_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Helper function to get user info from request state
    This is populated by the tenant_access_middleware
    """
    return getattr(request.state, "user", None)
