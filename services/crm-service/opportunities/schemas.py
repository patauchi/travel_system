"""
Opportunities Schemas for CRM Service
Pydantic models for opportunity request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
import uuid

from core.enums import OpportunityStage, TravelType, BudgetLevel

# ============================================
# OPPORTUNITY SCHEMAS
# ============================================

class OpportunityBase(BaseModel):
    """Base schema for Opportunity"""
    name: str = Field(..., max_length=200)
    stage: OpportunityStage = OpportunityStage.prospecting
    probability: int = Field(25, ge=0, le=100)
    amount: Optional[float] = Field(None, ge=0)
    expected_close_date: Optional[date] = None

    # Travel Information
    travel_type: Optional[TravelType] = None
    destinations: Optional[List[str]] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    number_of_adults: Optional[int] = Field(None, ge=1)
    number_of_children: Optional[int] = Field(None, ge=0)

    # Travel details
    room_configuration: Optional[List[str]] = None
    budget_level: Optional[BudgetLevel] = None
    special_requests: Optional[str] = None

    # Competition and next steps
    competitors: Optional[List[str]] = None
    next_steps: Optional[str] = None

    @validator('return_date')
    def validate_return_after_departure(cls, v, values):
        departure = values.get('departure_date')
        if v and departure and v <= departure:
            raise ValueError('Return date must be after departure date')
        return v

    @validator('expected_close_date')
    def validate_close_date_future(cls, v):
        if v and v < date.today():
            raise ValueError('Expected close date cannot be in the past')
        return v

class OpportunityCreate(OpportunityBase):
    """Schema for creating an Opportunity"""
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    campaign_id: Optional[int] = None

    @validator('account_id', 'contact_id')
    def validate_account_or_contact(cls, v, values):
        # At least one of account_id or contact_id should be provided
        if not v and not values.get('account_id') and not values.get('contact_id'):
            raise ValueError('Either account_id or contact_id must be provided')
        return v

class OpportunityUpdate(BaseModel):
    """Schema for updating an Opportunity"""
    name: Optional[str] = Field(None, max_length=200)
    stage: Optional[OpportunityStage] = None
    probability: Optional[int] = Field(None, ge=0, le=100)
    amount: Optional[float] = Field(None, ge=0)
    expected_close_date: Optional[date] = None
    actual_close_date: Optional[date] = None

    # Travel Information
    travel_type: Optional[TravelType] = None
    destinations: Optional[List[str]] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    number_of_adults: Optional[int] = Field(None, ge=1)
    number_of_children: Optional[int] = Field(None, ge=0)

    # Travel details
    room_configuration: Optional[List[str]] = None
    budget_level: Optional[BudgetLevel] = None
    special_requests: Optional[str] = None

    # Status
    is_closed: Optional[bool] = None
    close_reason: Optional[str] = Field(None, max_length=255)
    loss_reason: Optional[str] = None

    # Competition and next steps
    competitors: Optional[List[str]] = None
    next_steps: Optional[str] = None

    # Associations
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    campaign_id: Optional[int] = None

class OpportunityResponse(OpportunityBase):
    """Schema for Opportunity response"""
    id: int
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    owner_id: uuid.UUID
    campaign_id: Optional[int] = None

    # Status
    actual_close_date: Optional[date] = None
    is_closed: bool = False
    close_reason: Optional[str] = None
    loss_reason: Optional[str] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    # Related entity names
    account_name: Optional[str] = None
    contact_name: Optional[str] = None
    owner_name: Optional[str] = None

    # Quote information
    total_quotes: Optional[int] = None
    primary_quote_amount: Optional[float] = None

    class Config:
        from_attributes = True

class OpportunityListFilter(BaseModel):
    """Schema for filtering opportunity list"""
    stage: Optional[List[OpportunityStage]] = None
    travel_type: Optional[List[TravelType]] = None
    budget_level: Optional[List[BudgetLevel]] = None
    owner_id: Optional[uuid.UUID] = None
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    campaign_id: Optional[int] = None

    # Amount filters
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    min_probability: Optional[int] = Field(None, ge=0, le=100)
    max_probability: Optional[int] = Field(None, ge=0, le=100)

    # Date filters
    expected_close_from: Optional[date] = None
    expected_close_to: Optional[date] = None
    departure_from: Optional[date] = None
    departure_to: Optional[date] = None
    created_from: Optional[date] = None
    created_to: Optional[date] = None

    # Status filters
    is_closed: Optional[bool] = None
    has_quotes: Optional[bool] = None

    # Search
    search: Optional[str] = None  # Search in name, account name, contact name

    # Pagination and sorting
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", pattern="^(created_at|updated_at|name|amount|expected_close_date|probability|stage)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class OpportunityBulkAction(BaseModel):
    """Schema for bulk actions on opportunities"""
    opportunity_ids: List[int]
    action: str = Field(..., pattern="^(update_stage|assign_owner|delete|update_probability|close_won|close_lost)$")

    # Action-specific fields
    stage: Optional[OpportunityStage] = None  # For update_stage action
    owner_id: Optional[uuid.UUID] = None  # For assign_owner action
    probability: Optional[int] = Field(None, ge=0, le=100)  # For update_probability action
    close_reason: Optional[str] = Field(None, max_length=255)  # For close_won action
    loss_reason: Optional[str] = None  # For close_lost action

class OpportunityStats(BaseModel):
    """Schema for opportunity statistics"""
    total_opportunities: int
    open_opportunities: int
    closed_won: int
    closed_lost: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    average_deal_size: float
    win_rate: float
    opportunities_by_stage: dict
    opportunities_by_travel_type: dict
    monthly_forecast: dict

class OpportunityConvert(BaseModel):
    """Schema for converting opportunity to booking/sale"""
    close_as_won: bool = True
    close_reason: Optional[str] = Field(None, max_length=255)
    actual_close_date: Optional[date] = None
    final_amount: Optional[float] = Field(None, ge=0)
    create_booking: bool = False
    booking_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class OpportunityForecast(BaseModel):
    """Schema for opportunity forecasting"""
    month: str  # YYYY-MM format
    total_opportunities: int
    total_value: float
    weighted_value: float
    expected_closes: int
    confidence_level: str  # high, medium, low
