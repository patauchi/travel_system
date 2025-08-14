"""
Service Operations module schemas
Contains Pydantic schemas for ServiceOperation data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal

from common.enums import ServiceOperationStatus, OperationalAlert


# ============================================
# INCIDENT SCHEMAS
# ============================================

class IncidentBase(BaseModel):
    """Base schema for an incident"""
    type: str = Field(..., max_length=50, description="Incident type")
    severity: str = Field(..., max_length=20, description="Incident severity")
    description: str = Field(..., description="Incident description")
    action_taken: Optional[str] = Field(None, description="Action taken to resolve")
    reported_by: Optional[str] = Field(None, description="Who reported the incident")
    resolved: bool = Field(False, description="Is incident resolved")

    @validator('type')
    def validate_incident_type(cls, v):
        valid_types = ['medical', 'mechanical', 'weather', 'complaint', 'safety', 'documentation', 'other']
        if v.lower() not in valid_types:
            raise ValueError(f'Incident type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['minor', 'moderate', 'severe', 'critical']
        if v.lower() not in valid_severities:
            raise ValueError(f'Severity must be one of: {", ".join(valid_severities)}')
        return v.lower()


class IncidentCreate(IncidentBase):
    """Schema for creating an incident"""
    pass


class IncidentResponse(IncidentBase):
    """Schema for incident response"""
    time: datetime = Field(..., description="Incident timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# CHECK-IN SCHEMAS
# ============================================

class PassengerCheckIn(BaseModel):
    """Schema for passenger check-in"""
    passenger_id: int = Field(..., description="Passenger ID")
    checked_in_at: datetime = Field(..., description="Check-in timestamp")
    checked_by: str = Field(..., description="Who checked in the passenger")

    model_config = ConfigDict(from_attributes=True)


class PassengerCheckInRequest(BaseModel):
    """Schema for passenger check-in request"""
    passenger_id: int = Field(..., description="Passenger ID")
    checked_by: Optional[str] = Field(None, description="Who is checking in the passenger")


# ============================================
# PICKUP POINT SCHEMAS
# ============================================

class PickupPoint(BaseModel):
    """Schema for pickup point"""
    location: str = Field(..., description="Pickup location")
    scheduled_time: str = Field(..., description="Scheduled pickup time (HH:MM)")
    actual_time: Optional[str] = Field(None, description="Actual pickup time (HH:MM)")
    passengers_count: int = Field(0, ge=0, description="Number of passengers")
    notes: Optional[str] = Field(None, description="Pickup notes")

    @validator('scheduled_time', 'actual_time')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except:
                raise ValueError('Time must be in HH:MM format')
        return v


# ============================================
# COMMUNICATION LOG SCHEMAS
# ============================================

class CommunicationLog(BaseModel):
    """Schema for communication log entry"""
    time: datetime = Field(..., description="Communication timestamp")
    type: str = Field(..., description="Communication type")
    from_user: str = Field(..., description="Sender")
    to_user: str = Field(..., description="Recipient")
    message: str = Field(..., description="Message content")

    @validator('type')
    def validate_communication_type(cls, v):
        valid_types = ['phone', 'whatsapp', 'email', 'radio', 'sms', 'in_person', 'other']
        if v.lower() not in valid_types:
            raise ValueError(f'Communication type must be one of: {", ".join(valid_types)}')
        return v.lower()

    model_config = ConfigDict(from_attributes=True)


class CommunicationLogCreate(BaseModel):
    """Schema for creating communication log entry"""
    type: str = Field(..., description="Communication type")
    from_user: str = Field(..., description="Sender")
    to_user: str = Field(..., description="Recipient")
    message: str = Field(..., description="Message content")


# ============================================
# PASSENGER FEEDBACK SCHEMAS
# ============================================

class PassengerFeedback(BaseModel):
    """Schema for passenger feedback"""
    passenger_id: int = Field(..., description="Passenger ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comment: Optional[str] = Field(None, description="Feedback comment")
    submitted_at: datetime = Field(..., description="Submission timestamp")

    model_config = ConfigDict(from_attributes=True)


class PassengerFeedbackCreate(BaseModel):
    """Schema for creating passenger feedback"""
    passenger_id: int = Field(..., description="Passenger ID")
    rating: int = Field(..., ge=1, le=5, description="Rating (1-5)")
    comment: Optional[str] = Field(None, description="Feedback comment")


# ============================================
# OPERATING CONDITIONS SCHEMAS
# ============================================

class OperatingConditions(BaseModel):
    """Schema for operating conditions"""
    weather: Optional[str] = Field(None, description="Weather conditions")
    temperature: Optional[str] = Field(None, description="Temperature")
    visibility: Optional[str] = Field(None, description="Visibility conditions")
    sea_conditions: Optional[str] = Field(None, description="Sea conditions for boat tours")
    warnings: Optional[List[str]] = Field(None, description="Operational warnings")

    @validator('weather')
    def validate_weather(cls, v):
        if v is not None:
            valid_weather = ['sunny', 'cloudy', 'rainy', 'stormy', 'foggy', 'windy', 'snow']
            if v.lower() not in valid_weather:
                raise ValueError(f'Weather must be one of: {", ".join(valid_weather)}')
            return v.lower()
        return v

    @validator('visibility')
    def validate_visibility(cls, v):
        if v is not None:
            valid_visibility = ['excellent', 'good', 'fair', 'poor', 'very_poor']
            if v.lower() not in valid_visibility:
                raise ValueError(f'Visibility must be one of: {", ".join(valid_visibility)}')
            return v.lower()
        return v


# ============================================
# SERVICE OPERATION SCHEMAS
# ============================================

class ServiceOperationBase(BaseModel):
    """Base schema for Service Operation"""
    booking_line_id: int = Field(..., description="Booking line ID")
    booking_id: int = Field(..., description="Booking ID")
    order_id: int = Field(..., description="Order ID")
    operation_date: date = Field(..., description="Operation date")
    scheduled_start_time: Optional[time] = Field(None, description="Scheduled start time")
    scheduled_end_time: Optional[time] = Field(None, description="Scheduled end time")
    service_type: str = Field(..., max_length=50, description="Service type")
    service_name: str = Field(..., max_length=255, description="Service name")
    route_or_location: Optional[str] = Field(None, max_length=255, description="Route or location")
    passengers_expected: int = Field(0, ge=0, description="Expected passengers")
    actual_pickup_location: Optional[str] = Field(None, max_length=255, description="Actual pickup location")
    actual_dropoff_location: Optional[str] = Field(None, max_length=255, description="Actual dropoff location")
    service_quality: Optional[str] = Field(None, description="Service quality rating")
    quality_issues: Optional[List[str]] = Field(None, description="Quality issues")
    guide_notes: Optional[str] = Field(None, description="Guide notes")
    coordinator_notes: Optional[str] = Field(None, description="Coordinator notes")
    operating_conditions: Optional[OperatingConditions] = Field(None, description="Operating conditions")
    cash_collected: Decimal = Field(0, ge=0, description="Cash collected")
    tips_collected: Decimal = Field(0, ge=0, description="Tips collected")
    additional_sales: Decimal = Field(0, ge=0, description="Additional sales")
    requires_follow_up: bool = Field(False, description="Requires follow-up")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    manifest_number: Optional[str] = Field(None, max_length=50, description="Manifest number")
    manifest_url: Optional[str] = Field(None, max_length=500, description="Manifest URL")
    operation_documents: Optional[List[str]] = Field(None, description="Operation documents")
    pickup_points: Optional[List[PickupPoint]] = Field(None, description="Pickup points")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Operation tags")

    @validator('service_type')
    def validate_service_type(cls, v):
        valid_types = ['tour', 'transfer', 'flight', 'hotel', 'activity', 'transport', 'restaurant', 'ticket']
        if v.lower() not in valid_types:
            raise ValueError(f'Service type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('service_quality')
    def validate_service_quality(cls, v):
        if v is not None:
            valid_qualities = ['excellent', 'good', 'fair', 'poor']
            if v.lower() not in valid_qualities:
                raise ValueError(f'Service quality must be one of: {", ".join(valid_qualities)}')
            return v.lower()
        return v


class ServiceOperationCreate(ServiceOperationBase):
    """Schema for creating a new Service Operation"""
    pass


class ServiceOperationUpdate(BaseModel):
    """Schema for updating a Service Operation"""
    operation_status: Optional[ServiceOperationStatus] = Field(None, description="Operation status")
    scheduled_start_time: Optional[time] = Field(None, description="Scheduled start time")
    scheduled_end_time: Optional[time] = Field(None, description="Scheduled end time")
    actual_start_datetime: Optional[datetime] = Field(None, description="Actual start datetime")
    actual_end_datetime: Optional[datetime] = Field(None, description="Actual end datetime")
    service_name: Optional[str] = Field(None, max_length=255, description="Service name")
    route_or_location: Optional[str] = Field(None, max_length=255, description="Route or location")
    passengers_expected: Optional[int] = Field(None, ge=0, description="Expected passengers")
    actual_pickup_location: Optional[str] = Field(None, max_length=255, description="Actual pickup location")
    actual_dropoff_location: Optional[str] = Field(None, max_length=255, description="Actual dropoff location")
    service_quality: Optional[str] = Field(None, description="Service quality rating")
    quality_issues: Optional[List[str]] = Field(None, description="Quality issues")
    guide_notes: Optional[str] = Field(None, description="Guide notes")
    coordinator_notes: Optional[str] = Field(None, description="Coordinator notes")
    operating_conditions: Optional[OperatingConditions] = Field(None, description="Operating conditions")
    cash_collected: Optional[Decimal] = Field(None, ge=0, description="Cash collected")
    tips_collected: Optional[Decimal] = Field(None, ge=0, description="Tips collected")
    additional_sales: Optional[Decimal] = Field(None, ge=0, description="Additional sales")
    requires_follow_up: Optional[bool] = Field(None, description="Requires follow-up")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    manifest_number: Optional[str] = Field(None, max_length=50, description="Manifest number")
    manifest_url: Optional[str] = Field(None, max_length=500, description="Manifest URL")
    operation_documents: Optional[List[str]] = Field(None, description="Operation documents")
    pickup_points: Optional[List[PickupPoint]] = Field(None, description="Pickup points")
    completed_by: Optional[int] = Field(None, description="User ID who completed the operation")
    verified_by: Optional[int] = Field(None, description="User ID who verified the operation")
    is_verified: Optional[bool] = Field(None, description="Is operation verified")
    synced_to_accounting: Optional[bool] = Field(None, description="Synced to accounting")
    feedback_requested: Optional[bool] = Field(None, description="Feedback requested")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Operation tags")


class ServiceOperationResponse(ServiceOperationBase):
    """Schema for Service Operation response"""
    id: int = Field(..., description="Service operation ID")
    operation_status: ServiceOperationStatus = Field(..., description="Operation status")
    actual_start_datetime: Optional[datetime] = Field(None, description="Actual start datetime")
    actual_end_datetime: Optional[datetime] = Field(None, description="Actual end datetime")
    passengers_checked_in: int = Field(..., description="Passengers checked in")
    passengers_no_show: int = Field(..., description="Passengers no show")
    passengers_cancelled: int = Field(..., description="Passengers cancelled")
    check_in_details: Optional[List[PassengerCheckIn]] = Field(None, description="Check-in details")
    route_tracking: Optional[Dict[str, Any]] = Field(None, description="Route tracking")
    timing_checkpoints: Optional[List[Dict[str, Any]]] = Field(None, description="Timing checkpoints")
    has_incidents: bool = Field(..., description="Has incidents")
    incidents: Optional[List[IncidentResponse]] = Field(None, description="Incidents")
    financial_notes: Optional[Dict[str, Any]] = Field(None, description="Financial notes")
    passenger_feedback: Optional[List[PassengerFeedback]] = Field(None, description="Passenger feedback")
    communication_log: Optional[List[CommunicationLog]] = Field(None, description="Communication log")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    completed_by: Optional[int] = Field(None, description="User ID who completed")
    is_verified: bool = Field(..., description="Is operation verified")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    verified_by: Optional[int] = Field(None, description="User ID who verified")
    synced_to_accounting: bool = Field(..., description="Synced to accounting")
    feedback_requested: bool = Field(..., description="Feedback requested")
    feedback_requested_at: Optional[datetime] = Field(None, description="Feedback request timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    # Computed fields
    attendance_rate: Optional[float] = Field(None, description="Passenger attendance rate")
    total_financial_collection: Optional[Decimal] = Field(None, description="Total financial collection")
    average_rating: Optional[float] = Field(None, description="Average passenger rating")
    is_on_time: Optional[bool] = Field(None, description="Operation started on time")
    duration_minutes: Optional[int] = Field(None, description="Operation duration in minutes")
    unresolved_incidents_count: Optional[int] = Field(None, description="Number of unresolved incidents")

    model_config = ConfigDict(from_attributes=True)


class ServiceOperationListResponse(BaseModel):
    """Schema for Service Operation list response"""
    operations: List[ServiceOperationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# OPERATION MANAGEMENT SCHEMAS
# ============================================

class ServiceOperationStartRequest(BaseModel):
    """Schema for starting a service operation"""
    operation_id: int = Field(..., description="Operation ID")
    actual_start_datetime: datetime = Field(..., description="Actual start datetime")
    actual_pickup_location: Optional[str] = Field(None, description="Actual pickup location")
    operating_conditions: Optional[OperatingConditions] = Field(None, description="Operating conditions")
    notes: Optional[str] = Field(None, description="Start notes")


class ServiceOperationCompleteRequest(BaseModel):
    """Schema for completing a service operation"""
    operation_id: int = Field(..., description="Operation ID")
    actual_end_datetime: datetime = Field(..., description="Actual end datetime")
    actual_dropoff_location: Optional[str] = Field(None, description="Actual dropoff location")
    service_quality: str = Field(..., description="Service quality rating")
    quality_issues: Optional[List[str]] = Field(None, description="Quality issues")
    cash_collected: Optional[Decimal] = Field(None, ge=0, description="Cash collected")
    tips_collected: Optional[Decimal] = Field(None, ge=0, description="Tips collected")
    additional_sales: Optional[Decimal] = Field(None, ge=0, description="Additional sales")
    guide_notes: Optional[str] = Field(None, description="Guide notes")
    requires_follow_up: bool = Field(False, description="Requires follow-up")
    follow_up_notes: Optional[str] = Field(None, description="Follow-up notes")
    completed_by: int = Field(..., description="User ID who completed")


class ServiceOperationSummary(BaseModel):
    """Schema for service operation summary statistics"""
    total_operations: int
    operations_by_status: Dict[str, int]
    operations_by_type: Dict[str, int]
    total_passengers_served: int
    average_attendance_rate: float
    operations_with_incidents: int
    average_rating: Optional[float]
    total_financial_collection: Decimal

    model_config = ConfigDict(from_attributes=True)


class ServiceOperationSearch(BaseModel):
    """Schema for service operation search results"""
    id: int
    operation_date: date
    service_name: str
    service_type: str
    operation_status: str
    passengers_expected: int
    passengers_checked_in: int
    has_incidents: bool

    model_config = ConfigDict(from_attributes=True)


class ServiceOperationSearchResponse(BaseModel):
    """Schema for service operation search response"""
    results: List[ServiceOperationSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# MANIFEST SCHEMAS
# ============================================

class OperationManifest(BaseModel):
    """Schema for operation manifest"""
    operation_id: int
    operation_date: date
    service_name: str
    passengers: List[Dict[str, Any]]
    pickup_points: List[PickupPoint]
    special_requirements: Optional[str]
    emergency_contacts: Optional[str]
    guide_instructions: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# DAILY OPERATIONS SCHEMAS
# ============================================

class DailyOperationsSummary(BaseModel):
    """Schema for daily operations summary"""
    date: date
    total_operations: int
    operations_by_status: Dict[str, int]
    total_passengers: int
    operations_completed: int
    operations_with_issues: int
    average_rating: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class OperationAlert(BaseModel):
    """Schema for operation alerts"""
    operation_id: int
    alert_type: str
    severity: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
