"""
CRM Service Models - Quotes
Based on Laravel migrations from services-references/crm-services
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from models_core import Base

# ============================================
# ENUMS for Quotes
# ============================================

class QuoteStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class Currency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    PEN = "PEN"
    COP = "COP"
    ARS = "ARS"
    CLP = "CLP"
    MXN = "MXN"
    BOL = "BOL"

class QuoteLineType(str, enum.Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSFER = "transfer"
    TOUR = "tour"
    CRUISE = "cruise"
    INSURANCE = "insurance"
    VISA = "visa"
    OTHER = "other"
    PACKAGE = "package"
    ACTIVITY = "activity"
    CAR_RENTAL = "car_rental"
    TRAIN = "train"
    BUS = "bus"

# ============================================
# QUOTES TABLE
# ============================================

class Quote(Base):
    """Quote management for opportunities"""
    __tablename__ = "quotes"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey('opportunities.id', ondelete='CASCADE'), nullable=False)
    quote_number = Column(String(50), nullable=False)

    # Quote Information
    name = Column(String(200), nullable=False)
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.DRAFT, index=True)
    is_primary = Column(Boolean, default=False)

    # Dates
    quote_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    accepted_date = Column(Date, nullable=True)

    # Group/Rate breakdown
    rate_breakdown = Column(JSON, nullable=True)

    # Version history for quote lines
    quote_lines_history = Column(JSON, nullable=True)  # History of changes in QuoteLines

    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    currency = Column(SQLEnum(Currency), default=Currency.USD)
    payment_terms = Column(String(100), nullable=True)

    # Notes and communications
    special_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    opportunity = relationship("Opportunity", back_populates="quotes")
    quote_lines = relationship("QuoteLine", back_populates="quote", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('quote_number', 'deleted_at', name='uq_quote_number_deleted'),
        Index('idx_quote_opportunity_primary', 'opportunity_id', 'is_primary'),
        Index('idx_quote_status_expiration', 'status', 'expiration_date'),
        Index('idx_quote_date', 'quote_date'),
    )

# ============================================
# QUOTE LINES TABLE
# ============================================

class QuoteLine(Base):
    """Individual line items in a quote"""
    __tablename__ = "quote_lines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False)

    # Line item information
    line_number = Column(Integer, nullable=False)
    type = Column(SQLEnum(QuoteLineType), nullable=False)
    description = Column(Text, nullable=False)

    # Product/Service details
    product_id = Column(Integer, nullable=True)  # References products if exists
    service_id = Column(Integer, nullable=True)  # References services if exists
    supplier_id = Column(Integer, nullable=True)  # References suppliers if exists

    # Dates
    service_date = Column(Date, nullable=True)
    service_end_date = Column(Date, nullable=True)

    # Quantities and pricing
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # Cost information (for margin calculation)
    unit_cost = Column(Numeric(15, 2), nullable=True)
    total_cost = Column(Numeric(15, 2), nullable=True)
    margin_amount = Column(Numeric(15, 2), nullable=True)
    margin_percent = Column(Numeric(5, 2), nullable=True)

    # Additional details
    notes = Column(Text, nullable=True)
    is_optional = Column(Boolean, default=False)
    is_included = Column(Boolean, default=True)

    # Passenger assignment (for travel specific items)
    passenger_names = Column(JSON, nullable=True)  # Array of passenger names
    passenger_count = Column(Integer, nullable=True)

    # Supplier booking reference
    booking_reference = Column(String(100), nullable=True)
    confirmation_number = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quote = relationship("Quote", back_populates="quote_lines")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_quote_line_quote_id', 'quote_id'),
        Index('idx_quote_line_type', 'type'),
        Index('idx_quote_line_service_date', 'service_date'),
        UniqueConstraint('quote_id', 'line_number', name='uq_quote_line_number'),
    )
