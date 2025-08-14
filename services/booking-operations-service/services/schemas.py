"""
Services module schemas
Contains Pydantic schemas for Service data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from common.enums import ServiceType, OperationModel, PassengerType


class ServiceBase(BaseModel):
    """Base schema for Service"""
    supplier_id: int = Field(..., description="Supplier ID")
    cancellation_policy_id: Optional[int] = Field(None, description="Cancellation policy ID")
    code: str = Field(..., min_length=1, max_length=50, description="Service code")
    name: str = Field(..., min_length=1, max_length=255, description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    service_type: ServiceType = Field(..., description="Type of service")
    operation_model: OperationModel = Field(OperationModel.NO_DEFINED, description="Operation model")
    allowed_destinations: Optional[List[int]] = Field(None, description="Allowed destination IDs")
    duration_hours: Optional[Decimal] = Field(None, ge=0, description="Duration in hours")
    min_participants: Optional[int] = Field(None, ge=1, description="Minimum participants")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum participants")
    advance_booking_hours: Optional[int] = Field(None, ge=0, description="Advance booking required (hours)")
    cutoff_hours: Optional[int] = Field(None, ge=0, description="Booking cutoff (hours)")
    is_active: bool = Field(True, description="Service active status")
    is_featured: bool = Field(False, description="Featured service status")
    service_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ServiceCreate(ServiceBase):
    """Schema for creating a new Service"""
    pass


class ServiceUpdate(BaseModel):
    """Schema for updating a Service"""
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    cancellation_policy_id: Optional[int] = Field(None, description="Cancellation policy ID")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Service code")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Service name")
    description: Optional[str] = Field(None, description="Service description")
    service_type: Optional[ServiceType] = Field(None, description="Type of service")
    operation_model: Optional[OperationModel] = Field(None, description="Operation model")
    allowed_destinations: Optional[List[int]] = Field(None, description="Allowed destination IDs")
    duration_hours: Optional[Decimal] = Field(None, ge=0, description="Duration in hours")
    min_participants: Optional[int] = Field(None, ge=1, description="Minimum participants")
    max_participants: Optional[int] = Field(None, ge=1, description="Maximum participants")
    advance_booking_hours: Optional[int] = Field(None, ge=0, description="Advance booking required (hours)")
    cutoff_hours: Optional[int] = Field(None, ge=0, description="Booking cutoff (hours)")
    is_active: Optional[bool] = Field(None, description="Service active status")
    is_featured: Optional[bool] = Field(None, description="Featured service status")
    service_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SupplierBasic(BaseModel):
    """Basic supplier information for service response"""
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class ServiceResponse(ServiceBase):
    """Schema for Service response"""
    id: int = Field(..., description="Service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    supplier: Optional[SupplierBasic] = Field(None, description="Supplier information")

    model_config = ConfigDict(from_attributes=True)


class ServiceListResponse(BaseModel):
    """Schema for Service list response"""
    items: List[ServiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class ServiceAvailability(BaseModel):
    """Schema for service availability"""
    service_id: int
    date: str  # YYYY-MM-DD format
    available_capacity: int
    booked_capacity: int
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceSearch(BaseModel):
    """Schema for service search results"""
    id: int
    code: str
    name: str
    service_type: str
    supplier_name: str
    duration_hours: Optional[Decimal]
    min_participants: Optional[int]
    max_participants: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class ServiceSearchResponse(BaseModel):
    """Schema for service search response"""
    results: List[ServiceSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SERVICE DAILY CAPACITY SCHEMAS
# ============================================

class ServiceDailyCapacityBase(BaseModel):
    """Base schema for Service Daily Capacity"""
    service_id: int = Field(..., description="Service ID")
    service_date: date = Field(..., description="Service date")
    total_capacity: int = Field(0, ge=0, description="Total capacity")
    booked_capacity: int = Field(0, ge=0, description="Booked capacity")
    blocked_capacity: int = Field(0, ge=0, description="Blocked capacity")
    available_capacity: int = Field(0, ge=0, description="Available capacity")
    time_slot: Optional[str] = Field(None, max_length=20, description="Time slot")
    rate_override_id: Optional[int] = Field(None, description="Rate override ID")
    price_override: Optional[Decimal] = Field(None, ge=0, description="Price override")
    is_available: bool = Field(True, description="Is available")
    is_blocked: bool = Field(False, description="Is blocked")
    block_reason: Optional[str] = Field(None, max_length=255, description="Block reason")
    notes: Optional[str] = Field(None, description="Notes")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ServiceDailyCapacityCreate(ServiceDailyCapacityBase):
    """Schema for creating a Service Daily Capacity"""
    pass


class ServiceDailyCapacityUpdate(BaseModel):
    """Schema for updating a Service Daily Capacity"""
    total_capacity: Optional[int] = Field(None, ge=0, description="Total capacity")
    booked_capacity: Optional[int] = Field(None, ge=0, description="Booked capacity")
    blocked_capacity: Optional[int] = Field(None, ge=0, description="Blocked capacity")
    available_capacity: Optional[int] = Field(None, ge=0, description="Available capacity")
    time_slot: Optional[str] = Field(None, max_length=20, description="Time slot")
    rate_override_id: Optional[int] = Field(None, description="Rate override ID")
    price_override: Optional[Decimal] = Field(None, ge=0, description="Price override")
    is_available: Optional[bool] = Field(None, description="Is available")
    is_blocked: Optional[bool] = Field(None, description="Is blocked")
    block_reason: Optional[str] = Field(None, max_length=255, description="Block reason")
    notes: Optional[str] = Field(None, description="Notes")
    operational_notes: Optional[str] = Field(None, description="Operational notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ServiceDailyCapacityResponse(ServiceDailyCapacityBase):
    """Schema for Service Daily Capacity response"""
    id: int = Field(..., description="Service daily capacity ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SERVICE PARTICIPANT SCHEMAS
# ============================================

class ServiceParticipantBase(BaseModel):
    """Base schema for Service Participant"""
    service_id: int = Field(..., description="Service ID")
    booking_line_id: int = Field(..., description="Booking line ID")
    passenger_id: int = Field(..., description="Passenger ID")
    service_date: date = Field(..., description="Service date")
    time_slot: Optional[str] = Field(None, max_length=20, description="Time slot")
    participation_status: str = Field("confirmed", description="Participation status")
    check_in_status: str = Field("pending", description="Check-in status")
    passenger_type: PassengerType = Field(PassengerType.ADULT, description="Passenger type")
    special_requirements: Optional[Dict[str, Any]] = Field(None, description="Special requirements")
    rate_applied_id: Optional[int] = Field(None, description="Applied rate ID")
    price_paid: Optional[Decimal] = Field(None, ge=0, description="Price paid")

    @validator('participation_status')
    def validate_participation_status(cls, v):
        valid_statuses = ['confirmed', 'cancelled', 'no_show', 'completed']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Participation status must be one of: {", ".join(valid_statuses)}')
        return v.lower()

    @validator('check_in_status')
    def validate_check_in_status(cls, v):
        valid_statuses = ['pending', 'checked_in', 'no_show']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Check-in status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


class ServiceParticipantCreate(ServiceParticipantBase):
    """Schema for creating a Service Participant"""
    pass


class ServiceParticipantUpdate(BaseModel):
    """Schema for updating a Service Participant"""
    participation_status: Optional[str] = Field(None, description="Participation status")
    check_in_status: Optional[str] = Field(None, description="Check-in status")
    passenger_type: Optional[PassengerType] = Field(None, description="Passenger type")
    special_requirements: Optional[Dict[str, Any]] = Field(None, description="Special requirements")
    rate_applied_id: Optional[int] = Field(None, description="Applied rate ID")
    price_paid: Optional[Decimal] = Field(None, ge=0, description="Price paid")

    @validator('participation_status')
    def validate_participation_status(cls, v):
        if v is not None:
            valid_statuses = ['confirmed', 'cancelled', 'no_show', 'completed']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Participation status must be one of: {", ".join(valid_statuses)}')
            return v.lower()
        return v

    @validator('check_in_status')
    def validate_check_in_status(cls, v):
        if v is not None:
            valid_statuses = ['pending', 'checked_in', 'no_show']
            if v.lower() not in valid_statuses:
                raise ValueError(f'Check-in status must be one of: {", ".join(valid_statuses)}')
            return v.lower()
        return v


class ServiceParticipantResponse(ServiceParticipantBase):
    """Schema for Service Participant response"""
    id: int = Field(..., description="Service participant ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    cancelled_at: Optional[datetime] = Field(None, description="Cancellation timestamp")
    checked_in_at: Optional[datetime] = Field(None, description="Check-in timestamp")

    model_config = ConfigDict(from_attributes=True)
