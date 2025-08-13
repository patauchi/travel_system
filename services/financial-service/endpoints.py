"""
Financial Service - API Endpoints
Complete CRUD operations for financial transactions, payments, and invoices
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from enum import Enum

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models_invoices import (
    Invoice, InvoiceLine, Payment,
    TransactionType, PaymentMethod, PaymentType,
    InvoiceStatus
)
from models_orders import (
    PaymentStatus
)
# Import or define missing models
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Define Transaction model since it doesn't exist
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    transaction_number = Column(String(50), unique=True)
    type = Column(String(50))
    status = Column(String(50))
    amount = Column(Numeric(10, 2))
    currency = Column(String(3))
    description = Column(Text)
    reference_type = Column(String(50))
    reference_id = Column(String(100))
    booking_id = Column(Integer)
    customer_id = Column(Integer)
    payment_method = Column(String(50))
    payment_id = Column(Integer)
    transaction_metadata = Column(Text)
    status_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    failed_at = Column(DateTime)

# Define missing enums
class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"

class Currency(str, Enum):
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

# Import schemas - comment out for now if they don't exist
# from schemas import (
#     TransactionCreate, TransactionUpdate, TransactionResponse,
#     PaymentCreate, PaymentUpdate, PaymentResponse,
#     InvoiceCreate, InvoiceUpdate, InvoiceResponse,
#     BalanceResponse, FinancialReportResponse
# )

router = APIRouter()


# ============================================
# TRANSACTIONS ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/transactions")
async def create_transaction(
    tenant_id: str,
    transaction_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Create a new financial transaction

    Args:
        tenant_id: UUID of the tenant
        transaction_data: Transaction details

    Returns:
        Created transaction
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Create transaction
        transaction = Transaction(
            transaction_number=f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            type=transaction_data.get("type"),
            status=TransactionStatus.PENDING,
            amount=transaction_data.get("amount"),
            currency=transaction_data.get("currency", "USD"),
            description=transaction_data.get("description"),
            reference_type=transaction_data.get("reference_type"),
            reference_id=transaction_data.get("reference_id"),
            booking_id=transaction_data.get("booking_id"),
            customer_id=transaction_data.get("customer_id"),
            payment_method=transaction_data.get("payment_method"),
            transaction_metadata=transaction_data.get("metadata", {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(transaction)
        tenant_db.commit()
        tenant_db.refresh(transaction)

        # Return dictionary instead of using schema
        return {
            "id": transaction.id,
            "transaction_number": transaction.transaction_number,
            "type": transaction.type,
            "status": transaction.status,
            "amount": float(transaction.amount),
            "currency": transaction.currency,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None
        }

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transaction: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/transactions")
async def list_transactions(
    tenant_id: str,
    db: Session = Depends(get_db),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    # Filters
    type: Optional[TransactionType] = Query(None, description="Transaction type"),
    status: Optional[TransactionStatus] = Query(None, description="Transaction status"),
    customer_id: Optional[int] = Query(None, description="Filter by customer"),
    booking_id: Optional[int] = Query(None, description="Filter by booking"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Payment method"),
    date_from: Optional[date] = Query(None, description="Transaction date from"),
    date_to: Optional[date] = Query(None, description="Transaction date to"),
    min_amount: Optional[float] = Query(None, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, description="Maximum amount"),
    reference_type: Optional[str] = Query(None, description="Reference type"),
    reference_id: Optional[str] = Query(None, description="Reference ID"),
    search: Optional[str] = Query(None, description="Search in description and transaction number"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List financial transactions with advanced filtering

    Returns paginated list of transactions
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Build query
        query = tenant_db.query(Transaction)

        # Apply filters
        if type:
            query = query.filter(Transaction.type == type)

        if status:
            query = query.filter(Transaction.status == status)

        if customer_id:
            query = query.filter(Transaction.customer_id == customer_id)

        if booking_id:
            query = query.filter(Transaction.booking_id == booking_id)

        if payment_method:
            query = query.filter(Transaction.payment_method == payment_method)

        if date_from:
            query = query.filter(Transaction.created_at >= date_from)

        if date_to:
            query = query.filter(Transaction.created_at <= date_to)

        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)

        if reference_type:
            query = query.filter(Transaction.reference_type == reference_type)

        if reference_id:
            query = query.filter(Transaction.reference_id == reference_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Transaction.transaction_number.ilike(search_term),
                    Transaction.description.ilike(search_term)
                )
            )

        # Get total count
        total_count = query.count()

        # Apply sorting
        if hasattr(Transaction, sort_by):
            order_column = getattr(Transaction, sort_by)
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())

        # Apply pagination
        transactions = query.offset(skip).limit(limit).all()

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": [{
                "id": t.id,
                "transaction_number": t.transaction_number,
                "type": t.type,
                "status": t.status,
                "amount": float(t.amount) if t.amount else 0,
                "currency": t.currency,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transactions: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/transactions/{transaction_id}")
async def get_transaction(
    tenant_id: str,
    transaction_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific transaction by ID"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        transaction = tenant_db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )

        return {
            "id": transaction.id,
            "transaction_number": transaction.transaction_number,
            "type": transaction.type,
            "status": transaction.status,
            "amount": float(transaction.amount) if transaction.amount else 0,
            "currency": transaction.currency,
            "created_at": transaction.created_at.isoformat() if transaction.created_at else None
        }

    finally:
        tenant_db.close()


@router.put("/tenants/{tenant_id}/transactions/{transaction_id}/status")
async def update_transaction_status(
    tenant_id: str,
    transaction_id: int,
    status: TransactionStatus = Body(..., description="New status"),
    notes: Optional[str] = Body(None, description="Status change notes"),
    db: Session = Depends(get_db)
):
    """Update transaction status"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        transaction = tenant_db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )

        # Update status
        transaction.status = status
        transaction.status_notes = notes
        transaction.updated_at = datetime.utcnow()

        if status == TransactionStatus.COMPLETED:
            transaction.completed_at = datetime.utcnow()
        elif status == TransactionStatus.FAILED:
            transaction.failed_at = datetime.utcnow()

        tenant_db.commit()
        tenant_db.refresh(transaction)

        return {
            "id": transaction.id,
            "transaction_number": transaction.transaction_number,
            "status": transaction.status,
            "message": "Transaction status updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating transaction: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# PAYMENTS ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/payments")
