"""
Account Schemas for CRM Service
Pydantic models for account request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

from core.enums import AccountType, AccountStatus, PaymentMethod, RiskLevel

# ============================================
# ACCOUNT SCHEMAS
# ============================================

class AccountBase(BaseModel):
    """Base schema for Account"""
    account_type: AccountType
    account_status: AccountStatus = AccountStatus.PROSPECT
    parent_account_id: Optional[int] = None
    is_following: bool = False

    # Business Information
    tax_id: Optional[str] = Field(None, max_length=50)
    business_license: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[PaymentMethod] = None

    # Additional business information
    company_owner: Optional[uuid.UUID] = None
    employee_count: Optional[int] = Field(None, ge=0)
    time_zone: Optional[str] = Field(None, max_length=50)

    # Banking information
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=50)
    swift_code: Optional[str] = Field(None, max_length=20)

    # Metrics
    total_bookings: int = Field(0, ge=0)
    lifetime_value: float = Field(0, ge=0)
    last_booking_date: Optional[date] = None
    first_booking_date: Optional[date] = None

    # Segmentation information
    customer_segment: Optional[str] = Field(None, max_length=50)
    loyalty_points: int = Field(0, ge=0)
    risk_level: RiskLevel = RiskLevel.LOW

    # Industry association
    industry_id: Optional[int] = None

    @validator('last_booking_date', 'first_booking_date')
    def validate_booking_dates(cls, v):
        if v and v > date.today():
            raise ValueError('Booking dates cannot be in the future')
        return v

    @validator('last_booking_date')
    def validate_last_booking_after_first(cls, v, values):
        first_booking = values.get('first_booking_date')
        if v and first_booking and v < first_booking:
            raise ValueError('Last booking date cannot be before first booking date')
        return v

class AccountCreate(AccountBase):
    """Schema for creating an Account with Actor information"""
    # Actor information (required for new account)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=50)

    # Optional actor fields
    title: Optional[str] = Field(None, max_length=100)
    street: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=255)

    # Business-specific actor fields
    annual_revenue: Optional[float] = Field(None, ge=0)
    number_of_employees: Optional[int] = Field(None, ge=0)

    @validator('company_name', 'first_name')
    def validate_name_required(cls, v, values):
        account_type = values.get('account_type')
        if account_type == AccountType.BUSINESS and not values.get('company_name'):
            raise ValueError('Company name is required for business accounts')
        elif account_type == AccountType.PERSON and not values.get('first_name'):
            raise ValueError('First name is required for person accounts')
        return v

    @validator('email', 'phone', 'mobile')
    def validate_contact_info(cls, v, values):
        # At least one contact method is required
        if not v and not values.get('email') and not values.get('phone') and not values.get('mobile'):
            raise ValueError('At least one contact method (email, phone, or mobile) is required')
        return v

class AccountUpdate(BaseModel):
    """Schema for updating an Account"""
    account_type: Optional[AccountType] = None
    account_status: Optional[AccountStatus] = None
    parent_account_id: Optional[int] = None
    is_following: Optional[bool] = None
    tax_id: Optional[str] = Field(None, max_length=50)
    business_license: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[float] = Field(None, ge=0)
    payment_terms: Optional[str] = Field(None, max_length=50)
    payment_method: Optional[PaymentMethod] = None
    company_owner: Optional[uuid.UUID] = None
    employee_count: Optional[int] = Field(None, ge=0)
    time_zone: Optional[str] = Field(None, max_length=50)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_account: Optional[str] = Field(None, max_length=50)
    swift_code: Optional[str] = Field(None, max_length=20)
    total_bookings: Optional[int] = Field(None, ge=0)
    lifetime_value: Optional[float] = Field(None, ge=0)
    last_booking_date: Optional[date] = None
    first_booking_date: Optional[date] = None
    customer_segment: Optional[str] = Field(None, max_length=50)
    loyalty_points: Optional[int] = Field(None, ge=0)
    risk_level: Optional[RiskLevel] = None
    industry_id: Optional[int] = None

class AccountResponse(AccountBase):
    """Schema for Account response"""
    id: int
    actor_id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    # Actor information
    actor_first_name: Optional[str] = None
    actor_last_name: Optional[str] = None
    actor_company_name: Optional[str] = None
    actor_email: Optional[str] = None
    actor_phone: Optional[str] = None
    actor_mobile: Optional[str] = None
    actor_title: Optional[str] = None
    actor_website: Optional[str] = None
    actor_annual_revenue: Optional[float] = None
    actor_number_of_employees: Optional[int] = None

    # Industry information
    industry_name: Optional[str] = None
    industry_code: Optional[str] = None

    # Parent account information
    parent_account_name: Optional[str] = None

    # Contact counts
    total_contacts: Optional[int] = None
    primary_contacts: Optional[int] = None

    class Config:
        from_attributes = True

class AccountListFilter(BaseModel):
    """Schema for filtering account list"""
    account_type: Optional[List[AccountType]] = None
    account_status: Optional[List[AccountStatus]] = None
    industry_id: Optional[int] = None
    parent_account_id: Optional[int] = None
    customer_segment: Optional[str] = None
    risk_level: Optional[List[RiskLevel]] = None
    payment_method: Optional[List[PaymentMethod]] = None
    min_lifetime_value: Optional[float] = Field(None, ge=0)
    max_lifetime_value: Optional[float] = Field(None, ge=0)
    min_credit_limit: Optional[float] = Field(None, ge=0)
    max_credit_limit: Optional[float] = Field(None, ge=0)
    has_recent_bookings: Optional[bool] = None  # Bookings in last 12 months
    is_following: Optional[bool] = None
    search: Optional[str] = None  # Search in name, email, phone
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|company_name|first_name|last_name|lifetime_value|last_booking_date)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class AccountBulkAction(BaseModel):
    """Schema for bulk actions on accounts"""
    account_ids: List[int]
    action: str = Field(..., pattern="^(update_status|update_segment|assign_owner|delete|update_risk_level)$")
    account_status: Optional[AccountStatus] = None  # For update_status action
    customer_segment: Optional[str] = Field(None, max_length=50)  # For update_segment action
    company_owner: Optional[uuid.UUID] = None  # For assign_owner action
    risk_level: Optional[RiskLevel] = None  # For update_risk_level action

class AccountMetrics(BaseModel):
    """Schema for account metrics and analytics"""
    total_accounts: int
    accounts_by_type: dict
    accounts_by_status: dict
    accounts_by_segment: dict
    top_accounts_by_value: List[dict]
    recent_bookings_count: int
    average_lifetime_value: float
    total_lifetime_value: float

class AccountHierarchy(BaseModel):
    """Schema for account hierarchy (parent-child relationships)"""
    account_id: int
    account_name: str
    account_type: AccountType
    parent_account_id: Optional[int] = None
    parent_account_name: Optional[str] = None
    child_accounts: List[dict] = []
    hierarchy_level: int = 0
