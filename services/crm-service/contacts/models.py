"""
Contact Models for CRM Service
Contact-specific models and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from core.models import Base
from core.enums import ContactStatus, Gender, PreferredCommunication

# ============================================
# CONTACTS TABLE
# ============================================

class Contact(Base):
    """Contact management for confirmed customers and business contacts"""
    __tablename__ = "contacts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey('actors.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)

    # Passenger reference (if applicable)
    passenger_id = Column(Integer, nullable=True)  # References passengers table if exists

    # Contact specific fields
    contact_status = Column(SQLEnum(ContactStatus), default=ContactStatus.ACTIVE, index=True)
    is_primary_contact = Column(Boolean, default=False)
    department = Column(String(100), nullable=True)
    reports_to = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)

    # Personal travel information
    passport_number = Column(String(50), nullable=True)
    passport_expiry = Column(Date, nullable=True)
    visa_requirements = Column(JSON, nullable=True)
    dietary_restrictions = Column(Text, nullable=True)
    accessibility_needs = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)

    # Communication preferences
    email_opt_in = Column(Boolean, default=True)
    sms_opt_in = Column(Boolean, default=False)
    preferred_communication = Column(SQLEnum(PreferredCommunication), default=PreferredCommunication.EMAIL)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor = relationship("Actor", back_populates="contact")
    account = relationship("Account", back_populates="contacts", foreign_keys=[account_id])
    manager = relationship("Contact", remote_side=[id], foreign_keys=[reports_to])
    subordinates = relationship("Contact", back_populates="manager", foreign_keys=[reports_to])
    opportunities = relationship("Opportunity", back_populates="contact")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_contact_status_primary', 'contact_status', 'is_primary_contact'),
        Index('idx_contact_passport_expiry', 'passport_expiry'),
        Index('idx_contact_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Contact: {self.actor.first_name} {self.actor.last_name} - {self.contact_status}>"
