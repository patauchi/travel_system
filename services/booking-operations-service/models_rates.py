"""
Booking Operations Service Models - Rates and Cancellation Policies
Based on Laravel migrations from services-references/booking-operations-service
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, UniqueConstraint, Index, Time
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

class RateType(str, enum.Enum):
    STANDARD = "standard"
    SEASONAL = "seasonal"
    PROMOTIONAL = "promotional"
    SPECIAL = "special"
    CONTRACT = "contract"
    PACKAGE = "package"

class PricingModel(str, enum.Enum):
    PER_PERSON = "per_person"
    PER_GROUP = "per_group"
    PER_VEHICLE = "per_vehicle"
    PER_ROOM = "per_room"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_UNIT = "per_unit"
    TIERED = "tiered"
    DYNAMIC = "dynamic"

class SeasonType(str, enum.Enum):
    LOW = "low"
    SHOULDER = "shoulder"
    HIGH = "high"
    PEAK = "peak"

class CancellationPolicyType(str, enum.Enum):
    FLEXIBLE = "flexible"
    MODERATE = "moderate"
    STRICT = "strict"
    SUPER_STRICT = "super_strict"
    NON_REFUNDABLE = "non_refundable"
    CUSTOM = "custom"

class PassengerType(str, enum.Enum):
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    SENIOR = "senior"
    STUDENT = "student"

# ============================================
# CANCELLATION POLICIES TABLE
# ============================================

class CancellationPolicy(Base):
    """Cancellation policies for services"""
    __tablename__ = "cancellation_policies"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Policy Information
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    policy_type = Column(SQLEnum(CancellationPolicyType), default=CancellationPolicyType.MODERATE)

    # Cancellation Rules (JSON structure for flexibility)
    cancellation_rules = Column(JSON, nullable=False)
    """ Example structure:
    [
        {
            "hours_before": 72,
            "refund_percentage": 100,
            "fee_amount": 0
        },
        {
            "hours_before": 48,
            "refund_percentage": 50,
            "fee_amount": 25
        },
        {
            "hours_before": 24,
            "refund_percentage": 0,
            "fee_amount": 50
        }
    ]
    """

    # Modification Rules
    modification_allowed = Column(Boolean, default=True)
    modification_deadline_hours = Column(Integer, nullable=True)
    modification_fee = Column(Numeric(10, 2), nullable=True)
    max_modifications = Column(Integer, nullable=True)

    # No-show Policy
    no_show_fee_percentage = Column(Numeric(5, 2), default=100)
    no_show_fee_amount = Column(Numeric(10, 2), nullable=True)

    # Special Conditions
    exceptions = Column(JSON, nullable=True)  # Weather, strikes, etc.
    peak_season_rules = Column(JSON, nullable=True)  # Different rules for peak season
    group_size_rules = Column(JSON, nullable=True)  # Different rules based on group size

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_cancellation_policy_code', 'code'),
        Index('idx_cancellation_policy_type', 'policy_type'),
        Index('idx_cancellation_policy_active', 'is_active'),
        Index('idx_cancellation_policy_default', 'is_default'),
    )

# ============================================
# RATES TABLE
# ============================================

class Rate(Base):
    """Rate management for services"""
    __tablename__ = "rates"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Rate Information
    rate_code = Column(String(50), nullable=True)
    rate_name = Column(String(200), nullable=False)
    rate_type = Column(SQLEnum(RateType), default=RateType.STANDARD)
    description = Column(Text, nullable=True)

    # Pricing Model
    pricing_model = Column(SQLEnum(PricingModel), nullable=False)

    # Base Pricing
    base_price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Validity Period
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=True)
    booking_window_start = Column(Date, nullable=True)  # Can only book from this date
    booking_window_end = Column(Date, nullable=True)  # Can only book until this date

    # Season
    season_type = Column(SQLEnum(SeasonType), nullable=True)

    # Capacity Constraints
    min_passengers = Column(Integer, default=1)
    max_passengers = Column(Integer, nullable=True)
    min_nights = Column(Integer, nullable=True)  # For accommodations
    max_nights = Column(Integer, nullable=True)

    # Days of Week Availability
    available_monday = Column(Boolean, default=True)
    available_tuesday = Column(Boolean, default=True)
    available_wednesday = Column(Boolean, default=True)
    available_thursday = Column(Boolean, default=True)
    available_friday = Column(Boolean, default=True)
    available_saturday = Column(Boolean, default=True)
    available_sunday = Column(Boolean, default=True)

    # Time Restrictions
    blackout_dates = Column(JSON, nullable=True)  # ["2024-12-25", "2024-01-01"]
    minimum_advance_hours = Column(Integer, default=0)  # Hours before service
    maximum_advance_days = Column(Integer, nullable=True)  # Days before service

    # Commissions and Markups
    commission_percentage = Column(Numeric(5, 2), nullable=True)
    commission_amount = Column(Numeric(10, 2), nullable=True)
    markup_percentage = Column(Numeric(5, 2), nullable=True)
    markup_amount = Column(Numeric(10, 2), nullable=True)

    # Taxes and Fees
    tax_percentage = Column(Numeric(5, 2), default=0)
    service_fee = Column(Numeric(10, 2), default=0)

    # Discounts
    early_bird_discount = Column(Numeric(5, 2), nullable=True)  # Percentage
    early_bird_days = Column(Integer, nullable=True)  # Days in advance
    last_minute_discount = Column(Numeric(5, 2), nullable=True)
    last_minute_hours = Column(Integer, nullable=True)  # Hours before service

    # Package Details (if package rate)
    includes_items = Column(JSON, nullable=True)  # List of included items/services
    package_savings = Column(Numeric(10, 2), nullable=True)

    # Priority and Sorting
    priority = Column(Integer, default=0)  # Higher priority rates shown first
    is_promotional = Column(Boolean, default=False)
    promo_code = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=False)

    # Metadata
    rate_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    service = relationship("Service", back_populates="rates")
    rate_variants = relationship("RateVariant", back_populates="rate", cascade="all, delete-orphan")
    rate_passenger_prices = relationship("RatePassengerPrice", back_populates="rate", cascade="all, delete-orphan")
    rate_tier_prices = relationship("RateTierPrice", back_populates="rate", cascade="all, delete-orphan")
    package_rates = relationship("PackageRate", back_populates="rate", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_rate_service', 'service_id'),
        Index('idx_rate_type', 'rate_type'),
        Index('idx_rate_valid_dates', 'valid_from', 'valid_to'),
        Index('idx_rate_season', 'season_type'),
        Index('idx_rate_active', 'is_active'),
        Index('idx_rate_promotional', 'is_promotional'),
        Index('idx_rate_pricing_model', 'pricing_model'),
    )

# ============================================
# RATE VARIANTS TABLE
# ============================================

class RateVariant(Base):
    """Variants of rates (e.g., different room types, meal plans)"""
    __tablename__ = "rate_variants"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)

    # Variant Information
    variant_code = Column(String(50), nullable=True)
    variant_name = Column(String(200), nullable=False)
    variant_type = Column(String(50), nullable=False)  # room_type, meal_plan, view_type, etc.
    description = Column(Text, nullable=True)

    # Pricing
    price_adjustment = Column(Numeric(15, 2), default=0)  # Addition to base price
    price_adjustment_percentage = Column(Numeric(5, 2), nullable=True)  # Or percentage

    # Inventory (for limited availability variants)
    total_inventory = Column(Integer, nullable=True)
    available_inventory = Column(Integer, nullable=True)

    # Specific Features
    features = Column(JSON, nullable=True)  # {beds: 2, view: "ocean", floor: "high"}

    # Restrictions
    min_occupancy = Column(Integer, nullable=True)
    max_occupancy = Column(Integer, nullable=True)
    requires_availability_check = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Priority
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate = relationship("Rate", back_populates="rate_variants")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_rate_variant_rate', 'rate_id'),
        Index('idx_rate_variant_type', 'variant_type'),
        Index('idx_rate_variant_active', 'is_active'),
        Index('idx_rate_variant_default', 'is_default'),
    )

# ============================================
# RATE PASSENGER PRICES TABLE
# ============================================

class RatePassengerPrice(Base):
    """Different prices based on passenger type"""
    __tablename__ = "rate_passenger_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)

    # Passenger Type
    passenger_type = Column(SQLEnum(PassengerType), nullable=False)
    age_from = Column(Integer, nullable=True)  # Minimum age for this type
    age_to = Column(Integer, nullable=True)  # Maximum age for this type

    # Pricing
    price = Column(Numeric(15, 2), nullable=False)
    is_percentage_of_adult = Column(Boolean, default=False)
    percentage_of_adult = Column(Numeric(5, 2), nullable=True)  # If child is 50% of adult

    # Conditions
    requires_adult = Column(Boolean, default=False)  # Child/infant must be with adult
    max_per_adult = Column(Integer, nullable=True)  # Max children per adult

    # Free Conditions
    is_free = Column(Boolean, default=False)
    free_up_to_age = Column(Integer, nullable=True)
    free_quantity_per_adult = Column(Integer, nullable=True)  # First N children free

    # Notes
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate = relationship("Rate", back_populates="rate_passenger_prices")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('rate_id', 'passenger_type', name='uq_rate_passenger_type'),
        Index('idx_rate_passenger_rate', 'rate_id'),
        Index('idx_rate_passenger_type', 'passenger_type'),
        Index('idx_rate_passenger_active', 'is_active'),
    )

# ============================================
# RATE TIER PRICES TABLE
# ============================================

class RateTierPrice(Base):
    """Tiered pricing based on quantity"""
    __tablename__ = "rate_tier_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)

    # Tier Information
    tier_name = Column(String(100), nullable=True)
    quantity_from = Column(Integer, nullable=False)  # Minimum quantity for this tier
    quantity_to = Column(Integer, nullable=True)  # Maximum quantity (null = unlimited)

    # Pricing
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=True)  # Fixed total for the tier
    discount_percentage = Column(Numeric(5, 2), nullable=True)  # Discount from base price

    # Conditions
    applies_to = Column(String(50), nullable=True)  # passengers, nights, units, etc.

    # Description
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate = relationship("Rate", back_populates="rate_tier_prices")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_rate_tier_rate', 'rate_id'),
        Index('idx_rate_tier_quantity', 'quantity_from', 'quantity_to'),
        Index('idx_rate_tier_active', 'is_active'),
    )

# ============================================
# PACKAGE RATES TABLE
# ============================================

class PackageRate(Base):
    """Package combinations with special pricing"""
    __tablename__ = "package_rates"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)
    included_service_id = Column(Integer, ForeignKey('services.id'), nullable=True)

    # Package Component
    component_type = Column(String(50), nullable=False)  # service, meal, activity, etc.
    component_name = Column(String(200), nullable=False)
    component_description = Column(Text, nullable=True)

    # Quantity and Timing
    quantity = Column(Integer, default=1)
    day_number = Column(Integer, nullable=True)  # For multi-day packages
    time_slot = Column(Time, nullable=True)

    # Pricing within Package
    standard_price = Column(Numeric(15, 2), nullable=True)  # Regular price if bought separately
    package_price = Column(Numeric(15, 2), nullable=True)  # Price within package
    is_included = Column(Boolean, default=True)  # Included in base price or additional

    # Options
    is_mandatory = Column(Boolean, default=True)
    is_exchangeable = Column(Boolean, default=False)  # Can be swapped for alternatives
    alternatives = Column(JSON, nullable=True)  # List of alternative service IDs

    # Display
    display_order = Column(Integer, default=0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rate = relationship("Rate", back_populates="package_rates")
    package_passenger_prices = relationship("PackageRatePassengerPrice", back_populates="package_rate", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_package_rate_rate', 'rate_id'),
        Index('idx_package_rate_service', 'included_service_id'),
        Index('idx_package_rate_type', 'component_type'),
        Index('idx_package_rate_active', 'is_active'),
        Index('idx_package_rate_order', 'display_order'),
    )

# ============================================
# PACKAGE RATE PASSENGER PRICES TABLE
# ============================================

class PackageRatePassengerPrice(Base):
    """Passenger-specific pricing for package components"""
    __tablename__ = "package_rate_passenger_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    package_rate_id = Column(Integer, ForeignKey('package_rates.id', ondelete='CASCADE'), nullable=False)

    # Passenger Type
    passenger_type = Column(SQLEnum(PassengerType), nullable=False)

    # Pricing
    price = Column(Numeric(15, 2), nullable=False)
    is_percentage_of_adult = Column(Boolean, default=False)
    percentage_of_adult = Column(Numeric(5, 2), nullable=True)

    # Conditions
    is_included = Column(Boolean, default=True)
    is_optional = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    package_rate = relationship("PackageRate", back_populates="package_passenger_prices")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('package_rate_id', 'passenger_type', name='uq_package_rate_passenger'),
        Index('idx_package_passenger_rate', 'package_rate_id'),
        Index('idx_package_passenger_type', 'passenger_type'),
        Index('idx_package_passenger_active', 'is_active'),
    )

# ============================================
# SERVICE DAILY CAPACITY TABLE
# ============================================

class ServiceDailyCapacity(Base):
    """Daily capacity tracking for services"""
    __tablename__ = "service_daily_capacity"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Date
    capacity_date = Column(Date, nullable=False)

    # Capacity
    total_capacity = Column(Integer, nullable=False)
    used_capacity = Column(Integer, default=0)
    available_capacity = Column(Integer, nullable=False)
    reserved_capacity = Column(Integer, default=0)  # Held but not confirmed

    # Status
    is_available = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True)

    # Price Override
    price_override = Column(Numeric(15, 2), nullable=True)
    price_adjustment_percentage = Column(Numeric(5, 2), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('service_id', 'capacity_date', name='uq_service_daily_capacity'),
        Index('idx_daily_capacity_service', 'service_id'),
        Index('idx_daily_capacity_date', 'capacity_date'),
        Index('idx_daily_capacity_available', 'is_available'),
        Index('idx_daily_capacity_blocked', 'is_blocked'),
    )

# ============================================
# SERVICE PARTICIPANTS TABLE
# ============================================

class ServiceParticipant(Base):
    """Track participants in service bookings"""
    __tablename__ = "service_participants"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    booking_line_id = Column(Integer, ForeignKey('booking_lines.id', ondelete='CASCADE'), nullable=False)
    passenger_id = Column(Integer, ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False)

    # Participation Details
    participation_date = Column(Date, nullable=False)
    participant_type = Column(SQLEnum(PassengerType), nullable=False)

    # Check-in Status
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Service Execution
    participated = Column(Boolean, default=False)
    no_show = Column(Boolean, default=False)
    participation_notes = Column(Text, nullable=True)

    # Special Requirements
    special_requirements = Column(JSON, nullable=True)
    seat_assignment = Column(String(50), nullable=True)
    group_assignment = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('booking_line_id', 'passenger_id', name='uq_service_participant'),
        Index('idx_participant_service', 'service_id'),
        Index('idx_participant_booking', 'booking_line_id'),
        Index('idx_participant_passenger', 'passenger_id'),
        Index('idx_participant_date', 'participation_date'),
        Index('idx_participant_checkin', 'checked_in'),
    )
