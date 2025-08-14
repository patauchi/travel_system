"""
Voucher Module Endpoints
API endpoints for voucher management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import Voucher
from .schemas import (
    VoucherCreate, VoucherUpdate, VoucherResponse, VoucherListResponse,
    VoucherApprovalRequest, VoucherApprovalResponse,
    VoucherPaymentRequest, VoucherPaymentResponse,
    VoucherCancellationRequest, VoucherCancellationResponse,
    VoucherPostingRequest, VoucherPostingResponse,
    VoucherSummaryResponse, VoucherSummaryByStatus, VoucherSummaryByType,
    VoucherSummaryByPayee, VoucherSummaryByPeriod,
    BulkVoucherApprovalRequest, BulkVoucherApprovalResponse,
    BulkVoucherPaymentRequest, BulkVoucherPaymentResponse,
    VoucherStatus, VoucherType, PayeeType
)

router = APIRouter()

# ============================================
# VOUCHER ENDPOINTS
# ============================================

@router.post("/vouchers", response_model=VoucherResponse)
async def create_voucher(
    voucher_data: VoucherCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:create")

    try:
        voucher = Voucher(
            **voucher_data.model_dump(),
            created_by=current_user.get("user_id")
        )
        db.add(voucher)
        db.commit()
        db.refresh(voucher)

        return voucher
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating voucher: {str(e)}"
        )

@router.get("/vouchers", response_model=VoucherListResponse)
async def list_vouchers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_filter: Optional[VoucherStatus] = Query(None, description="Filter by voucher status"),
    voucher_type: Optional[VoucherType] = Query(None, description="Filter by voucher type"),
    payee_type: Optional[PayeeType] = Query(None, description="Filter by payee type"),
    payee_name: Optional[str] = Query(None, description="Filter by payee name"),
    start_date: Optional[date] = Query(None, description="Filter vouchers from this date"),
    end_date: Optional[date] = Query(None, description="Filter vouchers to this date"),
    expense_id: Optional[int] = Query(None, description="Filter by expense ID"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    accounting_period: Optional[str] = Query(None, description="Filter by accounting period"),
    is_approved: Optional[bool] = Query(None, description="Filter by approval status"),
    is_paid: Optional[bool] = Query(None, description="Filter by payment status"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List vouchers with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "vouchers:read")

    try:
        # Build query
        query = db.query(Voucher).filter(Voucher.deleted_at.is_(None))

        # Apply filters
        if status_filter:
            query = query.filter(Voucher.status == status_filter)
        if voucher_type:
            query = query.filter(Voucher.voucher_type == voucher_type)
        if payee_type:
            query = query.filter(Voucher.payee_type == payee_type)
        if payee_name:
            query = query.filter(Voucher.payee_name.ilike(f"%{payee_name}%"))
        if start_date:
            query = query.filter(Voucher.voucher_date >= start_date)
        if end_date:
            query = query.filter(Voucher.voucher_date <= end_date)
        if expense_id:
            query = query.filter(Voucher.expense_id == expense_id)
        if order_id:
            query = query.filter(Voucher.order_id == order_id)
        if supplier_id:
            query = query.filter(Voucher.supplier_id == supplier_id)
        if accounting_period:
            query = query.filter(Voucher.accounting_period == accounting_period)
        if is_approved is not None:
            query = query.filter(Voucher.is_approved == is_approved)
        if is_paid is not None:
            query = query.filter(Voucher.is_paid == is_paid)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        vouchers = query.order_by(desc(Voucher.voucher_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return VoucherListResponse(
            vouchers=vouchers,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing vouchers: {str(e)}"
        )

@router.get("/vouchers/{voucher_id}", response_model=VoucherResponse)
async def get_voucher(
    voucher_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific voucher by ID"""
    # Check permissions
    await require_permission(current_user, "vouchers:read")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    return voucher

@router.put("/vouchers/{voucher_id}", response_model=VoucherResponse)
async def update_voucher(
    voucher_id: int,
    voucher_data: VoucherUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an existing voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:update")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    # Check if voucher can be updated
    if voucher.is_approved or voucher.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update approved or paid vouchers"
        )

    # Check if user can update this voucher
    user_id = current_user.get("user_id")
    if voucher.created_by != user_id and not await require_permission(current_user, "vouchers:admin", raise_exception=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own vouchers"
        )

    try:
        # Update voucher fields
        update_data = voucher_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(voucher, field, value)

        voucher.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(voucher)

        return voucher
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating voucher: {str(e)}"
        )