async def create_payment(
    tenant_id: str,
    payment_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Process a new payment

    Args:
        tenant_id: UUID of the tenant
        payment_data: Payment details

    Returns:
        Created payment record
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Create payment record
        payment = Payment(
            payment_number=f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            transaction_id=payment_data.get("transaction_id"),
            invoice_id=payment_data.get("invoice_id"),
            amount=payment_data.get("amount"),
            currency=payment_data.get("currency", "USD"),
            payment_method=payment_data.get("payment_method"),
            status="pending",
            customer_id=payment_data.get("customer_id"),
            booking_id=payment_data.get("booking_id"),
            gateway=payment_data.get("gateway"),
            gateway_transaction_id=payment_data.get("gateway_transaction_id"),
            payment_metadata=payment_data.get("metadata", {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(payment)

        # If payment is for a transaction, update transaction
        if payment_data.get("transaction_id"):
            transaction = tenant_db.query(Transaction).filter(
                Transaction.id == payment_data.get("transaction_id")
            ).first()
            if transaction:
                transaction.payment_id = payment.id
                transaction.status = TransactionStatus.PROCESSING

        tenant_db.commit()
        tenant_db.refresh(payment)

        return {
            "id": payment.id,
            "payment_number": payment.payment_number,
            "status": payment.status,
            "amount": float(payment.amount) if payment.amount else 0,
            "currency": payment.currency,
            "created_at": payment.created_at.isoformat() if payment.created_at else None
        }

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/payments")
async def list_payments(
    tenant_id: str,
    db: Session = Depends(get_db),
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    # Filters
    status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    booking_id: Optional[int] = Query(None),
    invoice_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None)
):
    """List payments with filtering"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Build query
        query = tenant_db.query(Payment)

        # Apply filters
        if status:
            query = query.filter(Payment.status == status)

        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)

        if customer_id:
            query = query.filter(Payment.customer_id == customer_id)

        if booking_id:
            query = query.filter(Payment.booking_id == booking_id)

        if invoice_id:
            query = query.filter(Payment.invoice_id == invoice_id)

        if date_from:
            query = query.filter(Payment.created_at >= date_from)

        if date_to:
            query = query.filter(Payment.created_at <= date_to)

        if min_amount is not None:
            query = query.filter(Payment.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Payment.amount <= max_amount)

        # Get total count
        total_count = query.count()

        # Apply sorting and pagination
        payments = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": [{
                "id": p.id,
                "payment_number": p.payment_number if hasattr(p, 'payment_number') else f"PAY-{p.id}",
                "status": p.status,
                "amount": float(p.amount) if p.amount else 0,
                "created_at": p.created_at.isoformat() if p.created_at else None
            } for p in payments]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching payments: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.post("/tenants/{tenant_id}/payments/{payment_id}/confirm")
async def confirm_payment(
    tenant_id: str,
    payment_id: int,
    gateway_response: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Confirm a payment from gateway response"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        payment = tenant_db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )

        # Update payment status
        payment.status = "completed"
        payment.gateway_response = gateway_response
        payment.processed_at = datetime.utcnow()
        payment.updated_at = datetime.utcnow()

        # Update related transaction if exists
        if payment.transaction_id:
            transaction = tenant_db.query(Transaction).filter(
                Transaction.id == payment.transaction_id
            ).first()
            if transaction:
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()

        tenant_db.commit()

        return {"message": "Payment confirmed successfully", "payment_id": payment_id}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming payment: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# INVOICES ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/invoices")
async def create_invoice(
    tenant_id: str,
    invoice_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Generate a new invoice

    Args:
        tenant_id: UUID of the tenant
        invoice_data: Invoice details including line items

    Returns:
        Created invoice
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Calculate totals
        line_items = invoice_data.get("line_items", [])
        subtotal = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in line_items)
        tax_rate = invoice_data.get("tax_rate", 0)
        tax_amount = subtotal * (tax_rate / 100) if tax_rate else 0
        discount_amount = invoice_data.get("discount_amount", 0)
        total_amount = subtotal + tax_amount - discount_amount

        # Create invoice
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
            customer_id=invoice_data.get("customer_id"),
            booking_id=invoice_data.get("booking_id"),
            status="draft",
            issue_date=invoice_data.get("issue_date", date.today()),
            due_date=invoice_data.get("due_date", date.today() + timedelta(days=30)),
            currency=invoice_data.get("currency", "USD"),
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            discount_amount=discount_amount,
            total_amount=total_amount,
            notes=invoice_data.get("notes"),
            terms_conditions=invoice_data.get("terms_conditions"),
            invoice_metadata=invoice_data.get("metadata", {}),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(invoice)
        tenant_db.flush()  # Get invoice ID

        # Add line items
        for item_data in line_items:
            line_item = InvoiceLine(
                invoice_id=invoice.id,
                description=item_data.get("description"),
                quantity=item_data.get("quantity", 0),
                unit_price=item_data.get("unit_price", 0),
                amount=item_data.get("quantity", 0) * item_data.get("unit_price", 0),
                tax_rate=item_data.get("tax_rate"),
                created_at=datetime.utcnow()
            )
            tenant_db.add(line_item)

        tenant_db.commit()
        tenant_db.refresh(invoice)

        return {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None
        }

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating invoice: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/invoices")
async def list_invoices(
    tenant_id: str,
    db: Session = Depends(get_db),
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    # Filters
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    booking_id: Optional[int] = Query(None),
    issue_date_from: Optional[date] = Query(None),
    issue_date_to: Optional[date] = Query(None),
    due_date_from: Optional[date] = Query(None),
    due_date_to: Optional[date] = Query(None),
    overdue_only: bool = Query(False, description="Show only overdue invoices"),
    search: Optional[str] = Query(None, description="Search in invoice number")
):
    """List invoices with filtering"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Build query
        query = tenant_db.query(Invoice)

        # Apply filters
        if status:
            query = query.filter(Invoice.status == status)

        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)

        if booking_id:
            query = query.filter(Invoice.booking_id == booking_id)

        if issue_date_from:
            query = query.filter(Invoice.issue_date >= issue_date_from)

        if issue_date_to:
            query = query.filter(Invoice.issue_date <= issue_date_to)

        if due_date_from:
            query = query.filter(Invoice.due_date >= due_date_from)

        if due_date_to:
            query = query.filter(Invoice.due_date <= due_date_to)

        if overdue_only:
            query = query.filter(
                and_(
                    Invoice.due_date < date.today(),
                    Invoice.status != InvoiceStatus.PAID
                )
            )

        if search:
            query = query.filter(Invoice.invoice_number.ilike(f"%{search}%"))

        # Get total count
        total_count = query.count()

        # Apply sorting and pagination
        invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": [{
                "id": i.id,
                "invoice_number": i.invoice_number,
                "status": i.status,
                "total_amount": float(i.total_amount) if i.total_amount else 0,
                "issue_date": i.issue_date.isoformat() if i.issue_date else None,
                "due_date": i.due_date.isoformat() if i.due_date else None,
                "created_at": i.created_at.isoformat() if i.created_at else None
            } for i in invoices]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching invoices: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.post("/tenants/{tenant_id}/invoices/{invoice_id}/send")
