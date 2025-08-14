"""
CRM Service Core Models
Based on Laravel migrations from services-references/crm-services
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, UniqueConstraint, Index, Numeric, Date, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

# ============================================
# ENUMS
# ============================================

class ActorType(str, enum.Enum):
    LEAD = "lead"
    CONTACT = "contact"
    ACCOUNT_BUSINESS = "account_business"
    ACCOUNT_PERSON = "account_person"

class TravelFrequency(str, enum.Enum):
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    BUSINESS_REGULAR = "business_regular"

class Rating(int, enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    DISQUALIFIED = "disqualified"

class InterestLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DO_NOT_CONTACT = "do_not_contact"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class PreferredCommunication(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"

class AccountType(str, enum.Enum):
    BUSINESS = "business"
    PERSON = "person"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"

class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# ============================================
# ACTORS TABLE (Base for all CRM entities)
# ============================================

class Actor(Base):
    """Base entity for all CRM actors (leads, contacts, accounts)"""
    __tablename__ = "actors"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(SQLEnum(ActorType), nullable=False, index=True)

    # Personal/Company Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    company_name = Column(String(200), nullable=True)
    title = Column(String(100), nullable=True)
    tax_id = Column(String(100), nullable=True, unique=True, index=True)

    # Contact Information
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True, unique=True, index=True)

    # Address
    street = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # Business Information
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    number_of_employees = Column(Integer, nullable=True)

    # Travel Preferences (specific for travel agencies)
    preferred_destinations = Column(JSON, nullable=True)
    budget_range = Column(String(50), nullable=True)
    travel_frequency = Column(SQLEnum(TravelFrequency), nullable=True)
    group_size_preference = Column(String(50), nullable=True)

    # Metadata
    source = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=True, index=True)
    rating = Column(SQLEnum(Rating), nullable=True, index=True)
    description = Column(Text, nullable=True)

    # Audit fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="actor", uselist=False, cascade="all, delete-orphan")
    contact = relationship("Contact", back_populates="actor", uselist=False, cascade="all, delete-orphan")
    account = relationship("Account", back_populates="actor", uselist=False, cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_actor_type_status', 'type', 'status'),
        Index('idx_actor_created_at', 'created_at'),
        Index('idx_actor_deleted_at', 'deleted_at'),
    )

# ============================================
# INDUSTRIES TABLE
# ============================================

class Industry(Base):
    """Industries for categorizing accounts"""
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('industries.id'), nullable=True)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="industry")
    parent = relationship("Industry", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_industry_code', 'code'),
        Index('idx_industry_active', 'is_active'),
    )
