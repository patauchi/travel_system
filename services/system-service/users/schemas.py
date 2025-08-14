"""
Users Module Schemas
Pydantic schemas for user-related API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re

from common.enums import UserStatus


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    phone_secondary: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)
    currency: str = Field(default="USD", max_length=3)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, dots, hyphens and underscores')
        return v

    @validator('phone', 'phone_secondary')
    def validate_phone(cls, v):
        if v and not re.match(r'^[\+\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    role_ids: Optional[List[UUID]] = []
    team_ids: Optional[List[UUID]] = []
    send_welcome_email: bool = Field(default=True)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    phone_secondary: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None
    team_ids: Optional[List[UUID]] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]
    phone: Optional[str]
    phone_secondary: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    department: Optional[str]
    title: Optional[str]
    employee_id: Optional[str]
    timezone: str
    language: str
    currency: str
    status: UserStatus
    is_active: bool
    is_verified: bool
    email_verified_at: Optional[datetime]
    last_login_at: Optional[datetime]
    last_activity_at: Optional[datetime]
    two_factor_enabled: bool
    created_at: datetime
    updated_at: datetime
    roles: Optional[List['RoleResponse']] = []
    teams: Optional[List['TeamResponse']] = []

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Role Schemas
# ============================================

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: int = Field(default=0, ge=0, le=1000)
    max_users: Optional[int] = Field(None, ge=0)
    meta_data: Optional[Dict[str, Any]] = {}

    @validator('name')
    def validate_role_name(cls, v):
        if not re.match(r'^[a-z0-9_]+$', v.lower()):
            raise ValueError('Role name can only contain lowercase letters, numbers and underscores')
        return v.lower()


class RoleCreate(RoleBase):
    permission_ids: Optional[List[UUID]] = []
    is_active: bool = Field(default=True)


class RoleUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=1000)
    max_users: Optional[int] = Field(None, ge=0)
    meta_data: Optional[Dict[str, Any]] = None
    permission_ids: Optional[List[UUID]] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    priority: int
    max_users: Optional[int]
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List['PermissionResponse']] = []

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Permission Schemas
# ============================================

class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=50)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class PermissionCreate(PermissionBase):
    is_active: bool = Field(default=True)


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    resource: str
    action: str
    description: Optional[str]
    conditions: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Team Schemas
# ============================================

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_team_id: Optional[UUID] = None
    team_lead_id: Optional[UUID] = None
    meta_data: Optional[Dict[str, Any]] = {}


class TeamCreate(TeamBase):
    is_active: bool = Field(default=True)
    member_ids: Optional[List[UUID]] = []


class TeamUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_team_id: Optional[UUID] = None
    team_lead_id: Optional[UUID] = None
    meta_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    member_ids: Optional[List[UUID]] = None


class TeamResponse(BaseModel):
    id: UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    parent_team_id: Optional[UUID]
    team_lead_id: Optional[UUID]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    members: Optional[List['UserResponse']] = []
    subteams: Optional[List['TeamResponse']] = []

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Authentication Schemas
# ============================================

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(default=False)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# Forward references
UserResponse.update_forward_refs()
RoleResponse.update_forward_refs()
TeamResponse.update_forward_refs()