@router.delete("/vouchers/{voucher_id}")
async def delete_voucher(
    voucher_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete a voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:delete")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    # Check if voucher can be deleted
    if voucher.is_approved or voucher.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete approved or paid vouchers"
        )

    # Check if user can delete this voucher
    user_id = current_user.get("user_id")
    if voucher.created_by != user_id and not await require_permission(current_user, "vouchers:admin", raise_exception=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own vouchers"
        )

    try:
        voucher.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Voucher deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting voucher: {str(e)}"
        )

# ============================================
# VOUCHER APPROVAL ENDPOINTS
# ============================================

@router.post("/vouchers/{voucher_id}/approve", response_model=VoucherApprovalResponse)
async def approve_voucher(
    voucher_id: int,
    approval_data: VoucherApprovalRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Approve or reject a voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:approve")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    if voucher.status not in [VoucherStatus.DRAFT, VoucherStatus.PENDING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher is not in a state that can be approved/rejected"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        if approval_data.action.lower() == "approve":
            voucher.status = VoucherStatus.APPROVED
            voucher.is_approved = True
            voucher.approved_by = user_id
            voucher.approved_date = current_time
        elif approval_data.action.lower() == "reject":
            voucher.status = VoucherStatus.CANCELLED
            voucher.is_cancelled = True
            voucher.cancelled_by = user_id
            voucher.cancelled_date = current_time
            voucher.cancellation_reason = approval_data.rejection_reason
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'"
            )

        voucher.updated_at = current_time
        db.commit()

        return VoucherApprovalResponse(
            voucher_id=voucher.id,
            action=approval_data.action,
            approved_by=voucher.approved_by,
            approved_at=voucher.approved_date,
            approval_notes=approval_data.approval_notes,
            rejection_reason=approval_data.rejection_reason
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voucher approval: {str(e)}"
        )

