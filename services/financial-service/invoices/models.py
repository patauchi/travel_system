"""
Invoices Module Models
Invoice and accounts receivable/payable models for financial service
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
    InvoiceStatus, AccountsReceivableStatus, AccountsPayableStatus, AgingBucket, CollectionStatus
)

# ============================================
# INVOICES TABLE
# ============================================

class Invoice(Base):
    """Invoice management for orders"""
    __tablename__ = "invoices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    order_id = Column(Integer, nullable=False)  # References orders.id
    account_id = Column(Integer, nullable=True)  # References accounts.id from CRM service
    contact_id = Column(Integer, nullable=True)  # References contacts.id from CRM service
    created_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Invoice Information
    invoice_number = Column(String(50), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.draft, index=True)

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
    invoice_lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('invoice_number', 'deleted_at', name='uq_invoice_number_deleted'),
        Index('idx_invoice_status_due', 'status', 'due_date'),
        Index('idx_invoice_contact_status', 'contact_id', 'status'),
        Index('idx_invoice_dates', 'invoice_date', 'due_date'),
        Index('idx_invoice_balance', 'balance_due'),
        Index('idx_invoice_total', 'total_amount'),
        Index('idx_invoice_order', 'order_id'),
        Index('idx_invoice_account', 'account_id'),
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

    # Product/Service details
    product_code = Column(String(50), nullable=True)
    service_code = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_lines")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_invoice_line_invoice_id', 'invoice_id'),
        UniqueConstraint('invoice_id', 'line_number', name='uq_invoice_line_number'),
        Index('idx_invoice_line_order_line', 'order_line_id'),
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
    order_id = Column(Integer, nullable=True)  # References orders.id

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
    status = Column(SQLEnum(AccountsReceivableStatus), default=AccountsReceivableStatus.open, index=True)
    days_overdue = Column(Integer, default=0)

    # Aging buckets
    aging_bucket = Column(SQLEnum(AgingBucket), nullable=True)  # current, 30, 60, 90, 120+

    # Collection Information
    collection_status = Column(SQLEnum(CollectionStatus), nullable=True)  # normal, warning, collection, legal
    last_collection_date = Column(Date, nullable=True)
    next_collection_date = Column(Date, nullable=True)
    collection_notes = Column(Text, nullable=True)
    collection_attempts = Column(Integer, default=0)

    # Write-off Information
    is_written_off = Column(Boolean, default=False)
    written_off_date = Column(Date, nullable=True)
    written_off_amount = Column(Numeric(15, 2), nullable=True)
    written_off_reason = Column(Text, nullable=True)
    written_off_by = Column(UUID(as_uuid=True), nullable=True)

    # Credit hold information
    is_on_credit_hold = Column(Boolean, default=False)
    credit_hold_date = Column(Date, nullable=True)
    credit_hold_reason = Column(Text, nullable=True)
    credit_hold_by = Column(UUID(as_uuid=True), nullable=True)

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
        Index('idx_ar_collection_status', 'collection_status'),
        Index('idx_ar_invoice', 'invoice_id'),
        Index('idx_ar_credit_hold', 'is_on_credit_hold'),
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
    order_id = Column(Integer, nullable=True)  # References orders.id
    expense_id = Column(Integer, nullable=True)  # References expenses.id

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
    status = Column(SQLEnum(AccountsPayableStatus), default=AccountsPayableStatus.open, index=True)
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
        Index('idx_ap_order', 'order_id'),
        Index('idx_ap_expense', 'expense_id'),
        Index('idx_ap_disputed', 'is_disputed'),
    )
