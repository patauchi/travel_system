"""
Invoices Module Schemas
Pydantic schemas for invoice management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from common.enums import (
    InvoiceStatus, AccountsReceivableStatus, AccountsPayableStatus,
    AgingBucket, CollectionStatus
)

# ============================================
# INVOICE LINE SCHEMAS
# ============================================

class InvoiceLineBase(BaseModel):
    """Base schema for invoice lines"""
    line_number: int = Field(..., description="Line number within the invoice")
    description: str = Field(..., description="Description of the line item")
    order_line_id: Optional[int] = Field(None, description="Reference to order line ID")
    quantity: Decimal = Field(1, description="Quantity of items")
    unit_price: Decimal = Field(..., description="Unit price")
    discount_percent: Decimal = Field(0, description="Discount percentage")
    discount_amount: Decimal = Field(0, description="Discount amount")
    tax_rate: Decimal = Field(0, description="Tax rate")
    tax_amount: Decimal = Field(0, description="Tax amount")
    total_amount: Decimal = Field(..., description="Total amount for this line")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_taxable: bool = Field(True, description="Whether this line is taxable")
    product_code: Optional[str] = Field(None, description="Product code")
    service_code: Optional[str] = Field(None, description="Service code")

class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice lines"""
    pass

class InvoiceLineUpdate(BaseModel):
    """Schema for updating invoice lines"""
    line_number: Optional[int] = None
    description: Optional[str] = None
    order_line_id: Optional[int] = None
    quantity: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    is_taxable: Optional[bool] = None
    product_code: Optional[str] = None
    service_code: Optional[str] = None

class InvoiceLineResponse(InvoiceLineBase):
    """Schema for invoice line responses"""
    id: int
    invoice_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================
# INVOICE SCHEMAS
# ============================================

class InvoiceBase(BaseModel):
    """Base schema for invoices"""
    order_id: int = Field(..., description="Order ID this invoice is based on")
    account_id: Optional[int] = Field(None, description="Account ID from CRM service")
    contact_id: Optional[int] = Field(None, description="Contact ID from CRM service")
    invoice_number: str = Field(..., description="Unique invoice number")
    status: InvoiceStatus = Field(InvoiceStatus.draft, description="Invoice status")
    invoice_date: date = Field(..., description="Date the invoice was created")
    due_date: date = Field(..., description="Payment due date")
    sent_date: Optional[date] = Field(None, description="Date the invoice was sent")
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(0, description="Total tax amount")
    discount_amount: Decimal = Field(0, description="Total discount amount")
    total_amount: Decimal = Field(..., description="Total invoice amount")
    paid_amount: Decimal = Field(0, description="Amount already paid")
    balance_due: Decimal = Field(..., description="Remaining balance due")
    currency: str = Field("USD", description="Currency code")
    notes: Optional[str] = Field(None, description="Additional notes")
    terms_conditions: Optional[str] = Field(None, description="Terms and conditions")
    pdf_path: Optional[str] = Field(None, description="Path to PDF file")
    billing_name: Optional[str] = Field(None, description="Billing contact name")
    billing_address: Optional[str] = Field(None, description="Billing address")
    billing_city: Optional[str] = Field(None, description="Billing city")
    billing_state: Optional[str] = Field(None, description="Billing state")
    billing_postal_code: Optional[str] = Field(None, description="Billing postal code")
    billing_country: Optional[str] = Field(None, description="Billing country")

class InvoiceCreate(InvoiceBase):
    """Schema for creating invoices"""
    invoice_lines: Optional[List[InvoiceLineCreate]] = Field(None, description="Invoice line items")

class InvoiceUpdate(BaseModel):
    """Schema for updating invoices"""
    account_id: Optional[int] = None
    contact_id: Optional[int] = None
    status: Optional[InvoiceStatus] = None
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    sent_date: Optional[date] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    paid_amount: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    terms_conditions: Optional[str] = None
    pdf_path: Optional[str] = None
    billing_name: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_postal_code: Optional[str] = None
    billing_country: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    """Schema for invoice responses"""
    id: int
    created_by: Optional[str] = None
    paid_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    invoice_lines: List[InvoiceLineResponse] = []

    model_config = ConfigDict(from_attributes=True)

# ============================================
# ACCOUNTS RECEIVABLE SCHEMAS
# ============================================

