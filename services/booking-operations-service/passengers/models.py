"""
Passengers module models
Contains the Passenger model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import PassengerGender, DocumentType, LoyaltyTier

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
    document_type = Column(SQLEnum(DocumentType), nullable=True)
    document_number = Column(String(50), nullable=True)
    document_expiry_date = Column(Date, nullable=True)
    document_issuing_country = Column(String(2), nullable=True)

    # Contact Details
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)

    # Travel Preferences
    dietary_restrictions = Column(JSON, nullable=True)  # ["vegetarian", "gluten_free"]
    accessibility_needs = Column(JSON, nullable=True)  # ["wheelchair", "hearing_aid"]
    special_requests = Column(Text, nullable=True)

    # Loyalty and Preferences
    loyalty_tier = Column(SQLEnum(LoyaltyTier), default=LoyaltyTier.BRONZE)
    preferred_language = Column(String(2), nullable=True)  # ISO language code
    marketing_consent = Column(Boolean, default=False)

    # Medical Information
    medical_conditions = Column(JSON, nullable=True)
    medications = Column(JSON, nullable=True)
    allergies = Column(JSON, nullable=True)

    # Travel History
    previous_bookings_count = Column(Integer, default=0)
    total_spent = Column(Numeric(15, 2), default=0)
    last_booking_date = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    risk_level = Column(String(20), default="low")  # low, medium, high

    # Additional Information
    passenger_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking_passengers = relationship("BookingPassenger", back_populates="passenger", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_passenger_email', 'email'),
        Index('idx_passenger_phone', 'phone'),
        Index('idx_passenger_document', 'document_type', 'document_number'),
        Index('idx_passenger_name', 'last_name', 'first_name'),
        Index('idx_passenger_active', 'is_active'),
        Index('idx_passenger_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Passenger(id={self.id}, name='{self.first_name} {self.last_name}', email='{self.email}')>"

    @property
    def full_name(self):
        """Get passenger's full name"""
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        names.append(self.last_name)
        return " ".join(names)

    @property
    def age(self):
        """Calculate passenger's age"""
        if not self.date_of_birth:
            return None

        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def is_document_valid(self):
        """Check if passenger's document is valid"""
        if not self.document_expiry_date:
            return True

        from datetime import date
        return self.document_expiry_date > date.today()

    def has_special_needs(self):
        """Check if passenger has special needs"""
        return bool(self.accessibility_needs or self.medical_conditions or self.dietary_restrictions)
