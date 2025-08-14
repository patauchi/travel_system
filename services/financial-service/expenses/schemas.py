"""
Expenses Module Schemas
Pydantic schemas for expense management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from common.enums import ExpenseStatus, ExpenseType

# ============================================
# EXPENSE CATEGORY SCHEMAS
# ============================================

class ExpenseCategoryBase(BaseModel):
    """Base schema for expense categories"""
    name: str = Field(..., description="Category name")
    code: Optional[str] = Field(None, description="Category code")
    description: Optional[str] = Field(None, description="Category description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")
    budget_monthly: Optional[Decimal] = Field(None, description="Monthly budget amount")
    budget_yearly: Optional[Decimal] = Field(None, description="Yearly budget amount")
    account_code: Optional[str] = Field(None, description="Accounting code")
    tax_deductible: bool = Field(True, description="Whether expenses in this category are tax deductible")
    requires_receipt: bool = Field(True, description="Whether receipts are required")
    requires_approval: bool = Field(True, description="Whether approval is required")
    is_active: bool = Field(True, description="Whether the category is active")
    approval_limit: Optional[Decimal] = Field(None, description="Amount requiring approval")
    auto_approve_under: Optional[Decimal] = Field(None, description="Amount that can be auto-approved")

class ExpenseCategoryCreate(ExpenseCategoryBase):
    """Schema for creating expense categories"""
    pass

class ExpenseCategoryUpdate(BaseModel):
    """Schema for updating expense categories"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    budget_monthly: Optional[Decimal] = None
    budget_yearly: Optional[Decimal] = None
    account_code: Optional[str] = None
    tax_deductible: Optional[bool] = None
    requires_receipt: Optional[bool] = None
    requires_approval: Optional[bool] = None
    is_active: Optional[bool] = None
    approval_limit: Optional[Decimal] = None
    auto_approve_under: Optional[Decimal] = None