async def send_invoice(
    tenant_id: str,
    invoice_id: int,
    email_to: str = Body(..., description="Email address to send invoice"),
    db: Session = Depends(get_db)
):
    """Send invoice by email"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        invoice = tenant_db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invoice {invoice_id} not found"
            )

        # Update invoice status
        if invoice.status == "draft":
            invoice.status = "sent"
            invoice.sent_at = datetime.utcnow()

        invoice.updated_at = datetime.utcnow()
        tenant_db.commit()

        # TODO: Integrate with communication service to actually send email

        return {
            "message": f"Invoice {invoice.invoice_number} sent to {email_to}",
            "invoice_id": invoice_id,
            "status": invoice.status.value
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending invoice: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# BALANCE & REPORTS ENDPOINTS
# ============================================

@router.get("/tenants/{tenant_id}/balance")
async def get_balance(
    tenant_id: str,
    customer_id: Optional[int] = Query(None, description="Get balance for specific customer"),
    booking_id: Optional[int] = Query(None, description="Get balance for specific booking"),
    db: Session = Depends(get_db)
):
    """
    Get financial balance summary

    Returns balance information for tenant, customer, or booking
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Build base queries
        transactions_query = tenant_db.query(Transaction)
        payments_query = tenant_db.query(Payment)
        invoices_query = tenant_db.query(Invoice)

        # Apply filters
        if customer_id:
            transactions_query = transactions_query.filter(Transaction.customer_id == customer_id)
            payments_query = payments_query.filter(Payment.customer_id == customer_id)
            invoices_query = invoices_query.filter(Invoice.customer_id == customer_id)

        if booking_id:
            transactions_query = transactions_query.filter(Transaction.booking_id == booking_id)
            payments_query = payments_query.filter(Payment.booking_id == booking_id)
            invoices_query = invoices_query.filter(Invoice.booking_id == booking_id)

        # Calculate totals
        total_transactions = transactions_query.filter(
            Transaction.type == TransactionType.CHARGE
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        total_payments = payments_query.filter(
            Payment.status == PaymentStatus.COMPLETED
        ).with_entities(func.sum(Payment.amount)).scalar() or 0

        total_invoiced = invoices_query.filter(
            Invoice.status != "cancelled"
        ).with_entities(func.sum(Invoice.total_amount)).scalar() or 0

        total_paid_invoices = invoices_query.filter(
            Invoice.status == "paid"
        ).with_entities(func.sum(Invoice.paid_amount)).scalar() or 0

        pending_amount = total_invoiced - total_paid_invoices

        return {
            "total_charges": float(total_transactions),
            "total_payments": float(total_payments),
            "total_invoiced": float(total_invoiced),
            "total_paid": float(total_paid_invoices),
            "pending_amount": float(pending_amount),
            "balance": float(total_payments - total_transactions),
            "customer_id": customer_id,
            "booking_id": booking_id,
            "as_of": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating balance: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/reports/financial")
async def get_financial_report(
    tenant_id: str,
    db: Session = Depends(get_db),
    period_start: date = Query(..., description="Report period start"),
    period_end: date = Query(..., description="Report period end"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Group results by")
):
    """
    Generate financial report for a period

    Returns aggregated financial data grouped by day/week/month
    """
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Get tenant database session
    tenant_db = next(get_tenant_db(schema_name))

    try:
        # Determine date truncation based on grouping
        if group_by == "day":
            date_trunc = "day"
        elif group_by == "week":
            date_trunc = "week"
        else:  # month
            date_trunc = "month"

        # Query for transactions grouped by period
        transactions_data = tenant_db.execute(
            text(f"""
                SELECT
                    DATE_TRUNC('{date_trunc}', created_at) as period,
                    SUM(CASE WHEN type = 'charge' THEN amount ELSE 0 END) as revenue,
                    SUM(CASE WHEN type = 'payment' THEN amount ELSE 0 END) as payments,
                    SUM(CASE WHEN type = 'refund' THEN amount ELSE 0 END) as refunds,
                    SUM(CASE WHEN type = 'fee' THEN amount ELSE 0 END) as fees,
                    COUNT(*) as transaction_count
                FROM transactions
                WHERE created_at >= :period_start
                    AND created_at <= :period_end
                GROUP BY DATE_TRUNC('{date_trunc}', created_at)
                ORDER BY period
            """),
            {"period_start": period_start, "period_end": period_end}
        ).fetchall()

        # Format results
        report_data = []
        total_revenue = 0
        total_payments = 0
        total_refunds = 0
        total_fees = 0

        for row in transactions_data:
            period_str = row.period.strftime("%Y-%m-%d")
            revenue = float(row.revenue or 0)
            payments = float(row.payments or 0)
            refunds = float(row.refunds or 0)
            fees = float(row.fees or 0)

            total_revenue += revenue
            total_payments += payments
            total_refunds += refunds
            total_fees += fees

            report_data.append({
                "period": period_str,
                "total_revenue": revenue,
                "total_payments": payments,
                "total_refunds": refunds,
                "total_fees": fees,
                "net_revenue": revenue - refunds - fees,
                "transaction_count": row.transaction_count
            })

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "group_by": group_by,
            "summary": {
                "total_revenue": total_revenue,
                "total_payments": total_payments,
                "total_refunds": total_refunds,
                "total_fees": total_fees,
                "net_revenue": total_revenue - total_refunds - total_fees
            },
            "data": report_data,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )
    finally:
        tenant_db.close()
