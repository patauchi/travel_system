"""
Orders Module Models
Order management models for financial service
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models_base import Base
from common.enums import (
    OrderStatus, PaymentStatus, Currency, OrderLineType, DocumentType
)

# ============================================
# ORDERS TABLE
# ============================================

class Order(Base):
    """Order management for confirmed quotes"""
    __tablename__ = "orders"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys (references to CRM service tables)
    quote_id = Column(Integer, nullable=False)  # References quotes.id from CRM service
    cancelled_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Order Information
    order_number = Column(String(50), nullable=False)
    order_status = Column(SQLEnum(OrderStatus), default=OrderStatus.pending, index=True)

    # Financial Details (copied from Quote)
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(SQLEnum(Currency), default=Currency.usd)

    # Important Dates
    order_date = Column(Date, nullable=False)
    departure_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)

    # Payment Information
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.pending, index=True)
    payment_terms = Column(String(100), nullable=True)
    amount_paid = Column(Numeric(15, 2), default=0)
    amount_due = Column(Numeric(15, 2), nullable=False)

    # Cancellation and Refunds
    cancellation_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    refund_amount = Column(Numeric(15, 2), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)

    # Notes and Communications
    special_instructions = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order_lines = relationship("OrderLine", back_populates="order", cascade="all, delete-orphan")
    passenger_documents = relationship("PassengerDocument", back_populates="order", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('order_number', 'deleted_at', name='uq_order_number_deleted'),
        Index('idx_order_status_departure', 'order_status', 'departure_date'),
        Index('idx_order_payment_status_due', 'payment_status', 'amount_due'),
        Index('idx_order_date', 'order_date'),
        Index('idx_order_departure_return', 'departure_date', 'return_date'),
    )

# ============================================
# ORDER LINES TABLE
# ============================================

class OrderLine(Base):
    """Individual line items in an order"""
    __tablename__ = "order_lines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)

    # Line item information
    line_number = Column(Integer, nullable=False)
    type = Column(SQLEnum(OrderLineType), nullable=False)
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

    # Commission information
    commission_rate = Column(Numeric(5, 2), nullable=True)
    commission_amount = Column(Numeric(15, 2), nullable=True)

    # Additional details
    notes = Column(Text, nullable=True)
    is_optional = Column(Boolean, default=False)
    is_included = Column(Boolean, default=True)
    is_confirmed = Column(Boolean, default=False)

    # Passenger assignment (for travel specific items)
    passenger_names = Column(JSON, nullable=True)  # Array of passenger names
    passenger_count = Column(Integer, nullable=True)

    # Supplier booking reference
    booking_reference = Column(String(100), nullable=True)
    confirmation_number = Column(String(100), nullable=True)
    supplier_confirmation = Column(String(100), nullable=True)

    # Status tracking
    status = Column(String(50), default='pending')
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="order_lines")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_order_line_order_id', 'order_id'),
        Index('idx_order_line_type', 'type'),
        Index('idx_order_line_service_date', 'service_date'),
        Index('idx_order_line_status', 'status'),
        UniqueConstraint('order_id', 'line_number', name='uq_order_line_number'),
    )

# ============================================
# PASSENGER DOCUMENTS TABLE
# ============================================

class PassengerDocument(Base):
    """Passenger documents for orders"""
    __tablename__ = "passenger_documents"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    passenger_id = Column(Integer, nullable=True)  # References passengers table if exists

    # Document Information
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_number = Column(String(100), nullable=False)
    issuing_country = Column(String(2), nullable=True)  # ISO country code

    # Passenger Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20), nullable=True)
    nationality = Column(String(2), nullable=True)  # ISO country code

    # Document validity
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Additional information
    place_of_birth = Column(String(100), nullable=True)
    place_of_issue = Column(String(100), nullable=True)

    # File attachment
    document_file_path = Column(String(500), nullable=True)
    document_file_name = Column(String(255), nullable=True)

    # Verification
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    verification_notes = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default='pending')  # pending, verified, expired, rejected

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="passenger_documents")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_passenger_doc_order_id', 'order_id'),
        Index('idx_passenger_doc_type', 'document_type'),
        Index('idx_passenger_doc_expiry', 'expiry_date'),
        Index('idx_passenger_doc_status', 'status'),
        Index('idx_passenger_doc_passenger', 'passenger_id'),
    )
