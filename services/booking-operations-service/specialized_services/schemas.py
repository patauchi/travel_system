"""
Specialized Services module schemas
Contains Pydantic schemas for specialized service types validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from common.enums import TransferType, VehicleType, TourType, DurationType


# ============================================
# TRANSFER SERVICE SCHEMAS
# ============================================

class TransferServiceBase(BaseModel):
    """Base schema for Transfer Service"""
    service_id: int = Field(..., description="Service ID")
    transfer_type: TransferType = Field(..., description="Transfer type")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    max_passengers: int = Field(..., ge=1, description="Maximum passengers")
    max_luggage: Optional[int] = Field(None, ge=0, description="Maximum luggage pieces")
    origin_location: Optional[str] = Field(None, max_length=255, description="Origin location")
    destination_location: Optional[str] = Field(None, max_length=255, description="Destination location")
    route_description: Optional[str] = Field(None, description="Route description")
    distance_km: Optional[Decimal] = Field(None, ge=0, description="Distance in kilometers")
    estimated_duration_minutes: Optional[int] = Field(None, ge=0, description="Estimated duration in minutes")
    vehicle_features: Optional[Dict[str, Any]] = Field(None, description="Vehicle features")
    is_round_trip: bool = Field(False, description="Round trip service")
    has_meet_greet: bool = Field(False, description="Meet and greet service")
    waiting_time_minutes: int = Field(0, ge=0, description="Waiting time in minutes")
    includes_tolls: bool = Field(True, description="Includes tolls")
    includes_parking: bool = Field(True, description="Includes parking")
    includes_fuel: bool = Field(True, description="Includes fuel")


class TransferServiceCreate(TransferServiceBase):
    """Schema for creating a new Transfer Service"""
    pass


class TransferServiceUpdate(BaseModel):
    """Schema for updating a Transfer Service"""
    transfer_type: Optional[TransferType] = Field(None, description="Transfer type")
    vehicle_type: Optional[VehicleType] = Field(None, description="Vehicle type")
    max_passengers: Optional[int] = Field(None, ge=1, description="Maximum passengers")
    max_luggage: Optional[int] = Field(None, ge=0, description="Maximum luggage pieces")
    origin_location: Optional[str] = Field(None, max_length=255, description="Origin location")
    destination_location: Optional[str] = Field(None, max_length=255, description="Destination location")
    route_description: Optional[str] = Field(None, description="Route description")
    distance_km: Optional[Decimal] = Field(None, ge=0, description="Distance in kilometers")
    estimated_duration_minutes: Optional[int] = Field(None, ge=0, description="Estimated duration in minutes")
    vehicle_features: Optional[Dict[str, Any]] = Field(None, description="Vehicle features")
    is_round_trip: Optional[bool] = Field(None, description="Round trip service")
    has_meet_greet: Optional[bool] = Field(None, description="Meet and greet service")
    waiting_time_minutes: Optional[int] = Field(None, ge=0, description="Waiting time in minutes")
    includes_tolls: Optional[bool] = Field(None, description="Includes tolls")
    includes_parking: Optional[bool] = Field(None, description="Includes parking")
    includes_fuel: Optional[bool] = Field(None, description="Includes fuel")


class TransferServiceResponse(TransferServiceBase):
    """Schema for Transfer Service response"""
    id: int = Field(..., description="Transfer service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# TOUR SERVICE SCHEMAS
# ============================================

class TourComponentBase(BaseModel):
    """Base schema for Tour Component"""
    component_type: str = Field(..., max_length=50, description="Component type")
    name: str = Field(..., max_length=255, description="Component name")
    description: Optional[str] = Field(None, description="Component description")
    location: Optional[str] = Field(None, max_length=255, description="Component location")
    duration_minutes: Optional[int] = Field(None, ge=0, description="Duration in minutes")
    sequence_order: int = Field(1, ge=1, description="Sequence order")
    start_time: Optional[str] = Field(None, max_length=10, description="Start time (HH:MM)")
    end_time: Optional[str] = Field(None, max_length=10, description="End time (HH:MM)")
    is_optional: bool = Field(False, description="Optional component")
    is_weather_dependent: bool = Field(False, description="Weather dependent")
    component_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('component_type')
    def validate_component_type(cls, v):
        valid_types = ['activity', 'meal', 'transport', 'accommodation', 'break', 'visit']
        if v.lower() not in valid_types:
            raise ValueError(f'Component type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        if v is not None:
            try:
                hour, minute = map(int, v.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError
            except:
                raise ValueError('Time must be in HH:MM format')
        return v


class TourComponentCreate(TourComponentBase):
    """Schema for creating a Tour Component"""
    pass


class TourComponentResponse(TourComponentBase):
    """Schema for Tour Component response"""
    id: int = Field(..., description="Component ID")
    tour_service_id: int = Field(..., description="Tour service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TourServiceBase(BaseModel):
    """Base schema for Tour Service"""
    service_id: int = Field(..., description="Service ID")
    tour_type: TourType = Field(..., description="Tour type")
    duration_type: DurationType = Field(..., description="Duration type")
    physical_difficulty: Optional[str] = Field(None, max_length=20, description="Physical difficulty level")
    min_age: Optional[int] = Field(None, ge=0, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, description="Maximum age")
    itinerary: Optional[List[Dict[str, Any]]] = Field(None, description="Tour itinerary")
    highlights: Optional[List[str]] = Field(None, description="Tour highlights")
    inclusions: Optional[List[str]] = Field(None, description="Tour inclusions")
    exclusions: Optional[List[str]] = Field(None, description="Tour exclusions")
    fitness_level_required: Optional[str] = Field(None, max_length=20, description="Required fitness level")
    special_requirements: Optional[List[str]] = Field(None, description="Special requirements")
    meeting_point: Optional[str] = Field(None, max_length=500, description="Meeting point")
    meeting_time: Optional[str] = Field(None, max_length=100, description="Meeting time")
    drop_off_point: Optional[str] = Field(None, max_length=500, description="Drop-off point")
    max_group_size: Optional[int] = Field(None, ge=1, description="Maximum group size")
    private_tour_available: bool = Field(False, description="Private tour available")
    equipment_provided: Optional[List[str]] = Field(None, description="Equipment provided")
    equipment_required: Optional[List[str]] = Field(None, description="Equipment required")
    languages_available: Optional[List[str]] = Field(None, description="Available languages")

    @validator('physical_difficulty', 'fitness_level_required')
    def validate_difficulty_level(cls, v):
        if v is not None:
            valid_levels = ['easy', 'moderate', 'challenging', 'extreme']
            if v.lower() not in valid_levels:
                raise ValueError(f'Difficulty level must be one of: {", ".join(valid_levels)}')
            return v.lower()
        return v


class TourServiceCreate(TourServiceBase):
    """Schema for creating a new Tour Service"""
    components: Optional[List[TourComponentCreate]] = Field(None, description="Tour components")


class TourServiceUpdate(BaseModel):
    """Schema for updating a Tour Service"""
    tour_type: Optional[TourType] = Field(None, description="Tour type")
    duration_type: Optional[DurationType] = Field(None, description="Duration type")
    physical_difficulty: Optional[str] = Field(None, max_length=20, description="Physical difficulty level")
    min_age: Optional[int] = Field(None, ge=0, description="Minimum age")
    max_age: Optional[int] = Field(None, ge=0, description="Maximum age")
    itinerary: Optional[List[Dict[str, Any]]] = Field(None, description="Tour itinerary")
    highlights: Optional[List[str]] = Field(None, description="Tour highlights")
    inclusions: Optional[List[str]] = Field(None, description="Tour inclusions")
    exclusions: Optional[List[str]] = Field(None, description="Tour exclusions")
    fitness_level_required: Optional[str] = Field(None, max_length=20, description="Required fitness level")
    special_requirements: Optional[List[str]] = Field(None, description="Special requirements")
    meeting_point: Optional[str] = Field(None, max_length=500, description="Meeting point")
    meeting_time: Optional[str] = Field(None, max_length=100, description="Meeting time")
    drop_off_point: Optional[str] = Field(None, max_length=500, description="Drop-off point")
    max_group_size: Optional[int] = Field(None, ge=1, description="Maximum group size")
    private_tour_available: Optional[bool] = Field(None, description="Private tour available")
    equipment_provided: Optional[List[str]] = Field(None, description="Equipment provided")
    equipment_required: Optional[List[str]] = Field(None, description="Equipment required")
    languages_available: Optional[List[str]] = Field(None, description="Available languages")


class TourServiceResponse(TourServiceBase):
    """Schema for Tour Service response"""
    id: int = Field(..., description="Tour service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    tour_components: Optional[List[TourComponentResponse]] = Field(None, description="Tour components")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# TRANSPORT SERVICE SCHEMAS
# ============================================

class TransportServiceBase(BaseModel):
    """Base schema for Transport Service"""
    service_id: int = Field(..., description="Service ID")
    transport_mode: str = Field(..., max_length=50, description="Transport mode")
    carrier_name: Optional[str] = Field(None, max_length=100, description="Carrier name")
    service_class: Optional[str] = Field(None, max_length=50, description="Service class")
    origin_code: Optional[str] = Field(None, max_length=10, description="Origin code")
    destination_code: Optional[str] = Field(None, max_length=10, description="Destination code")
    route_number: Optional[str] = Field(None, max_length=20, description="Route number")
    departure_time: Optional[str] = Field(None, max_length=10, description="Departure time")
    arrival_time: Optional[str] = Field(None, max_length=10, description="Arrival time")
    total_duration_minutes: Optional[int] = Field(None, ge=0, description="Total duration in minutes")
    passenger_capacity: Optional[int] = Field(None, ge=1, description="Passenger capacity")
    baggage_allowance: Optional[Dict[str, str]] = Field(None, description="Baggage allowance")
    onboard_services: Optional[List[str]] = Field(None, description="Onboard services")
    seat_configuration: Optional[str] = Field(None, max_length=20, description="Seat configuration")
    operates_on_days: Optional[List[int]] = Field(None, description="Operating days (1-7)")
    seasonal_operation: bool = Field(False, description="Seasonal operation")
    check_in_required: bool = Field(True, description="Check-in required")
    check_in_time_minutes: Optional[int] = Field(None, ge=0, description="Check-in time in minutes")

    @validator('transport_mode')
    def validate_transport_mode(cls, v):
        valid_modes = ['flight', 'bus', 'train', 'ferry', 'taxi', 'shuttle']
        if v.lower() not in valid_modes:
            raise ValueError(f'Transport mode must be one of: {", ".join(valid_modes)}')
        return v.lower()

    @validator('operates_on_days')
    def validate_operating_days(cls, v):
        if v is not None:
            for day in v:
                if not (1 <= day <= 7):
                    raise ValueError('Operating days must be between 1 (Monday) and 7 (Sunday)')
        return v


class TransportServiceCreate(TransportServiceBase):
    """Schema for creating a new Transport Service"""
    pass


class TransportServiceUpdate(BaseModel):
    """Schema for updating a Transport Service"""
    transport_mode: Optional[str] = Field(None, max_length=50, description="Transport mode")
    carrier_name: Optional[str] = Field(None, max_length=100, description="Carrier name")
    service_class: Optional[str] = Field(None, max_length=50, description="Service class")
    origin_code: Optional[str] = Field(None, max_length=10, description="Origin code")
    destination_code: Optional[str] = Field(None, max_length=10, description="Destination code")
    route_number: Optional[str] = Field(None, max_length=20, description="Route number")
    departure_time: Optional[str] = Field(None, max_length=10, description="Departure time")
    arrival_time: Optional[str] = Field(None, max_length=10, description="Arrival time")
    total_duration_minutes: Optional[int] = Field(None, ge=0, description="Total duration in minutes")
    passenger_capacity: Optional[int] = Field(None, ge=1, description="Passenger capacity")
    baggage_allowance: Optional[Dict[str, str]] = Field(None, description="Baggage allowance")
    onboard_services: Optional[List[str]] = Field(None, description="Onboard services")
    seat_configuration: Optional[str] = Field(None, max_length=20, description="Seat configuration")
    operates_on_days: Optional[List[int]] = Field(None, description="Operating days (1-7)")
    seasonal_operation: Optional[bool] = Field(None, description="Seasonal operation")
    check_in_required: Optional[bool] = Field(None, description="Check-in required")
    check_in_time_minutes: Optional[int] = Field(None, ge=0, description="Check-in time in minutes")


class TransportServiceResponse(TransportServiceBase):
    """Schema for Transport Service response"""
    id: int = Field(..., description="Transport service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RESTAURANT SERVICE SCHEMAS
# ============================================

class RestaurantServiceBase(BaseModel):
    """Base schema for Restaurant Service"""
    service_id: int = Field(..., description="Service ID")
    cuisine_type: Optional[List[str]] = Field(None, description="Cuisine types")
    restaurant_type: Optional[str] = Field(None, max_length=50, description="Restaurant type")
    price_range: Optional[str] = Field(None, max_length=10, description="Price range")
    meal_types: Optional[List[str]] = Field(None, description="Meal types offered")
    menu_options: Optional[List[str]] = Field(None, description="Menu options")
    beverage_options: Optional[List[str]] = Field(None, description="Beverage options")
    total_capacity: Optional[int] = Field(None, ge=1, description="Total capacity")
    indoor_seating: Optional[int] = Field(None, ge=0, description="Indoor seating")
    outdoor_seating: Optional[int] = Field(None, ge=0, description="Outdoor seating")
    private_rooms: Optional[int] = Field(None, ge=0, description="Private rooms")
    location_type: Optional[str] = Field(None, max_length=50, description="Location type")
    ambiance: Optional[List[str]] = Field(None, description="Ambiance options")
    dress_code: Optional[str] = Field(None, max_length=50, description="Dress code")
    table_service: bool = Field(True, description="Table service available")
    takeaway_available: bool = Field(False, description="Takeaway available")
    delivery_available: bool = Field(False, description="Delivery available")
    reservations_required: bool = Field(False, description="Reservations required")
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Operating hours by day")

    @validator('restaurant_type')
    def validate_restaurant_type(cls, v):
        if v is not None:
            valid_types = ['fine_dining', 'casual', 'fast_food', 'cafe', 'buffet', 'food_truck']
            if v.lower() not in valid_types:
                raise ValueError(f'Restaurant type must be one of: {", ".join(valid_types)}')
            return v.lower()
        return v

    @validator('price_range')
    def validate_price_range(cls, v):
        if v is not None:
            valid_ranges = ['$', '$$', '$$$', '$$$$']
            if v not in valid_ranges:
                raise ValueError(f'Price range must be one of: {", ".join(valid_ranges)}')
        return v


class RestaurantServiceCreate(RestaurantServiceBase):
    """Schema for creating a new Restaurant Service"""
    pass


class RestaurantServiceUpdate(BaseModel):
    """Schema for updating a Restaurant Service"""
    cuisine_type: Optional[List[str]] = Field(None, description="Cuisine types")
    restaurant_type: Optional[str] = Field(None, max_length=50, description="Restaurant type")
    price_range: Optional[str] = Field(None, max_length=10, description="Price range")
    meal_types: Optional[List[str]] = Field(None, description="Meal types offered")
    menu_options: Optional[List[str]] = Field(None, description="Menu options")
    beverage_options: Optional[List[str]] = Field(None, description="Beverage options")
    total_capacity: Optional[int] = Field(None, ge=1, description="Total capacity")
    indoor_seating: Optional[int] = Field(None, ge=0, description="Indoor seating")
    outdoor_seating: Optional[int] = Field(None, ge=0, description="Outdoor seating")
    private_rooms: Optional[int] = Field(None, ge=0, description="Private rooms")
    location_type: Optional[str] = Field(None, max_length=50, description="Location type")
    ambiance: Optional[List[str]] = Field(None, description="Ambiance options")
    dress_code: Optional[str] = Field(None, max_length=50, description="Dress code")
    table_service: Optional[bool] = Field(None, description="Table service available")
    takeaway_available: Optional[bool] = Field(None, description="Takeaway available")
    delivery_available: Optional[bool] = Field(None, description="Delivery available")
    reservations_required: Optional[bool] = Field(None, description="Reservations required")
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Operating hours by day")


class RestaurantServiceResponse(RestaurantServiceBase):
    """Schema for Restaurant Service response"""
    id: int = Field(..., description="Restaurant service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# TICKET SERVICE SCHEMAS
# ============================================

class TicketServiceBase(BaseModel):
    """Base schema for Ticket Service"""
    service_id: int = Field(..., description="Service ID")
    venue_name: str = Field(..., max_length=255, description="Venue name")
    venue_type: Optional[str] = Field(None, max_length=50, description="Venue type")
    venue_address: Optional[str] = Field(None, description="Venue address")
    ticket_types: Optional[List[str]] = Field(None, description="Available ticket types")
    age_restrictions: Optional[Dict[str, Any]] = Field(None, description="Age restrictions")
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Operating hours")
    seasonal_schedule: Optional[Dict[str, Any]] = Field(None, description="Seasonal schedule")
    closed_days: Optional[List[str]] = Field(None, description="Closed days")
    daily_capacity: Optional[int] = Field(None, ge=1, description="Daily capacity")
    time_slots: Optional[List[str]] = Field(None, description="Available time slots")
    visit_duration_minutes: Optional[int] = Field(None, ge=0, description="Visit duration in minutes")
    facilities: Optional[List[str]] = Field(None, description="Available facilities")
    accessibility_features: Optional[List[str]] = Field(None, description="Accessibility features")
    languages_supported: Optional[List[str]] = Field(None, description="Supported languages")
    advance_booking_required: bool = Field(False, description="Advance booking required")
    identification_required: bool = Field(False, description="Identification required")
    photography_allowed: bool = Field(True, description="Photography allowed")
    includes_guide: bool = Field(False, description="Includes guide")
    includes_audio_guide: bool = Field(False, description="Includes audio guide")
    group_discounts_available: bool = Field(False, description="Group discounts available")

    @validator('venue_type')
    def validate_venue_type(cls, v):
        if v is not None:
            valid_types = ['museum', 'park', 'monument', 'attraction', 'gallery', 'theater', 'stadium']
            if v.lower() not in valid_types:
                raise ValueError(f'Venue type must be one of: {", ".join(valid_types)}')
            return v.lower()
        return v


class TicketServiceCreate(TicketServiceBase):
    """Schema for creating a new Ticket Service"""
    pass


class TicketServiceUpdate(BaseModel):
    """Schema for updating a Ticket Service"""
    venue_name: Optional[str] = Field(None, max_length=255, description="Venue name")
    venue_type: Optional[str] = Field(None, max_length=50, description="Venue type")
    venue_address: Optional[str] = Field(None, description="Venue address")
    ticket_types: Optional[List[str]] = Field(None, description="Available ticket types")
    age_restrictions: Optional[Dict[str, Any]] = Field(None, description="Age restrictions")
    operating_hours: Optional[Dict[str, Dict[str, str]]] = Field(None, description="Operating hours")
    seasonal_schedule: Optional[Dict[str, Any]] = Field(None, description="Seasonal schedule")
    closed_days: Optional[List[str]] = Field(None, description="Closed days")
    daily_capacity: Optional[int] = Field(None, ge=1, description="Daily capacity")
    time_slots: Optional[List[str]] = Field(None, description="Available time slots")
    visit_duration_minutes: Optional[int] = Field(None, ge=0, description="Visit duration in minutes")
    facilities: Optional[List[str]] = Field(None, description="Available facilities")
    accessibility_features: Optional[List[str]] = Field(None, description="Accessibility features")
    languages_supported: Optional[List[str]] = Field(None, description="Supported languages")
    advance_booking_required: Optional[bool] = Field(None, description="Advance booking required")
    identification_required: Optional[bool] = Field(None, description="Identification required")
    photography_allowed: Optional[bool] = Field(None, description="Photography allowed")
    includes_guide: Optional[bool] = Field(None, description="Includes guide")
    includes_audio_guide: Optional[bool] = Field(None, description="Includes audio guide")
    group_discounts_available: Optional[bool] = Field(None, description="Group discounts available")


class TicketServiceResponse(TicketServiceBase):
    """Schema for Ticket Service response"""
    id: int = Field(..., description="Ticket service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# GUIDE SERVICE SCHEMAS
# ============================================

class GuideServiceBase(BaseModel):
    """Base schema for Guide Service"""
    service_id: int = Field(..., description="Service ID")
    guide_name: Optional[str] = Field(None, max_length=255, description="Guide name")
    guide_type: str = Field(..., max_length=50, description="Guide type")
    specialization: Optional[List[str]] = Field(None, description="Guide specializations")
    certifications: Optional[List[str]] = Field(None, description="Guide certifications")
    languages_spoken: Optional[List[str]] = Field(None, description="Languages spoken")
    experience_years: Optional[int] = Field(None, ge=0, description="Years of experience")
    group_size_max: Optional[int] = Field(None, ge=1, description="Maximum group size")
    private_guide_available: bool = Field(True, description="Private guide available")
    areas_covered: Optional[List[str]] = Field(None, description="Areas covered")
    service_types: Optional[List[str]] = Field(None, description="Service types offered")
    duration_options: Optional[List[str]] = Field(None, description="Duration options")
    equipment_provided: Optional[List[str]] = Field(None, description="Equipment provided")
    transportation_included: bool = Field(False, description="Transportation included")
    available_days: Optional[List[int]] = Field(None, description="Available days (1-7)")
    advance_notice_hours: Optional[int] = Field(None, ge=0, description="Advance notice required (hours)")
    hourly_rate_available: bool = Field(True, description="Hourly rate available")
    daily_rate_available: bool = Field(True, description="Daily rate available")
    group_rate_available: bool = Field(True, description="Group rate available")
    customer_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Customer rating")
    total_tours_completed: int = Field(0, ge=0, description="Total tours completed")

    @validator('guide_type')
    def validate_guide_type(cls, v):
        valid_types = ['local', 'professional', 'specialized', 'certified', 'freelance']
        if v.lower() not in valid_types:
            raise ValueError(f'Guide type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('available_days')
    def validate_available_days(cls, v):
        if v is not None:
            for day in v:
                if not (1 <= day <= 7):
                    raise ValueError('Available days must be between 1 (Monday) and 7 (Sunday)')
        return v


class GuideServiceCreate(GuideServiceBase):
    """Schema for creating a new Guide Service"""
    pass


class GuideServiceUpdate(BaseModel):
    """Schema for updating a Guide Service"""
    guide_name: Optional[str] = Field(None, max_length=255, description="Guide name")
    guide_type: Optional[str] = Field(None, max_length=50, description="Guide type")
    specialization: Optional[List[str]] = Field(None, description="Guide specializations")
    certifications: Optional[List[str]] = Field(None, description="Guide certifications")
    languages_spoken: Optional[List[str]] = Field(None, description="Languages spoken")
    experience_years: Optional[int] = Field(None, ge=0, description="Years of experience")
    group_size_max: Optional[int] = Field(None, ge=1, description="Maximum group size")
    private_guide_available: Optional[bool] = Field(None, description="Private guide available")
    areas_covered: Optional[List[str]] = Field(None, description="Areas covered")
    service_types: Optional[List[str]] = Field(None, description="Service types offered")
    duration_options: Optional[List[str]] = Field(None, description="Duration options")
    equipment_provided: Optional[List[str]] = Field(None, description="Equipment provided")
    transportation_included: Optional[bool] = Field(None, description="Transportation included")
    available_days: Optional[List[int]] = Field(None, description="Available days (1-7)")
    advance_notice_hours: Optional[int] = Field(None, ge=0, description="Advance notice required (hours)")
    hourly_rate_available: Optional[bool] = Field(None, description="Hourly rate available")
    daily_rate_available: Optional[bool] = Field(None, description="Daily rate available")
    group_rate_available: Optional[bool] = Field(None, description="Group rate available")
    customer_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Customer rating")
    total_tours_completed: Optional[int] = Field(None, ge=0, description="Total tours completed")


class GuideServiceResponse(GuideServiceBase):
    """Schema for Guide Service response"""
    id: int = Field(..., description="Guide service ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# EQUIPMENT SERVICE SCHEMAS
# ============================================

class EquipmentServiceBase(BaseModel):
    """Base schema for Equipment Service"""
    service_id: int = Field(..., description="Service ID")
    equipment_type: str = Field(..., max_length=100, description="Equipment type")
    equipment_category: Optional[str] = Field(None, max_length=50, description="Equipment category")
    brand: Optional[str] = Field(None, max_length=100, description="Brand")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    total_quantity: int = Field(1, ge=1, description="Total quantity")
    available_quantity: int = Field(1, ge=0, description="Available quantity")
    condition_status: str = Field("excellent", max_length=20, description="Condition status")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")
    size_options: Optional[List[str]] = Field(None, description="Size options")
    min_rental_hours: int = Field(1, ge=1, description="Minimum rental hours")
    max_rental_days: Optional[int] = Field(None, ge=1, description="Maximum rental days")
    deposit_required: bool = Field(False, description="Deposit required")
    deposit_amount: Optional[Decimal] = Field(None, ge=0, description="Deposit amount")
    rental_includes: Optional[List[str]] = Field(None, description="Rental includes")
    usage_restrictions: Optional[List[str]] = Field(None, description="Usage restrictions")
    maintenance_schedule: Optional[Dict[str, Any]] = Field(None, description="Maintenance schedule")
    last_service_date: Optional[date] = Field(None, description="Last service date")
    next_service_date: Optional[date] = Field(None, description="Next service date")
    safety_instructions: Optional[str] = Field(None, description="Safety instructions")
    accessories_included: Optional[List[str]] = Field(None, description="Accessories included")
    optional_accessories: Optional[List[str]] = Field(None, description="Optional accessories")
    requires_training: bool = Field(False, description="Requires training")
    training_duration_hours: Optional[int] = Field(None, ge=1, description="Training duration hours")
    insurance_required: bool = Field(False, description="Insurance required")
    insurance_options: Optional[List[Dict[str, Any]]] = Field(None, description="Insurance options")
    replacement_value: Optional[Decimal] = Field(None, ge=0, description="Replacement value")

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
        }


class EquipmentServiceUpdate(BaseModel):
    """Schema for updating an Equipment Service"""
    equipment_type: Optional[str] = Field(None, max_length=100, description="Equipment type")
    equipment_category: Optional[str] = Field(None, max_length=50, description="Equipment category")
    brand: Optional[str] = Field(None, max_length=100, description="Brand")
    model: Optional[str] = Field(None, max_length=100, description="Model")
    total_quantity: Optional[int] = Field(None, ge=1, description="Total quantity")
    available_quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    condition_status: Optional[str] = Field(None, max_length=20, description="Condition status")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Technical specifications")
    size_options: Optional[List[str]] = Field(None, description="Size options")
    min_rental_hours: Optional[int] = Field(None, ge=1, description="Minimum rental hours")
    max_rental_days: Optional[int] = Field(None, ge=1, description="Maximum rental days")
    deposit_required: Optional[bool] = Field(None, description="Deposit required")
    deposit_amount: Optional[Decimal] = Field(None, ge=0, description="Deposit amount")
    rental_includes: Optional[List[str]] = Field(None, description="Rental includes")
    usage_restrictions: Optional[List[str]] = Field(None, description="Usage restrictions")
    maintenance_schedule: Optional[Dict[str, Any]] = Field(None, description="Maintenance schedule")
    last_service_date: Optional[date] = Field(None, description="Last service date")
    next_service_date: Optional[date] = Field(None, description="Next service date")
    safety_instructions: Optional[str] = Field(None, description="Safety instructions")
    accessories_included: Optional[List[str]] = Field(None, description="Accessories included")
    optional_accessories: Optional[List[str]] = Field(None, description="Optional accessories")
    requires_training: Optional[bool] = Field(None, description="Requires training")
    training_duration_hours: Optional[int] = Field(None, ge=1, description="Training duration hours")
    insurance_required: Optional[bool] = Field(None, description="Insurance required")
    insurance_options: Optional[List[Dict[str, Any]]] = Field(None, description="Insurance options")
    replacement_value: Optional[Decimal] = Field(None, ge=0, description="Replacement value")

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
        }
