"""
Financial Service Models - Invoices and Payments
Based on Laravel migrations from services-references/financial-service
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

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL_PAID = "partial_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    WIRE_TRANSFER = "wire_transfer"
    OTHER = "other"

class PaymentType(str, enum.Enum):
    DEPOSIT = "deposit"
    PARTIAL = "partial"
    FULL = "full"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CREDIT = "credit"
    DEBIT = "debit"
    ADJUSTMENT = "adjustment"

# ============================================
# INVOICES TABLE
# ============================================

class Invoice(Base):
    """Invoice management for orders"""
    __tablename__ = "invoices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    account_id = Column(Integer, nullable=True)  # References accounts.id from CRM service
    contact_id = Column(Integer, nullable=True)  # References contacts.id from CRM service
    created_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Invoice Information
    invoice_number = Column(String(50), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT, index=True)

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    sent_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)

    # Financial Information
    subtotal = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    balance_due = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Additional Information
    notes = Column(Text, nullable=True)
    terms_conditions = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)

    # Billing Address
    billing_name = Column(String(255), nullable=True)
    billing_address = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="invoices")
    invoice_lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('invoice_number', 'deleted_at', name='uq_invoice_number_deleted'),
        Index('idx_invoice_status_due', 'status', 'due_date'),
        Index('idx_invoice_contact_status', 'contact_id', 'status'),
        Index('idx_invoice_dates', 'invoice_date', 'due_date'),
        Index('idx_invoice_balance', 'balance_due'),
        Index('idx_invoice_total', 'total_amount'),
    )

# ============================================
# INVOICE LINES TABLE
# ============================================

class InvoiceLine(Base):
    """Individual line items in an invoice"""
    __tablename__ = "invoice_lines"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)

    # Line item information
    line_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)

    # Reference to order line (if applicable)
    order_line_id = Column(Integer, nullable=True)  # References order_lines.id

    # Quantities and pricing
    quantity = Column(Numeric(10, 2), default=1)
    unit_price = Column(Numeric(15, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # Additional details
    notes = Column(Text, nullable=True)
    is_taxable = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_lines")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_invoice_line_invoice_id', 'invoice_id'),
        UniqueConstraint('invoice_id', 'line_number', name='uq_invoice_line_number'),
    )

# ============================================
# PAYMENTS TABLE
# ============================================

class Payment(Base):
    """Payment transactions for invoices and orders"""
    __tablename__ = "payments"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    account_id = Column(Integer, nullable=True)  # References accounts.id from CRM service
    contact_id = Column(Integer, nullable=True)  # References contacts.id from CRM service
    processed_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Payment Information
    payment_number = Column(String(50), nullable=False, unique=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Payment Details
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_type = Column(SQLEnum(PaymentType), default=PaymentType.PARTIAL)
    transaction_type = Column(SQLEnum(TransactionType), default=TransactionType.PAYMENT)

    # Transaction Details
    reference_number = Column(String(100), nullable=True)
    transaction_id = Column(String(255), nullable=True)  # External transaction ID
    gateway_response = Column(JSON, nullable=True)  # Store gateway response

    # Bank/Card Information (encrypted in production)
    bank_name = Column(String(100), nullable=True)
    account_number_last4 = Column(String(4), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(50), nullable=True)

    # Check Information
    check_number = Column(String(50), nullable=True)
    check_date = Column(Date, nullable=True)

    # Status
    status = Column(String(50), default='completed')  # pending, processing, completed, failed, refunded
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Refund Information (if applicable)
    is_refund = Column(Boolean, default=False)
    refund_reason = Column(Text, nullable=True)
    original_payment_id = Column(Integer, ForeignKey('payments.id'), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    refunds = relationship("Payment", backref="original_payment", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_payment_invoice_id', 'invoice_id'),
        Index('idx_payment_order_id', 'order_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_transaction_id', 'transaction_id'),
    )

# ============================================
# ACCOUNTS RECEIVABLE TABLE
# ============================================

class AccountsReceivable(Base):
    """Accounts receivable tracking"""
    __tablename__ = "accounts_receivables"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    account_id = Column(Integer, nullable=False)  # References accounts.id from CRM service
    invoice_id = Column(Integer, ForeignKey('invoices.id', ondelete='SET NULL'), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)

    # AR Information
    ar_number = Column(String(50), nullable=False, unique=True)
    transaction_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    # Amounts
    original_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Status
    status = Column(String(50), default='open')  # open, partial, paid, overdue, written_off
    days_overdue = Column(Integer, default=0)

    # Aging buckets
    aging_bucket = Column(String(50), nullable=True)  # current, 30, 60, 90, 120+

    # Collection Information
    collection_status = Column(String(50), nullable=True)  # normal, warning, collection, legal
    last_collection_date = Column(Date, nullable=True)
    next_collection_date = Column(Date, nullable=True)
    collection_notes = Column(Text, nullable=True)

    # Write-off Information
    is_written_off = Column(Boolean, default=False)
    written_off_date = Column(Date, nullable=True)
    written_off_amount = Column(Numeric(15, 2), nullable=True)
    written_off_reason = Column(Text, nullable=True)
    written_off_by = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_ar_account_id', 'account_id'),
        Index('idx_ar_status', 'status'),
        Index('idx_ar_due_date', 'due_date'),
        Index('idx_ar_aging', 'aging_bucket'),
        Index('idx_ar_balance', 'balance'),
    )

# ============================================
# ACCOUNTS PAYABLE TABLE
# ============================================

class AccountsPayable(Base):
    """Accounts payable tracking"""
    __tablename__ = "accounts_payables"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    supplier_id = Column(Integer, nullable=False)  # References suppliers table
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete='SET NULL'), nullable=True)

    # AP Information
    ap_number = Column(String(50), nullable=False, unique=True)
    invoice_number = Column(String(100), nullable=True)  # Supplier's invoice number
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    # Amounts
    original_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Status
    status = Column(String(50), default='open')  # open, partial, paid, overdue, disputed
    days_overdue = Column(Integer, default=0)

    # Payment Terms
    payment_terms = Column(String(100), nullable=True)
    discount_terms = Column(String(100), nullable=True)
    early_payment_discount = Column(Numeric(5, 2), nullable=True)

    # Approval Workflow
    is_approved = Column(Boolean, default=False)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Dispute Information
    is_disputed = Column(Boolean, default=False)
    dispute_reason = Column(Text, nullable=True)
    dispute_date = Column(Date, nullable=True)
    dispute_resolved_date = Column(Date, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_ap_supplier_id', 'supplier_id'),
        Index('idx_ap_status', 'status'),
        Index('idx_ap_due_date', 'due_date'),
        Index('idx_ap_balance', 'balance'),
        Index('idx_ap_approval', 'is_approved', 'approved_date'),
    )
