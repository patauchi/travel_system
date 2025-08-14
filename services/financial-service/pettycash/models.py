"""
Petty Cash Module Models
Petty cash management models for financial service
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
from common.enums import PettyCashTransactionType, PettyCashStatus

# ============================================
# PETTY CASH TABLE
# ============================================

class PettyCash(Base):
    """Petty cash fund management"""
    __tablename__ = "petty_cashes"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Fund Information
    fund_name = Column(String(100), nullable=False)
    fund_code = Column(String(20), nullable=True, unique=True)
    description = Column(Text, nullable=True)

    # Custodian
    custodian_id = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    location = Column(String(100), nullable=True)

    # Fund Amounts
    initial_amount = Column(Numeric(15, 2), nullable=False)
    current_balance = Column(Numeric(15, 2), nullable=False)
    minimum_balance = Column(Numeric(15, 2), default=0)
    maximum_balance = Column(Numeric(15, 2), nullable=True)
    replenishment_amount = Column(Numeric(15, 2), nullable=True)

    # Status
    status = Column(SQLEnum(PettyCashStatus), default=PettyCashStatus.OPEN, index=True)
    is_active = Column(Boolean, default=True)

    # Reconciliation
    last_reconciled_date = Column(Date, nullable=True)
    last_reconciled_by = Column(UUID(as_uuid=True), nullable=True)
    reconciliation_frequency = Column(String(50), default='monthly')  # daily, weekly, monthly

    # Audit
    last_audit_date = Column(Date, nullable=True)
    last_audited_by = Column(UUID(as_uuid=True), nullable=True)
    audit_notes = Column(Text, nullable=True)

    # Settings
    requires_receipt = Column(Boolean, default=True)
    max_transaction_amount = Column(Numeric(15, 2), nullable=True)
    allowed_expense_categories = Column(JSON, nullable=True)  # Array of category IDs

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    transactions = relationship("PettyCashTransaction", back_populates="petty_cash", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_petty_cash_custodian', 'custodian_id'),
        Index('idx_petty_cash_status', 'status'),
        Index('idx_petty_cash_active', 'is_active'),
    )

# ============================================
# PETTY CASH TRANSACTIONS TABLE
# ============================================

class PettyCashTransaction(Base):
    """Individual transactions for petty cash funds"""
    __tablename__ = "petty_cash_transactions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    petty_cash_id = Column(Integer, ForeignKey('petty_cashes.id', ondelete='CASCADE'), nullable=False)
    expense_id = Column(Integer, nullable=True)  # References expenses.id
    performed_by = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Transaction Information
    transaction_number = Column(String(50), nullable=False, unique=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    transaction_type = Column(SQLEnum(PettyCashTransactionType), nullable=False)

    # Amount
    amount = Column(Numeric(15, 2), nullable=False)
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)

    # Details
    description = Column(Text, nullable=False)
    reference_number = Column(String(100), nullable=True)
    vendor_name = Column(String(255), nullable=True)

    # Receipt Information
    has_receipt = Column(Boolean, default=False)
    receipt_number = Column(String(100), nullable=True)
    receipt_file_path = Column(String(500), nullable=True)

    # Category
    expense_category_id = Column(Integer, nullable=True)  # References expense_categories.id

    # Approval
    requires_approval = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)

    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_date = Column(Date, nullable=True)
    reconciled_by = Column(UUID(as_uuid=True), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    petty_cash = relationship("PettyCash", back_populates="transactions")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_petty_cash_trans_fund', 'petty_cash_id'),
        Index('idx_petty_cash_trans_date', 'transaction_date'),
        Index('idx_petty_cash_trans_type', 'transaction_type'),
        Index('idx_petty_cash_trans_reconciled', 'is_reconciled', 'reconciled_date'),
    )
