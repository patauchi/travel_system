"""
Voucher Module Models
Payment voucher models for financial service
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

# ============================================
# VOUCHERS TABLE
# ============================================

class Voucher(Base):
    """Payment vouchers for formal payment authorization"""
    __tablename__ = "vouchers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    expense_id = Column(Integer, nullable=True)  # References expenses.id
    order_id = Column(Integer, nullable=True)  # References orders.id
    supplier_id = Column(Integer, nullable=True)  # References suppliers table
    created_by = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    paid_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Voucher Information
    voucher_number = Column(String(50), nullable=False, unique=True)
    voucher_date = Column(Date, nullable=False)
    voucher_type = Column(String(50), nullable=False)  # payment, receipt, journal, contra

    # Payee Information
    payee_name = Column(String(255), nullable=False)
    payee_type = Column(String(50), nullable=True)  # employee, supplier, customer, other

    # Financial Information
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    exchange_rate = Column(Numeric(10, 6), default=1.0)
    amount_in_words = Column(Text, nullable=True)

    # Payment Details
    payment_method = Column(String(50), nullable=True)
    bank_account = Column(String(100), nullable=True)
    check_number = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)

    # Purpose
    purpose = Column(Text, nullable=False)
    cost_center = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)

    # Status
    status = Column(String(50), default='draft')  # draft, pending, approved, paid, cancelled
    is_approved = Column(Boolean, default=False)
    approved_date = Column(DateTime(timezone=True), nullable=True)
    is_paid = Column(Boolean, default=False)
    paid_date = Column(DateTime(timezone=True), nullable=True)

    # Accounting
    accounting_period = Column(String(20), nullable=True)  # YYYY-MM
    is_posted = Column(Boolean, default=False)
    posted_date = Column(Date, nullable=True)
    journal_entry_number = Column(String(50), nullable=True)

    # Supporting Documents
    attachments = Column(JSON, nullable=True)  # Array of file paths
    supporting_documents = Column(Text, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Cancellation
    is_cancelled = Column(Boolean, default=False)
    cancelled_date = Column(DateTime(timezone=True), nullable=True)
    cancelled_by = Column(UUID(as_uuid=True), nullable=True)
    cancellation_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_voucher_status', 'status'),
        Index('idx_voucher_date', 'voucher_date'),
        Index('idx_voucher_type', 'voucher_type'),
        Index('idx_voucher_supplier', 'supplier_id'),
        Index('idx_voucher_paid', 'is_paid', 'paid_date'),
        Index('idx_voucher_approved', 'is_approved', 'approved_date'),
        Index('idx_voucher_expense', 'expense_id'),
        Index('idx_voucher_order', 'order_id'),
        Index('idx_voucher_payee', 'payee_name'),
        Index('idx_voucher_accounting_period', 'accounting_period'),
    )
