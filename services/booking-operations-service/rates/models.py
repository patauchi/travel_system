"""
Rates module models
Contains rate-related models and database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import RateType, PricingModel, SeasonType, PassengerType

# ============================================
# RATES TABLE
# ============================================

class Rate(Base):
    """Service rates and pricing management"""
    __tablename__ = "rates"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Rate Information
    rate_code = Column(String(50), nullable=True)  # RAT-CUZ-001, RAT-TRANS-001
    name = Column(String(200), nullable=False)  # "Tarifa Regular 2025", "Tarifa Alta Temporada"
    description = Column(Text, nullable=True)

    # Pricing model
    pricing_model = Column(SQLEnum(PricingModel), nullable=False)

    # Validity period
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)

    # Season and schedule
    season_type = Column(SQLEnum(SeasonType), default=SeasonType.LOW)
    applicable_days = Column(JSON, nullable=True)  # [1,2,3,4,5] días de la semana
    blocked_dates = Column(JSON, nullable=True)  # fechas específicas bloqueadas

    # Currency
    currency = Column(String(3), default='USD')  # USD, EUR, GBP, JPY, PEN, etc.

    # Additional configuration
    rate_metadata = Column(JSON, nullable=True)  # datos adicionales

    # Status
    is_active = Column(Boolean, default=True)
    is_promotional = Column(Boolean, default=False)
    priority = Column(Integer, default=0)  # para ordenar múltiples rates

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    service = relationship("Service", back_populates="rates")
    rate_variants = relationship("RateVariant", back_populates="rate", cascade="all, delete-orphan")
    rate_passenger_prices = relationship("RatePassengerPrice", back_populates="rate", cascade="all, delete-orphan")
    rate_tier_prices = relationship("RateTierPrice", back_populates="rate", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('service_id', 'rate_code', name='uq_service_rate_code'),
        Index('idx_rate_service_active', 'service_id', 'is_active'),
        Index('idx_rate_validity', 'valid_from', 'valid_to'),
        Index('idx_rate_service_season', 'service_id', 'season_type'),
        Index('idx_rate_validity_active', 'service_id', 'valid_from', 'valid_to', 'is_active'),
        Index('idx_rate_pricing_model', 'pricing_model'),
        Index('idx_rate_priority', 'priority'),
    )

    def __repr__(self):
        return f"<Rate(id={self.id}, service_id={self.service_id}, code='{self.rate_code}', name='{self.name}')>"

    def is_valid_for_date(self, check_date):
        """Check if rate is valid for a specific date"""
        return self.valid_from <= check_date <= self.valid_to

    def is_applicable_for_day(self, day_of_week):
        """Check if rate applies to a specific day of week (1=Monday, 7=Sunday)"""
        if not self.applicable_days:
            return True
        return day_of_week in self.applicable_days

    def is_date_blocked(self, check_date):
        """Check if a specific date is blocked"""
        if not self.blocked_dates:
            return False
        return check_date.isoformat() in self.blocked_dates


# ============================================
# RATE VARIANTS TABLE
# ============================================

class RateVariant(Base):
    """Rate variants for different service configurations"""
    __tablename__ = "rate_variants"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)

    # Variant Information
    variant_code = Column(String(50), nullable=False)  # H1, SPRINTER, SPRINTER_LARGE
    variant_name = Column(String(255), nullable=False)  # "H1 (1-4 personas)", "Sprinter (4-10 personas)"
    description = Column(Text, nullable=True)

    # Additional specifications
    specifications = Column(JSON, nullable=True)  # {"tipo": "vehiculo", "capacidad": 4}

    # Availability
    is_default = Column(Boolean, default=False)  # Variante por defecto
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)  # Orden de presentación

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rate = relationship("Rate", back_populates="rate_variants")
    rate_passenger_prices = relationship("RatePassengerPrice", back_populates="variant", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('rate_id', 'variant_code', name='uq_rate_variant_code'),
        Index('idx_rate_variant_rate_active', 'rate_id', 'is_active'),
        Index('idx_rate_variant_code', 'variant_code'),
        Index('idx_rate_variant_display_order', 'display_order'),
    )

    def __repr__(self):
        return f"<RateVariant(id={self.id}, rate_id={self.rate_id}, code='{self.variant_code}', name='{self.variant_name}')>"


# ============================================
# RATE PASSENGER PRICES TABLE
# ============================================

class RatePassengerPrice(Base):
    """Passenger-specific pricing within rates"""
    __tablename__ = "rate_passenger_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(Integer, ForeignKey('rate_variants.id', ondelete='CASCADE'), nullable=True)

    # Passenger category
    passenger_category = Column(SQLEnum(PassengerType), default=PassengerType.ADULT)

    # Nationality differentiation
    nationality_type = Column(String(20), default='all')  # local, foreign, all

    # Pricing options
    price = Column(Numeric(10, 2), nullable=True)  # Precio absoluto
    discount_percentage = Column(Numeric(5, 2), nullable=True)  # O descuento sobre precio base
    discount_amount = Column(Numeric(10, 2), nullable=True)

    # Special conditions
    requires_documentation = Column(Boolean, default=False)  # Requiere documento (ISIC, etc)
    documentation_types = Column(JSON, nullable=True)  # ["ISIC", "DNI", "PASSPORT"]
    special_conditions = Column(JSON, nullable=True)  # Condiciones adicionales

    # Age validation (override passenger_type defaults if needed)
    min_age_override = Column(Integer, nullable=True)
    max_age_override = Column(Integer, nullable=True)

    # Group requirements
    min_passengers = Column(Integer, default=1)  # Mínimo de este tipo de pasajero
    max_passengers = Column(Integer, nullable=True)  # Máximo de este tipo de pasajero
    requires_adult_supervision = Column(Boolean, default=False)  # Para menores

    # Availability
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # Notes
    notes = Column(Text, nullable=True)  # Notas internas
    public_notes = Column(Text, nullable=True)  # Notas para mostrar al cliente

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rate = relationship("Rate", back_populates="rate_passenger_prices")
    variant = relationship("RateVariant", back_populates="rate_passenger_prices")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_rate_passenger_price_rate_active', 'rate_id', 'is_active'),
        Index('idx_rate_passenger_price_variant_active', 'variant_id', 'is_active'),
        Index('idx_rate_passenger_price_nationality', 'nationality_type'),
        Index('idx_rate_passenger_price_display_order', 'display_order'),
        Index('idx_rate_passenger_price_category', 'passenger_category'),
    )

    def __repr__(self):
        return f"<RatePassengerPrice(id={self.id}, rate_id={self.rate_id}, category='{self.passenger_category}', price={self.price})>"

    def calculate_final_price(self, base_price=None):
        """Calculate final price based on pricing rules"""
        if self.price is not None:
            return self.price

        if base_price is None:
            return None

        if self.discount_percentage is not None:
            return base_price * (1 - self.discount_percentage / 100)

        if self.discount_amount is not None:
            return max(0, base_price - self.discount_amount)

        return base_price


# ============================================
# RATE TIER PRICES TABLE
# ============================================

class RateTierPrice(Base):
    """Tiered pricing based on group size or quantity"""
    __tablename__ = "rate_tier_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    rate_id = Column(Integer, ForeignKey('rates.id', ondelete='CASCADE'), nullable=False)

    # Tier Configuration
    tier_name = Column(String(100), nullable=False)  # "1-4 personas", "5-10 personas"
    min_quantity = Column(Integer, nullable=False)
    max_quantity = Column(Integer, nullable=True)  # NULL = sin límite superior

    # Pricing
    price_per_unit = Column(Numeric(12, 2), nullable=True)  # Precio por unidad en este tier
    fixed_price = Column(Numeric(12, 2), nullable=True)  # Precio fijo para el tier completo
    discount_percentage = Column(Numeric(5, 2), nullable=True)  # Descuento sobre precio base

    # Conditions
    apply_to_passenger_types = Column(JSON, nullable=True)  # ["adult", "child"] - a qué tipos aplica
    special_conditions = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # Notes
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rate = relationship("Rate", back_populates="rate_tier_prices")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_rate_tier_price_rate_active', 'rate_id', 'is_active'),
        Index('idx_rate_tier_price_quantity', 'min_quantity', 'max_quantity'),
        Index('idx_rate_tier_price_display_order', 'display_order'),
    )

    def __repr__(self):
        return f"<RateTierPrice(id={self.id}, rate_id={self.rate_id}, tier='{self.tier_name}', min={self.min_quantity}, max={self.max_quantity})>"

    def applies_to_quantity(self, quantity):
        """Check if this tier applies to a given quantity"""
        if quantity < self.min_quantity:
            return False
        if self.max_quantity is not None and quantity > self.max_quantity:
            return False
        return True


# ============================================
# PACKAGE RATES TABLE
# ============================================

class PackageRate(Base):
    """Package rates for multiple services"""
    __tablename__ = "package_rates"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Package Information
    package_code = Column(String(50), nullable=True)
    package_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Services included (JSON array of service IDs)
    included_services = Column(JSON, nullable=False)  # [service_id1, service_id2, ...]

    # Package pricing
    package_price = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Validity
    valid_from = Column(Date, nullable=False)
    valid_to = Column(Date, nullable=False)

    # Package conditions
    min_passengers = Column(Integer, default=1)
    max_passengers = Column(Integer, nullable=True)
    min_duration_days = Column(Integer, default=1)

    # Booking conditions
    advance_booking_days = Column(Integer, default=0)
    cancellation_policy_id = Column(Integer, ForeignKey('cancellation_policies.id'), nullable=True)

    # Discounts and promotions
    early_bird_discount_percentage = Column(Numeric(5, 2), nullable=True)
    early_bird_days_before = Column(Integer, nullable=True)
    group_discount_threshold = Column(Integer, nullable=True)
    group_discount_percentage = Column(Numeric(5, 2), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    priority = Column(Integer, default=0)

    # Additional data
    inclusions = Column(JSON, nullable=True)  # What's included in the package
    exclusions = Column(JSON, nullable=True)  # What's not included
    special_conditions = Column(JSON, nullable=True)
    package_rate_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    cancellation_policy = relationship("CancellationPolicy")
    package_passenger_prices = relationship("PackageRatePassengerPrice", back_populates="package_rate", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('package_code', 'deleted_at', name='uq_package_code_deleted'),
        Index('idx_package_rate_validity', 'valid_from', 'valid_to'),
        Index('idx_package_rate_active', 'is_active'),
        Index('idx_package_rate_featured', 'is_featured'),
        Index('idx_package_rate_priority', 'priority'),
    )

    def __repr__(self):
        return f"<PackageRate(id={self.id}, code='{self.package_code}', name='{self.package_name}')>"


# ============================================
# PACKAGE RATE PASSENGER PRICES TABLE
# ============================================

class PackageRatePassengerPrice(Base):
    """Passenger-specific pricing for package rates"""
    __tablename__ = "package_rate_passenger_prices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    package_rate_id = Column(Integer, ForeignKey('package_rates.id', ondelete='CASCADE'), nullable=False)

    # Passenger category
    passenger_category = Column(SQLEnum(PassengerType), default=PassengerType.ADULT)

    # Pricing
    price = Column(Numeric(12, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=True)  # Descuento sobre precio adulto

    # Age validation
    min_age = Column(Integer, nullable=True)
    max_age = Column(Integer, nullable=True)

    # Special conditions
    requires_adult_supervision = Column(Boolean, default=False)
    special_conditions = Column(JSON, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    package_rate = relationship("PackageRate", back_populates="package_passenger_prices")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_package_passenger_price_package_active', 'package_rate_id', 'is_active'),
        Index('idx_package_passenger_price_category', 'passenger_category'),
        Index('idx_package_passenger_price_display_order', 'display_order'),
    )

    def __repr__(self):
        return f"<PackageRatePassengerPrice(id={self.id}, package_rate_id={self.package_rate_id}, category='{self.passenger_category}', price={self.price})>"
