"""
Core Models for CRM Service
Base models used across multiple modules
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Index, Numeric, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from .enums import ActorType, TravelFrequency, Rating

Base = declarative_base()

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

    def __repr__(self):
        if self.type == ActorType.lead:
            name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        elif self.type == ActorType.contact:
            name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        else:  # ACCOUNT
            name = self.company_name or f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"<Actor({self.type}): {name}>"
