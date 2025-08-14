"""
Petty Cash Module Schemas
Pydantic schemas for petty cash management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from common.enums import PettyCashTransactionType, PettyCashStatus

# ============================================
# PETTY CASH SCHEMAS
# ============================================

class PettyCashBase(BaseModel):
    """Base schema for petty cash funds"""
    fund_name: str = Field(..., description="Name of the petty cash fund")
    fund_code: Optional[str] = Field(None, description="Unique code for the fund")
    description: Optional[str] = Field(None, description="Description of the fund")
    custodian_id: str = Field(..., description="User ID of the fund custodian")
    location: Optional[str] = Field(None, description="Physical location of the fund")
    initial_amount: Decimal = Field(..., description="Initial fund amount")
    current_balance: Decimal = Field(..., description="Current balance of the fund")
    minimum_balance: Decimal = Field(0, description="Minimum balance threshold")
    maximum_balance: Optional[Decimal] = Field(None, description="Maximum balance allowed")
    replenishment_amount: Optional[Decimal] = Field(None, description="Standard replenishment amount")
    status: PettyCashStatus = Field(PettyCashStatus.OPEN, description="Status of the fund")
    is_active: bool = Field(True, description="Whether the fund is active")
    reconciliation_frequency: str = Field("monthly", description="How often to reconcile (daily, weekly, monthly)")
    requires_receipt: bool = Field(True, description="Whether receipts are required for transactions")
    max_transaction_amount: Optional[Decimal] = Field(None, description="Maximum amount per transaction")
    allowed_expense_categories: Optional[List[int]] = Field(None, description="Allowed expense category IDs")

class PettyCashCreate(PettyCashBase):
    """Schema for creating petty cash funds"""
    pass

class PettyCashUpdate(BaseModel):
    """Schema for updating petty cash funds"""
    fund_name: Optional[str] = None
    fund_code: Optional[str] = None
    description: Optional[str] = None
    custodian_id: Optional[str] = None
    location: Optional[str] = None
    current_balance: Optional[Decimal] = None
    minimum_balance: Optional[Decimal] = None
    maximum_balance: Optional[Decimal] = None
    replenishment_amount: Optional[Decimal] = None
    status: Optional[PettyCashStatus] = None
    is_active: Optional[bool] = None
    reconciliation_frequency: Optional[str] = None
    requires_receipt: Optional[bool] = None
    max_transaction_amount: Optional[Decimal] = None
    allowed_expense_categories: Optional[List[int]] = None
    audit_notes: Optional[str] = None

class PettyCashResponse(PettyCashBase):
    """Schema for petty cash fund responses"""
    id: int
    last_reconciled_date: Optional[date] = None
    last_reconciled_by: Optional[str] = None
    last_audit_date: Optional[date] = None
    last_audited_by: Optional[str] = None
    audit_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PETTY CASH TRANSACTION SCHEMAS
# ============================================

class PettyCashTransactionBase(BaseModel):
    """Base schema for petty cash transactions"""
    petty_cash_id: int = Field(..., description="Petty cash fund ID")
    expense_id: Optional[int] = Field(None, description="Related expense ID")
    transaction_number: str = Field(..., description="Unique transaction number")
    transaction_date: datetime = Field(..., description="Date and time of transaction")
    transaction_type: PettyCashTransactionType = Field(..., description="Type of transaction")
    amount: Decimal = Field(..., description="Transaction amount")
    balance_before: Decimal = Field(..., description="Balance before transaction")
    balance_after: Decimal = Field(..., description="Balance after transaction")
    description: str = Field(..., description="Transaction description")
    reference_number: Optional[str] = Field(None, description="Reference number")
    vendor_name: Optional[str] = Field(None, description="Vendor name")
    has_receipt: bool = Field(False, description="Whether receipt is attached")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    receipt_file_path: Optional[str] = Field(None, description="Path to receipt file")
    expense_category_id: Optional[int] = Field(None, description="Expense category ID")
    requires_approval: bool = Field(False, description="Whether transaction requires approval")
    notes: Optional[str] = Field(None, description="Additional notes")

class PettyCashTransactionCreate(PettyCashTransactionBase):
    """Schema for creating petty cash transactions"""
    pass

class PettyCashTransactionUpdate(BaseModel):
    """Schema for updating petty cash transactions"""
    expense_id: Optional[int] = None
    transaction_date: Optional[datetime] = None
    transaction_type: Optional[PettyCashTransactionType] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    vendor_name: Optional[str] = None
    has_receipt: Optional[bool] = None
    receipt_number: Optional[str] = None
    receipt_file_path: Optional[str] = None
    expense_category_id: Optional[int] = None
    notes: Optional[str] = None
    approval_notes: Optional[str] = None

class PettyCashTransactionResponse(PettyCashTransactionBase):
    """Schema for petty cash transaction responses"""
    id: int
    performed_by: str
    approved_by: Optional[str] = None
    is_approved: bool = False
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    is_reconciled: bool = False
    reconciled_date: Optional[date] = None
    reconciled_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PETTY CASH APPROVAL SCHEMAS
# ============================================

class PettyCashTransactionApprovalRequest(BaseModel):
    """Schema for petty cash transaction approval requests"""
    action: str = Field(..., description="Action to take: approve or reject")
    approval_notes: Optional[str] = Field(None, description="Approval notes")

class PettyCashTransactionApprovalResponse(BaseModel):
    """Schema for petty cash transaction approval responses"""
    transaction_id: int
    action: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

# ============================================
# PETTY CASH RECONCILIATION SCHEMAS
# ============================================

class PettyCashReconciliationRequest(BaseModel):
    """Schema for petty cash reconciliation requests"""
    reconciliation_date: date = Field(..., description="Date of reconciliation")
    actual_balance: Decimal = Field(..., description="Actual counted balance")
    discrepancy_reason: Optional[str] = Field(None, description="Reason for any discrepancy")
    notes: Optional[str] = Field(None, description="Reconciliation notes")

class PettyCashReconciliationResponse(BaseModel):
    """Schema for petty cash reconciliation responses"""
    petty_cash_id: int
    reconciliation_date: date
    book_balance: Decimal
    actual_balance: Decimal
    discrepancy: Decimal
    discrepancy_reason: Optional[str] = None
    notes: Optional[str] = None
    reconciled_by: str
    reconciled_at: datetime
    transactions_reconciled: int

# ============================================
# PETTY CASH REPLENISHMENT SCHEMAS
# ============================================

class PettyCashReplenishmentRequest(BaseModel):
    """Schema for petty cash replenishment requests"""
    amount: Decimal = Field(..., description="Amount to replenish")
    replenishment_date: date = Field(..., description="Date of replenishment")
    payment_method: str = Field(..., description="Payment method used")
    reference_number: Optional[str] = Field(None, description="Reference number")
    notes: Optional[str] = Field(None, description="Replenishment notes")

class PettyCashReplenishmentResponse(BaseModel):
    """Schema for petty cash replenishment responses"""
    petty_cash_id: int
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    replenishment_date: date
    payment_method: str
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    processed_by: str
    processed_at: datetime

# ============================================
# LIST SCHEMAS
# ============================================

class PettyCashListResponse(BaseModel):
    """Schema for petty cash fund list responses"""
    funds: List[PettyCashResponse]
    total: int
    page: int
    size: int
    pages: int

class PettyCashTransactionListResponse(BaseModel):
    """Schema for petty cash transaction list responses"""
    transactions: List[PettyCashTransactionResponse]
    total: int
    page: int
    size: int
    pages: int

# ============================================
# SUMMARY SCHEMAS
# ============================================

class PettyCashSummaryByType(BaseModel):
    """Schema for petty cash summary by transaction type"""
    transaction_type: PettyCashTransactionType
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class PettyCashSummaryByCategory(BaseModel):
    """Schema for petty cash summary by expense category"""
    category_id: Optional[int]
    category_name: Optional[str]
    total_amount: Decimal
    count: int

class PettyCashFundSummary(BaseModel):
    """Schema for individual fund summary"""
    fund_id: int
    fund_name: str
    current_balance: Decimal
    total_transactions: int
    total_expenses: Decimal
    total_deposits: Decimal
    last_transaction_date: Optional[datetime]
    days_since_reconciliation: Optional[int]

class PettyCashSummaryResponse(BaseModel):
    """Schema for comprehensive petty cash summary"""
    total_funds: int
    active_funds: int
    total_balance: Decimal
    total_transactions: int
    by_type: List[PettyCashSummaryByType]
    by_category: List[PettyCashSummaryByCategory]
    fund_summaries: List[PettyCashFundSummary]
    funds_needing_reconciliation: int
    funds_below_minimum: int
    pending_approvals: int
