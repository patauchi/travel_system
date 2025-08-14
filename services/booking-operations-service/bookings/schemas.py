"""
Bookings module schemas
Contains Pydantic schemas for booking data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from common.enums import BookingOverallStatus, BookingLineStatus, RiskLevel


# ============================================
# BOOKING LINE SCHEMAS
# ============================================

class BookingLineBase(BaseModel):
    """Base schema for Booking Line"""
    order_line_id: int = Field(..., description="Order line ID")
    handled_by: Optional[int] = Field(None, description="User ID handling this booking")
    booking_method: Optional[str] = Field(None, max_length=50, description="Booking method")
    booking_platform: Optional[str] = Field(None, max_length=100, description="Booking platform")
    supplier_confirmation_code: Optional[str] = Field(None, max_length=100, description="Supplier confirmation code")
    supplier_booking_reference: Optional[str] = Field(None, max_length=100, description="Supplier booking reference")
    confirmed_with: Optional[str] = Field(None, max_length=100, description="Contact person at supplier")
    service_confirmed_start: Optional[datetime] = Field(None, description="Confirmed start time")
    service_confirmed_end: Optional[datetime] = Field(None, description="Confirmed end time")
    pickup_confirmation: Optional[str] = Field(None, max_length=255, description="Pickup confirmation details")
    service_specifics: Optional[Dict[str, Any]] = Field(None, description="Service specific details")
    voucher_number: Optional[str] = Field(None, max_length=100, description="Voucher number")
    voucher_url: Optional[str] = Field(None, max_length=500, description="Voucher URL")
    ticket_number: Optional[str] = Field(None, max_length=100, description="Ticket number")
    booking_documents: Optional[List[str]] = Field(None, description="Booking documents")
    cancellation_reason: Optional[str] = Field(None, max_length=255, description="Cancellation reason")
    cancellation_code: Optional[str] = Field(None, max_length=50, description="Supplier cancellation code")
    cancellation_fee: Optional[Decimal] = Field(None, ge=0, description="Cancellation fee")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Risk level")
    booking_notes: Optional[str] = Field(None, description="Booking notes")
    supplier_notes: Optional[str] = Field(None, description="Supplier notes")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('booking_method')
    def validate_booking_method(cls, v):
        if v is not None:
            valid_methods = ['api', 'email', 'phone', 'portal', 'manual']
            if v.lower() not in valid_methods:
                raise ValueError(f'Booking method must be one of: {", ".join(valid_methods)}')
            return v.lower()
        return v


class BookingLineCreate(BookingLineBase):
    """Schema for creating a booking line"""
    pass


class BookingLineUpdate(BaseModel):
    """Schema for updating a booking line"""
    handled_by: Optional[int] = Field(None, description="User ID handling this booking")
    booking_status: Optional[BookingLineStatus] = Field(None, description="Booking status")
    supplier_confirmation_code: Optional[str] = Field(None, max_length=100, description="Supplier confirmation code")
    supplier_booking_reference: Optional[str] = Field(None, max_length=100, description="Supplier booking reference")
    confirmed_with: Optional[str] = Field(None, max_length=100, description="Contact person at supplier")
    service_confirmed_start: Optional[datetime] = Field(None, description="Confirmed start time")
    service_confirmed_end: Optional[datetime] = Field(None, description="Confirmed end time")
    pickup_confirmation: Optional[str] = Field(None, max_length=255, description="Pickup confirmation details")
    service_specifics: Optional[Dict[str, Any]] = Field(None, description="Service specific details")
    voucher_number: Optional[str] = Field(None, max_length=100, description="Voucher number")
    voucher_url: Optional[str] = Field(None, max_length=500, description="Voucher URL")
    ticket_number: Optional[str] = Field(None, max_length=100, description="Ticket number")
    booking_documents: Optional[List[str]] = Field(None, description="Booking documents")
    cancellation_reason: Optional[str] = Field(None, max_length=255, description="Cancellation reason")
    cancellation_code: Optional[str] = Field(None, max_length=50, description="Supplier cancellation code")
    cancellation_fee: Optional[Decimal] = Field(None, ge=0, description="Cancellation fee")
    risk_level: Optional[RiskLevel] = Field(None, description="Risk level")
    booking_notes: Optional[str] = Field(None, description="Booking notes")
    supplier_notes: Optional[str] = Field(None, description="Supplier notes")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BookingLineResponse(BookingLineBase):
    """Schema for booking line response"""
    id: int = Field(..., description="Booking line ID")
    booking_id: int = Field(..., description="Booking ID")
    booking_status: BookingLineStatus = Field(..., description="Booking status")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    booking_requested_at: Optional[datetime] = Field(None, description="Booking request timestamp")
    confirmation_attempts: int = Field(..., description="Number of confirmation attempts")
    last_confirmation_attempt: Optional[datetime] = Field(None, description="Last confirmation attempt")
    last_modified_at: Optional[datetime] = Field(None, description="Last modification timestamp")
    modification_count: int = Field(..., description="Number of modifications")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    cancellation_confirmed: bool = Field(..., description="Cancellation confirmed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# BOOKING PASSENGER SCHEMAS
# ============================================

class BookingPassengerBase(BaseModel):
    """Base schema for Booking Passenger"""
    passenger_id: int = Field(..., description="Passenger ID")
    booking_line_id: int = Field(..., description="Booking line ID")
    account_id: int = Field(..., description="Account ID")
    order_id: int = Field(..., description="Order ID")
    order_line_id: int = Field(..., description="Order line ID")
    passenger_type: str = Field("adult", description="Passenger type")
    age_at_travel: Optional[int] = Field(None, ge=0, description="Age at travel")
    is_lead_passenger: bool = Field(False, description="Is lead passenger")
    passenger_price: Decimal = Field(0, ge=0, description="Passenger price")
    passenger_cost: Decimal = Field(0, ge=0, description="Passenger cost")
    commission_amount: Decimal = Field(0, ge=0, description="Commission amount")
    price_type: Optional[str] = Field(None, max_length=50, description="Price type")
    price_notes: Optional[str] = Field(None, description="Price notes")
    confirmation_reference: Optional[str] = Field(None, max_length=100, description="Confirmation reference")
    check_in_status: str = Field("pending", description="Check-in status")
    checked_in_by: Optional[str] = Field(None, max_length=100, description="Checked in by")
    documents_required: bool = Field(False, description="Documents required")
    documents_verified: bool = Field(False, description="Documents verified")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('passenger_type')
    def validate_passenger_type(cls, v):
        valid_types = ['adult', 'child', 'infant', 'student', 'senior']
        if v.lower() not in valid_types:
            raise ValueError(f'Passenger type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('price_type')
    def validate_price_type(cls, v):
        if v is not None:
            valid_types = ['per_person', 'shared', 'free', 'supplement']
            if v.lower() not in valid_types:
                raise ValueError(f'Price type must be one of: {", ".join(valid_types)}')
            return v.lower()
        return v

    @validator('check_in_status')
    def validate_check_in_status(cls, v):
        valid_statuses = ['not_required', 'pending', 'checked_in', 'no_show', 'late', 'cancelled']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Check-in status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


class BookingPassengerCreate(BookingPassengerBase):
    """Schema for creating a booking passenger"""
    pass


class BookingPassengerUpdate(BaseModel):
    """Schema for updating a booking passenger"""
    passenger_type: Optional[str] = Field(None, description="Passenger type")
    age_at_travel: Optional[int] = Field(None, ge=0, description="Age at travel")
    is_lead_passenger: Optional[bool] = Field(None, description="Is lead passenger")
    passenger_price: Optional[Decimal] = Field(None, ge=0, description="Passenger price")
    passenger_cost: Optional[Decimal] = Field(None, ge=0, description="Passenger cost")
    commission_amount: Optional[Decimal] = Field(None, ge=0, description="Commission amount")
    price_type: Optional[str] = Field(None, max_length=50, description="Price type")
    price_notes: Optional[str] = Field(None, description="Price notes")
    confirmation_status: Optional[BookingLineStatus] = Field(None, description="Confirmation status")
    confirmation_reference: Optional[str] = Field(None, max_length=100, description="Confirmation reference")
    check_in_status: Optional[str] = Field(None, description="Check-in status")
    checked_in_by: Optional[str] = Field(None, max_length=100, description="Checked in by")
    documents_required: Optional[bool] = Field(None, description="Documents required")
    documents_verified: Optional[bool] = Field(None, description="Documents verified")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BookingPassengerResponse(BookingPassengerBase):
    """Schema for booking passenger response"""
    id: int = Field(..., description="Booking passenger ID")
    booking_id: int = Field(..., description="Booking ID")
    confirmation_status: BookingLineStatus = Field(..., description="Confirmation status")
    confirmed_at: Optional[datetime] = Field(None, description="Confirmation timestamp")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in timestamp")
    documents_verified_at: Optional[datetime] = Field(None, description="Documents verification timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# BOOKING SCHEMAS
# ============================================

class BookingBase(BaseModel):
    """Base schema for Booking"""
    order_id: int = Field(..., description="Order ID")
    booking_number: str = Field(..., min_length=1, max_length=50, description="Booking number")
    external_reference: Optional[str] = Field(None, max_length=100, description="External reference")
    travel_start_date: Optional[date] = Field(None, description="Travel start date")
    travel_end_date: Optional[date] = Field(None, description="Travel end date")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    emergency_contacts: Optional[str] = Field(None, description="Emergency contacts")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('currency')
    def validate_currency(cls, v):
        return v.upper()

    @validator('travel_end_date')
    def validate_travel_dates(cls, v, values):
        start_date = values.get('travel_start_date')
        if v is not None and start_date is not None and v < start_date:
            raise ValueError('Travel end date must be after or equal to start date')
        return v


class BookingCreate(BookingBase):
    """Schema for creating a new booking"""
    booking_lines: List[BookingLineCreate] = Field(..., min_items=1, description="Booking lines")
    booking_passengers: List[BookingPassengerCreate] = Field(..., min_items=1, description="Booking passengers")


class BookingUpdate(BaseModel):
    """Schema for updating a booking"""
    external_reference: Optional[str] = Field(None, max_length=100, description="External reference")
    overall_status: Optional[BookingOverallStatus] = Field(None, description="Overall status")
    travel_start_date: Optional[date] = Field(None, description="Travel start date")
    travel_end_date: Optional[date] = Field(None, description="Travel end date")
    special_requirements: Optional[str] = Field(None, description="Special requirements")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    emergency_contacts: Optional[str] = Field(None, description="Emergency contacts")
    documents_complete: Optional[bool] = Field(None, description="Documents complete")
    confirmation_emails_sent: Optional[Dict[str, Any]] = Field(None, description="Confirmation emails sent")
    reminder_schedule: Optional[Dict[str, Any]] = Field(None, description="Reminder schedule")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('travel_end_date')
    def validate_travel_dates(cls, v, values):
        start_date = values.get('travel_start_date')
        if v is not None and start_date is not None and v < start_date:
            raise ValueError('Travel end date must be after or equal to start date')
        return v


class BookingResponse(BookingBase):
    """Schema for Booking response"""
    id: int = Field(..., description="Booking ID")
    overall_status: BookingOverallStatus = Field(..., description="Overall status")
    total_services: int = Field(..., description="Total services")
    confirmed_services: int = Field(..., description="Confirmed services")
    cancelled_services: int = Field(..., description="Cancelled services")
    pending_services: int = Field(..., description="Pending services")
    total_passengers: int = Field(..., description="Total passengers")
    adults_count: int = Field(..., description="Adults count")
    children_count: int = Field(..., description="Children count")
    infants_count: int = Field(..., description="Infants count")
    passenger_manifest: Optional[Dict[str, Any]] = Field(None, description="Passenger manifest")
    travel_documents: Optional[Dict[str, Any]] = Field(None, description="Travel documents")
    documents_complete: bool = Field(..., description="Documents complete")
    documents_verified_at: Optional[datetime] = Field(None, description="Documents verification timestamp")
    confirmation_emails_sent: Optional[Dict[str, Any]] = Field(None, description="Confirmation emails sent")
    reminder_schedule: Optional[Dict[str, Any]] = Field(None, description="Reminder schedule")
    last_customer_notification: Optional[datetime] = Field(None, description="Last customer notification")
    total_amount: Decimal = Field(..., description="Total amount")
    total_paid: Decimal = Field(..., description="Total paid")
    total_commission: Decimal = Field(..., description="Total commission")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    # Related data
    booking_lines: Optional[List[BookingLineResponse]] = Field(None, description="Booking lines")
    booking_passengers: Optional[List[BookingPassengerResponse]] = Field(None, description="Booking passengers")

    # Computed fields
    progress_percentage: Optional[float] = Field(None, description="Progress percentage")
    is_fully_confirmed: Optional[bool] = Field(None, description="Is fully confirmed")
    has_cancelled_services: Optional[bool] = Field(None, description="Has cancelled services")

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    """Schema for Booking list response"""
    items: List[BookingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class BookingSummary(BaseModel):
    """Schema for booking summary statistics"""
    total_bookings: int
    bookings_by_status: Dict[str, int]
    total_passengers: int
    total_amount: Decimal
    upcoming_bookings: int
    completed_bookings: int
    cancelled_bookings: int

    model_config = ConfigDict(from_attributes=True)


class BookingSearch(BaseModel):
    """Schema for booking search results"""
    id: int
    booking_number: str
    overall_status: str
    travel_start_date: Optional[date]
    total_passengers: int
    total_amount: Decimal
    currency: str

    model_config = ConfigDict(from_attributes=True)


class BookingSearchResponse(BaseModel):
    """Schema for booking search response"""
    results: List[BookingSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# BOOKING OPERATIONS SCHEMAS
# ============================================

class BookingConfirmationRequest(BaseModel):
    """Schema for booking confirmation request"""
    booking_line_id: int = Field(..., description="Booking line ID")
    supplier_confirmation_code: str = Field(..., description="Supplier confirmation code")
    supplier_booking_reference: Optional[str] = Field(None, description="Supplier booking reference")
    confirmed_with: Optional[str] = Field(None, description="Contact person")
    service_confirmed_start: Optional[datetime] = Field(None, description="Confirmed start time")
    service_confirmed_end: Optional[datetime] = Field(None, description="Confirmed end time")
    voucher_number: Optional[str] = Field(None, description="Voucher number")
    voucher_url: Optional[str] = Field(None, description="Voucher URL")
    supplier_response: Optional[Dict[str, Any]] = Field(None, description="Supplier response")


class BookingCancellationRequest(BaseModel):
    """Schema for booking cancellation request"""
    booking_line_id: int = Field(..., description="Booking line ID")
    cancellation_reason: str = Field(..., description="Cancellation reason")
    cancellation_code: Optional[str] = Field(None, description="Supplier cancellation code")
    cancellation_fee: Optional[Decimal] = Field(None, ge=0, description="Cancellation fee")
    refund_amount: Optional[Decimal] = Field(None, ge=0, description="Refund amount")


class BookingManifestResponse(BaseModel):
    """Schema for booking manifest response"""
    booking_id: int
    booking_number: str
    travel_date: date
    passengers: List[Dict[str, Any]]
    services: List[Dict[str, Any]]
    emergency_contacts: Optional[str]
    special_requirements: Optional[str]
    dietary_restrictions: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)


class BookingStatusUpdate(BaseModel):
    """Schema for booking status update"""
    booking_id: int = Field(..., description="Booking ID")
    new_status: BookingOverallStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    updated_by: Optional[int] = Field(None, description="User ID who updated")
