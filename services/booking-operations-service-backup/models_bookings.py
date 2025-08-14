"""
Booking Operations Service Models - Bookings and Passengers
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

class BookingOverallStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    PARTIALLY_CANCELLED = "partially_cancelled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class BookingLineStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    MODIFIED = "modified"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PassengerGender(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVER_LICENSE = "driver_license"
    BIRTH_CERTIFICATE = "birth_certificate"
    OTHER = "other"

class LoyaltyTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

class ServiceOperationStatus(str, enum.Enum):
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"
    INCIDENT = "incident"

class OperationalAlert(str, enum.Enum):
    NONE = "none"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    SUPPLIER_ISSUE = "supplier_issue"
    PASSENGER_ISSUE = "passenger_issue"
    DOCUMENTATION = "documentation"
    PAYMENT = "payment"
    OTHER = "other"

# ============================================
# COUNTRIES TABLE
# ============================================

class Country(Base):
    """Countries reference table"""
    __tablename__ = "countries"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Country Information
    code = Column(String(2), nullable=False, unique=True)  # ISO 3166-1 alpha-2
    code3 = Column(String(3), nullable=False, unique=True)  # ISO 3166-1 alpha-3
    name = Column(String(100), nullable=False)
    official_name = Column(String(200), nullable=True)
    native_name = Column(String(100), nullable=True)

    # Geographic Information
    continent = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    subregion = Column(String(100), nullable=True)
    capital = Column(String(100), nullable=True)

    # Additional Information
    currency_code = Column(String(3), nullable=True)
    phone_code = Column(String(10), nullable=True)
    timezone_codes = Column(JSON, nullable=True)  # Array of timezone codes
    languages = Column(JSON, nullable=True)  # Array of language codes

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    destinations = relationship("Destination", back_populates="country", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_country_code', 'code'),
        Index('idx_country_active', 'is_active'),
        Index('idx_country_continent', 'continent'),
    )

# ============================================
# DESTINATIONS TABLE
# ============================================

class Destination(Base):
    """Travel destinations"""
    __tablename__ = "destinations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    parent_destination_id = Column(Integer, ForeignKey('destinations.id'), nullable=True)

    # Destination Information
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # city, region, area, district, landmark

    # Geographic Information
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    altitude_meters = Column(Integer, nullable=True)
    timezone = Column(String(50), nullable=True)

    # Description
    description = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)
    best_time_to_visit = Column(JSON, nullable=True)  # {months: [1,2,3], notes: "..."}

    # Travel Information
    airport_codes = Column(JSON, nullable=True)  # ["LIM", "CUZ"]
    nearest_airport_distance_km = Column(Numeric(10, 2), nullable=True)
    requires_special_permit = Column(Boolean, default=False)

    # Tourism Data
    tourism_rating = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00
    safety_rating = Column(Numeric(3, 2), nullable=True)
    popularity_score = Column(Integer, nullable=True)  # 1-100

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Metadata
    destination_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    country = relationship("Country", back_populates="destinations")
    parent_destination = relationship("Destination", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('code', 'deleted_at', name='uq_destination_code_deleted'),
        Index('idx_destination_country', 'country_id'),
        Index('idx_destination_parent', 'parent_destination_id'),
        Index('idx_destination_type', 'type'),
        Index('idx_destination_active', 'is_active'),
        Index('idx_destination_featured', 'is_featured'),
    )

# ============================================
# PASSENGERS TABLE
# ============================================

class Passenger(Base):
    """Passenger information for bookings"""
    __tablename__ = "passengers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Personal Information
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(PassengerGender), nullable=True)
    nationality = Column(String(2), nullable=True)  # ISO country code

    # Document Information
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.PASSPORT)
    document_number = Column(String(50), nullable=False)
    document_issue_date = Column(Date, nullable=True)
    document_expiry_date = Column(Date, nullable=True)
    document_issuing_country = Column(String(2), nullable=True)  # ISO country code

    # Linkage to CRM Contact
    contact_id = Column(Integer, nullable=True)  # References contacts.id from CRM service

    # Travel Metrics
    total_trips = Column(Integer, default=0)
    total_spent = Column(Numeric(15, 2), default=0)
    first_travel_date = Column(Date, nullable=True)
    last_travel_date = Column(Date, nullable=True)
    is_frequent_traveler = Column(Boolean, default=False)
    loyalty_tier = Column(SQLEnum(LoyaltyTier), nullable=True)

    # Emergency Contact
    emergency_contact = Column(JSON, nullable=True)  # {name, relationship, phone, email}

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking_passengers = relationship("BookingPassenger", back_populates="passenger", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('document_type', 'document_number', 'deleted_at', name='uq_passenger_document_deleted'),
        Index('idx_passenger_contact', 'contact_id'),
        Index('idx_passenger_name', 'last_name', 'first_name', 'date_of_birth'),
        Index('idx_passenger_loyalty', 'loyalty_tier'),
        Index('idx_passenger_travel', 'last_travel_date'),
        Index('idx_passenger_frequent', 'is_frequent_traveler'),
        Index('idx_passenger_nationality', 'nationality'),
    )

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
    booking_number = Column(String(50), nullable=False)  # BK-2025-00001

    # Overall Status
    overall_status = Column(SQLEnum(BookingOverallStatus), default=BookingOverallStatus.PENDING, index=True)

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
    travel_documents = Column(JSON, nullable=True)  # {passports: [ids], visas: [], insurance: []}
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
    currency = Column(String(3), default='USD')

    # Metadata
    booking_metadata = Column(JSON, nullable=True)  # Additional flexible data

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking_lines = relationship("BookingLine", back_populates="booking", cascade="all, delete-orphan")
    booking_passengers = relationship("BookingPassenger", back_populates="booking", cascade="all, delete-orphan")
    service_operations = relationship("ServiceOperation", back_populates="booking", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('booking_number', 'deleted_at', name='uq_booking_number_deleted'),
        Index('idx_booking_status_travel', 'overall_status', 'travel_start_date'),
        Index('idx_booking_order_status', 'order_id', 'overall_status'),
        Index('idx_booking_travel_start', 'travel_start_date'),
        Index('idx_booking_travel_end', 'travel_end_date'),
    )

# ============================================
# BOOKING LINES TABLE
# ============================================

class BookingLine(Base):
    """Individual service bookings within a main booking"""
    __tablename__ = "booking_lines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    order_line_id = Column(Integer, nullable=False, unique=True)  # References order_lines.id from financial service
    handled_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Booking Status
    booking_status = Column(SQLEnum(BookingLineStatus), default=BookingLineStatus.PENDING)

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
    service_confirmed_start = Column(DateTime(timezone=True), nullable=True)
    service_confirmed_end = Column(DateTime(timezone=True), nullable=True)
    pickup_confirmation = Column(String(255), nullable=True)
    service_specifics = Column(JSON, nullable=True)  # {room_number, seat_numbers, etc}

    # Documentation
    voucher_number = Column(String(100), nullable=True)
    voucher_url = Column(String(500), nullable=True)
    ticket_number = Column(String(100), nullable=True)
    booking_documents = Column(JSON, nullable=True)  # URLs/paths to confirmations

    # Modification Tracking
    last_modified_at = Column(DateTime(timezone=True), nullable=True)
    modification_count = Column(Integer, default=0)

    # Cancellation Details
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    cancellation_code = Column(String(50), nullable=True)
    cancellation_fee = Column(Numeric(15, 2), nullable=True)
    cancellation_confirmed = Column(Boolean, default=False)

    # Risk and Alerts
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)

    # Notes
    booking_notes = Column(Text, nullable=True)
    supplier_notes = Column(Text, nullable=True)
    operational_notes = Column(Text, nullable=True)

    # Metadata
    booking_line_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking = relationship("Booking", back_populates="booking_lines")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_booking_line_booking_status', 'booking_id', 'booking_status'),
        Index('idx_booking_line_status_created', 'booking_status', 'created_at'),
        Index('idx_booking_line_risk', 'risk_level'),
        Index('idx_booking_line_service_start', 'service_confirmed_start'),
    )

# ============================================
# BOOKING PASSENGERS TABLE
# ============================================

class BookingPassenger(Base):
    """Links passengers to bookings with specific roles"""
    __tablename__ = "booking_passengers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    passenger_id = Column(Integer, ForeignKey('passengers.id', ondelete='CASCADE'), nullable=False)

    # Passenger Role in Booking
    is_lead_passenger = Column(Boolean, default=False)
    passenger_type = Column(String(20), nullable=False)  # adult, child, infant
    age_at_travel = Column(Integer, nullable=True)

    # Room/Service Assignment
    room_assignment = Column(String(50), nullable=True)
    seat_assignment = Column(String(50), nullable=True)
    service_assignments = Column(JSON, nullable=True)  # Which services this passenger is in

    # Special Requirements
    special_requirements = Column(Text, nullable=True)
    dietary_restrictions = Column(JSON, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    accessibility_needs = Column(JSON, nullable=True)

    # Documents Status
    documents_received = Column(Boolean, default=False)
    documents_verified = Column(Boolean, default=False)
    missing_documents = Column(JSON, nullable=True)

    # Check-in Status
    checked_in = Column(Boolean, default=False)
    checked_in_at = Column(DateTime(timezone=True), nullable=True)
    no_show = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="booking_passengers")
    passenger = relationship("Passenger", back_populates="booking_passengers")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('booking_id', 'passenger_id', name='uq_booking_passenger'),
        Index('idx_booking_passenger_booking', 'booking_id'),
        Index('idx_booking_passenger_passenger', 'passenger_id'),
        Index('idx_booking_passenger_lead', 'is_lead_passenger'),
        Index('idx_booking_passenger_type', 'passenger_type'),
    )

# ============================================
# SERVICE OPERATIONS TABLE
# ============================================

class ServiceOperation(Base):
    """Operational tracking for service execution"""
    __tablename__ = "service_operations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    booking_line_id = Column(Integer, ForeignKey('booking_lines.id', ondelete='CASCADE'), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # References users.id (operator/guide)
    supervised_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Operation Details
    operation_date = Column(Date, nullable=False)
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(SQLEnum(ServiceOperationStatus), default=ServiceOperationStatus.PLANNED)
    operational_alert = Column(SQLEnum(OperationalAlert), default=OperationalAlert.NONE)

    # Location Tracking
    pickup_location = Column(Text, nullable=True)
    pickup_coordinates = Column(JSON, nullable=True)  # {lat, lng}
    dropoff_location = Column(Text, nullable=True)
    dropoff_coordinates = Column(JSON, nullable=True)

    # Passenger Management
    expected_passengers = Column(Integer, default=0)
    actual_passengers = Column(Integer, nullable=True)
    passenger_checklist = Column(JSON, nullable=True)  # [{id, name, checked_in, notes}]

    # Provider/Guide Details
    provider_name = Column(String(255), nullable=True)
    guide_name = Column(String(255), nullable=True)
    driver_name = Column(String(255), nullable=True)
    vehicle_info = Column(JSON, nullable=True)  # {plate, model, color}

    # Quality Control
    checklist_completed = Column(Boolean, default=False)
    quality_checks = Column(JSON, nullable=True)  # [{item, status, notes}]
    incidents = Column(JSON, nullable=True)  # Array of incident reports

    # Communication
    customer_contacted = Column(Boolean, default=False)
    last_customer_contact = Column(DateTime(timezone=True), nullable=True)
    provider_confirmed = Column(Boolean, default=False)
    provider_confirmation_time = Column(DateTime(timezone=True), nullable=True)

    # Post-Operation
    feedback_collected = Column(Boolean, default=False)
    customer_rating = Column(Numeric(3, 2), nullable=True)  # 1.00 to 5.00
    customer_feedback = Column(Text, nullable=True)
    photos_uploaded = Column(Boolean, default=False)
    photo_urls = Column(JSON, nullable=True)

    # Notes
    pre_operation_notes = Column(Text, nullable=True)
    operation_notes = Column(Text, nullable=True)
    post_operation_notes = Column(Text, nullable=True)

    # Metadata
    operation_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="service_operations")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_service_op_booking', 'booking_id'),
        Index('idx_service_op_line', 'booking_line_id'),
        Index('idx_service_op_date', 'operation_date'),
        Index('idx_service_op_status', 'status'),
        Index('idx_service_op_assigned', 'assigned_to'),
        Index('idx_service_op_alert', 'operational_alert'),
        Index('idx_service_op_scheduled', 'scheduled_start', 'scheduled_end'),
    )
