"""
Users Module
Exports all user-related models, schemas, and endpoints
"""

from .models import (
    User,
    Role,
    Permission,
    Team,
    UserSession,
    PasswordResetToken,
    EmailVerificationToken,
    ApiKey,
    role_permissions,
    user_permissions,
    user_roles,
    team_members,
)

from .schemas import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionBase,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
    TeamBase,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest,
)

from .endpoints import router as users_router

__all__ = [
    # Models
    "User",
    "Role",
    "Permission",
    "Team",
    "UserSession",
    "PasswordResetToken",
    "EmailVerificationToken",
    "ApiKey",
    "role_permissions",
    "user_permissions",
    "user_roles",
    "team_members",

    # Schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "PermissionBase",
    "PermissionCreate",
    "PermissionUpdate",
    "PermissionResponse",
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "ChangePasswordRequest",

    # Router
    "users_router",
]
