"""
Services module models
Contains the Service model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import ServiceType, OperationModel, PassengerType

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

    # Basic Information
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    service_type = Column(SQLEnum(ServiceType), nullable=False, index=True)
    operation_model = Column(SQLEnum(OperationModel), default=OperationModel.no_defined)

    # Service Configuration
    allowed_destinations = Column(JSON, nullable=True)  # destination ids [1, 3, 5, 9]
    duration_hours = Column(Numeric(10, 2), nullable=True)  # Service duration in hours
    min_participants = Column(Integer, nullable=True)
    max_participants = Column(Integer, nullable=True)

    # Booking Configuration
    advance_booking_hours = Column(Integer, nullable=True)  # Minimum advance booking required
    cutoff_hours = Column(Integer, nullable=True)  # Booking cutoff time

    # Status and Visibility
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)

    # Metadata
    service_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    supplier = relationship("Supplier", back_populates="services")
    cancellation_policy = relationship("CancellationPolicy")

    # Service-specific relationships
    transfer_service = relationship("TransferService", back_populates="service", uselist=False)
    tour_service = relationship("TourService", back_populates="service", uselist=False)
    transport_service = relationship("TransportService", back_populates="service", uselist=False)
    restaurant_service = relationship("RestaurantService", back_populates="service", uselist=False)
    ticket_service = relationship("TicketService", back_populates="service", uselist=False)
    guide_service = relationship("GuideService", back_populates="service", uselist=False)
    equipment_service = relationship("EquipmentService", back_populates="service", uselist=False)

    # Operational relationships
    service_availability = relationship("ServiceAvailability", back_populates="service", cascade="all, delete-orphan")
    service_daily_capacity = relationship("ServiceDailyCapacity", back_populates="service", cascade="all, delete-orphan")
    service_participants = relationship("ServiceParticipant", back_populates="service", cascade="all, delete-orphan")
    rates = relationship("Rate", back_populates="service", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('supplier_id', 'code', 'deleted_at', name='uq_service_supplier_code_deleted'),
        Index('idx_service_supplier', 'supplier_id'),
        Index('idx_service_type', 'service_type'),
        Index('idx_service_active', 'is_active'),
        Index('idx_service_featured', 'is_featured'),
        Index('idx_service_deleted', 'deleted_at'),
        Index('idx_service_name', 'name'),
    )

    def __repr__(self):
        return f"<Service(id={self.id}, code='{self.code}', name='{self.name}', type='{self.service_type}')>"

# ============================================
# SERVICE AVAILABILITY TABLE
# ============================================

class ServiceAvailability(Base):
    """Service availability tracking"""
    __tablename__ = "service_availability"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Availability Information
    date = Column(DateTime(timezone=True), nullable=False)
    total_capacity = Column(Integer, nullable=False, default=0)
    booked_capacity = Column(Integer, nullable=False, default=0)
    blocked_capacity = Column(Integer, nullable=False, default=0)
    available_capacity = Column(Integer, nullable=False, default=0)

    # Status
    is_available = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)

    # Metadata
    availability_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service", back_populates="service_availability")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('service_id', 'date', name='uq_service_availability_date'),
        Index('idx_availability_service', 'service_id'),
        Index('idx_availability_date', 'date'),
        Index('idx_availability_status', 'is_available'),
    )

    def __repr__(self):
        return f"<ServiceAvailability(id={self.id}, service_id={self.service_id}, date='{self.date}', available={self.available_capacity})>"


# ============================================
# SERVICE DAILY CAPACITY TABLE
# ============================================

class ServiceDailyCapacity(Base):
    """Daily capacity and availability tracking for services"""
    __tablename__ = "service_daily_capacity"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)

    # Date and capacity
    service_date = Column(Date, nullable=False)
    total_capacity = Column(Integer, nullable=False, default=0)
    booked_capacity = Column(Integer, nullable=False, default=0)
    blocked_capacity = Column(Integer, nullable=False, default=0)
    available_capacity = Column(Integer, nullable=False, default=0)

    # Time-specific capacity (for services with multiple time slots)
    time_slot = Column(String(20), nullable=True)  # "09:00", "14:30", "all_day"

    # Pricing override for this specific date
    rate_override_id = Column(Integer, nullable=True)  # References rates.id
    price_override = Column(Numeric(12, 2), nullable=True)

    # Status
    is_available = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String(255), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    operational_notes = Column(Text, nullable=True)

    # Metadata
    service_daily_capacity_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service = relationship("Service")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('service_id', 'service_date', 'time_slot', name='uq_service_date_time'),
        Index('idx_service_capacity_service_date', 'service_id', 'service_date'),
        Index('idx_service_capacity_date', 'service_date'),
        Index('idx_service_capacity_available', 'is_available'),
        Index('idx_service_capacity_blocked', 'is_blocked'),
    )

    def __repr__(self):
        return f"<ServiceDailyCapacity(id={self.id}, service_id={self.service_id}, date='{self.service_date}', capacity={self.available_capacity}/{self.total_capacity})>"

    def update_availability(self):
        """Update available capacity based on total, booked, and blocked"""
        self.available_capacity = max(0, self.total_capacity - self.booked_capacity - self.blocked_capacity)
        self.is_available = self.available_capacity > 0 and not self.is_blocked

    def can_book(self, requested_capacity):
        """Check if requested capacity can be booked"""
        return self.is_available and self.available_capacity >= requested_capacity


# ============================================
# SERVICE PARTICIPANTS TABLE
# ============================================

class ServiceParticipant(Base):
    """Track participants in services for capacity management"""
    __tablename__ = "service_participants"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    booking_line_id = Column(Integer, ForeignKey('booking_lines.id', ondelete='CASCADE'), nullable=False)
    passenger_id = Column(Integer, ForeignKey('passengers.id', ondelete='RESTRICT'), nullable=False)

    # Service details
    service_date = Column(Date, nullable=False)
    time_slot = Column(String(20), nullable=True)

    # Participant status
    participation_status = Column(String(20), default='confirmed')  # confirmed, cancelled, no_show, completed
    check_in_status = Column(String(20), default='pending')  # pending, checked_in, no_show

    # Participant information
    passenger_type = Column(SQLEnum(PassengerType), default=PassengerType.adult)
    special_requirements = Column(JSON, nullable=True)

    # Pricing information
    rate_applied_id = Column(Integer, nullable=True)  # References rates.id
    price_paid = Column(Numeric(12, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    service = relationship("Service")
    booking_line = relationship("BookingLine")
    passenger = relationship("Passenger")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('service_id', 'booking_line_id', 'passenger_id', 'service_date', name='uq_service_participant'),
        Index('idx_service_participant_service_date', 'service_id', 'service_date'),
        Index('idx_service_participant_booking', 'booking_line_id'),
        Index('idx_service_participant_passenger', 'passenger_id'),
        Index('idx_service_participant_status', 'participation_status'),
        Index('idx_service_participant_check_in', 'check_in_status'),
    )

    def __repr__(self):
        return f"<ServiceParticipant(id={self.id}, service_id={self.service_id}, passenger_id={self.passenger_id}, date='{self.service_date}', status='{self.participation_status}')>"
