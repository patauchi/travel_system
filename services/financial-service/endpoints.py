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
from models import (
    Transaction, Payment, Invoice, InvoiceLine,
    TransactionType, TransactionStatus, PaymentStatus,
    PaymentMethod, InvoiceStatus, Currency
)
from schemas import (
    TransactionCreate, TransactionUpdate, TransactionResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    BalanceResponse, FinancialReportResponse
)

router = APIRouter()


# ============================================
# TRANSACTIONS ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/transactions", response_model=TransactionResponse)
async def create_transaction(
    tenant_id: str,
    transaction_data: TransactionCreate,
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
            type=transaction_data.type,
            status=TransactionStatus.PENDING,
            amount=transaction_data.amount,
            currency=transaction_data.currency or Currency.USD,
            description=transaction_data.description,
            reference_type=transaction_data.reference_type,
            reference_id=transaction_data.reference_id,
            booking_id=transaction_data.booking_id,
            customer_id=transaction_data.customer_id,
            payment_method=transaction_data.payment_method,
            metadata=transaction_data.metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(transaction)
        tenant_db.commit()
        tenant_db.refresh(transaction)

        return TransactionResponse.from_orm(transaction)

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
            "data": [TransactionResponse.from_orm(t) for t in transactions]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching transactions: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/transactions/{transaction_id}", response_model=TransactionResponse)
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

        return TransactionResponse.from_orm(transaction)

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

        return TransactionResponse.from_orm(transaction)

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

@router.post("/tenants/{tenant_id}/payments", response_model=PaymentResponse)
async def create_payment(
    tenant_id: str,
    payment_data: PaymentCreate,
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
            transaction_id=payment_data.transaction_id,
            invoice_id=payment_data.invoice_id,
            amount=payment_data.amount,
            currency=payment_data.currency or Currency.USD,
            payment_method=payment_data.payment_method,
            status=PaymentStatus.PENDING,
            customer_id=payment_data.customer_id,
            booking_id=payment_data.booking_id,
            gateway=payment_data.gateway,
            gateway_transaction_id=payment_data.gateway_transaction_id,
            metadata=payment_data.metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(payment)

        # If payment is for a transaction, update transaction
        if payment_data.transaction_id:
            transaction = tenant_db.query(Transaction).filter(
                Transaction.id == payment_data.transaction_id
            ).first()
            if transaction:
                transaction.payment_id = payment.id
                transaction.status = TransactionStatus.PROCESSING

        tenant_db.commit()
        tenant_db.refresh(payment)

        return PaymentResponse.from_orm(payment)

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
    status: Optional[PaymentStatus] = Query(None),
    payment_method: Optional[PaymentMethod] = Query(None),
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
            "data": [PaymentResponse.from_orm(p) for p in payments]
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
        payment.status = PaymentStatus.COMPLETED
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

@router.post("/tenants/{tenant_id}/invoices", response_model=InvoiceResponse)
async def create_invoice(
    tenant_id: str,
    invoice_data: InvoiceCreate,
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
        subtotal = sum(item.quantity * item.unit_price for item in invoice_data.line_items)
        tax_amount = subtotal * (invoice_data.tax_rate / 100) if invoice_data.tax_rate else 0
        total_amount = subtotal + tax_amount - (invoice_data.discount_amount or 0)

        # Create invoice
        invoice = Invoice(
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
            customer_id=invoice_data.customer_id,
            booking_id=invoice_data.booking_id,
            status=InvoiceStatus.DRAFT,
            issue_date=invoice_data.issue_date or date.today(),
            due_date=invoice_data.due_date or (date.today() + timedelta(days=30)),
            currency=invoice_data.currency or Currency.USD,
            subtotal=subtotal,
            tax_rate=invoice_data.tax_rate,
            tax_amount=tax_amount,
            discount_amount=invoice_data.discount_amount or 0,
            total_amount=total_amount,
            notes=invoice_data.notes,
            terms_conditions=invoice_data.terms_conditions,
            metadata=invoice_data.metadata or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(invoice)
        tenant_db.flush()  # Get invoice ID

        # Add line items
        for item_data in invoice_data.line_items:
            line_item = InvoiceLine(
                invoice_id=invoice.id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=item_data.quantity * item_data.unit_price,
                tax_rate=item_data.tax_rate,
                created_at=datetime.utcnow()
            )
            tenant_db.add(line_item)

        tenant_db.commit()
        tenant_db.refresh(invoice)

        return InvoiceResponse.from_orm(invoice)

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
    status: Optional[InvoiceStatus] = Query(None),
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
            "data": [InvoiceResponse.from_orm(i) for i in invoices]
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
        if invoice.status == InvoiceStatus.DRAFT:
            invoice.status = InvoiceStatus.SENT
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

@router.get("/tenants/{tenant_id}/balance", response_model=BalanceResponse)
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
            Invoice.status != InvoiceStatus.CANCELLED
        ).with_entities(func.sum(Invoice.total_amount)).scalar() or 0

        total_paid_invoices = invoices_query.filter(
            Invoice.status == InvoiceStatus.PAID
        ).with_entities(func.sum(Invoice.paid_amount)).scalar() or 0

        pending_amount = total_invoiced - total_paid_invoices

        return BalanceResponse(
            total_charges=float(total_transactions),
            total_payments=float(total_payments),
            total_invoiced=float(total_invoiced),
            total_paid=float(total_paid_invoices),
            pending_amount=float(pending_amount),
            balance=float(total_payments - total_transactions),
            customer_id=customer_id,
            booking_id=booking_id,
            as_of=datetime.utcnow()
        )

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
