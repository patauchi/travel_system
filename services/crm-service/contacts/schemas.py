"""
Contact Schemas for CRM Service
Pydantic models for contact request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

from core.enums import ContactStatus, Gender, PreferredCommunication

# ============================================
# CONTACT SCHEMAS
# ============================================

class ContactBase(BaseModel):
    """Base schema for Contact"""
    contact_status: ContactStatus = ContactStatus.active
    is_primary_contact: bool = False
    department: Optional[str] = Field(None, max_length=100)
    reports_to: Optional[int] = None

    # Personal travel information
    passport_number: Optional[str] = Field(None, max_length=50)
    passport_expiry: Optional[date] = None
    visa_requirements: Optional[List[str]] = None
    dietary_restrictions: Optional[str] = None
    accessibility_needs: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None

    # Communication preferences
    email_opt_in: bool = True
    sms_opt_in: bool = False
    preferred_communication: PreferredCommunication = PreferredCommunication.email

    @validator('passport_expiry')
    def validate_passport_expiry(cls, v):
        if v and v < date.today():
            raise ValueError('Passport expiry date cannot be in the past')
        return v

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

class ContactCreate(ContactBase):
    """Schema for creating a Contact with Actor information"""
    # Actor information (required for new contact)
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

    # Account association (optional)
    account_id: Optional[int] = None
    passenger_id: Optional[int] = None

    @validator('email', 'phone', 'mobile')
    def validate_contact_info(cls, v, values):
        # At least one contact method is required
        if not v and not values.get('email') and not values.get('phone') and not values.get('mobile'):
            raise ValueError('At least one contact method (email, phone, or mobile) is required')
        return v

class ContactUpdate(BaseModel):
    """Schema for updating a Contact"""
    contact_status: Optional[ContactStatus] = None
    is_primary_contact: Optional[bool] = None
    department: Optional[str] = Field(None, max_length=100)
    reports_to: Optional[int] = None
    passport_number: Optional[str] = Field(None, max_length=50)
    passport_expiry: Optional[date] = None
    visa_requirements: Optional[List[str]] = None
    dietary_restrictions: Optional[str] = None
    accessibility_needs: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    email_opt_in: Optional[bool] = None
    sms_opt_in: Optional[bool] = None
    preferred_communication: Optional[PreferredCommunication] = None
    account_id: Optional[int] = None
    passenger_id: Optional[int] = None

class ContactResponse(ContactBase):
    """Schema for Contact response"""
    id: int
    actor_id: int
    account_id: Optional[int] = None
    passenger_id: Optional[int] = None
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

    # Manager information (if reports_to is set)
    manager_name: Optional[str] = None

    class Config:
        from_attributes = True

class ContactListFilter(BaseModel):
    """Schema for filtering contact list"""
    contact_status: Optional[List[ContactStatus]] = None
    account_id: Optional[int] = None
    is_primary_contact: Optional[bool] = None
    department: Optional[str] = None
    gender: Optional[List[Gender]] = None
    email_opt_in: Optional[bool] = None
    sms_opt_in: Optional[bool] = None
    preferred_communication: Optional[List[PreferredCommunication]] = None
    passport_expiring_days: Optional[int] = Field(None, ge=0, le=365)  # Show contacts with passport expiring in X days
    search: Optional[str] = None  # Search in name, email, phone
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|first_name|last_name|company_name)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class ContactBulkAction(BaseModel):
    """Schema for bulk actions on contacts"""
    contact_ids: List[int]
    action: str = Field(..., pattern="^(update_status|assign_account|delete|update_communication_prefs)$")
    contact_status: Optional[ContactStatus] = None  # For update_status action
    account_id: Optional[int] = None  # For assign_account action
    email_opt_in: Optional[bool] = None  # For update_communication_prefs action
    sms_opt_in: Optional[bool] = None  # For update_communication_prefs action
    preferred_communication: Optional[PreferredCommunication] = None  # For update_communication_prefs action
