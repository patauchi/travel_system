"""
Invoices Module Endpoints
API endpoints for invoice management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import Invoice, InvoiceLine, AccountsReceivable, AccountsPayable
from .schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceListResponse,
    InvoiceLineCreate, InvoiceLineUpdate, InvoiceLineResponse, InvoiceLineListResponse,
    AccountsReceivableCreate, AccountsReceivableUpdate, AccountsReceivableResponse,
    AccountsReceivableListResponse, AccountsPayableCreate, AccountsPayableUpdate,
    AccountsPayableResponse, AccountsPayableListResponse,
    InvoiceSendRequest, InvoiceSendResponse, InvoicePaymentRequest, InvoicePaymentResponse,
    WriteOffRequest, WriteOffResponse, CreditHoldRequest, CreditHoldResponse,
    CreditHoldReleaseRequest, InvoiceSummaryResponse, InvoiceSummaryByStatus,
    InvoiceSummaryByAge, AccountsReceivableSummary, AccountsPayableSummary
)
from common.enums import (
    InvoiceStatus, AccountsReceivableStatus, AccountsPayableStatus,
    AgingBucket, CollectionStatus
)

router = APIRouter()

# ============================================
# INVOICE ENDPOINTS
# ============================================

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(
    invoice_data: InvoiceCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new invoice"""
    # Check permissions
    await require_permission(current_user, "invoices:create")

    try:
        # Create invoice
        invoice = Invoice(
            **invoice_data.model_dump(exclude={'invoice_lines'}),
            created_by=current_user.get("user_id")
        )
        db.add(invoice)
        db.flush()  # Get the invoice ID

        # Create invoice lines if provided
        if invoice_data.invoice_lines:
            for line_data in invoice_data.invoice_lines:
                invoice_line = InvoiceLine(
                    invoice_id=invoice.id,
                    **line_data.model_dump()
                )
                db.add(invoice_line)

        db.commit()
        db.refresh(invoice)

        return invoice
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating invoice: {str(e)}"
        )

