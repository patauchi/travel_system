"""
Voucher Module Schemas
Pydantic schemas for voucher management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

# ============================================
# VOUCHER STATUS ENUMS
# ============================================

from common.enums import VoucherStatus, VoucherType, PayeeType

# ============================================
# VOUCHER SCHEMAS
# ============================================

class VoucherBase(BaseModel):
    """Base schema for vouchers"""
    expense_id: Optional[int] = Field(None, description="Related expense ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    supplier_id: Optional[int] = Field(None, description="Related supplier ID")
    voucher_number: str = Field(..., description="Unique voucher number")
    voucher_date: date = Field(..., description="Date of the voucher")
    voucher_type: VoucherType = Field(..., description="Type of voucher")
    payee_name: str = Field(..., description="Name of the payee")
    payee_type: Optional[PayeeType] = Field(None, description="Type of payee")
    amount: Decimal = Field(..., description="Voucher amount")
    currency: str = Field("USD", description="Currency code")
    exchange_rate: Decimal = Field(1.0, description="Exchange rate if different currency")
    amount_in_words: Optional[str] = Field(None, description="Amount written in words")
    payment_method: Optional[str] = Field(None, description="Payment method")
    bank_account: Optional[str] = Field(None, description="Bank account for payment")
    check_number: Optional[str] = Field(None, description="Check number if applicable")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    purpose: str = Field(..., description="Purpose of the voucher")
    cost_center: Optional[str] = Field(None, description="Cost center code")
    project_code: Optional[str] = Field(None, description="Project code")
    status: VoucherStatus = Field(VoucherStatus.draft, description="Voucher status")
    accounting_period: Optional[str] = Field(None, description="Accounting period (YYYY-MM)")
    attachments: Optional[List[str]] = Field(None, description="List of attachment file paths")
    supporting_documents: Optional[str] = Field(None, description="Supporting documents description")
    notes: Optional[str] = Field(None, description="Additional notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes")

class VoucherCreate(VoucherBase):
    """Schema for creating vouchers"""
    pass

class VoucherUpdate(BaseModel):
    """Schema for updating vouchers"""
    expense_id: Optional[int] = None
    order_id: Optional[int] = None
    supplier_id: Optional[int] = None
    voucher_date: Optional[date] = None
    voucher_type: Optional[VoucherType] = None
    payee_name: Optional[str] = None
    payee_type: Optional[PayeeType] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    amount_in_words: Optional[str] = None
    payment_method: Optional[str] = None
    bank_account: Optional[str] = None
    check_number: Optional[str] = None
    payment_reference: Optional[str] = None
    purpose: Optional[str] = None
    cost_center: Optional[str] = None
    project_code: Optional[str] = None
    status: Optional[VoucherStatus] = None
    accounting_period: Optional[str] = None
    attachments: Optional[List[str]] = None
    supporting_documents: Optional[str] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

class VoucherResponse(VoucherBase):
    """Schema for voucher responses"""
    id: int
    created_by: str
    approved_by: Optional[str] = None
    paid_by: Optional[str] = None
    is_approved: bool = False
    approved_date: Optional[datetime] = None
    is_paid: bool = False
    paid_date: Optional[datetime] = None
    is_posted: bool = False
    posted_date: Optional[date] = None
    journal_entry_number: Optional[str] = None
    is_cancelled: bool = False
    cancelled_date: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# VOUCHER APPROVAL SCHEMAS
# ============================================

class VoucherApprovalRequest(BaseModel):
    """Schema for voucher approval requests"""
    action: str = Field(..., description="Action to take: approve or reject")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if rejecting")

class VoucherApprovalResponse(BaseModel):
    """Schema for voucher approval responses"""
    voucher_id: int
    action: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

# ============================================
# VOUCHER PAYMENT SCHEMAS
# ============================================

class VoucherPaymentRequest(BaseModel):
    """Schema for voucher payment requests"""
    payment_date: date = Field(..., description="Date of payment")
    payment_method: str = Field(..., description="Payment method used")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    bank_account: Optional[str] = Field(None, description="Bank account used")
    check_number: Optional[str] = Field(None, description="Check number if applicable")
    notes: Optional[str] = Field(None, description="Payment notes")

class VoucherPaymentResponse(BaseModel):
    """Schema for voucher payment responses"""
    voucher_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    payment_reference: Optional[str] = None
    bank_account: Optional[str] = None
    check_number: Optional[str] = None
    notes: Optional[str] = None
    paid_by: str
    paid_at: datetime

# ============================================
# VOUCHER CANCELLATION SCHEMAS
# ============================================

class VoucherCancellationRequest(BaseModel):
    """Schema for voucher cancellation requests"""
    cancellation_reason: str = Field(..., description="Reason for cancellation")
    notes: Optional[str] = Field(None, description="Additional cancellation notes")

class VoucherCancellationResponse(BaseModel):
    """Schema for voucher cancellation responses"""
    voucher_id: int
    cancellation_reason: str
    notes: Optional[str] = None
    cancelled_by: str
    cancelled_at: datetime

# ============================================
# VOUCHER POSTING SCHEMAS
# ============================================

class VoucherPostingRequest(BaseModel):
    """Schema for voucher posting to accounting"""
    accounting_period: str = Field(..., description="Accounting period (YYYY-MM)")
    journal_entry_number: Optional[str] = Field(None, description="Journal entry number")
    posted_date: date = Field(..., description="Date of posting")
    notes: Optional[str] = Field(None, description="Posting notes")

class VoucherPostingResponse(BaseModel):
    """Schema for voucher posting responses"""
    voucher_id: int
    accounting_period: str
    journal_entry_number: Optional[str] = None
    posted_date: date
    notes: Optional[str] = None
    posted_by: str
    posted_at: datetime

# ============================================
# LIST SCHEMAS
# ============================================

class VoucherListResponse(BaseModel):
    """Schema for voucher list responses"""
    vouchers: List[VoucherResponse]
    total: int
    page: int
    size: int
    pages: int

# ============================================
# VOUCHER SUMMARY SCHEMAS
# ============================================

class VoucherSummaryByStatus(BaseModel):
    """Schema for voucher summary by status"""
    status: VoucherStatus
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class VoucherSummaryByType(BaseModel):
    """Schema for voucher summary by type"""
    voucher_type: VoucherType
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class VoucherSummaryByPayee(BaseModel):
    """Schema for voucher summary by payee type"""
    payee_type: Optional[PayeeType]
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class VoucherSummaryByPeriod(BaseModel):
    """Schema for voucher summary by accounting period"""
    accounting_period: Optional[str]
    total_amount: Decimal
    count: int
    by_status: List[VoucherSummaryByStatus]

class VoucherSummaryResponse(BaseModel):
    """Schema for comprehensive voucher summary"""
    total_vouchers: int
    total_amount: Decimal
    by_status: List[VoucherSummaryByStatus]
    by_type: List[VoucherSummaryByType]
    by_payee: List[VoucherSummaryByPayee]
    by_period: List[VoucherSummaryByPeriod]
    pending_approval_count: int
    pending_approval_amount: Decimal
    approved_unpaid_count: int
    approved_unpaid_amount: Decimal
    posted_count: int
    posted_amount: Decimal

# ============================================
# BULK OPERATIONS SCHEMAS
# ============================================

class BulkVoucherApprovalRequest(BaseModel):
    """Schema for bulk voucher approval"""
    voucher_ids: List[int] = Field(..., description="List of voucher IDs to approve")
    approval_notes: Optional[str] = Field(None, description="Approval notes for all vouchers")

class BulkVoucherApprovalResponse(BaseModel):
    """Schema for bulk voucher approval response"""
    approved_count: int
    failed_count: int
    approved_vouchers: List[int]
    failed_vouchers: List[Dict[str, Any]]  # {voucher_id, error_message}

class BulkVoucherPaymentRequest(BaseModel):
    """Schema for bulk voucher payment"""
    voucher_ids: List[int] = Field(..., description="List of voucher IDs to pay")
    payment_date: date = Field(..., description="Payment date for all vouchers")
    payment_method: str = Field(..., description="Payment method for all vouchers")
    payment_reference: Optional[str] = Field(None, description="Payment reference")
    notes: Optional[str] = Field(None, description="Payment notes")

class BulkVoucherPaymentResponse(BaseModel):
    """Schema for bulk voucher payment response"""
    paid_count: int
    failed_count: int
    total_amount: Decimal
    paid_vouchers: List[int]
    failed_vouchers: List[Dict[str, Any]]  # {voucher_id, error_message}