@router.post("/vouchers/bulk-approve", response_model=BulkVoucherApprovalResponse)
async def bulk_approve_vouchers(
    approval_data: BulkVoucherApprovalRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Bulk approve vouchers"""
    # Check permissions
    await require_permission(current_user, "vouchers:approve")

    approved_vouchers = []
    failed_vouchers = []
    user_id = current_user.get("user_id")
    current_time = datetime.utcnow()

    try:
        for voucher_id in approval_data.voucher_ids:
            voucher = db.query(Voucher).filter(
                and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
            ).first()

            if not voucher:
                failed_vouchers.append({
                    "voucher_id": voucher_id,
                    "error_message": "Voucher not found"
                })
                continue

            if voucher.status not in [VoucherStatus.DRAFT, VoucherStatus.PENDING]:
                failed_vouchers.append({
                    "voucher_id": voucher_id,
                    "error_message": "Voucher is not in a state that can be approved"
                })
                continue

            voucher.status = VoucherStatus.APPROVED
            voucher.is_approved = True
            voucher.approved_by = user_id
            voucher.approved_date = current_time
            voucher.updated_at = current_time
            approved_vouchers.append(voucher_id)

        db.commit()

        return BulkVoucherApprovalResponse(
            approved_count=len(approved_vouchers),
            failed_count=len(failed_vouchers),
            approved_vouchers=approved_vouchers,
            failed_vouchers=failed_vouchers
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk voucher approval: {str(e)}"
        )

# ============================================
# VOUCHER PAYMENT ENDPOINTS
# ============================================

@router.post("/vouchers/{voucher_id}/pay", response_model=VoucherPaymentResponse)
async def pay_voucher(
    voucher_id: int,
    payment_data: VoucherPaymentRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Process payment for a voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:pay")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    if voucher.status != VoucherStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher must be approved before payment"
        )

    if voucher.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher has already been paid"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        voucher.status = VoucherStatus.PAID
        voucher.is_paid = True
        voucher.paid_by = user_id
        voucher.paid_date = current_time
        voucher.payment_method = payment_data.payment_method
        voucher.payment_reference = payment_data.payment_reference
        voucher.bank_account = payment_data.bank_account
        voucher.check_number = payment_data.check_number
        voucher.updated_at = current_time

        if payment_data.notes:
            voucher.notes = (voucher.notes or "") + f"\nPayment notes: {payment_data.notes}"

        db.commit()

        return VoucherPaymentResponse(
            voucher_id=voucher.id,
            amount=voucher.amount,
            payment_date=payment_data.payment_date,
            payment_method=payment_data.payment_method,
            payment_reference=payment_data.payment_reference,
            bank_account=payment_data.bank_account,
            check_number=payment_data.check_number,
            notes=payment_data.notes,
            paid_by=user_id,
            paid_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing voucher payment: {str(e)}"
        )

@router.post("/vouchers/bulk-pay", response_model=BulkVoucherPaymentResponse)
async def bulk_pay_vouchers(
    payment_data: BulkVoucherPaymentRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Bulk pay vouchers"""
    # Check permissions
    await require_permission(current_user, "vouchers:pay")

    paid_vouchers = []
    failed_vouchers = []
    total_amount = 0
    user_id = current_user.get("user_id")
    current_time = datetime.utcnow()

    try:
        for voucher_id in payment_data.voucher_ids:
            voucher = db.query(Voucher).filter(
                and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
            ).first()

            if not voucher:
                failed_vouchers.append({
                    "voucher_id": voucher_id,
                    "error_message": "Voucher not found"
                })
                continue

            if voucher.status != VoucherStatus.APPROVED:
                failed_vouchers.append({
                    "voucher_id": voucher_id,
                    "error_message": "Voucher must be approved before payment"
                })
                continue

            if voucher.is_paid:
                failed_vouchers.append({
                    "voucher_id": voucher_id,
                    "error_message": "Voucher has already been paid"
                })
                continue

            voucher.status = VoucherStatus.PAID
            voucher.is_paid = True
            voucher.paid_by = user_id
            voucher.paid_date = current_time
            voucher.payment_method = payment_data.payment_method
            voucher.payment_reference = payment_data.payment_reference
            voucher.updated_at = current_time

            if payment_data.notes:
                voucher.notes = (voucher.notes or "") + f"\nBulk payment notes: {payment_data.notes}"

            paid_vouchers.append(voucher_id)
            total_amount += voucher.amount

        db.commit()

        return BulkVoucherPaymentResponse(
            paid_count=len(paid_vouchers),
            failed_count=len(failed_vouchers),
            total_amount=total_amount,
            paid_vouchers=paid_vouchers,
            failed_vouchers=failed_vouchers
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk voucher payment: {str(e)}"
        )

# ============================================
# VOUCHER CANCELLATION ENDPOINTS
# ============================================

@router.post("/vouchers/{voucher_id}/cancel", response_model=VoucherCancellationResponse)
async def cancel_voucher(
    voucher_id: int,
    cancellation_data: VoucherCancellationRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Cancel a voucher"""
    # Check permissions
    await require_permission(current_user, "vouchers:cancel")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    if voucher.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a paid voucher"
        )

    if voucher.is_cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher is already cancelled"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        voucher.status = VoucherStatus.CANCELLED
        voucher.is_cancelled = True
        voucher.cancelled_by = user_id
        voucher.cancelled_date = current_time
        voucher.cancellation_reason = cancellation_data.cancellation_reason
        voucher.updated_at = current_time

        if cancellation_data.notes:
            voucher.notes = (voucher.notes or "") + f"\nCancellation notes: {cancellation_data.notes}"

        db.commit()

        return VoucherCancellationResponse(
            voucher_id=voucher.id,
            cancellation_reason=cancellation_data.cancellation_reason,
            notes=cancellation_data.notes,
            cancelled_by=user_id,
            cancelled_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling voucher: {str(e)}"
        )

# ============================================
# VOUCHER POSTING ENDPOINTS
# ============================================

@router.post("/vouchers/{voucher_id}/post", response_model=VoucherPostingResponse)
async def post_voucher(
    voucher_id: int,
    posting_data: VoucherPostingRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Post a voucher to accounting"""
    # Check permissions
    await require_permission(current_user, "vouchers:post")

    voucher = db.query(Voucher).filter(
        and_(Voucher.id == voucher_id, Voucher.deleted_at.is_(None))
    ).first()

    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voucher not found"
        )

    if not voucher.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher must be paid before posting"
        )

    if voucher.is_posted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Voucher has already been posted"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        voucher.is_posted = True
        voucher.posted_date = posting_data.posted_date
        voucher.accounting_period = posting_data.accounting_period
        voucher.journal_entry_number = posting_data.journal_entry_number
        voucher.updated_at = current_time

        if posting_data.notes:
            voucher.notes = (voucher.notes or "") + f"\nPosting notes: {posting_data.notes}"

        db.commit()

        return VoucherPostingResponse(
            voucher_id=voucher.id,
            accounting_period=posting_data.accounting_period,
            journal_entry_number=posting_data.journal_entry_number,
            posted_date=posting_data.posted_date,
            notes=posting_data.notes,
            posted_by=user_id,
            posted_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error posting voucher: {str(e)}"
        )

# ============================================
# VOUCHER SUMMARY ENDPOINTS
# ============================================

