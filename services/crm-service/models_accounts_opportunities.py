"""
CRM Service Models - Accounts and Opportunities
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
    Base, AccountType, AccountStatus, PaymentMethod, RiskLevel
)

# ============================================
# ENUMS for Opportunities
# ============================================

import enum

class OpportunityStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    DECISION_MAKING = "decision_making"
    PERCEPTION_ANALYSIS = "perception_analysis"
    QUOTES = "quotes"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class TravelType(str, enum.Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    CORPORATE = "corporate"
    HONEYMOON = "honeymoon"
    FAMILY = "family"
    ADVENTURE = "adventure"
    LUXURY = "luxury"
    CULTURAL = "cultural"
    EDUCATIONAL = "educational"
    MEDICAL = "medical"
    RELIGIOUS = "religious"
    BACKPACKING = "backpacking"
    VOLUNTEER = "volunteer"
    SPORTS = "sports"
    WELLNESS = "wellness"
    PERSONAL = "personal"
    ECOTOURISM = "ecotourism"
    OTHER = "other"

class BudgetLevel(str, enum.Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"

# ============================================
# ACCOUNTS TABLE
# ============================================

class Account(Base):
    """Account management for businesses and individual customers"""
    __tablename__ = "accounts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey('actors.id', ondelete='CASCADE'), nullable=False)
    industry_id = Column(Integer, ForeignKey('industries.id', ondelete='SET NULL'), nullable=True)

    # Account specific fields
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    account_status = Column(SQLEnum(AccountStatus), default=AccountStatus.PROSPECT, index=True)
    parent_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    is_following = Column(Boolean, default=False)

    # Business Information (for business accounts)
    tax_id = Column(String(50), nullable=True)
    business_license = Column(String(100), nullable=True)
    credit_limit = Column(Numeric(15, 2), nullable=True)
    payment_terms = Column(String(50), nullable=True)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)

    # Additional business information
    company_owner = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    employee_count = Column(Integer, nullable=True)
    time_zone = Column(String(50), nullable=True)

    # Banking information
    bank_name = Column(String(100), nullable=True)
    bank_account = Column(String(50), nullable=True)
    swift_code = Column(String(20), nullable=True)

    # Metrics
    total_bookings = Column(Integer, default=0)
    lifetime_value = Column(Numeric(15, 2), default=0)
    last_booking_date = Column(Date, nullable=True)
    first_booking_date = Column(Date, nullable=True)

    # Segmentation information
    customer_segment = Column(String(50), nullable=True)
    loyalty_points = Column(Integer, default=0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor = relationship("Actor", back_populates="account")
    industry = relationship("Industry", back_populates="accounts")
    parent = relationship("Account", remote_side=[id], foreign_keys=[parent_account_id])
    subsidiaries = relationship("Account", back_populates="parent", foreign_keys=[parent_account_id])
    contacts = relationship("Contact", back_populates="account", foreign_keys="Contact.account_id")
    opportunities = relationship("Opportunity", back_populates="account")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_account_type_status', 'account_type', 'account_status'),
        Index('idx_account_segment_ltv', 'customer_segment', 'lifetime_value'),
        Index('idx_account_last_booking', 'last_booking_date'),
        Index('idx_account_deleted', 'deleted_at'),
    )

# ============================================
# OPPORTUNITIES TABLE
# ============================================

class Opportunity(Base):
    """Opportunity management for sales pipeline"""
    __tablename__ = "opportunities"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic information
    name = Column(String(200), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    campaign_id = Column(Integer, nullable=True)  # References campaigns if exists

    # Opportunity information
    stage = Column(SQLEnum(OpportunityStage), default=OpportunityStage.PROSPECTING, index=True)
    probability = Column(Integer, default=25)  # 0-100%
    amount = Column(Numeric(15, 2), nullable=True)
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)

    # Travel Information
    travel_type = Column(SQLEnum(TravelType), nullable=True)
    destinations = Column(JSON, nullable=True)  # Array of destination_ids
    departure_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)
    number_of_adults = Column(Integer, nullable=True)
    number_of_children = Column(Integer, nullable=True)

    # Travel details
    room_configuration = Column(JSON, nullable=True)  # ["1 double", "1 single"]
    budget_level = Column(SQLEnum(BudgetLevel), nullable=True)
    special_requests = Column(Text, nullable=True)

    # Status
    is_closed = Column(Boolean, default=False)
    close_reason = Column(String(255), nullable=True)
    loss_reason = Column(Text, nullable=True)

    # Competition
    competitors = Column(JSON, nullable=True)
    next_steps = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="opportunities")
    contact = relationship("Contact", back_populates="opportunities")
    quotes = relationship("Quote", back_populates="opportunity", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_opportunity_stage_close', 'stage', 'expected_close_date'),
        Index('idx_opportunity_owner_stage', 'owner_id', 'stage'),
        Index('idx_opportunity_departure_stage', 'departure_date', 'stage'),
        Index('idx_opportunity_closed', 'is_closed'),
        Index('idx_opportunity_deleted', 'deleted_at'),
    )
