"""
Payments Module Models
Payment processing models for financial service
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
from common.enums import PaymentMethod, PaymentType, TransactionType

# ============================================
# PAYMENT TABLE
# ============================================

class Payment(Base):
    """Payment transactions for invoices and orders"""
    __tablename__ = "payments"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    invoice_id = Column(Integer, nullable=True)  # References invoices.id
    order_id = Column(Integer, nullable=True)  # References orders.id
    account_id = Column(Integer, nullable=True)  # References accounts.id from CRM service
    contact_id = Column(Integer, nullable=True)  # References contacts.id from CRM service
    processed_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id

    # Payment Information
    payment_number = Column(String(50), nullable=False, unique=True)
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Payment Details
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_type = Column(SQLEnum(PaymentType), default=PaymentType.PARTIAL)
    transaction_type = Column(SQLEnum(TransactionType), default=TransactionType.PAYMENT)

    # Transaction Details
    reference_number = Column(String(100), nullable=True)
    transaction_id = Column(String(255), nullable=True)  # External transaction ID
    gateway_response = Column(JSON, nullable=True)  # Store gateway response
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_fee = Column(Numeric(15, 2), nullable=True)

    # Bank/Card Information (encrypted in production)
    bank_name = Column(String(100), nullable=True)
    account_number_last4 = Column(String(4), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_brand = Column(String(50), nullable=True)
    card_type = Column(String(50), nullable=True)  # credit, debit
    authorization_code = Column(String(50), nullable=True)

    # Check Information
    check_number = Column(String(50), nullable=True)
    check_date = Column(Date, nullable=True)
    bank_routing_number = Column(String(20), nullable=True)

    # Wire Transfer Information
    wire_reference = Column(String(100), nullable=True)
    correspondent_bank = Column(String(100), nullable=True)
    swift_code = Column(String(20), nullable=True)

    # Digital Payment Information
    digital_wallet_type = Column(String(50), nullable=True)  # paypal, apple_pay, google_pay
    digital_transaction_id = Column(String(255), nullable=True)

    # Status and Processing
    status = Column(String(50), default='completed')  # pending, processing, completed, failed, refunded, cancelled
    processing_status = Column(String(50), nullable=True)  # submitted, authorized, captured, settled
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), nullable=True)

    # Exchange Rate Information
    exchange_rate = Column(Numeric(10, 6), default=1.0)
    base_currency = Column(String(3), nullable=True)
    base_amount = Column(Numeric(15, 2), nullable=True)

    # Settlement Information
    is_settled = Column(Boolean, default=False)
    settled_date = Column(Date, nullable=True)
    settlement_reference = Column(String(100), nullable=True)
    merchant_fee = Column(Numeric(15, 2), default=0)
    net_amount = Column(Numeric(15, 2), nullable=True)

    # Notes and Communication
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    customer_notes = Column(Text, nullable=True)

    # Refund Information (if applicable)
    is_refund = Column(Boolean, default=False)
    refund_reason = Column(Text, nullable=True)
    original_payment_id = Column(Integer, ForeignKey('payments.id'), nullable=True)
    refund_fee = Column(Numeric(15, 2), nullable=True)

    # Dispute Information
    is_disputed = Column(Boolean, default=False)
    dispute_date = Column(DateTime(timezone=True), nullable=True)
    dispute_reason = Column(Text, nullable=True)
    dispute_amount = Column(Numeric(15, 2), nullable=True)
    dispute_status = Column(String(50), nullable=True)  # open, won, lost, pending
    dispute_resolved_date = Column(DateTime(timezone=True), nullable=True)

    # Risk and Fraud Detection
    risk_score = Column(Numeric(5, 2), nullable=True)
    fraud_check_status = Column(String(50), nullable=True)  # passed, failed, review
    fraud_check_notes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Recurring Payment Information
    is_recurring = Column(Boolean, default=False)
    recurring_payment_id = Column(Integer, nullable=True)  # References recurring_payments.id
    subscription_id = Column(String(100), nullable=True)
    billing_cycle = Column(String(50), nullable=True)  # monthly, quarterly, yearly

    # Compliance and Audit
    compliance_status = Column(String(50), nullable=True)  # compliant, review, flagged
    aml_check_status = Column(String(50), nullable=True)  # passed, failed, pending
    kyc_verified = Column(Boolean, default=False)
    tax_withheld = Column(Numeric(15, 2), default=0)
    tax_jurisdiction = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    refunds = relationship("Payment", backref="original_payment", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_payment_invoice_id', 'invoice_id'),
        Index('idx_payment_order_id', 'order_id'),
        Index('idx_payment_date', 'payment_date'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_transaction_id', 'transaction_id'),
        Index('idx_payment_gateway_transaction_id', 'gateway_transaction_id'),
        Index('idx_payment_reference', 'reference_number'),
        Index('idx_payment_account', 'account_id'),
        Index('idx_payment_contact', 'contact_id'),
        Index('idx_payment_processed_by', 'processed_by'),
        Index('idx_payment_verification', 'is_verified', 'verified_at'),
        Index('idx_payment_settlement', 'is_settled', 'settled_date'),
        Index('idx_payment_refund', 'is_refund', 'original_payment_id'),
        Index('idx_payment_dispute', 'is_disputed', 'dispute_status'),
        Index('idx_payment_recurring', 'is_recurring', 'recurring_payment_id'),
        Index('idx_payment_risk', 'risk_score', 'fraud_check_status'),
        Index('idx_payment_compliance', 'compliance_status', 'aml_check_status'),
    )

# ============================================
# PAYMENT GATEWAY CONFIGURATION TABLE
# ============================================

class PaymentGateway(Base):
    """Payment gateway configuration"""
    __tablename__ = "payment_gateways"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Gateway Information
    gateway_name = Column(String(100), nullable=False)
    gateway_code = Column(String(50), nullable=False, unique=True)
    gateway_type = Column(String(50), nullable=False)  # stripe, paypal, square, authorize_net

    # Configuration
    is_active = Column(Boolean, default=True)
    is_test_mode = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Lower number = higher priority

    # API Configuration (encrypted in production)
    api_endpoint = Column(String(255), nullable=True)
    api_key = Column(Text, nullable=True)  # Should be encrypted
    api_secret = Column(Text, nullable=True)  # Should be encrypted
    webhook_secret = Column(Text, nullable=True)  # Should be encrypted
    merchant_id = Column(String(100), nullable=True)

    # Supported Features
    supports_credit_cards = Column(Boolean, default=True)
    supports_debit_cards = Column(Boolean, default=True)
    supports_bank_transfer = Column(Boolean, default=False)
    supports_digital_wallets = Column(Boolean, default=False)
    supports_recurring = Column(Boolean, default=False)
    supports_refunds = Column(Boolean, default=True)
    supports_partial_refunds = Column(Boolean, default=True)

    # Fee Structure
    transaction_fee_percent = Column(Numeric(5, 4), default=0)
    transaction_fee_fixed = Column(Numeric(10, 2), default=0)
    refund_fee_percent = Column(Numeric(5, 4), default=0)
    refund_fee_fixed = Column(Numeric(10, 2), default=0)

    # Limits
    min_transaction_amount = Column(Numeric(15, 2), nullable=True)
    max_transaction_amount = Column(Numeric(15, 2), nullable=True)
    daily_transaction_limit = Column(Numeric(15, 2), nullable=True)
    monthly_transaction_limit = Column(Numeric(15, 2), nullable=True)

    # Currency Support
    supported_currencies = Column(JSON, nullable=True)  # Array of currency codes
    default_currency = Column(String(3), default='USD')

    # Processing Times
    authorization_time_minutes = Column(Integer, nullable=True)
    settlement_time_days = Column(Integer, nullable=True)
    refund_time_days = Column(Integer, nullable=True)

    # Webhook Configuration
    webhook_url = Column(String(500), nullable=True)
    webhook_events = Column(JSON, nullable=True)  # Array of event types
    webhook_signature_method = Column(String(50), nullable=True)

    # Notes and Configuration
    configuration_notes = Column(Text, nullable=True)
    setup_instructions = Column(Text, nullable=True)

    # Status
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    health_status = Column(String(50), nullable=True)  # healthy, degraded, down
    error_rate_percent = Column(Numeric(5, 2), default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_gateway_active', 'is_active'),
        Index('idx_gateway_priority', 'priority'),
        Index('idx_gateway_type', 'gateway_type'),
        Index('idx_gateway_health', 'health_status', 'last_health_check'),
    )

# ============================================
# PAYMENT ATTEMPT TABLE
# ============================================

class PaymentAttempt(Base):
    """Track payment attempts for failed transactions"""
    __tablename__ = "payment_attempts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=True)
    gateway_id = Column(Integer, ForeignKey('payment_gateways.id'), nullable=False)
    invoice_id = Column(Integer, nullable=True)
    order_id = Column(Integer, nullable=True)

    # Attempt Information
    attempt_number = Column(Integer, nullable=False)
    attempt_date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')

    # Gateway Response
    gateway_response_code = Column(String(50), nullable=True)
    gateway_response_message = Column(Text, nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_reference = Column(String(100), nullable=True)

    # Status
    status = Column(String(50), nullable=False)  # success, failed, error, timeout
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_eligible = Column(Boolean, default=True)

    # Processing Details
    processing_time_ms = Column(Integer, nullable=True)
    request_payload = Column(JSON, nullable=True)
    response_payload = Column(JSON, nullable=True)

    # Risk Information
    risk_score = Column(Numeric(5, 2), nullable=True)
    decline_reason = Column(String(100), nullable=True)
    cvv_result = Column(String(10), nullable=True)
    avs_result = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    payment = relationship("Payment")
    gateway = relationship("PaymentGateway")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_attempt_payment', 'payment_id'),
        Index('idx_attempt_gateway', 'gateway_id'),
        Index('idx_attempt_status', 'status'),
        Index('idx_attempt_date', 'attempt_date'),
        Index('idx_attempt_invoice', 'invoice_id'),
        Index('idx_attempt_order', 'order_id'),
        UniqueConstraint('payment_id', 'attempt_number', name='uq_payment_attempt'),
    )
