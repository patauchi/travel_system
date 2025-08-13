"""
Financial Service Models - Expenses and Petty Cash
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

class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    REIMBURSED = "reimbursed"
    CANCELLED = "cancelled"

class ExpenseType(str, enum.Enum):
    TRAVEL = "travel"
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    TRANSPORTATION = "transportation"
    SUPPLIES = "supplies"
    UTILITIES = "utilities"
    MARKETING = "marketing"
    OFFICE = "office"
    ENTERTAINMENT = "entertainment"
    PROFESSIONAL_FEES = "professional_fees"
    INSURANCE = "insurance"
    TAXES = "taxes"
    OTHER = "other"

class PettyCashTransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    EXPENSE = "expense"
    REIMBURSEMENT = "reimbursement"
    ADJUSTMENT = "adjustment"

class PettyCashStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    RECONCILED = "reconciled"

# ============================================
# EXPENSE CATEGORIES TABLE
# ============================================

class ExpenseCategory(Base):
    """Categories for organizing expenses"""
    __tablename__ = "expense_categories"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Category Information
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=True)

    # Budget Information
    budget_monthly = Column(Numeric(15, 2), nullable=True)
    budget_yearly = Column(Numeric(15, 2), nullable=True)

    # Accounting Information
    account_code = Column(String(50), nullable=True)
    tax_deductible = Column(Boolean, default=True)
    requires_receipt = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)

    # Settings
    is_active = Column(Boolean, default=True)
    approval_limit = Column(Numeric(15, 2), nullable=True)
    auto_approve_under = Column(Numeric(15, 2), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    parent = relationship("ExpenseCategory", remote_side=[id])
    expenses = relationship("Expense", back_populates="category")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_expense_category_code', 'code'),
        Index('idx_expense_category_active', 'is_active'),
        Index('idx_expense_category_parent', 'parent_id'),
    )

# ============================================
# EXPENSES TABLE
# ============================================

class Expense(Base):
    """Expense tracking and management"""
    __tablename__ = "expenses"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    supplier_id = Column(Integer, nullable=True)  # References suppliers table
    employee_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    paid_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Expense Information
    expense_number = Column(String(50), nullable=False, unique=True)
    expense_date = Column(Date, nullable=False)
    expense_type = Column(SQLEnum(ExpenseType), nullable=False)
    description = Column(Text, nullable=False)

    # Financial Information
    amount = Column(Numeric(15, 2), nullable=False)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Payment Information
    payment_method = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=True)
    is_reimbursable = Column(Boolean, default=False)
    reimbursed_amount = Column(Numeric(15, 2), nullable=True)
    reimbursement_date = Column(Date, nullable=True)

    # Receipt Information
    has_receipt = Column(Boolean, default=False)
    receipt_number = Column(String(100), nullable=True)
    receipt_file_path = Column(String(500), nullable=True)
    receipt_file_name = Column(String(255), nullable=True)

    # Vendor Information
    vendor_name = Column(String(255), nullable=True)
    vendor_invoice_number = Column(String(100), nullable=True)

    # Status and Approval
    status = Column(SQLEnum(ExpenseStatus), default=ExpenseStatus.PENDING, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Mileage (for travel expenses)
    mileage_km = Column(Numeric(10, 2), nullable=True)
    mileage_rate = Column(Numeric(10, 4), nullable=True)
    origin_location = Column(String(255), nullable=True)
    destination_location = Column(String(255), nullable=True)

    # Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)

    # Accounting
    is_billable = Column(Boolean, default=False)
    client_id = Column(Integer, nullable=True)  # References accounts.id from CRM
    is_posted = Column(Boolean, default=False)
    posted_date = Column(Date, nullable=True)
    accounting_period = Column(String(20), nullable=True)  # YYYY-MM

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    category = relationship("ExpenseCategory", back_populates="expenses")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_expense_status', 'status'),
        Index('idx_expense_date', 'expense_date'),
        Index('idx_expense_category', 'category_id'),
        Index('idx_expense_employee', 'employee_id'),
        Index('idx_expense_order', 'order_id'),
        Index('idx_expense_billable', 'is_billable', 'client_id'),
    )

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
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete='SET NULL'), nullable=True)
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
    expense_category_id = Column(Integer, ForeignKey('expense_categories.id'), nullable=True)

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

# ============================================
# VOUCHERS TABLE
# ============================================

class Voucher(Base):
    """Payment vouchers for formal payment authorization"""
    __tablename__ = "vouchers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete='SET NULL'), nullable=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
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
    )
