"""
Lead Schemas for CRM Service
Pydantic models for lead request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

from core.enums import LeadStatus, InterestLevel

# ============================================
# LEAD SCHEMAS
# ============================================

class LeadBase(BaseModel):
    """Base schema for Lead"""
    lead_source: Optional[str] = Field(None, max_length=100)
    lead_status: LeadStatus = LeadStatus.new
    conversion_probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    estimated_value: Optional[float] = Field(None, ge=0)

    # Conversion Information
    interest_level: InterestLevel = InterestLevel.low
    inquiry_type: Optional[str] = Field(None, max_length=255)
    last_contacted_at: Optional[date] = None
    is_qualified: bool = False
    disqualification_reason: Optional[str] = None
    referral_source: Optional[str] = None

    # Travel specific
    travel_interests: Optional[List[str]] = None
    preferred_travel_date: Optional[date] = None
    number_of_travelers: Optional[int] = Field(None, ge=1)
    special_requirements: Optional[str] = None

    # Management
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None
    campaign_id: Optional[str] = Field(None, max_length=255)
    score: int = Field(0, ge=0, le=100)

class LeadCreate(LeadBase):
    """Schema for creating a Lead with Actor information"""
    # Actor information (required for new lead)
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

    @validator('email', 'phone', 'mobile')
    def validate_contact_info(cls, v, values):
        # At least one contact method is required
        if not v and not values.get('email') and not values.get('phone') and not values.get('mobile'):
            raise ValueError('At least one contact method (email, phone, or mobile) is required')
        return v

class LeadUpdate(BaseModel):
    """Schema for updating a Lead"""
    lead_source: Optional[str] = Field(None, max_length=100)
    lead_status: Optional[LeadStatus] = None
    conversion_probability: Optional[int] = Field(None, ge=0, le=100)
    expected_close_date: Optional[date] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    interest_level: Optional[InterestLevel] = None
    inquiry_type: Optional[str] = Field(None, max_length=255)
    last_contacted_at: Optional[date] = None
    is_qualified: Optional[bool] = None
    disqualification_reason: Optional[str] = None
    referral_source: Optional[str] = None
    travel_interests: Optional[List[str]] = None
    preferred_travel_date: Optional[date] = None
    number_of_travelers: Optional[int] = Field(None, ge=1)
    special_requirements: Optional[str] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None
    campaign_id: Optional[str] = Field(None, max_length=255)
    score: Optional[int] = Field(None, ge=0, le=100)
    lead_owner_id: Optional[uuid.UUID] = None

class LeadResponse(LeadBase):
    """Schema for Lead response"""
    id: int
    actor_id: int
    lead_owner_id: Optional[uuid.UUID] = None
    converted_date: Optional[datetime] = None
    converted_contact_id: Optional[int] = None
    converted_account_id: Optional[int] = None
    converted_opportunity_id: Optional[int] = None
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

    class Config:
        from_attributes = True

class LeadConvert(BaseModel):
    """Schema for converting a lead"""
    create_contact: bool = True
    create_account: bool = True
    create_opportunity: bool = False
    account_name: Optional[str] = Field(None, max_length=200)
    opportunity_name: Optional[str] = Field(None, max_length=200)
    opportunity_amount: Optional[float] = Field(None, ge=0)
    opportunity_close_date: Optional[date] = None

class LeadListFilter(BaseModel):
    """Schema for filtering lead list"""
    lead_status: Optional[List[LeadStatus]] = None
    interest_level: Optional[List[InterestLevel]] = None
    lead_owner_id: Optional[uuid.UUID] = None
    is_qualified: Optional[bool] = None
    min_score: Optional[int] = Field(None, ge=0, le=100)
    max_score: Optional[int] = Field(None, ge=0, le=100)
    min_value: Optional[float] = Field(None, ge=0)
    max_value: Optional[float] = Field(None, ge=0)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = None  # Search in name, email, phone
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|score|estimated_value|expected_close_date)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class LeadBulkAction(BaseModel):
    """Schema for bulk actions on leads"""
    lead_ids: List[int]
    action: str = Field(..., pattern="^(assign|update_status|delete|score)$")
    lead_owner_id: Optional[uuid.UUID] = None  # For assign action
    lead_status: Optional[LeadStatus] = None  # For update_status action
    score_adjustment: Optional[int] = Field(None, ge=-100, le=100)  # For score action