@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_filter: Optional[InvoiceStatus] = Query(None, description="Filter by invoice status"),
    invoice_number: Optional[str] = Query(None, description="Filter by invoice number"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    start_date: Optional[date] = Query(None, description="Filter invoices from this date"),
    end_date: Optional[date] = Query(None, description="Filter invoices to this date"),
    overdue_only: bool = Query(False, description="Show only overdue invoices"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List invoices with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "invoices:read")

    try:
        # Build query
        query = db.query(Invoice).filter(Invoice.deleted_at.is_(None))

        # Apply filters
        if status_filter:
            query = query.filter(Invoice.status == status_filter)
        if invoice_number:
            query = query.filter(Invoice.invoice_number.ilike(f"%{invoice_number}%"))
        if account_id:
            query = query.filter(Invoice.account_id == account_id)
        if order_id:
            query = query.filter(Invoice.order_id == order_id)
        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)
        if overdue_only:
            query = query.filter(
                and_(
                    Invoice.due_date < date.today(),
                    Invoice.balance_due > 0
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        invoices = query.order_by(desc(Invoice.invoice_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return InvoiceListResponse(
            invoices=invoices,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing invoices: {str(e)}"
        )

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific invoice by ID"""
    # Check permissions
    await require_permission(current_user, "invoices:read")

    invoice = db.query(Invoice).filter(
        and_(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    return invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an existing invoice"""
    # Check permissions
    await require_permission(current_user, "invoices:update")

    invoice = db.query(Invoice).filter(
        and_(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Check if invoice can be updated
    if invoice.status in [InvoiceStatus.PAID]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update paid invoices"
        )

    try:
        # Update invoice fields
        update_data = invoice_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)

        invoice.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(invoice)

        return invoice
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating invoice: {str(e)}"
        )

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete an invoice"""
    # Check permissions
    await require_permission(current_user, "invoices:delete")

    invoice = db.query(Invoice).filter(
        and_(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Check if invoice can be deleted
    if invoice.status in [InvoiceStatus.SENT, InvoiceStatus.PARTIAL_PAID, InvoiceStatus.PAID]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete sent or paid invoices"
        )

    try:
        invoice.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Invoice deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting invoice: {str(e)}"
        )

# ============================================
# INVOICE ACTIONS ENDPOINTS
# ============================================

@router.post("/invoices/{invoice_id}/send", response_model=InvoiceSendResponse)
async def send_invoice(
    invoice_id: int,
    send_data: InvoiceSendRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Send an invoice via email"""
    # Check permissions
    await require_permission(current_user, "invoices:send")

    invoice = db.query(Invoice).filter(
        and_(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.SENT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice must be in draft or sent status to send"
        )

    try:
        # Update invoice status
        invoice.status = InvoiceStatus.SENT
        invoice.sent_date = date.today()
        invoice.updated_at = datetime.utcnow()

        # Here you would implement actual email sending logic
        # For now, we'll just simulate it

        db.commit()

        return InvoiceSendResponse(
            invoice_id=invoice.id,
            sent_to=send_data.email_addresses,
            sent_at=datetime.utcnow(),
            email_subject=send_data.subject or f"Invoice {invoice.invoice_number}",
            pdf_attached=send_data.send_pdf
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending invoice: {str(e)}"
        )

@router.post("/invoices/{invoice_id}/payment", response_model=InvoicePaymentResponse)
async def record_invoice_payment(
    invoice_id: int,
    payment_data: InvoicePaymentRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Record a payment for an invoice"""
    # Check permissions
    await require_permission(current_user, "invoices:payment")

    invoice = db.query(Invoice).filter(
        and_(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
    ).first()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero"
        )

    if payment_data.amount > invoice.balance_due:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount cannot exceed balance due"
        )

    try:
        # Update invoice payment info
        invoice.paid_amount += payment_data.amount
        invoice.balance_due -= payment_data.amount

        # Update status based on balance
        if invoice.balance_due == 0:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_date = payment_data.payment_date
        elif invoice.paid_amount > 0:
            invoice.status = InvoiceStatus.PARTIAL_PAID

        invoice.updated_at = datetime.utcnow()

        # Update related AR if exists
        ar_record = db.query(AccountsReceivable).filter(
            AccountsReceivable.invoice_id == invoice_id
        ).first()

        if ar_record:
            ar_record.paid_amount += payment_data.amount
            ar_record.balance -= payment_data.amount
            if ar_record.balance == 0:
                ar_record.status = AccountsReceivableStatus.PAID

        db.commit()

        return InvoicePaymentResponse(
            invoice_id=invoice.id,
            amount=payment_data.amount,
            payment_date=payment_data.payment_date,
            payment_method=payment_data.payment_method,
            payment_reference=payment_data.payment_reference,
            notes=payment_data.notes,
            new_balance=invoice.balance_due,
            is_fully_paid=(invoice.balance_due == 0)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording payment: {str(e)}"
        )

# ============================================
# ACCOUNTS RECEIVABLE ENDPOINTS
# ============================================

@router.post("/accounts-receivable", response_model=AccountsReceivableResponse)
async def create_accounts_receivable(
    ar_data: AccountsReceivableCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new accounts receivable record"""
    # Check permissions
    await require_permission(current_user, "invoices:create")

    try:
        ar_record = AccountsReceivable(**ar_data.model_dump())
        db.add(ar_record)
        db.commit()
        db.refresh(ar_record)

        return ar_record
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating accounts receivable: {str(e)}"
        )

@router.get("/accounts-receivable", response_model=AccountsReceivableListResponse)
async def list_accounts_receivable(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    status_filter: Optional[AccountsReceivableStatus] = Query(None, description="Filter by status"),
    aging_bucket: Optional[AgingBucket] = Query(None, description="Filter by aging bucket"),
    overdue_only: bool = Query(False, description="Show only overdue records"),
    credit_hold_only: bool = Query(False, description="Show only credit hold records"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List accounts receivable records"""
    # Check permissions
    await require_permission(current_user, "invoices:read")

    try:
        # Build query
        query = db.query(AccountsReceivable).filter(AccountsReceivable.deleted_at.is_(None))

        # Apply filters
        if account_id:
            query = query.filter(AccountsReceivable.account_id == account_id)
        if status_filter:
            query = query.filter(AccountsReceivable.status == status_filter)
        if aging_bucket:
            query = query.filter(AccountsReceivable.aging_bucket == aging_bucket)
        if overdue_only:
            query = query.filter(AccountsReceivable.days_overdue > 0)
        if credit_hold_only:
            query = query.filter(AccountsReceivable.is_on_credit_hold == True)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        ar_records = query.order_by(desc(AccountsReceivable.due_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return AccountsReceivableListResponse(
            accounts_receivable=ar_records,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing accounts receivable: {str(e)}"
        )

@router.post("/accounts-receivable/{ar_id}/write-off", response_model=WriteOffResponse)
async def write_off_receivable(
    ar_id: int,
    write_off_data: WriteOffRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Write off an accounts receivable"""
    # Check permissions
    await require_permission(current_user, "invoices:write_off")

    ar_record = db.query(AccountsReceivable).filter(
        and_(AccountsReceivable.id == ar_id, AccountsReceivable.deleted_at.is_(None))
    ).first()

    if not ar_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accounts receivable record not found"
        )

    if ar_record.is_written_off:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Record has already been written off"
        )

    if write_off_data.amount > ar_record.balance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Write-off amount cannot exceed balance"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        ar_record.is_written_off = True
        ar_record.written_off_date = date.today()
        ar_record.written_off_amount = write_off_data.amount
        ar_record.written_off_reason = write_off_data.reason
        ar_record.written_off_by = user_id
        ar_record.balance -= write_off_data.amount

        if ar_record.balance == 0:
            ar_record.status = AccountsReceivableStatus.WRITTEN_OFF

        ar_record.updated_at = current_time
        db.commit()

        return WriteOffResponse(
            ar_id=ar_record.id,
            amount=write_off_data.amount,
            reason=write_off_data.reason,
            notes=write_off_data.notes,
            written_off_by=user_id,
            written_off_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error writing off receivable: {str(e)}"
        )

@router.post("/accounts-receivable/{ar_id}/credit-hold", response_model=CreditHoldResponse)
async def place_credit_hold(
    ar_id: int,
    credit_hold_data: CreditHoldRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Place an account on credit hold"""
    # Check permissions
    await require_permission(current_user, "invoices:credit_hold")

    ar_record = db.query(AccountsReceivable).filter(
        and_(AccountsReceivable.id == ar_id, AccountsReceivable.deleted_at.is_(None))
    ).first()

    if not ar_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accounts receivable record not found"
        )

    if ar_record.is_on_credit_hold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already on credit hold"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        ar_record.is_on_credit_hold = True
        ar_record.credit_hold_date = date.today()
        ar_record.credit_hold_reason = credit_hold_data.reason
        ar_record.credit_hold_by = user_id
        ar_record.updated_at = current_time

        db.commit()

        return CreditHoldResponse(
            ar_id=ar_record.id,
            reason=credit_hold_data.reason,
            notes=credit_hold_data.notes,
            credit_hold_by=user_id,
            credit_hold_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error placing credit hold: {str(e)}"
        )

@router.post("/accounts-receivable/{ar_id}/release-credit-hold")
async def release_credit_hold(
    ar_id: int,
    release_data: CreditHoldReleaseRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Release an account from credit hold"""
    # Check permissions
    await require_permission(current_user, "invoices:credit_hold")

    ar_record = db.query(AccountsReceivable).filter(
        and_(AccountsReceivable.id == ar_id, AccountsReceivable.deleted_at.is_(None))
    ).first()

    if not ar_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Accounts receivable record not found"
        )

    if not ar_record.is_on_credit_hold:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not on credit hold"
        )

    try:
        ar_record.is_on_credit_hold = False
        ar_record.credit_hold_date = None
        ar_record.credit_hold_reason = None
        ar_record.credit_hold_by = None
        ar_record.updated_at = datetime.utcnow()

        db.commit()

        return {"message": "Credit hold released successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error releasing credit hold: {str(e)}"
        )

# ============================================
# ACCOUNTS PAYABLE ENDPOINTS
# ============================================

@router.post("/accounts-payable", response_model=AccountsPayableResponse)
async def create_accounts_payable(
    ap_data: AccountsPayableCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new accounts payable record"""
    # Check permissions
    await require_permission(current_user, "invoices:create")

    try:
        ap_record = AccountsPayable(**ap_data.model_dump())
        db.add(ap_record)
        db.commit()
        db.refresh(ap_record)

        return ap_record
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating accounts payable: {str(e)}"
        )

@router.get("/accounts-payable", response_model=AccountsPayableListResponse)
async def list_accounts_payable(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status_filter: Optional[AccountsPayableStatus] = Query(None, description="Filter by status"),
    overdue_only: bool = Query(False, description="Show only overdue records"),
    pending_approval: bool = Query(False, description="Show only pending approval"),
    disputed_only: bool = Query(False, description="Show only disputed records"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List accounts payable records"""
    # Check permissions
    await require_permission(current_user, "invoices:read")

    try:
        # Build query
        query = db.query(AccountsPayable).filter(AccountsPayable.deleted_at.is_(None))

        # Apply filters
        if supplier_id:
            query = query.filter(AccountsPayable.supplier_id == supplier_id)
        if status_filter:
            query = query.filter(AccountsPayable.status == status_filter)
        if overdue_only:
            query = query.filter(AccountsPayable.days_overdue > 0)
        if pending_approval:
            query = query.filter(AccountsPayable.is_approved == False)
        if disputed_only:
            query = query.filter(AccountsPayable.is_disputed == True)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        ap_records = query.order_by(desc(AccountsPayable.due_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return AccountsPayableListResponse(
            accounts_payable=ap_records,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing accounts payable: {str(e)}"
        )

# ============================================
# SUMMARY ENDPOINTS
# ============================================

@router.get("/invoices/summary", response_model=InvoiceSummaryResponse)
async def get_invoice_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get invoice summary and statistics"""
    # Check permissions
    await require_permission(current_user, "invoices:read")

    try:
        # Build base query
        query = db.query(Invoice).filter(Invoice.deleted_at.is_(None))

        if start_date:
            query = query.filter(Invoice.invoice_date >= start_date)
        if end_date:
            query = query.filter(Invoice.invoice_date <= end_date)

        # Get total invoices and amounts
        total_result = query.with_entities(
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.total_amount).label('total_amount'),
            func.sum(Invoice.paid_amount).label('total_paid'),
            func.sum(Invoice.balance_due).label('total_outstanding')
        ).first()

        total_invoices = total_result.count or 0
        total_amount = total_result.total_amount or 0
        total_paid = total_result.total_paid or 0
        total_outstanding = total_result.total_outstanding or 0

        # Summary by status
        status_summary = query.with_entities(
            Invoice.status,
            func.sum(Invoice.total_amount).label('total_amount'),
            func.count(Invoice.id).label('count'),
            func.avg(Invoice.total_amount).label('avg_amount')
        ).group_by(Invoice.status).all()

        by_status = [
            InvoiceSummaryByStatus(
                status=InvoiceStatus(row.status),
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in status_summary
        ]

        # Summary by age (simplified)
        today = date.today()
        current_invoices = query.filter(Invoice.due_date >= today).count()
        overdue_1_30 = query.filter(
            and_(Invoice.due_date < today, Invoice.due_date >= today.replace(day=today.day-30))
        ).count()
        overdue_31_60 = query.filter(
            and_(Invoice.due_date < today.replace(day=today.day-30),
                 Invoice.due_date >= today.replace(day=today.day-60))
        ).count()

        by_age = [
            InvoiceSummaryByAge(age_bucket="current", total_amount=0, count=current_invoices),
            InvoiceSummaryByAge(age_bucket="1-30", total_amount=0, count=overdue_1_30),
            InvoiceSummaryByAge(age_bucket="31-60", total_amount=0, count=overdue_31_60),
        ]

        # Overdue invoices
        overdue_result = query.filter(
            and_(Invoice.due_date < today, Invoice.balance_due > 0)
        ).with_entities(
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.balance_due).label('amount')
        ).first()

        overdue_invoices_count = overdue_result.count or 0
        overdue_amount = overdue_result.amount or 0

        # Simple AR and AP summaries (would be more complex in real implementation)
        ar_summary = AccountsReceivableSummary(
            total_outstanding=total_outstanding,
            total_overdue=overdue_amount,
            by_aging=by_age,
            by_status=[],
            credit_hold_amount=0,
            credit_hold_count=0
        )

        ap_summary = AccountsPayableSummary(
            total_outstanding=0,
            total_overdue=0,
            by_status=[],
            pending_approval_amount=0,
            pending_approval_count=0,
            disputed_amount=0,
            disputed_count=0
        )

        return InvoiceSummaryResponse(
            total_invoices=total_invoices,
            total_amount=total_amount,
            total_paid=total_paid,
            total_outstanding=total_outstanding,
            by_status=by_status,
            by_age=by_age,
            ar_summary=ar_summary,
            ap_summary=ap_summary,
            overdue_invoices_count=overdue_invoices_count,
            overdue_amount=overdue_amount
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating invoice summary: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/invoices/health")
async def invoices_health():
    """Health check for invoices module"""
    return {
        "status": "healthy",
        "module": "invoices",
        "timestamp": datetime.utcnow().isoformat()
    }
