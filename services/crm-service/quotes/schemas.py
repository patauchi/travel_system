"""
Quotes Schemas for CRM Service
Pydantic models for quote request/response validation
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, validator
import uuid

from core.enums import QuoteStatus, Currency, QuoteLineType

# ============================================
# QUOTE SCHEMAS
# ============================================

class QuoteBase(BaseModel):
    """Base schema for Quote"""
    name: str = Field(..., max_length=200)
    status: QuoteStatus = QuoteStatus.draft
    is_primary: bool = False
    quote_date: date
    expiration_date: date
    currency: Currency = Currency.usd
    payment_terms: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None

    @validator('expiration_date')
    def validate_expiration_after_quote_date(cls, v, values):
        quote_date = values.get('quote_date')
        if v and quote_date and v <= quote_date:
            raise ValueError('Expiration date must be after quote date')
        return v

class QuoteCreate(QuoteBase):
    """Schema for creating a Quote"""
    opportunity_id: int
    quote_number: Optional[str] = None  # Auto-generated if not provided

class QuoteUpdate(BaseModel):
    """Schema for updating a Quote"""
    name: Optional[str] = Field(None, max_length=200)
    status: Optional[QuoteStatus] = None
    is_primary: Optional[bool] = None
    expiration_date: Optional[date] = None
    currency: Optional[Currency] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None
    accepted_date: Optional[date] = None

class QuoteResponse(QuoteBase):
    """Schema for Quote response"""
    id: int
    opportunity_id: int
    quote_number: str
    accepted_date: Optional[date] = None
    subtotal: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    total_amount: float = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    # Related entity information
    opportunity_name: Optional[str] = None
    line_count: Optional[int] = None

    class Config:
        from_attributes = True

# ============================================
# QUOTE LINE SCHEMAS
# ============================================

class QuoteLineBase(BaseModel):
    """Base schema for Quote Line"""
    line_number: int
    type: QuoteLineType
    description: str
    quantity: int = Field(1, ge=1)
    unit_price: float = Field(..., ge=0)
    discount_percent: float = Field(0, ge=0, le=100)
    tax_rate: float = Field(0, ge=0, le=100)
    service_date: Optional[date] = None
    service_end_date: Optional[date] = None
    notes: Optional[str] = None
    is_optional: bool = False
    is_included: bool = True

    @validator('service_end_date')
    def validate_service_end_after_start(cls, v, values):
        service_date = values.get('service_date')
        if v and service_date and v <= service_date:
            raise ValueError('Service end date must be after service date')
        return v

class QuoteLineCreate(QuoteLineBase):
    """Schema for creating a Quote Line"""
    quote_id: int

class QuoteLineUpdate(BaseModel):
    """Schema for updating a Quote Line"""
    line_number: Optional[int] = None
    type: Optional[QuoteLineType] = None
    description: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    unit_price: Optional[float] = Field(None, ge=0)
    discount_percent: Optional[float] = Field(None, ge=0, le=100)
    tax_rate: Optional[float] = Field(None, ge=0, le=100)
    service_date: Optional[date] = None
    service_end_date: Optional[date] = None
    notes: Optional[str] = None
    is_optional: Optional[bool] = None
    is_included: Optional[bool] = None

class QuoteLineResponse(QuoteLineBase):
    """Schema for Quote Line response"""
    id: int
    quote_id: int
    discount_amount: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    margin_amount: Optional[float] = None
    margin_percent: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# FILTERING AND BULK OPERATIONS
# ============================================

class QuoteListFilter(BaseModel):
    """Schema for filtering quote list"""
    status: Optional[List[QuoteStatus]] = None
    opportunity_id: Optional[int] = None
    currency: Optional[List[Currency]] = None
    is_primary: Optional[bool] = None
    quote_date_from: Optional[date] = None
    quote_date_to: Optional[date] = None
    expiration_date_from: Optional[date] = None
    expiration_date_to: Optional[date] = None
    min_amount: Optional[float] = Field(None, ge=0)
    max_amount: Optional[float] = Field(None, ge=0)
    search: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class QuoteBulkAction(BaseModel):
    """Schema for bulk actions on quotes"""
    quote_ids: List[int]
    action: str = Field(..., pattern="^(update_status|delete|send|accept|expire)$")
    status: Optional[QuoteStatus] = None

class QuoteAccept(BaseModel):
    """Schema for accepting a quote"""
    accepted_date: Optional[date] = None
    notes: Optional[str] = None
    create_booking: bool = False

class QuoteStats(BaseModel):
    """Schema for quote statistics"""
    total_quotes: int
    quotes_by_status: dict
    total_value: float
    accepted_quotes: int
    acceptance_rate: float
    average_quote_value: float
    expired_quotes: int

class QuoteSend(BaseModel):
    """Schema for sending a quote"""
    recipient_email: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    send_copy_to_owner: bool = True
