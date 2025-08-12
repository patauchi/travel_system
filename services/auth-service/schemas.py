from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    tenant_id: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    tenants: Optional[List[Dict[str, Any]]] = []

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UserLogin(BaseModel):
    username: str
    password: str
    tenant_slug: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    tenant: Optional[Dict[str, Any]] = None

class TokenData(BaseModel):
    sub: str
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[datetime] = None
    type: str = "access"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

    @validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        return v

class VerifyEmail(BaseModel):
    token: str

class TwoFactorSetup(BaseModel):
    enable: bool
    code: Optional[str] = Field(None, min_length=6, max_length=6)

class TwoFactorVerify(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class TenantContext(BaseModel):
    tenant_id: str
    tenant_slug: str
    tenant_name: str
    role: str
    permissions: Optional[List[str]] = []

class AuditLogCreate(BaseModel):
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class EmailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str
    template: Optional[str] = None
    variables: Optional[Dict[str, Any]] = {}

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    version: Optional[str] = "1.0.0"
    dependencies: Optional[List[Dict[str, Any]]] = []

class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    timestamp: datetime
    path: Optional[str] = None
    method: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

class TenantInfo(BaseModel):
    id: str
    name: str
    slug: str
    status: str
    subscription_plan: str
    max_users: int
    max_storage_gb: int
    created_at: datetime
    trial_ends_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class UserTenantRole(BaseModel):
    tenant_id: str
    tenant_name: str
    tenant_slug: str
    role: str
    is_owner: bool
    joined_at: datetime
    permissions: Optional[Dict[str, Any]] = {}

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    tenant_id: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class FeatureFlag(BaseModel):
    name: str
    enabled: bool
    description: Optional[str] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)
    tenant_overrides: Optional[Dict[str, bool]] = {}

class SystemSetting(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None
    is_public: bool = False
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