class ExpenseCategoryResponse(ExpenseCategoryBase):
    """Schema for expense category responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# EXPENSE SCHEMAS
# ============================================

class ExpenseBase(BaseModel):
    """Base schema for expenses"""
    category_id: int = Field(..., description="Expense category ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    supplier_id: Optional[int] = Field(None, description="Supplier ID")
    employee_id: Optional[str] = Field(None, description="Employee user ID")
    expense_number: str = Field(..., description="Unique expense number")
    expense_date: date = Field(..., description="Date of the expense")
    expense_type: ExpenseType = Field(..., description="Type of expense")
    description: str = Field(..., description="Expense description")
    amount: Decimal = Field(..., description="Expense amount before tax")
    tax_amount: Decimal = Field(0, description="Tax amount")
    total_amount: Decimal = Field(..., description="Total expense amount")
    currency: str = Field("USD", description="Currency code")
    payment_method: Optional[str] = Field(None, description="Payment method used")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    is_reimbursable: bool = Field(False, description="Whether this expense is reimbursable")
    has_receipt: bool = Field(False, description="Whether a receipt is attached")
    receipt_number: Optional[str] = Field(None, description="Receipt number")
    receipt_file_path: Optional[str] = Field(None, description="Path to receipt file")
    receipt_file_name: Optional[str] = Field(None, description="Receipt file name")
    vendor_name: Optional[str] = Field(None, description="Vendor name")
    vendor_invoice_number: Optional[str] = Field(None, description="Vendor invoice number")
    mileage_km: Optional[Decimal] = Field(None, description="Mileage in kilometers")
    mileage_rate: Optional[Decimal] = Field(None, description="Mileage rate per kilometer")
    origin_location: Optional[str] = Field(None, description="Origin location for travel")
    destination_location: Optional[str] = Field(None, description="Destination location for travel")
    notes: Optional[str] = Field(None, description="Additional notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes")
    is_billable: bool = Field(False, description="Whether this expense is billable to a client")
    client_id: Optional[int] = Field(None, description="Client ID if billable")
    accounting_period: Optional[str] = Field(None, description="Accounting period (YYYY-MM)")

class ExpenseCreate(ExpenseBase):
    """Schema for creating expenses"""
    pass

class ExpenseUpdate(BaseModel):
    """Schema for updating expenses"""
    category_id: Optional[int] = None
    order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    employee_id: Optional[str] = None
    expense_date: Optional[date] = None
    expense_type: Optional[ExpenseType] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    is_reimbursable: Optional[bool] = None
    has_receipt: Optional[bool] = None
    receipt_number: Optional[str] = None
    receipt_file_path: Optional[str] = None
    receipt_file_name: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_invoice_number: Optional[str] = None
    mileage_km: Optional[Decimal] = None
    mileage_rate: Optional[Decimal] = None
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    is_billable: Optional[bool] = None
    client_id: Optional[int] = None
    accounting_period: Optional[str] = None
    status: Optional[ExpenseStatus] = None
    rejection_reason: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    """Schema for expense responses"""
    id: int
    status: ExpenseStatus
    approved_by: Optional[str] = None
    paid_by: Optional[str] = None
    reimbursed_amount: Optional[Decimal] = None
    reimbursement_date: Optional[date] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    paid_at: Optional[datetime] = None
    is_posted: bool = False
    posted_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    category: Optional[ExpenseCategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# EXPENSE APPROVAL SCHEMAS
# ============================================

class ExpenseApprovalRequest(BaseModel):
    """Schema for expense approval requests"""
    action: str = Field(..., description="Action to take: approve or reject")
    notes: Optional[str] = Field(None, description="Approval/rejection notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection")

class ExpenseApprovalResponse(BaseModel):
    """Schema for expense approval responses"""
    expense_id: int
    action: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

# ============================================
# EXPENSE REIMBURSEMENT SCHEMAS
# ============================================

class ExpenseReimbursementRequest(BaseModel):
    """Schema for expense reimbursement requests"""
    amount: Decimal = Field(..., description="Amount to reimburse")
    reimbursement_date: date = Field(..., description="Date of reimbursement")
    payment_method: str = Field(..., description="Payment method for reimbursement")
    payment_reference: Optional[str] = Field(None, description="Payment reference")
    notes: Optional[str] = Field(None, description="Reimbursement notes")

class ExpenseReimbursementResponse(BaseModel):
    """Schema for expense reimbursement responses"""
    expense_id: int
    reimbursed_amount: Decimal
    reimbursement_date: date
    payment_method: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: datetime

# ============================================
# LIST SCHEMAS
# ============================================

class ExpenseCategoryListResponse(BaseModel):
    """Schema for expense category list responses"""
    categories: List[ExpenseCategoryResponse]
    total: int
    page: int
    size: int
    pages: int

class ExpenseListResponse(BaseModel):
    """Schema for expense list responses"""
    expenses: List[ExpenseResponse]
    total: int
    page: int
    size: int
    pages: int

# ============================================
# EXPENSE SUMMARY SCHEMAS
# ============================================

class ExpenseSummaryByCategory(BaseModel):
    """Schema for expense summary by category"""
    category_id: int
    category_name: str
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class ExpenseSummaryByStatus(BaseModel):
    """Schema for expense summary by status"""
    status: ExpenseStatus
    total_amount: Decimal
    count: int

class ExpenseSummaryByPeriod(BaseModel):
    """Schema for expense summary by period"""
    period: str  # YYYY-MM
    total_amount: Decimal
    count: int
    categories: List[ExpenseSummaryByCategory]

class ExpenseSummaryResponse(BaseModel):
    """Schema for comprehensive expense summary"""
    total_expenses: Decimal
    total_count: int
    by_status: List[ExpenseSummaryByStatus]
    by_category: List[ExpenseSummaryByCategory]
    by_period: List[ExpenseSummaryByPeriod]
    pending_approval_amount: Decimal
    pending_approval_count: int
    reimbursable_amount: Decimal
    reimbursable_count: int
