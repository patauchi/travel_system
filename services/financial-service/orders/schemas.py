"""
Orders Module Schemas
Pydantic schemas for order management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from common.enums import (
    OrderStatus, PaymentStatus, Currency, OrderLineType, DocumentType
)

# ============================================
# ORDER SCHEMAS
# ============================================

class OrderLineBase(BaseModel):
    """Base schema for order lines"""
    line_number: int = Field(..., description="Line number within the order")
    type: OrderLineType = Field(..., description="Type of order line item")
    description: str = Field(..., description="Description of the line item")
    product_id: Optional[int] = Field(None, description="Product ID if applicable")
    service_id: Optional[int] = Field(None, description="Service ID if applicable")
    supplier_id: Optional[int] = Field(None, description="Supplier ID if applicable")
    service_date: Optional[date] = Field(None, description="Date of service")
    service_end_date: Optional[date] = Field(None, description="End date of service")
    quantity: int = Field(1, description="Quantity of items")
    unit_price: Decimal = Field(..., description="Unit price")
    discount_percent: Decimal = Field(0, description="Discount percentage")
    discount_amount: Decimal = Field(0, description="Discount amount")
    tax_rate: Decimal = Field(0, description="Tax rate")
    tax_amount: Decimal = Field(0, description="Tax amount")
    total_amount: Decimal = Field(..., description="Total amount for this line")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost for margin calculation")
    total_cost: Optional[Decimal] = Field(None, description="Total cost for margin calculation")
    margin_amount: Optional[Decimal] = Field(None, description="Margin amount")
    margin_percent: Optional[Decimal] = Field(None, description="Margin percentage")
    commission_rate: Optional[Decimal] = Field(None, description="Commission rate")
    commission_amount: Optional[Decimal] = Field(None, description="Commission amount")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_optional: bool = Field(False, description="Whether this line item is optional")
    is_included: bool = Field(True, description="Whether this line item is included")
    is_confirmed: bool = Field(False, description="Whether this line item is confirmed")
    passenger_names: Optional[List[str]] = Field(None, description="Passenger names for this item")
    passenger_count: Optional[int] = Field(None, description="Number of passengers")
    booking_reference: Optional[str] = Field(None, description="Booking reference number")
    confirmation_number: Optional[str] = Field(None, description="Confirmation number")
    supplier_confirmation: Optional[str] = Field(None, description="Supplier confirmation number")
    status: str = Field("pending", description="Status of the line item")

class OrderLineCreate(OrderLineBase):
    """Schema for creating order lines"""
    pass

class OrderLineUpdate(BaseModel):
    """Schema for updating order lines"""
    line_number: Optional[int] = None
    type: Optional[OrderLineType] = None
    description: Optional[str] = None
    product_id: Optional[int] = None
    service_id: Optional[int] = None
    supplier_id: Optional[int] = None
    service_date: Optional[date] = None
    service_end_date: Optional[date] = None
    quantity: Optional[int] = None
    unit_price: Optional[Decimal] = None
    discount_percent: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    tax_rate: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    margin_amount: Optional[Decimal] = None
    margin_percent: Optional[Decimal] = None
    commission_rate: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    is_optional: Optional[bool] = None
    is_included: Optional[bool] = None
    is_confirmed: Optional[bool] = None
    passenger_names: Optional[List[str]] = None
    passenger_count: Optional[int] = None
    booking_reference: Optional[str] = None
    confirmation_number: Optional[str] = None
    supplier_confirmation: Optional[str] = None
    status: Optional[str] = None

class OrderLineResponse(OrderLineBase):
    """Schema for order line responses"""
    id: int
    order_id: int
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    """Base schema for orders"""
    quote_id: int = Field(..., description="ID of the quote this order is based on")
    order_number: str = Field(..., description="Unique order number")
    order_status: OrderStatus = Field(OrderStatus.pending, description="Status of the order")
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(..., description="Tax amount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    total_amount: Decimal = Field(..., description="Total order amount")
    currency: Currency = Field(Currency.usd, description="Currency code")
    order_date: date = Field(..., description="Date the order was placed")
    departure_date: Optional[date] = Field(None, description="Departure date")
    return_date: Optional[date] = Field(None, description="Return date")
    payment_status: PaymentStatus = Field(PaymentStatus.pending, description="Payment status")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    amount_paid: Decimal = Field(0, description="Amount already paid")
    amount_due: Decimal = Field(..., description="Amount still due")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    internal_notes: Optional[str] = Field(None, description="Internal notes")

class OrderCreate(OrderBase):
    """Schema for creating orders"""
    order_lines: Optional[List[OrderLineCreate]] = Field(None, description="Order line items")

class OrderUpdate(BaseModel):
    """Schema for updating orders"""
    order_status: Optional[OrderStatus] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[Currency] = None
    order_date: Optional[date] = None
    departure_date: Optional[date] = None
    return_date: Optional[date] = None
    payment_status: Optional[PaymentStatus] = None
    payment_terms: Optional[str] = None
    amount_paid: Optional[Decimal] = None
    amount_due: Optional[Decimal] = None
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    refund_amount: Optional[Decimal] = None

class OrderResponse(OrderBase):
    """Schema for order responses"""
    id: int
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    refund_amount: Optional[Decimal] = None
    refunded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    order_lines: List[OrderLineResponse] = []

    model_config = ConfigDict(from_attributes=True)

# ============================================
# PASSENGER DOCUMENT SCHEMAS
# ============================================

class PassengerDocumentBase(BaseModel):
    """Base schema for passenger documents"""
    order_id: int = Field(..., description="Order ID this document belongs to")
    passenger_id: Optional[int] = Field(None, description="Passenger ID if applicable")
    document_type: DocumentType = Field(..., description="Type of document")
    document_number: str = Field(..., description="Document number")
    issuing_country: Optional[str] = Field(None, description="ISO country code of issuing country")
    first_name: str = Field(..., description="Passenger first name")
    last_name: str = Field(..., description="Passenger last name")
    middle_name: Optional[str] = Field(None, description="Passenger middle name")
    date_of_birth: date = Field(..., description="Passenger date of birth")
    gender: Optional[str] = Field(None, description="Passenger gender")
    nationality: Optional[str] = Field(None, description="ISO country code of nationality")
    issue_date: Optional[date] = Field(None, description="Document issue date")
    expiry_date: Optional[date] = Field(None, description="Document expiry date")
    place_of_birth: Optional[str] = Field(None, description="Place of birth")
    place_of_issue: Optional[str] = Field(None, description="Place of document issue")
    document_file_path: Optional[str] = Field(None, description="Path to document file")
    document_file_name: Optional[str] = Field(None, description="Document file name")
    verification_notes: Optional[str] = Field(None, description="Verification notes")
    status: str = Field("pending", description="Document status")

class PassengerDocumentCreate(PassengerDocumentBase):
    """Schema for creating passenger documents"""
    pass

class PassengerDocumentUpdate(BaseModel):
    """Schema for updating passenger documents"""
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    place_of_birth: Optional[str] = None
    place_of_issue: Optional[str] = None
    document_file_path: Optional[str] = None
    document_file_name: Optional[str] = None
    verification_notes: Optional[str] = None
    status: Optional[str] = None
    is_verified: Optional[bool] = None

class PassengerDocumentResponse(PassengerDocumentBase):
    """Schema for passenger document responses"""
    id: int
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# ============================================
# LIST SCHEMAS
# ============================================

class OrderListResponse(BaseModel):
    """Schema for order list responses"""
    orders: List[OrderResponse]
    total: int
    page: int
    size: int
    pages: int

class OrderLineListResponse(BaseModel):
    """Schema for order line list responses"""
    order_lines: List[OrderLineResponse]
    total: int
    page: int
    size: int
    pages: int

class PassengerDocumentListResponse(BaseModel):
    """Schema for passenger document list responses"""
    documents: List[PassengerDocumentResponse]
    total: int
    page: int
    size: int
    pages: int