@router.get("/vouchers/summary", response_model=VoucherSummaryResponse)
async def get_voucher_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get voucher summary and statistics"""
    # Check permissions
    await require_permission(current_user, "vouchers:read")

    try:
        # Build base query
        query = db.query(Voucher).filter(Voucher.deleted_at.is_(None))

        if start_date:
            query = query.filter(Voucher.voucher_date >= start_date)
        if end_date:
            query = query.filter(Voucher.voucher_date <= end_date)

        # Get total vouchers
        total_result = query.with_entities(
            func.count(Voucher.id).label('count'),
            func.sum(Voucher.amount).label('total_amount')
        ).first()

        total_vouchers = total_result.count or 0
        total_amount = total_result.total_amount or 0

        # Summary by status
        status_summary = query.with_entities(
            Voucher.status,
            func.sum(Voucher.amount).label('total_amount'),
            func.count(Voucher.id).label('count'),
            func.avg(Voucher.amount).label('avg_amount')
        ).group_by(Voucher.status).all()

        by_status = [
            VoucherSummaryByStatus(
                status=VoucherStatus(row.status),
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in status_summary
        ]

        # Summary by type
        type_summary = query.with_entities(
            Voucher.voucher_type,
            func.sum(Voucher.amount).label('total_amount'),
            func.count(Voucher.id).label('count'),
            func.avg(Voucher.amount).label('avg_amount')
        ).group_by(Voucher.voucher_type).all()

        by_type = [
            VoucherSummaryByType(
                voucher_type=VoucherType(row.voucher_type),
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in type_summary
        ]

        # Summary by payee type
        payee_summary = query.with_entities(
            Voucher.payee_type,
            func.sum(Voucher.amount).label('total_amount'),
            func.count(Voucher.id).label('count'),
            func.avg(Voucher.amount).label('avg_amount')
        ).group_by(Voucher.payee_type).all()

        by_payee = [
            VoucherSummaryByPayee(
                payee_type=PayeeType(row.payee_type) if row.payee_type else None,
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in payee_summary
        ]

        # Summary by period
        period_summary = query.with_entities(
            Voucher.accounting_period,
            func.sum(Voucher.amount).label('total_amount'),
            func.count(Voucher.id).label('count')
        ).group_by(Voucher.accounting_period).all()

        by_period = []
        for period_row in period_summary:
            period_status_summary = query.filter(
                Voucher.accounting_period == period_row.accounting_period
            ).with_entities(
                Voucher.status,
                func.sum(Voucher.amount).label('total_amount'),
                func.count(Voucher.id).label('count'),
                func.avg(Voucher.amount).label('avg_amount')
            ).group_by(Voucher.status).all()

            period_by_status = [
                VoucherSummaryByStatus(
                    status=VoucherStatus(row.status),
                    total_amount=row.total_amount or 0,
                    count=row.count or 0,
                    avg_amount=row.avg_amount or 0
                ) for row in period_status_summary
            ]

            by_period.append(VoucherSummaryByPeriod(
                accounting_period=period_row.accounting_period,
                total_amount=period_row.total_amount or 0,
                count=period_row.count or 0,
                by_status=period_by_status
            ))

        # Additional metrics
        pending_approval = query.filter(
            and_(Voucher.is_approved == False, Voucher.is_cancelled == False)
        ).with_entities(
            func.count(Voucher.id).label('count'),
            func.sum(Voucher.amount).label('total_amount')
        ).first()

        pending_approval_count = pending_approval.count or 0
        pending_approval_amount = pending_approval.total_amount or 0

        approved_unpaid = query.filter(
            and_(Voucher.is_approved == True, Voucher.is_paid == False, Voucher.is_cancelled == False)
        ).with_entities(
            func.count(Voucher.id).label('count'),
            func.sum(Voucher.amount).label('total_amount')
        ).first()

        approved_unpaid_count = approved_unpaid.count or 0
        approved_unpaid_amount = approved_unpaid.total_amount or 0

        posted = query.filter(Voucher.is_posted == True).with_entities(
            func.count(Voucher.id).label('count'),
            func.sum(Voucher.amount).label('total_amount')
        ).first()

        posted_count = posted.count or 0
        posted_amount = posted.total_amount or 0

        return VoucherSummaryResponse(
            total_vouchers=total_vouchers,
            total_amount=total_amount,
            by_status=by_status,
            by_type=by_type,
            by_payee=by_payee,
            by_period=by_period,
            pending_approval_count=pending_approval_count,
            pending_approval_amount=pending_approval_amount,
            approved_unpaid_count=approved_unpaid_count,
            approved_unpaid_amount=approved_unpaid_amount,
            posted_count=posted_count,
            posted_amount=posted_amount
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating voucher summary: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/vouchers/health")
async def voucher_health():
    """Health check for voucher module"""
    return {
        "status": "healthy",
        "module": "voucher",
        "timestamp": datetime.utcnow().isoformat()
    }
