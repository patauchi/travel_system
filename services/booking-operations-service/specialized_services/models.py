"""
Specialized Services module models
Contains specialized service models for different service types
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import TransferType, VehicleType, TourType, DurationType

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

    def __repr__(self):
        return f"<TransferService(id={self.id}, service_id={self.service_id}, type='{self.transfer_type}')>"

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
    physical_difficulty = Column(String(20), nullable=True)  # easy, moderate, challenging, extreme
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)

    # Itinerary
    itinerary = Column(JSON, nullable=True)  # [{time, activity, location, duration}]
    highlights = Column(JSON, nullable=True)  # ["Machu Picchu", "Inca Trail"]
    inclusions = Column(JSON, nullable=True)  # ["meals", "entrance_fees", "guide"]
    exclusions = Column(JSON, nullable=True)  # ["flights", "personal_expenses"]

    # Requirements
    fitness_level_required = Column(String(20), nullable=True)
    special_requirements = Column(JSON, nullable=True)  # ["passport", "yellow_fever_vaccine"]

    # Meeting Points
    meeting_point = Column(String(500), nullable=True)
    meeting_time = Column(String(100), nullable=True)
    drop_off_point = Column(String(500), nullable=True)

    # Group Details
    max_group_size = Column(Integer, nullable=True)
    private_tour_available = Column(Boolean, default=False)

    # Equipment
    equipment_provided = Column(JSON, nullable=True)
    equipment_required = Column(JSON, nullable=True)

    # Language Options
    languages_available = Column(JSON, nullable=True)  # ["english", "spanish", "portuguese"]

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="tour_service")
    tour_components = relationship("TourComponent", back_populates="tour_service", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_tour_type', 'tour_type'),
        Index('idx_tour_duration', 'duration_type'),
        Index('idx_tour_difficulty', 'physical_difficulty'),
    )

    def __repr__(self):
        return f"<TourService(id={self.id}, service_id={self.service_id}, type='{self.tour_type}')>"

# ============================================
# TOUR COMPONENTS TABLE
# ============================================

class TourComponent(Base):
    """Individual components of tour services"""
    __tablename__ = "tour_components"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    tour_service_id = Column(Integer, ForeignKey('tour_services.id', ondelete='CASCADE'), nullable=False)

    # Component Details
    component_type = Column(String(50), nullable=False)  # activity, meal, transport, accommodation
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    sequence_order = Column(Integer, nullable=False, default=1)

    # Timing
    start_time = Column(String(10), nullable=True)  # "09:00"
    end_time = Column(String(10), nullable=True)  # "17:00"

    # Status
    is_optional = Column(Boolean, default=False)
    is_weather_dependent = Column(Boolean, default=False)

    # Additional Information
    component_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tour_service = relationship("TourService", back_populates="tour_components")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_component_tour', 'tour_service_id'),
        Index('idx_component_type', 'component_type'),
        Index('idx_component_order', 'sequence_order'),
    )

    def __repr__(self):
        return f"<TourComponent(id={self.id}, name='{self.name}', type='{self.component_type}')>"

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
    service_class = Column(String(50), nullable=True)  # economy, business, first_class

    # Route Details
    origin_code = Column(String(10), nullable=True)  # Airport/station codes
    destination_code = Column(String(10), nullable=True)
    route_number = Column(String(20), nullable=True)  # Flight number, bus line, etc.

    # Schedule
    departure_time = Column(String(10), nullable=True)  # "14:30"
    arrival_time = Column(String(10), nullable=True)  # "16:45"
    total_duration_minutes = Column(Integer, nullable=True)

    # Capacity and Baggage
    passenger_capacity = Column(Integer, nullable=True)
    baggage_allowance = Column(JSON, nullable=True)  # {checked: "23kg", carry_on: "8kg"}

    # Services and Amenities
    onboard_services = Column(JSON, nullable=True)  # ["wifi", "meals", "entertainment"]
    seat_configuration = Column(String(20), nullable=True)  # "3-3", "2-4-2"

    # Operational Details
    operates_on_days = Column(JSON, nullable=True)  # [1,2,3,4,5] for Mon-Fri
    seasonal_operation = Column(Boolean, default=False)
    check_in_required = Column(Boolean, default=True)
    check_in_time_minutes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="transport_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_transport_mode', 'transport_mode'),
        Index('idx_transport_carrier', 'carrier_name'),
        Index('idx_transport_route', 'origin_code', 'destination_code'),
    )

    def __repr__(self):
        return f"<TransportService(id={self.id}, mode='{self.transport_mode}', route='{self.route_number}')>"

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
    price_range = Column(String(10), nullable=True)  # $, $$, $$$, $$$$

    # Dining Options
    meal_types = Column(JSON, nullable=True)  # ["breakfast", "lunch", "dinner", "snacks"]
    menu_options = Column(JSON, nullable=True)  # ["vegetarian", "vegan", "gluten_free", "halal"]
    beverage_options = Column(JSON, nullable=True)  # ["alcoholic", "non_alcoholic", "specialty_drinks"]

    # Capacity and Seating
    total_capacity = Column(Integer, nullable=True)
    indoor_seating = Column(Integer, nullable=True)
    outdoor_seating = Column(Integer, nullable=True)
    private_rooms = Column(Integer, nullable=True)

    # Location and Ambiance
    location_type = Column(String(50), nullable=True)  # downtown, beachfront, mountain_view, historic
    ambiance = Column(JSON, nullable=True)  # ["romantic", "family_friendly", "business", "casual"]
    dress_code = Column(String(50), nullable=True)  # casual, smart_casual, formal

    # Services
    table_service = Column(Boolean, default=True)
    takeaway_available = Column(Boolean, default=False)
    delivery_available = Column(Boolean, default=False)
    reservations_required = Column(Boolean, default=False)

    # Operating Hours
    operating_hours = Column(JSON, nullable=True)  # {monday: {open: "09:00", close: "22:00"}}

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="restaurant_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_restaurant_type', 'restaurant_type'),
        Index('idx_restaurant_price', 'price_range'),
        Index('idx_restaurant_capacity', 'total_capacity'),
    )

    def __repr__(self):
        return f"<RestaurantService(id={self.id}, type='{self.restaurant_type}', capacity={self.total_capacity})>"

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

    # Ticket Types
    ticket_types = Column(JSON, nullable=True)  # ["general", "vip", "group", "student", "senior"]
    age_restrictions = Column(JSON, nullable=True)  # {min_age: 0, max_age: null, child_price_age: 12}

    # Operating Information
    operating_hours = Column(JSON, nullable=True)  # {monday: {open: "09:00", close: "17:00"}}
    seasonal_schedule = Column(JSON, nullable=True)  # Different hours by season
    closed_days = Column(JSON, nullable=True)  # ["monday", "december_25"]

    # Capacity and Timing
    daily_capacity = Column(Integer, nullable=True)
    time_slots = Column(JSON, nullable=True)  # ["09:00", "11:00", "14:00", "16:00"]
    visit_duration_minutes = Column(Integer, nullable=True)

    # Services and Facilities
    facilities = Column(JSON, nullable=True)  # ["parking", "restaurant", "gift_shop", "guided_tours"]
    accessibility_features = Column(JSON, nullable=True)  # ["wheelchair_accessible", "audio_guide"]
    languages_supported = Column(JSON, nullable=True)  # ["english", "spanish", "french"]

    # Special Requirements
    advance_booking_required = Column(Boolean, default=False)
    identification_required = Column(Boolean, default=False)
    photography_allowed = Column(Boolean, default=True)

    # Pricing Information
    includes_guide = Column(Boolean, default=False)
    includes_audio_guide = Column(Boolean, default=False)
    group_discounts_available = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="ticket_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_ticket_venue_type', 'venue_type'),
        Index('idx_ticket_capacity', 'daily_capacity'),
        Index('idx_ticket_advance_booking', 'advance_booking_required'),
    )

    def __repr__(self):
        return f"<TicketService(id={self.id}, venue='{self.venue_name}', type='{self.venue_type}')>"

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
    specialization = Column(JSON, nullable=True)  # ["history", "archaeology", "nature", "adventure"]

    # Qualifications
    certifications = Column(JSON, nullable=True)  # ["official_guide", "first_aid", "mountain_guide"]
    languages_spoken = Column(JSON, nullable=True)  # ["english", "spanish", "quechua"]
    experience_years = Column(Integer, nullable=True)

    # Service Details
    group_size_max = Column(Integer, nullable=True)
    private_guide_available = Column(Boolean, default=True)
    areas_covered = Column(JSON, nullable=True)  # ["cusco", "sacred_valley", "machu_picchu"]

    # Service Types
    service_types = Column(JSON, nullable=True)  # ["walking_tour", "driving_tour", "trekking", "cultural"]
    duration_options = Column(JSON, nullable=True)  # ["half_day", "full_day", "multi_day"]

    # Equipment and Tools
    equipment_provided = Column(JSON, nullable=True)  # ["radio", "first_aid_kit", "binoculars"]
    transportation_included = Column(Boolean, default=False)

    # Availability
    available_days = Column(JSON, nullable=True)  # [1,2,3,4,5,6,7] for days of week
    advance_notice_hours = Column(Integer, nullable=True)

    # Pricing Structure
    hourly_rate_available = Column(Boolean, default=True)
    daily_rate_available = Column(Boolean, default=True)
    group_rate_available = Column(Boolean, default=True)

    # Performance Metrics
    customer_rating = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00
    total_tours_completed = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="guide_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_guide_type', 'guide_type'),
        Index('idx_guide_rating', 'customer_rating'),
        Index('idx_guide_experience', 'experience_years'),
    )

    def __repr__(self):
        return f"<GuideService(id={self.id}, name='{self.guide_name}', type='{self.guide_type}')>"

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

    # Inventory Management
    total_quantity = Column(Integer, nullable=False, default=1)
    available_quantity = Column(Integer, nullable=False, default=1)
    condition_status = Column(String(20), default="excellent")  # excellent, good, fair, needs_repair

    # Technical Specifications
    specifications = Column(JSON, nullable=True)  # {size, weight, features, compatibility}
    size_options = Column(JSON, nullable=True)  # ["XS", "S", "M", "L", "XL"]

    # Rental Terms
    min_rental_hours = Column(Integer, default=1)
    max_rental_hours = Column(Integer, nullable=True)
    rental_increments = Column(String(20), default="hourly")  # hourly, daily, weekly

    # Requirements and Restrictions
    age_restrictions = Column(JSON, nullable=True)  # {min_age: 18, max_age: null}
    skill_level_required = Column(String(20), nullable=True)  # beginner, intermediate, advanced
    certification_required = Column(Boolean, default=False)
    deposit_required = Column(Boolean, default=True)

    # Safety and Maintenance
    safety_equipment_included = Column(JSON, nullable=True)  # ["helmet", "life_jacket", "safety_rope"]
    maintenance_schedule = Column(String(50), nullable=True)  # daily, weekly, monthly
    last_maintenance_date = Column(DateTime(timezone=True), nullable=True)

    # Delivery Options
    pickup_location = Column(String(500), nullable=True)
    delivery_available = Column(Boolean, default=False)
    delivery_radius_km = Column(Numeric(10, 2), nullable=True)

    # Insurance and Liability
    insurance_included = Column(Boolean, default=False)
    damage_policy = Column(Text, nullable=True)
    replacement_cost = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="equipment_service")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_equipment_type', 'equipment_type'),
        Index('idx_equipment_category', 'equipment_category'),
        Index('idx_equipment_availability', 'available_quantity'),
        Index('idx_equipment_condition', 'condition_status'),
    )

    def __repr__(self):
        return f"<EquipmentService(id={self.id}, type='{self.equipment_type}', available={self.available_quantity})>"
