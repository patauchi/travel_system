"""
Expenses Module Models
Expense management models for financial service
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
from common.enums import ExpenseStatus, ExpenseType

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
    order_id = Column(Integer, nullable=True)  # References orders.id
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
    status = Column(SQLEnum(ExpenseStatus), default=ExpenseStatus.pending, index=True)
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