class AccountsReceivableBase(BaseModel):
    """Base schema for accounts receivable"""
    account_id: int = Field(..., description="Account ID from CRM service")
    invoice_id: Optional[int] = Field(None, description="Related invoice ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    ar_number: str = Field(..., description="Unique AR number")
    transaction_date: date = Field(..., description="Transaction date")
    due_date: date = Field(..., description="Payment due date")
    original_amount: Decimal = Field(..., description="Original amount owed")
    paid_amount: Decimal = Field(0, description="Amount already paid")
    balance: Decimal = Field(..., description="Remaining balance")
    currency: str = Field("USD", description="Currency code")
    status: AccountsReceivableStatus = Field(AccountsReceivableStatus.open, description="AR status")
    days_overdue: int = Field(0, description="Number of days overdue")
    aging_bucket: Optional[AgingBucket] = Field(None, description="Aging bucket classification")
    collection_status: Optional[CollectionStatus] = Field(None, description="Collection status")
    last_collection_date: Optional[date] = Field(None, description="Last collection attempt date")
    next_collection_date: Optional[date] = Field(None, description="Next scheduled collection date")
    collection_notes: Optional[str] = Field(None, description="Collection notes")
    collection_attempts: int = Field(0, description="Number of collection attempts")
    is_on_credit_hold: bool = Field(False, description="Whether account is on credit hold")
    credit_hold_reason: Optional[str] = Field(None, description="Reason for credit hold")

class AccountsReceivableCreate(AccountsReceivableBase):
    """Schema for creating accounts receivable"""
    pass

class AccountsReceivableUpdate(BaseModel):
    """Schema for updating accounts receivable"""
    paid_amount: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    status: Optional[AccountsReceivableStatus] = None
    days_overdue: Optional[int] = None
    aging_bucket: Optional[AgingBucket] = None
    collection_status: Optional[CollectionStatus] = None
    last_collection_date: Optional[date] = None
    next_collection_date: Optional[date] = None
    collection_notes: Optional[str] = None
    collection_attempts: Optional[int] = None
    is_on_credit_hold: Optional[bool] = None
    credit_hold_reason: Optional[str] = None

class AccountsReceivableResponse(AccountsReceivableBase):
    """Schema for accounts receivable responses"""
    id: int
    is_written_off: bool = False
    written_off_date: Optional[date] = None
    written_off_amount: Optional[Decimal] = None
    written_off_reason: Optional[str] = None
    written_off_by: Optional[str] = None
    credit_hold_date: Optional[date] = None
    credit_hold_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# ACCOUNTS PAYABLE SCHEMAS
# ============================================

class AccountsPayableBase(BaseModel):
    """Base schema for accounts payable"""
    supplier_id: int = Field(..., description="Supplier ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    expense_id: Optional[int] = Field(None, description="Related expense ID")
    ap_number: str = Field(..., description="Unique AP number")
    invoice_number: Optional[str] = Field(None, description="Supplier's invoice number")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Payment due date")
    original_amount: Decimal = Field(..., description="Original amount owed")
    paid_amount: Decimal = Field(0, description="Amount already paid")
    balance: Decimal = Field(..., description="Remaining balance")
    currency: str = Field("USD", description="Currency code")
    status: AccountsPayableStatus = Field(AccountsPayableStatus.open, description="AP status")
    days_overdue: int = Field(0, description="Number of days overdue")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    discount_terms: Optional[str] = Field(None, description="Discount terms")
    early_payment_discount: Optional[Decimal] = Field(None, description="Early payment discount percentage")
    is_approved: bool = Field(False, description="Whether AP is approved for payment")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    is_disputed: bool = Field(False, description="Whether AP is disputed")
    dispute_reason: Optional[str] = Field(None, description="Dispute reason")
    notes: Optional[str] = Field(None, description="Additional notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes")

class AccountsPayableCreate(AccountsPayableBase):
    """Schema for creating accounts payable"""
    pass

class AccountsPayableUpdate(BaseModel):
    """Schema for updating accounts payable"""
    paid_amount: Optional[Decimal] = None
    balance: Optional[Decimal] = None
    status: Optional[AccountsPayableStatus] = None
    days_overdue: Optional[int] = None
    payment_terms: Optional[str] = None
    discount_terms: Optional[str] = None
    early_payment_discount: Optional[Decimal] = None
    is_approved: Optional[bool] = None
    approval_notes: Optional[str] = None
    is_disputed: Optional[bool] = None
    dispute_reason: Optional[str] = None
    dispute_date: Optional[date] = None
    dispute_resolved_date: Optional[date] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None

class AccountsPayableResponse(AccountsPayableBase):
    """Schema for accounts payable responses"""
    id: int
    approved_by: Optional[str] = None
    approved_date: Optional[datetime] = None
    dispute_date: Optional[date] = None
    dispute_resolved_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# INVOICE ACTIONS SCHEMAS
# ============================================

class InvoiceSendRequest(BaseModel):
    """Schema for sending invoice"""
    email_addresses: List[str] = Field(..., description="Email addresses to send to")
    subject: Optional[str] = Field(None, description="Email subject")
    message: Optional[str] = Field(None, description="Email message")
    send_pdf: bool = Field(True, description="Whether to attach PDF")

class InvoiceSendResponse(BaseModel):
    """Schema for invoice send response"""
    invoice_id: int
    sent_to: List[str]
    sent_at: datetime
    email_subject: str
    pdf_attached: bool

class InvoicePaymentRequest(BaseModel):
    """Schema for recording invoice payment"""
    amount: Decimal = Field(..., description="Payment amount")
    payment_date: date = Field(..., description="Payment date")
    payment_method: str = Field(..., description="Payment method")
    payment_reference: Optional[str] = Field(None, description="Payment reference")
    notes: Optional[str] = Field(None, description="Payment notes")

class InvoicePaymentResponse(BaseModel):
    """Schema for invoice payment response"""
    invoice_id: int
    amount: Decimal
    payment_date: date
    payment_method: str
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
    new_balance: Decimal
    is_fully_paid: bool

# ============================================
# WRITE-OFF SCHEMAS
# ============================================

class WriteOffRequest(BaseModel):
    """Schema for write-off requests"""
    amount: Decimal = Field(..., description="Amount to write off")
    reason: str = Field(..., description="Reason for write-off")
    notes: Optional[str] = Field(None, description="Additional notes")

class WriteOffResponse(BaseModel):
    """Schema for write-off responses"""
    ar_id: int
    amount: Decimal
    reason: str
    notes: Optional[str] = None
    written_off_by: str
    written_off_at: datetime

# ============================================
# CREDIT HOLD SCHEMAS
# ============================================

class CreditHoldRequest(BaseModel):
    """Schema for credit hold requests"""
    reason: str = Field(..., description="Reason for credit hold")
    notes: Optional[str] = Field(None, description="Additional notes")

class CreditHoldResponse(BaseModel):
    """Schema for credit hold responses"""
    ar_id: int
    reason: str
    notes: Optional[str] = None
    credit_hold_by: str
    credit_hold_at: datetime

class CreditHoldReleaseRequest(BaseModel):
    """Schema for credit hold release requests"""
    release_reason: str = Field(..., description="Reason for releasing credit hold")
    notes: Optional[str] = Field(None, description="Additional notes")

# ============================================
# LIST SCHEMAS
# ============================================

class InvoiceListResponse(BaseModel):
    """Schema for invoice list responses"""
    invoices: List[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int

class InvoiceLineListResponse(BaseModel):
    """Schema for invoice line list responses"""
    invoice_lines: List[InvoiceLineResponse]
    total: int
    page: int
    size: int
    pages: int

class AccountsReceivableListResponse(BaseModel):
    """Schema for accounts receivable list responses"""
    accounts_receivable: List[AccountsReceivableResponse]
    total: int
    page: int
    size: int
    pages: int

class AccountsPayableListResponse(BaseModel):
    """Schema for accounts payable list responses"""
    accounts_payable: List[AccountsPayableResponse]
    total: int
    page: int
    size: int
    pages: int

# ============================================
# SUMMARY SCHEMAS
# ============================================

class InvoiceSummaryByStatus(BaseModel):
    """Schema for invoice summary by status"""
    status: InvoiceStatus
    total_amount: Decimal
    count: int
    avg_amount: Decimal

class InvoiceSummaryByAge(BaseModel):
    """Schema for invoice summary by age"""
    age_bucket: str  # "current", "1-30", "31-60", "61-90", "90+"
    total_amount: Decimal
    count: int

class AccountsReceivableSummary(BaseModel):
    """Schema for AR summary"""
    total_outstanding: Decimal
    total_overdue: Decimal
    by_aging: List[InvoiceSummaryByAge]
    by_status: List[AccountsReceivableResponse]
    credit_hold_amount: Decimal
    credit_hold_count: int

class AccountsPayableSummary(BaseModel):
    """Schema for AP summary"""
    total_outstanding: Decimal
    total_overdue: Decimal
    by_status: List[AccountsPayableResponse]
    pending_approval_amount: Decimal
    pending_approval_count: int
    disputed_amount: Decimal
    disputed_count: int

class InvoiceSummaryResponse(BaseModel):
    """Schema for comprehensive invoice summary"""
    total_invoices: int
    total_amount: Decimal
    total_paid: Decimal
    total_outstanding: Decimal
    by_status: List[InvoiceSummaryByStatus]
    by_age: List[InvoiceSummaryByAge]
    ar_summary: AccountsReceivableSummary
    ap_summary: AccountsPayableSummary
    overdue_invoices_count: int
    overdue_amount: Decimal
