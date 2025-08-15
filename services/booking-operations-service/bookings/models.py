"""
Bookings module models
Contains booking-related models and database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import BookingOverallStatus, BookingLineStatus, RiskLevel

# ============================================
# BOOKINGS TABLE
# ============================================

class Booking(Base):
    """Main booking management table"""
    __tablename__ = "bookings"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    order_id = Column(Integer, nullable=False)  # References orders.id from financial service

    # Booking Identification
    booking_number = Column(String(50), nullable=False, unique=True, index=True)  # BK-2025-00001
    external_reference = Column(String(100), nullable=True)

    # Overall Status
    overall_status = Column(SQLEnum(BookingOverallStatus), default=BookingOverallStatus.pending, index=True)

    # Progress Tracking
    total_services = Column(Integer, default=0)
    confirmed_services = Column(Integer, default=0)
    cancelled_services = Column(Integer, default=0)
    pending_services = Column(Integer, default=0)

    # Passenger Information
    total_passengers = Column(Integer, default=0)
    adults_count = Column(Integer, default=0)
    children_count = Column(Integer, default=0)
    infants_count = Column(Integer, default=0)
    passenger_manifest = Column(JSON, nullable=True)  # Full passenger details

    # Important Dates
    travel_start_date = Column(Date, nullable=True)
    travel_end_date = Column(Date, nullable=True)

    # Documentation
    travel_documents = Column(JSON, nullable=True)  # {passports: [passenger_ids], visas: [], insurance: []}
    documents_complete = Column(Boolean, default=False)
    documents_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Communication
    confirmation_emails_sent = Column(JSON, nullable=True)  # Track sent confirmations
    reminder_schedule = Column(JSON, nullable=True)  # Scheduled reminders
    last_customer_notification = Column(DateTime(timezone=True), nullable=True)

    # Special Requirements
    special_requirements = Column(Text, nullable=True)
    dietary_restrictions = Column(JSON, nullable=True)
    emergency_contacts = Column(Text, nullable=True)

    # Financial Summary (calculated from booking lines)
    total_amount = Column(Numeric(15, 2), default=0)
    total_paid = Column(Numeric(15, 2), default=0)
    total_commission = Column(Numeric(15, 2), default=0)
    currency = Column(String(3), default="USD")

    # Metadata
    booking_metadata = Column(JSON, nullable=True)  # Additional flexible data

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking_lines = relationship("BookingLine", back_populates="booking", cascade="all, delete-orphan")
    booking_passengers = relationship("BookingPassenger", back_populates="booking", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_booking_overall_status_travel_start', 'overall_status', 'travel_start_date'),
        Index('idx_booking_order_status', 'order_id', 'overall_status'),
        Index('idx_booking_travel_start', 'travel_start_date'),
        Index('idx_booking_travel_end', 'travel_end_date'),
        UniqueConstraint('booking_number', 'deleted_at', name='uq_booking_number_deleted'),
    )

    def __repr__(self):
        return f"<Booking(id={self.id}, number='{self.booking_number}', status='{self.overall_status}')>"

    def calculate_progress_percentage(self):
        """Calculate booking completion percentage"""
        if self.total_services == 0:
            return 0
        return (self.confirmed_services / self.total_services) * 100

    def is_fully_confirmed(self):
        """Check if all services are confirmed"""
        return self.confirmed_services == self.total_services and self.total_services > 0

    def has_cancelled_services(self):
        """Check if booking has any cancelled services"""
        return self.cancelled_services > 0


# ============================================
# BOOKING LINES TABLE
# ============================================

class BookingLine(Base):
    """Individual service lines within a booking"""
    __tablename__ = "booking_lines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    order_line_id = Column(Integer, unique=True, nullable=False)  # References order_lines.id
    handled_by = Column(Integer, nullable=True)  # References users.id

    # Booking Status
    booking_status = Column(SQLEnum(BookingLineStatus), default=BookingLineStatus.pending)

    # Supplier Confirmation
    supplier_confirmation_code = Column(String(100), nullable=True)
    supplier_booking_reference = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_with = Column(String(100), nullable=True)  # Contact person at supplier
    supplier_response = Column(JSON, nullable=True)  # Full API/email response

    # Booking Details
    booking_method = Column(String(50), nullable=True)  # api, email, phone, portal
    booking_platform = Column(String(100), nullable=True)  # Which system/API used
    booking_requested_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_attempts = Column(Integer, default=0)
    last_confirmation_attempt = Column(DateTime(timezone=True), nullable=True)

    # Service Execution Details
    service_confirmed_start = Column(DateTime(timezone=True), nullable=True)  # Confirmed start time by supplier
    service_confirmed_end = Column(DateTime(timezone=True), nullable=True)  # Confirmed end time by supplier
    pickup_confirmation = Column(String(255), nullable=True)  # Specific pickup details
    service_specifics = Column(JSON, nullable=True)  # {room_number, seat_numbers, etc}

    # Documentation
    voucher_number = Column(String(100), nullable=True)
    voucher_url = Column(String(500), nullable=True)
    ticket_number = Column(String(100), nullable=True)
    booking_documents = Column(JSON, nullable=True)  # URLs/paths to confirmations

    last_modified_at = Column(DateTime(timezone=True), nullable=True)
    modification_count = Column(Integer, default=0)

    # Cancellation Details
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    cancellation_code = Column(String(50), nullable=True)  # Supplier cancellation code
    cancellation_fee = Column(Numeric(15, 2), nullable=True)
    cancellation_confirmed = Column(Boolean, default=False)

    # Risk and Alerts
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.low)

    # Notes
    booking_notes = Column(Text, nullable=True)  # Notes about the booking process
    supplier_notes = Column(Text, nullable=True)  # Notes from/about supplier
    operational_notes = Column(Text, nullable=True)  # Notes for operations team

    # Metadata
    booking_line_metadata = Column(JSON, nullable=True)  # Flexible additional data

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="booking_lines")
    service_operations = relationship("ServiceOperation", back_populates="booking_line", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_booking_line_booking_status', 'booking_id', 'booking_status'),
        Index('idx_booking_line_status_created', 'booking_status', 'created_at'),
        Index('idx_booking_line_risk_level', 'risk_level'),
        Index('idx_booking_line_service_start', 'service_confirmed_start'),
    )

    def __repr__(self):
        return f"<BookingLine(id={self.id}, booking_id={self.booking_id}, status='{self.booking_status}')>"

    def is_confirmed(self):
        """Check if booking line is confirmed"""
        return self.booking_status == BookingLineStatus.confirmed

    def is_cancelled(self):
        """Check if booking line is cancelled"""
        return self.booking_status == BookingLineStatus.cancelled

    def needs_reconfirmation(self):
        """Check if booking line needs reconfirmation"""
        return self.booking_status in [BookingLineStatus.pending, BookingLineStatus.confirming]


# ============================================
# BOOKING PASSENGERS TABLE
# ============================================

class BookingPassenger(Base):
    """Links passengers to bookings with specific roles and details"""
    __tablename__ = "booking_passengers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core Relationships
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    booking_line_id = Column(Integer, ForeignKey('booking_lines.id', ondelete='CASCADE'), nullable=False)
    passenger_id = Column(Integer, ForeignKey('passengers.id', ondelete='RESTRICT'), nullable=False)

    # Context References
    account_id = Column(Integer, nullable=False)  # References accounts.id
    order_id = Column(Integer, nullable=False)  # References orders.id
    order_line_id = Column(Integer, nullable=False)  # References order_lines.id

    # Passenger Type for this Service
    passenger_type = Column(SQLEnum(BookingLineStatus), default='adult')  # adult, child, infant, student, senior
    age_at_travel = Column(Integer, nullable=True)  # Calculated age at travel date
    is_lead_passenger = Column(Boolean, default=False)

    # Pricing for this Passenger/Service
    passenger_price = Column(Numeric(12, 2), default=0)  # What we charge
    passenger_cost = Column(Numeric(12, 2), default=0)  # What we pay supplier
    commission_amount = Column(Numeric(12, 2), default=0)
    price_type = Column(String(50), nullable=True)  # 'per_person', 'shared', 'free', 'supplement'
    price_notes = Column(Text, nullable=True)  # "Free infant on lap", "Child discount applied"

    # Service Status
    confirmation_status = Column(SQLEnum(BookingLineStatus), default=BookingLineStatus.pending)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_reference = Column(String(100), nullable=True)  # Supplier confirmation for this pax

    # Check-in/Attendance
    check_in_status = Column(String(20), default='pending')  # not_required, pending, checked_in, no_show, late, cancelled
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    checked_in_by = Column(String(100), nullable=True)  # User or system that checked in

    # Documents for this Service
    documents_required = Column(Boolean, default=False)
    documents_verified = Column(Boolean, default=False)
    documents_verified_at = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    booking_passenger_metadata = Column(JSON, nullable=True)  # Flexible field for additional data

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="booking_passengers")
    passenger = relationship("Passenger", back_populates="booking_passengers")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('booking_line_id', 'passenger_id', 'deleted_at', name='uq_booking_line_passenger_deleted'),
        Index('idx_booking_passenger_booking', 'booking_id', 'passenger_id'),
        Index('idx_booking_passenger_passenger', 'passenger_id', 'account_id'),
        Index('idx_booking_passenger_account_status', 'account_id', 'confirmation_status'),
        Index('idx_booking_passenger_order', 'order_id'),
        Index('idx_booking_passenger_check_in', 'check_in_status'),
        Index('idx_booking_passenger_travel_history', 'passenger_id', 'created_at'),
        Index('idx_booking_passenger_lead', 'is_lead_passenger', 'booking_id'),
    )

    def __repr__(self):
        return f"<BookingPassenger(id={self.id}, booking_id={self.booking_id}, passenger_id={self.passenger_id}, type='{self.passenger_type}')>"

    def is_checked_in(self):
        """Check if passenger is checked in"""
        return self.check_in_status == 'checked_in'

    def is_confirmed(self):
        """Check if passenger is confirmed for the service"""
        return self.confirmation_status == BookingLineStatus.confirmed

    def calculate_commission(self):
        """Calculate commission amount based on price difference"""
        return self.passenger_price - self.passenger_cost
