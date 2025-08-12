"""
Pydantic schemas for system-service
Defines request/response models for API endpoints
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import re


# ============================================
# User Schemas
# ============================================

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    timezone: str = Field(default="UTC", max_length=50)
    language: str = Field(default="en", max_length=10)

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, dots, hyphens and underscores')
        return v

    @validator('phone', 'mobile')
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
    mobile: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    employee_id: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
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
    mobile: Optional[str]
    avatar_url: Optional[str]
    department: Optional[str]
    job_title: Optional[str]
    employee_id: Optional[str]
    location: Optional[str]
    timezone: str
    language: str
    status: str
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
    is_active: Optional[bool] = None
    permission_ids: Optional[List[UUID]] = None
    meta_data: Optional[Dict[str, Any]] = None


class RoleResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    is_active: bool
    priority: int
    max_users: Optional[int]
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    permissions: Optional[List['PermissionResponse']] = []
    user_count: Optional[int] = 0

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Permission Schemas
# ============================================

class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    resource: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None

    @validator('name')
    def validate_permission_name(cls, v):
        if not re.match(r'^[a-z0-9_.]+$', v.lower()):
            raise ValueError('Permission name can only contain lowercase letters, numbers, dots and underscores')
        return v.lower()


class PermissionCreate(PermissionBase):
    is_active: bool = Field(default=True)


class PermissionUpdate(BaseModel):
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
    member_ids: Optional[List[UUID]] = []
    is_active: bool = Field(default=True)


class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    parent_team_id: Optional[UUID] = None
    team_lead_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None


class TeamResponse(BaseModel):
    id: UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    parent_team_id: Optional[UUID]
    team_lead_id: Optional[UUID]
    is_active: bool
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    subteams: Optional[List['TeamResponse']] = []

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Setting Schemas
# ============================================

class SettingBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=100)
    value: Any
    value_type: str = Field(..., pattern='^(string|number|boolean|json)$')
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    validation_rules: Optional[Dict[str, Any]] = None
    allowed_values: Optional[List[Any]] = None
    default_value: Optional[Any] = None


class SettingCreate(SettingBase):
    is_public: bool = Field(default=False)
    is_encrypted: bool = Field(default=False)
    is_system: bool = Field(default=False)


class SettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None
    is_public: Optional[bool] = None


class SettingResponse(BaseModel):
    id: UUID
    category: str
    key: str
    value: Any
    value_type: str
    display_name: Optional[str]
    description: Optional[str]
    is_public: bool
    is_encrypted: bool
    is_system: bool
    validation_rules: Optional[Dict[str, Any]]
    allowed_values: Optional[List[Any]]
    default_value: Optional[Any]
    meta_data: Dict[str, Any]
    updated_at: datetime
    updated_by: Optional[UUID]

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Authentication Schemas
# ============================================

class LoginRequest(BaseModel):
    username: str = Field(..., description="Email or username")
    password: str = Field(...)
    remember_me: bool = Field(default=False)
    two_factor_code: Optional[str] = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordReset(BaseModel):
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


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ============================================
# Audit Log Schemas
# ============================================

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    changes: Optional[Dict[str, Any]]
    result: Optional[str]
    error_message: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[UUID]
    request_id: Optional[str]
    duration_ms: Optional[int]
    meta_data: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Session Schemas
# ============================================

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_info: Optional[Dict[str, Any]]
    location: Optional[Dict[str, Any]]
    is_active: bool
    last_activity: datetime
    expires_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# API Key Schemas
# ============================================

class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    scopes: Optional[List[str]] = []
    rate_limit: int = Field(default=1000, ge=1, le=10000)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    scopes: List[str]
    rate_limit: int
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    last_used_ip: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class ApiKeyFullResponse(ApiKeyResponse):
    api_key: str  # Only returned on creation


# Update forward references
UserResponse.model_rebuild()
RoleResponse.model_rebuild()
TeamResponse.model_rebuild()
