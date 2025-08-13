"""
Booking Operations Service Models - Suppliers and Services
Based on Laravel migrations from services-references/booking-operations-service
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from models_base import Base

# ============================================
# ENUMS
# ============================================

class SupplierType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"

class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLIST = "blacklist"

class ServiceType(str, enum.Enum):
    ACCOMMODATION = "accommodation"
    TRANSFER = "transfer"
    TOUR = "tour"
    TRANSPORT = "transport"
    RESTAURANT = "restaurant"
    TICKET = "ticket"
    GUIDE = "guide"
    EQUIPMENT = "equipment"
    OTHER = "other"

class OperationModel(str, enum.Enum):
    NO_DEFINED = "no_defined"
    DIRECT = "direct"
    RESALE = "resale"
    WHITE_LABEL = "white_label"
    HYBRID = "hybrid"

class TransferType(str, enum.Enum):
    PRIVATE = "private"
    SHARED = "shared"
    SHUTTLE = "shuttle"
    EXECUTIVE = "executive"
    LUXURY = "luxury"

class VehicleType(str, enum.Enum):
    SEDAN = "sedan"
    SUV = "suv"
    VAN = "van"
    MINIBUS = "minibus"
    BUS = "bus"
    LIMOUSINE = "limousine"
    HELICOPTER = "helicopter"
    BOAT = "boat"
    OTHER = "other"

class TourType(str, enum.Enum):
    PRIVATE = "private"
    GROUP = "group"
    REGULAR = "regular"
    VIP = "vip"

class DurationType(str, enum.Enum):
    HOURS = "hours"
    HALF_DAY = "half_day"
    FULL_DAY = "full_day"
    MULTI_DAY = "multi_day"

# ============================================
# SUPPLIERS TABLE
# ============================================

class Supplier(Base):
    """Supplier management for travel services"""
    __tablename__ = "suppliers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    type = Column(SQLEnum(SupplierType), default=SupplierType.COMPANY)

    # Contact Information (JSON fields)
    contact_info = Column(JSON, nullable=True)  # {phones, emails, websites, social_media}
    address = Column(JSON, nullable=True)  # {street, city, state, country, postal_code, coordinates}

    # Financial Information
    banking_info = Column(JSON, nullable=True)  # {accounts, swift, payment_methods}

    # Certifications and Compliance
    certifications = Column(JSON, nullable=True)  # {licenses, insurance, quality_seals}

    # Service Configuration
    allowed_services = Column(JSON, nullable=True)  # {ticket, tour, restaurant, equipment, guide, transport, transfer}
    allowed_destinations = Column(JSON, nullable=True)  # destination ids {1, 3, 5, 9}

    # Status and Rating
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.ACTIVE, index=True)
    ratings = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00

    # Additional Data
    supplier_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    services = relationship("Service", back_populates="supplier", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('code', 'deleted_at', name='uq_supplier_code_deleted'),
        Index('idx_supplier_code', 'code'),
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_name_status', 'name', 'status'),
        Index('idx_supplier_deleted', 'deleted_at'),
    )

# ============================================
# SERVICES TABLE
# ============================================

class Service(Base):
    """Service catalog from suppliers"""
    __tablename__ = "services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    supplier_id = Column(Integer, ForeignKey('suppliers.id', ondelete='CASCADE'), nullable=False)
    cancellation_policy_id = Column(Integer, ForeignKey('cancellation_policies.id'), nullable=True)

    # Service Identification
    service_code = Column(String(50), nullable=True)  # Internal provider code: "HTL-001", "TRF-APT-001"

    # Coverage
    coverage_destinations_ids = Column(JSON, nullable=True)  # Array of destination IDs

    # Operation Model
    operation_model = Column(SQLEnum(OperationModel), default=OperationModel.NO_DEFINED)

    # Service Details
    name = Column(String(200), nullable=False)  # "Airport Transfer Premium", "City Tour Lima"
    description = Column(Text, nullable=True)  # Detailed description
    short_description = Column(Text, nullable=True)  # Short description for listings
    service_type = Column(SQLEnum(ServiceType), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=False)

    # Service Content
    inclusions = Column(JSON, nullable=True)  # ["pickup", "dropoff", "guide", "entrance_fees"]
    exclusions = Column(JSON, nullable=True)  # ["tips", "personal_expenses", "insurance"]

    # Languages
    languages = Column(JSON, nullable=True)  # ['es', 'en', 'fr']

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="services")
    transfer_service = relationship("TransferService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    tour_service = relationship("TourService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    transport_service = relationship("TransportService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    restaurant_service = relationship("RestaurantService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    ticket_service = relationship("TicketService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    guide_service = relationship("GuideService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    equipment_service = relationship("EquipmentService", back_populates="service", uselist=False, cascade="all, delete-orphan")
    rates = relationship("Rate", back_populates="service", cascade="all, delete-orphan")
    tour_components = relationship("TourComponent", back_populates="service", cascade="all, delete-orphan")
    service_availability = relationship("ServiceAvailability", back_populates="service", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_services_supplier_type', 'supplier_id', 'service_type'),
        Index('idx_services_type_active', 'service_type', 'is_active'),
        Index('idx_services_code', 'service_code'),
        Index('idx_services_deleted', 'deleted_at'),
    )

# ============================================
# TRANSFER SERVICES TABLE
# ============================================

class TransferService(Base):
    """Specialized table for transfer services"""
    __tablename__ = "transfer_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Transfer Specifics
    transfer_type = Column(SQLEnum(TransferType), nullable=False)
    vehicle_type = Column(SQLEnum(VehicleType), nullable=False)
    max_passengers = Column(Integer, nullable=False)
    max_luggage = Column(Integer, nullable=True)

    # Route Information
    origin_location = Column(String(255), nullable=True)
    destination_location = Column(String(255), nullable=True)
    route_description = Column(Text, nullable=True)
    distance_km = Column(Numeric(10, 2), nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)

    # Vehicle Details
    vehicle_features = Column(JSON, nullable=True)  # {air_conditioning, wifi, wheelchair_accessible}

    # Operational Details
    is_round_trip = Column(Boolean, default=False)
    has_meet_greet = Column(Boolean, default=False)
    waiting_time_minutes = Column(Integer, default=0)

    # Additional Services
    includes_tolls = Column(Boolean, default=True)
    includes_parking = Column(Boolean, default=True)
    includes_fuel = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="transfer_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_transfer_type', 'transfer_type'),
        Index('idx_transfer_vehicle', 'vehicle_type'),
        Index('idx_transfer_passengers', 'max_passengers'),
    )

# ============================================
# TOUR SERVICES TABLE
# ============================================

class TourService(Base):
    """Specialized table for tour services"""
    __tablename__ = "tour_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Tour Specifics
    tour_type = Column(SQLEnum(TourType), nullable=False)
    duration_type = Column(SQLEnum(DurationType), nullable=False)
    duration_hours = Column(Numeric(5, 2), nullable=True)
    duration_days = Column(Integer, nullable=True)

    # Capacity
    min_participants = Column(Integer, default=1)
    max_participants = Column(Integer, nullable=True)

    # Schedule
    departure_times = Column(JSON, nullable=True)  # ["09:00", "14:00"]
    operating_days = Column(JSON, nullable=True)  # ["mon", "tue", "wed", "thu", "fri"]
    blackout_dates = Column(JSON, nullable=True)  # ["2024-12-25", "2024-01-01"]
    season_start = Column(Date, nullable=True)
    season_end = Column(Date, nullable=True)

    # Tour Details
    difficulty_level = Column(String(50), nullable=True)  # easy, moderate, challenging, extreme
    physical_rating = Column(Integer, nullable=True)  # 1-5
    age_restrictions = Column(JSON, nullable=True)  # {min_age: 8, max_age: 70}

    # Itinerary
    itinerary = Column(JSON, nullable=True)  # Array of stops/activities
    highlights = Column(JSON, nullable=True)  # Key attractions

    # Guide Information
    guide_required = Column(Boolean, default=True)
    guide_languages = Column(JSON, nullable=True)
    guide_ratio = Column(String(20), nullable=True)  # "1:10" (1 guide per 10 people)

    # Included Services
    includes_transportation = Column(Boolean, default=False)
    includes_meals = Column(Boolean, default=False)
    includes_tickets = Column(Boolean, default=False)
    includes_equipment = Column(Boolean, default=False)

    # Meeting Point
    meeting_point = Column(String(500), nullable=True)
    meeting_point_coordinates = Column(JSON, nullable=True)  # {lat, lng}
    meeting_instructions = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="tour_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_tour_type', 'tour_type'),
        Index('idx_tour_duration', 'duration_type'),
        Index('idx_tour_capacity', 'max_participants'),
        Index('idx_tour_dates', 'season_start', 'season_end'),
    )

# ============================================
# TRANSPORT SERVICES TABLE
# ============================================

class TransportService(Base):
    """Specialized table for transport services (flights, buses, trains)"""
    __tablename__ = "transport_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Transport Type
    transport_mode = Column(String(50), nullable=False)  # flight, bus, train, ferry
    carrier_name = Column(String(100), nullable=True)
    carrier_code = Column(String(10), nullable=True)  # IATA/carrier code

    # Route Information
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    route_code = Column(String(50), nullable=True)

    # Schedule
    departure_time = Column(String(10), nullable=True)  # HH:MM format
    arrival_time = Column(String(10), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    frequency = Column(String(50), nullable=True)  # daily, weekly, etc.

    # Service Classes
    available_classes = Column(JSON, nullable=True)  # ["economy", "business", "first"]

    # Amenities
    amenities = Column(JSON, nullable=True)  # {wifi, meals, entertainment, power_outlets}

    # Baggage Policy
    baggage_policy = Column(JSON, nullable=True)  # {carry_on, checked, excess_fees}

    # Operational
    is_direct = Column(Boolean, default=True)
    stops = Column(JSON, nullable=True)  # Array of intermediate stops
    connection_info = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="transport_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_transport_mode', 'transport_mode'),
        Index('idx_transport_route', 'origin', 'destination'),
        Index('idx_transport_carrier', 'carrier_code'),
    )

# ============================================
# RESTAURANT SERVICES TABLE
# ============================================

class RestaurantService(Base):
    """Specialized table for restaurant services"""
    __tablename__ = "restaurant_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Restaurant Details
    cuisine_type = Column(JSON, nullable=True)  # ["peruvian", "italian", "japanese"]
    restaurant_type = Column(String(50), nullable=True)  # fine_dining, casual, fast_food, cafe

    # Capacity
    total_capacity = Column(Integer, nullable=True)
    private_rooms = Column(Integer, default=0)
    outdoor_seating = Column(Boolean, default=False)

    # Operating Hours
    operating_hours = Column(JSON, nullable=True)  # {mon: "12:00-22:00", tue: "12:00-22:00"}

    # Meal Services
    serves_breakfast = Column(Boolean, default=False)
    serves_lunch = Column(Boolean, default=True)
    serves_dinner = Column(Boolean, default=True)
    serves_brunch = Column(Boolean, default=False)

    # Menu Information
    menu_url = Column(String(500), nullable=True)
    average_price_per_person = Column(Numeric(10, 2), nullable=True)
    price_range = Column(String(10), nullable=True)  # $, $$, $$$, $$$$

    # Dietary Options
    dietary_options = Column(JSON, nullable=True)  # {vegetarian, vegan, gluten_free, halal, kosher}

    # Features
    features = Column(JSON, nullable=True)  # {wifi, parking, wheelchair_accessible, kid_friendly}

    # Reservation Policy
    accepts_reservations = Column(Boolean, default=True)
    reservation_required = Column(Boolean, default=False)
    max_group_size = Column(Integer, nullable=True)
    cancellation_hours = Column(Integer, default=24)

    # Dress Code
    dress_code = Column(String(50), nullable=True)  # casual, smart_casual, business, formal

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="restaurant_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_restaurant_type', 'restaurant_type'),
        Index('idx_restaurant_price', 'price_range'),
    )

# ============================================
# TICKET SERVICES TABLE
# ============================================

class TicketService(Base):
    """Specialized table for ticket/entrance services"""
    __tablename__ = "ticket_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Venue Information
    venue_name = Column(String(255), nullable=False)
    venue_type = Column(String(50), nullable=True)  # museum, park, monument, attraction
    venue_address = Column(Text, nullable=True)
    venue_coordinates = Column(JSON, nullable=True)  # {lat, lng}

    # Ticket Types
    ticket_types = Column(JSON, nullable=True)  # [{type: "adult", price: 25}, {type: "child", price: 15}]

    # Validity
    validity_type = Column(String(50), nullable=True)  # specific_date, date_range, anytime
    validity_days = Column(Integer, nullable=True)  # Number of days valid from purchase

    # Operating Information
    operating_hours = Column(JSON, nullable=True)  # {mon: "09:00-18:00"}
    last_admission = Column(String(10), nullable=True)  # HH:MM format
    closed_dates = Column(JSON, nullable=True)  # Annual closing dates

    # Access Information
    skip_line = Column(Boolean, default=False)
    guided_tour_included = Column(Boolean, default=False)
    audio_guide_included = Column(Boolean, default=False)
    audio_guide_languages = Column(JSON, nullable=True)

    # Restrictions
    age_restrictions = Column(JSON, nullable=True)  # {min_age, max_age}
    requires_id = Column(Boolean, default=False)
    photography_allowed = Column(Boolean, default=True)

    # Additional Services
    includes_transportation = Column(Boolean, default=False)
    includes_meal = Column(Boolean, default=False)

    # Booking Requirements
    advance_booking_required = Column(Boolean, default=False)
    advance_booking_days = Column(Integer, nullable=True)
    instant_confirmation = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="ticket_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_ticket_venue_type', 'venue_type'),
        Index('idx_ticket_validity', 'validity_type'),
        Index('idx_ticket_skip_line', 'skip_line'),
    )

# ============================================
# GUIDE SERVICES TABLE
# ============================================

class GuideService(Base):
    """Specialized table for guide services"""
    __tablename__ = "guide_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Guide Information
    guide_name = Column(String(255), nullable=True)
    guide_type = Column(String(50), nullable=False)  # local, professional, specialized
    license_number = Column(String(100), nullable=True)
    years_experience = Column(Integer, nullable=True)

    # Languages
    primary_language = Column(String(10), nullable=False)
    languages_spoken = Column(JSON, nullable=False)  # ["es", "en", "fr", "de"]

    # Specializations
    specializations = Column(JSON, nullable=True)  # ["history", "art", "nature", "adventure"]
    certifications = Column(JSON, nullable=True)  # ["first_aid", "wilderness", "cultural"]

    # Service Details
    service_duration_hours = Column(Numeric(5, 2), nullable=True)
    max_group_size = Column(Integer, nullable=True)
    min_group_size = Column(Integer, default=1)

    # Availability
    available_days = Column(JSON, nullable=True)  # ["mon", "tue", "wed"]
    available_hours = Column(JSON, nullable=True)  # {start: "08:00", end: "18:00"}
    advance_booking_required = Column(Integer, default=24)  # Hours in advance

    # Coverage
    coverage_areas = Column(JSON, nullable=True)  # ["lima", "cusco", "arequipa"]

    # Included Services
    includes_transportation = Column(Boolean, default=False)
    includes_equipment = Column(Boolean, default=False)
    includes_entrance_fees = Column(Boolean, default=False)

    # Rates
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    daily_rate = Column(Numeric(10, 2), nullable=True)
    overtime_rate = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="guide_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_guide_type', 'guide_type'),
        Index('idx_guide_languages', 'primary_language'),
        Index('idx_guide_group_size', 'max_group_size'),
    )

# ============================================
# EQUIPMENT SERVICES TABLE
# ============================================

class EquipmentService(Base):
    """Specialized table for equipment rental services"""
    __tablename__ = "equipment_services"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), unique=True, nullable=False)

    # Equipment Details
    equipment_type = Column(String(100), nullable=False)  # bike, camera, diving_gear, ski_equipment
    equipment_category = Column(String(50), nullable=True)  # sports, photography, outdoor, water_sports
    brand = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)

    # Inventory
    total_units = Column(Integer, nullable=True)
    available_units = Column(Integer, nullable=True)

    # Rental Terms
    rental_period_type = Column(String(20), nullable=True)  # hourly, daily, weekly
    min_rental_period = Column(Integer, default=1)
    max_rental_period = Column(Integer, nullable=True)

    # Pricing
    hourly_rate = Column(Numeric(10, 2), nullable=True)
    daily_rate = Column(Numeric(10, 2), nullable=True)
    weekly_rate = Column(Numeric(10, 2), nullable=True)
    deposit_required = Column(Numeric(10, 2), nullable=True)

    # Specifications
    specifications = Column(JSON, nullable=True)  # Technical details
    size_options = Column(JSON, nullable=True)  # ["S", "M", "L", "XL"]

    # Included Items
    included_accessories = Column(JSON, nullable=True)  # ["helmet", "lock", "pump"]

    # Requirements
    requires_id = Column(Boolean, default=True)
    requires_experience = Column(Boolean, default=False)
    requires_certification = Column(Boolean, default=False)
    age_requirement = Column(Integer, nullable=True)

    # Delivery Options
    delivery_available = Column(Boolean, default=False)
    pickup_location = Column(String(500), nullable=True)
    delivery_fee = Column(Numeric(10, 2), nullable=True)

    # Insurance
    insurance_available = Column(Boolean, default=False)
    insurance_cost = Column(Numeric(10, 2), nullable=True)
    damage_policy = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="equipment_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_equipment_type', 'equipment_type'),
        Index('idx_equipment_category', 'equipment_category'),
        Index('idx_equipment_availability', 'available_units'),
    )

# ============================================
# TOUR COMPONENTS TABLE (For complex tours)
# ============================================

class TourComponent(Base):
    """Components that make up a complex tour package"""
    __tablename__ = "tour_components"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    component_service_id = Column(Integer, ForeignKey('services.id'), nullable=True)

    # Component Details
    day_number = Column(Integer, nullable=True)  # For multi-day tours
    sequence_order = Column(Integer, nullable=False)  # Order within the day
    component_type = Column(String(50), nullable=False)  # transfer, activity, meal, accommodation

    # Timing
    start_time = Column(String(10), nullable=True)  # HH:MM format
    duration_minutes = Column(Integer, nullable=True)

    # Description
    component_name = Column(String(255), nullable=False)
    component_description = Column(Text, nullable=True)

    # Location
    location = Column(String(255), nullable=True)
    meeting_point = Column(String(500), nullable=True)

    # Requirements
    is_mandatory = Column(Boolean, default=True)
    is_included = Column(Boolean, default=True)

    # Pricing (if not included)
    additional_cost = Column(Numeric(10, 2), nullable=True)

    # Notes
    special_instructions = Column(Text, nullable=True)

    # Metadata
    component_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", foreign_keys=[service_id], back_populates="tour_components")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_tour_component_service', 'service_id'),
        Index('idx_tour_component_order', 'service_id', 'day_number', 'sequence_order'),
        Index('idx_tour_component_type', 'component_type'),
    )

# ============================================
# SERVICE AVAILABILITY TABLE
# ============================================

class ServiceAvailability(Base):
    """Availability calendar for services"""
    __tablename__ = "service_availability"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Date Range
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Availability Type
    availability_type = Column(String(20), nullable=False)  # available, blocked, limited

    # Days of Week (if recurring)
    available_days = Column(JSON, nullable=True)  # ["mon", "tue", "wed"]

    # Time Slots
    time_slots = Column(JSON, nullable=True)  # [{start: "09:00", end: "10:00", capacity: 10}]

    # Capacity
    daily_capacity = Column(Integer, nullable=True)
    current_bookings = Column(Integer, default=0)

    # Pricing Adjustments
    price_adjustment = Column(Numeric(5, 2), nullable=True)  # Percentage adjustment
