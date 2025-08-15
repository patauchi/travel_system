"""
Payments Module Schemas
Pydantic schemas for payment management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from common.enums import PaymentMethod, PaymentType, TransactionType

# ============================================
# PAYMENT SCHEMAS
# ============================================

class PaymentBase(BaseModel):
    """Base schema for payments"""
    invoice_id: Optional[int] = Field(None, description="Related invoice ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    account_id: Optional[int] = Field(None, description="Account ID from CRM service")
    contact_id: Optional[int] = Field(None, description="Contact ID from CRM service")
    payment_number: str = Field(..., description="Unique payment number")
    payment_date: date = Field(..., description="Date of payment")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field("USD", description="Currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method used")
    payment_type: PaymentType = Field(PaymentType.partial, description="Type of payment")
    transaction_type: TransactionType = Field(TransactionType.payment, description="Transaction type")
    reference_number: Optional[str] = Field(None, description="Reference number")
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    gateway_fee: Optional[Decimal] = Field(None, description="Gateway processing fee")
    bank_name: Optional[str] = Field(None, description="Bank name")
    account_number_last4: Optional[str] = Field(None, description="Last 4 digits of account")
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card")
    card_brand: Optional[str] = Field(None, description="Card brand (Visa, MasterCard, etc.)")
    card_type: Optional[str] = Field(None, description="Card type (credit, debit)")
    authorization_code: Optional[str] = Field(None, description="Authorization code")
    check_number: Optional[str] = Field(None, description="Check number if applicable")
    check_date: Optional[date] = Field(None, description="Check date")
    wire_reference: Optional[str] = Field(None, description="Wire transfer reference")
    digital_wallet_type: Optional[str] = Field(None, description="Digital wallet type")
    digital_transaction_id: Optional[str] = Field(None, description="Digital wallet transaction ID")
    status: str = Field("completed", description="Payment status")
    exchange_rate: Decimal = Field(1.0, description="Exchange rate if different currency")
    base_currency: Optional[str] = Field(None, description="Base currency")
    base_amount: Optional[Decimal] = Field(None, description="Amount in base currency")
    merchant_fee: Decimal = Field(0, description="Merchant processing fee")
    net_amount: Optional[Decimal] = Field(None, description="Net amount after fees")
    notes: Optional[str] = Field(None, description="Payment notes")
    internal_notes: Optional[str] = Field(None, description="Internal notes")
    customer_notes: Optional[str] = Field(None, description="Customer notes")

class PaymentCreate(PaymentBase):
    """Schema for creating payments"""
    pass

class PaymentUpdate(BaseModel):
    """Schema for updating payments"""
    payment_date: Optional[date] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    payment_type: Optional[PaymentType] = None
    transaction_type: Optional[TransactionType] = None
    reference_number: Optional[str] = None
    transaction_id: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    gateway_fee: Optional[Decimal] = None
    bank_name: Optional[str] = None
    account_number_last4: Optional[str] = None
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    card_type: Optional[str] = None
    authorization_code: Optional[str] = None
    check_number: Optional[str] = None
    check_date: Optional[date] = None
    wire_reference: Optional[str] = None
    digital_wallet_type: Optional[str] = None
    digital_transaction_id: Optional[str] = None
    status: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    base_currency: Optional[str] = None
    base_amount: Optional[Decimal] = None
    merchant_fee: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    """Schema for payment responses"""
    id: int
    processed_by: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    processing_status: Optional[str] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    is_settled: bool = False
    settled_date: Optional[date] = None
    settlement_reference: Optional[str] = None
    is_refund: bool = False
    refund_reason: Optional[str] = None
    original_payment_id: Optional[int] = None
    refund_fee: Optional[Decimal] = None
    is_disputed: bool = False
    dispute_date: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    dispute_amount: Optional[Decimal] = None
    dispute_status: Optional[str] = None
    dispute_resolved_date: Optional[datetime] = None
    risk_score: Optional[Decimal] = None
    fraud_check_status: Optional[str] = None
    fraud_check_notes: Optional[str] = None
    is_recurring: bool = False
    recurring_payment_id: Optional[int] = None
    subscription_id: Optional[str] = None
    billing_cycle: Optional[str] = None
    compliance_status: Optional[str] = None
    aml_check_status: Optional[str] = None
    kyc_verified: bool = False
    tax_withheld: Decimal = 0
    tax_jurisdiction: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PAYMENT GATEWAY SCHEMAS
# ============================================

class PaymentGatewayBase(BaseModel):
    """Base schema for payment gateways"""
    gateway_name: str = Field(..., description="Gateway name")
    gateway_code: str = Field(..., description="Unique gateway code")
    gateway_type: str = Field(..., description="Gateway type (stripe, paypal, etc.)")
    is_active: bool = Field(True, description="Whether gateway is active")
    is_test_mode: bool = Field(True, description="Whether in test mode")
    priority: int = Field(0, description="Gateway priority (lower = higher priority)")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    merchant_id: Optional[str] = Field(None, description="Merchant ID")
    supports_credit_cards: bool = Field(True, description="Supports credit cards")
    supports_debit_cards: bool = Field(True, description="Supports debit cards")
    supports_bank_transfer: bool = Field(False, description="Supports bank transfers")
    supports_digital_wallets: bool = Field(False, description="Supports digital wallets")
    supports_recurring: bool = Field(False, description="Supports recurring payments")
    supports_refunds: bool = Field(True, description="Supports refunds")
    supports_partial_refunds: bool = Field(True, description="Supports partial refunds")
    transaction_fee_percent: Decimal = Field(0, description="Transaction fee percentage")
    transaction_fee_fixed: Decimal = Field(0, description="Fixed transaction fee")
    refund_fee_percent: Decimal = Field(0, description="Refund fee percentage")
    refund_fee_fixed: Decimal = Field(0, description="Fixed refund fee")
    min_transaction_amount: Optional[Decimal] = Field(None, description="Minimum transaction amount")
    max_transaction_amount: Optional[Decimal] = Field(None, description="Maximum transaction amount")
    daily_transaction_limit: Optional[Decimal] = Field(None, description="Daily transaction limit")
    monthly_transaction_limit: Optional[Decimal] = Field(None, description="Monthly transaction limit")
    supported_currencies: Optional[List[str]] = Field(None, description="Supported currencies")
    default_currency: str = Field("USD", description="Default currency")
    authorization_time_minutes: Optional[int] = Field(None, description="Authorization time in minutes")
    settlement_time_days: Optional[int] = Field(None, description="Settlement time in days")
    refund_time_days: Optional[int] = Field(None, description="Refund time in days")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    webhook_events: Optional[List[str]] = Field(None, description="Webhook events")
    configuration_notes: Optional[str] = Field(None, description="Configuration notes")

class PaymentGatewayCreate(PaymentGatewayBase):
    """Schema for creating payment gateways"""
    api_key: Optional[str] = Field(None, description="API key (will be encrypted)")
    api_secret: Optional[str] = Field(None, description="API secret (will be encrypted)")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret (will be encrypted)")

class PaymentGatewayUpdate(BaseModel):
    """Schema for updating payment gateways"""
    gateway_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_test_mode: Optional[bool] = None
    priority: Optional[int] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    webhook_secret: Optional[str] = None
    merchant_id: Optional[str] = None
    supports_credit_cards: Optional[bool] = None
    supports_debit_cards: Optional[bool] = None
    supports_bank_transfer: Optional[bool] = None
    supports_digital_wallets: Optional[bool] = None
    supports_recurring: Optional[bool] = None
    supports_refunds: Optional[bool] = None
    supports_partial_refunds: Optional[bool] = None
    transaction_fee_percent: Optional[Decimal] = None
    transaction_fee_fixed: Optional[Decimal] = None
    refund_fee_percent: Optional[Decimal] = None
    refund_fee_fixed: Optional[Decimal] = None
    min_transaction_amount: Optional[Decimal] = None
    max_transaction_amount: Optional[Decimal] = None
    daily_transaction_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    supported_currencies: Optional[List[str]] = None
    default_currency: Optional[str] = None
    authorization_time_minutes: Optional[int] = None
    settlement_time_days: Optional[int] = None
    refund_time_days: Optional[int] = None
    webhook_url: Optional[str] = None
    webhook_events: Optional[List[str]] = None
    configuration_notes: Optional[str] = None

class PaymentGatewayResponse(PaymentGatewayBase):
    """Schema for payment gateway responses"""
    id: int
    last_health_check: Optional[datetime] = None
    health_status: Optional[str] = None
    error_rate_percent: Decimal = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PAYMENT ATTEMPT SCHEMAS
# ============================================

class PaymentAttemptBase(BaseModel):
    """Base schema for payment attempts"""
    payment_id: Optional[int] = Field(None, description="Related payment ID")
    gateway_id: int = Field(..., description="Gateway used for attempt")
    invoice_id: Optional[int] = Field(None, description="Related invoice ID")
    order_id: Optional[int] = Field(None, description="Related order ID")
    attempt_number: int = Field(..., description="Attempt number")
    attempt_date: datetime = Field(..., description="Date and time of attempt")
    amount: Decimal = Field(..., description="Attempted amount")
    currency: str = Field("USD", description="Currency code")
    gateway_response_code: Optional[str] = Field(None, description="Gateway response code")
    gateway_response_message: Optional[str] = Field(None, description="Gateway response message")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    gateway_reference: Optional[str] = Field(None, description="Gateway reference")
    status: str = Field(..., description="Attempt status")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_eligible: bool = Field(True, description="Whether retry is eligible")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    risk_score: Optional[Decimal] = Field(None, description="Risk score")
    decline_reason: Optional[str] = Field(None, description="Decline reason")
    cvv_result: Optional[str] = Field(None, description="CVV verification result")
    avs_result: Optional[str] = Field(None, description="Address verification result")

class PaymentAttemptCreate(PaymentAttemptBase):
    """Schema for creating payment attempts"""
    request_payload: Optional[Dict[str, Any]] = Field(None, description="Request payload")
    response_payload: Optional[Dict[str, Any]] = Field(None, description="Response payload")

class PaymentAttemptResponse(PaymentAttemptBase):
    """Schema for payment attempt responses"""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PAYMENT PROCESSING SCHEMAS
# ============================================

class PaymentProcessRequest(BaseModel):
    """Schema for payment processing requests"""
    invoice_id: Optional[int] = Field(None, description="Invoice to pay")
    order_id: Optional[int] = Field(None, description="Order to pay")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field("USD", description="Currency code")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    gateway_code: Optional[str] = Field(None, description="Preferred gateway code")

    # Card information (for card payments)
    card_number: Optional[str] = Field(None, description="Card number")
    card_expiry_month: Optional[int] = Field(None, description="Card expiry month")
    card_expiry_year: Optional[int] = Field(None, description="Card expiry year")
    card_cvv: Optional[str] = Field(None, description="Card CVV")
    card_holder_name: Optional[str] = Field(None, description="Card holder name")

    # Billing information
    billing_address: Optional[str] = Field(None, description="Billing address")
    billing_city: Optional[str] = Field(None, description="Billing city")
    billing_state: Optional[str] = Field(None, description="Billing state")
    billing_postal_code: Optional[str] = Field(None, description="Billing postal code")
    billing_country: Optional[str] = Field(None, description="Billing country")

    # Bank information (for bank transfers)
    bank_account_number: Optional[str] = Field(None, description="Bank account number")
    bank_routing_number: Optional[str] = Field(None, description="Bank routing number")
    bank_name: Optional[str] = Field(None, description="Bank name")

    # Digital wallet information
    wallet_type: Optional[str] = Field(None, description="Wallet type (paypal, apple_pay, etc.)")
    wallet_token: Optional[str] = Field(None, description="Wallet token")

    # Additional information
    customer_ip: Optional[str] = Field(None, description="Customer IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    notes: Optional[str] = Field(None, description="Payment notes")

class PaymentProcessResponse(BaseModel):
    """Schema for payment processing responses"""
    payment_id: Optional[int] = Field(None, description="Created payment ID")
    status: str = Field(..., description="Processing status")
    success: bool = Field(..., description="Whether payment was successful")
    transaction_id: Optional[str] = Field(None, description="Transaction ID")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    authorization_code: Optional[str] = Field(None, description="Authorization code")
    amount: Decimal = Field(..., description="Processed amount")
    currency: str = Field(..., description="Currency")
    gateway_fee: Optional[Decimal] = Field(None, description="Gateway fee")
    net_amount: Optional[Decimal] = Field(None, description="Net amount")
    risk_score: Optional[Decimal] = Field(None, description="Risk score")
    decline_reason: Optional[str] = Field(None, description="Decline reason if failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_eligible: bool = Field(True, description="Whether retry is eligible")
    processing_time_ms: Optional[int] = Field(None, description="Processing time")
    gateway_response: Optional[Dict[str, Any]] = Field(None, description="Full gateway response")

# ============================================
# REFUND SCHEMAS
# ============================================

class RefundRequest(BaseModel):
    """Schema for refund requests"""
    amount: Optional[Decimal] = Field(None, description="Refund amount (null for full refund)")
    reason: str = Field(..., description="Refund reason")
    notes: Optional[str] = Field(None, description="Additional notes")
    notify_customer: bool = Field(True, description="Whether to notify customer")

class RefundResponse(BaseModel):
    """Schema for refund responses"""
    refund_payment_id: int = Field(..., description="Created refund payment ID")
    original_payment_id: int = Field(..., description="Original payment ID")
    refund_amount: Decimal = Field(..., description="Refunded amount")
    refund_fee: Optional[Decimal] = Field(None, description="Refund processing fee")
    net_refund: Decimal = Field(..., description="Net refund amount")
    status: str = Field(..., description="Refund status")
    gateway_refund_id: Optional[str] = Field(None, description="Gateway refund ID")
    expected_settlement_days: Optional[int] = Field(None, description="Expected settlement time")

# ============================================
# DISPUTE SCHEMAS
# ============================================

class DisputeCreateRequest(BaseModel):
    """Schema for creating dispute records"""
    dispute_reason: str = Field(..., description="Dispute reason")
    dispute_amount: Decimal = Field(..., description="Disputed amount")
    evidence_files: Optional[List[str]] = Field(None, description="Evidence file paths")
    notes: Optional[str] = Field(None, description="Dispute notes")

class DisputeUpdateRequest(BaseModel):
    """Schema for updating disputes"""
    dispute_status: Optional[str] = Field(None, description="Dispute status")
    evidence_files: Optional[List[str]] = Field(None, description="Additional evidence files")
    notes: Optional[str] = Field(None, description="Updated notes")

class DisputeResponse(BaseModel):
    """Schema for dispute responses"""
    payment_id: int
    dispute_amount: Decimal
    dispute_reason: str
    dispute_status: str
    dispute_date: datetime
    dispute_resolved_date: Optional[datetime] = None
    evidence_files: Optional[List[str]] = None
    notes: Optional[str] = None

# ============================================
# LIST SCHEMAS
# ============================================

class PaymentListResponse(BaseModel):
    """Schema for payment list responses"""
    payments: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int

class PaymentGatewayListResponse(BaseModel):
    """Schema for payment gateway list responses"""
    gateways: List[PaymentGatewayResponse]
    total: int
    page: int
    size: int
    pages: int

class PaymentAttemptListResponse(BaseModel):
    """Schema for payment attempt list responses"""
    attempts: List[PaymentAttemptResponse]
    total: int
    page: int
    size: int
    pages: int

# ============================================
# SUMMARY SCHEMAS
# ============================================

class PaymentSummaryByMethod(BaseModel):
    """Schema for payment summary by method"""
    payment_method: PaymentMethod
    total_amount: Decimal
    count: int
    avg_amount: Decimal
    success_rate: Decimal

class PaymentSummaryByStatus(BaseModel):
    """Schema for payment summary by status"""
    status: str
    total_amount: Decimal
    count: int

class PaymentSummaryByGateway(BaseModel):
    """Schema for payment summary by gateway"""
    gateway_name: str
    gateway_code: str
    total_amount: Decimal
    count: int
    success_rate: Decimal
    avg_processing_time_ms: Optional[int]

class PaymentSummaryResponse(BaseModel):
    """Schema for comprehensive payment summary"""
    total_payments: int
    total_amount: Decimal
    total_refunds: Decimal
    total_fees: Decimal
    net_amount: Decimal
    success_rate: Decimal
    by_method: List[PaymentSummaryByMethod]
    by_status: List[PaymentSummaryByStatus]
    by_gateway: List[PaymentSummaryByGateway]
    dispute_count: int
    dispute_amount: Decimal
    chargeback_count: int
    chargeback_amount: Decimal
    avg_processing_time_ms: Optional[int]
    failed_payment_count: int
    retry_success_rate: Decimal
