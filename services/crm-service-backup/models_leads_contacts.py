"""
CRM Service Models - Leads and Contacts
Based on Laravel migrations from services-references/crm-services
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models_core import (
    Base, LeadStatus, InterestLevel, ContactStatus,
    Gender, PreferredCommunication
)

# ============================================
# LEADS TABLE
# ============================================

class Lead(Base):
    """Lead management for potential customers"""
    __tablename__ = "leads"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey('actors.id', ondelete='CASCADE'), nullable=False)

    # Lead specific fields
    lead_source = Column(String(100), nullable=True, index=True)
    lead_status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, index=True)
    conversion_probability = Column(Integer, nullable=True)  # 0-100%
    expected_close_date = Column(Date, nullable=True)
    estimated_value = Column(Numeric(15, 2), nullable=True)

    # Conversion Information
    converted_date = Column(DateTime(timezone=True), nullable=True)
    interest_level = Column(SQLEnum(InterestLevel), default=InterestLevel.LOW)
    inquiry_type = Column(String(255), nullable=True)
    last_contacted_at = Column(Date, nullable=True)
    is_qualified = Column(Boolean, default=False)
    disqualification_reason = Column(Text, nullable=True)
    referral_source = Column(Text, nullable=True)

    # Owner and conversion references
    lead_owner_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    converted_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    converted_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    converted_opportunity_id = Column(Integer, ForeignKey('opportunities.id', ondelete='SET NULL'), nullable=True)

    # Travel specific information
    travel_interests = Column(JSON, nullable=True)
    preferred_travel_date = Column(Date, nullable=True)
    number_of_travelers = Column(Integer, nullable=True)
    special_requirements = Column(Text, nullable=True)

    # Management fields
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    campaign_id = Column(String(255), nullable=True)
    score = Column(Integer, default=0, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor = relationship("Actor", back_populates="lead")
    converted_contact = relationship("Contact", foreign_keys=[converted_contact_id])
    converted_account = relationship("Account", foreign_keys=[converted_account_id])
    converted_opportunity = relationship("Opportunity", foreign_keys=[converted_opportunity_id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_lead_status_created', 'lead_status', 'created_at'),
        Index('idx_lead_probability_close', 'conversion_probability', 'expected_close_date'),
        Index('idx_lead_converted_date', 'converted_date'),
        Index('idx_lead_score_interest', 'score', 'interest_level'),
        Index('idx_lead_follow_up', 'follow_up_date'),
        Index('idx_lead_deleted', 'deleted_at'),
    )

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
