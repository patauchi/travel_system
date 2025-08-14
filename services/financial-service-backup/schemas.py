"""
Financial Service - Pydantic Schemas
Data validation and serialization schemas for financial operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID


# ============================================
# ENUMS
# ============================================

class TransactionType(str, Enum):
    """Types of financial transactions"""
    CHARGE = "charge"
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    COMMISSION = "commission"
    FEE = "fee"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"


class PaymentStatus(str, Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Available payment methods"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    CHECK = "check"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    WIRE_TRANSFER = "wire_transfer"
    CRYPTO = "crypto"
    OTHER = "other"


class InvoiceStatus(str, Enum):
    """Invoice status"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    MXN = "MXN"
    BRL = "BRL"
    JPY = "JPY"
    CNY = "CNY"
    INR = "INR"


# ============================================
# TRANSACTION SCHEMAS
# ============================================

class TransactionBase(BaseModel):
    """Base transaction schema"""
    type: TransactionType
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Currency = Field(default=Currency.USD)
    description: Optional[str] = Field(None, max_length=500)
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[str] = Field(None, max_length=100)
    booking_id: Optional[int] = None
    customer_id: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction"""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction"""
    status: Optional[TransactionStatus] = None
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    status_notes: Optional[str] = Field(None, max_length=1000)


class TransactionResponse(TransactionBase):
    """Transaction response schema"""
    id: int
    transaction_number: str
    status: TransactionStatus
    payment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    status_notes: Optional[str] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# ============================================
# PAYMENT SCHEMAS
# ============================================

class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Currency = Field(default=Currency.USD)
    payment_method: PaymentMethod
    customer_id: Optional[int] = None
    booking_id: Optional[int] = None
    invoice_id: Optional[int] = None
    transaction_id: Optional[int] = None
    gateway: Optional[str] = Field(None, max_length=50)
    gateway_transaction_id: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PaymentCreate(PaymentBase):
    """Schema for creating a payment"""
    pass


class PaymentUpdate(BaseModel):
    """Schema for updating a payment"""
    status: Optional[PaymentStatus] = None
    gateway_response: Optional[Dict[str, Any]] = None
    notes: Optional[str] = Field(None, max_length=1000)


class PaymentResponse(PaymentBase):
    """Payment response schema"""
    id: int
    payment_number: str
    status: PaymentStatus
    gateway_response: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    refund_amount: Optional[Decimal] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# ============================================
# INVOICE SCHEMAS
# ============================================

class InvoiceLineBase(BaseModel):
    """Base invoice line item schema"""
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class InvoiceLineCreate(InvoiceLineBase):
    """Schema for creating invoice line item"""
    pass


class InvoiceLineResponse(InvoiceLineBase):
    """Invoice line item response schema"""
    id: int
    invoice_id: int
    amount: Decimal
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    customer_id: int
    booking_id: Optional[int] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    currency: Currency = Field(default=Currency.USD)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=1000)
    terms_conditions: Optional[str] = Field(None, max_length=2000)
    billing_address: Optional[Dict[str, str]] = None
    shipping_address: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class InvoiceCreate(InvoiceBase):
    """Schema for creating an invoice"""
    line_items: List[InvoiceLineCreate] = Field(..., min_items=1)

    @validator('line_items')
    def validate_line_items(cls, v):
        if not v:
            raise ValueError('Invoice must have at least one line item')
        return v


class InvoiceUpdate(BaseModel):
    """Schema for updating an invoice"""
    status: Optional[InvoiceStatus] = None
    due_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    paid_amount: Optional[Decimal] = Field(None, ge=0)
    payment_date: Optional[date] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema"""
    id: int
    invoice_number: str
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Optional[Decimal] = None
    balance_due: Optional[Decimal] = None
    line_items: Optional[List[InvoiceLineResponse]] = None
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# ============================================
# BALANCE & REPORTS SCHEMAS
# ============================================

class BalanceResponse(BaseModel):
    """Balance summary response"""
    total_charges: float
    total_payments: float
    total_invoiced: float
    total_paid: float
    pending_amount: float
    balance: float
    customer_id: Optional[int] = None
    booking_id: Optional[int] = None
    as_of: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FinancialReportItem(BaseModel):
    """Individual item in financial report"""
    period: str
    total_revenue: float
    total_payments: float
    total_refunds: float
    total_fees: float
    net_revenue: float
    transaction_count: int
    payment_count: int
    invoice_count: int


class FinancialReportResponse(BaseModel):
    """Financial report response"""
    period_start: date
    period_end: date
    currency: Currency
    summary: Dict[str, float]
    data: List[FinancialReportItem]
    generated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class RefundRequest(BaseModel):
    """Request to process a refund"""
    payment_id: int
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    reason: str = Field(..., max_length=500)
    notify_customer: bool = Field(default=True)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Refund amount must be greater than 0')
        return v


class RefundResponse(BaseModel):
    """Refund processing response"""
    id: int
    refund_number: str
    payment_id: int
    amount: Decimal
    status: PaymentStatus
    reason: str
    processed_at: Optional[datetime] = None
    gateway_refund_id: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }


# ============================================
# STATISTICS SCHEMAS
# ============================================

class PaymentStatistics(BaseModel):
    """Payment statistics response"""
    total_payments: int
    successful_payments: int
    failed_payments: int
    pending_payments: int
    total_amount: float
    average_amount: float
    by_method: Dict[str, int]
    by_status: Dict[str, int]
    period: Optional[str] = None


class InvoiceStatistics(BaseModel):
    """Invoice statistics response"""
    total_invoices: int
    paid_invoices: int
    overdue_invoices: int
    cancelled_invoices: int
    total_amount: float
    paid_amount: float
    outstanding_amount: float
    average_invoice_value: float
    average_payment_time_days: Optional[float] = None
    period: Optional[str] = None


class TransactionStatistics(BaseModel):
    """Transaction statistics response"""
    total_transactions: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    total_volume: float
    average_transaction_value: float
    success_rate: float
    period: Optional[str] = None
