"""
Petty Cash Module Endpoints
API endpoints for petty cash management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import PettyCash, PettyCashTransaction
from .schemas import (
    PettyCashCreate, PettyCashUpdate, PettyCashResponse, PettyCashListResponse,
    PettyCashTransactionCreate, PettyCashTransactionUpdate, PettyCashTransactionResponse,
    PettyCashTransactionListResponse, PettyCashTransactionApprovalRequest,
    PettyCashTransactionApprovalResponse, PettyCashReconciliationRequest,
    PettyCashReconciliationResponse, PettyCashReplenishmentRequest,
    PettyCashReplenishmentResponse, PettyCashSummaryResponse,
    PettyCashSummaryByType, PettyCashSummaryByCategory, PettyCashFundSummary
)
from common.enums import PettyCashTransactionType, PettyCashStatus

router = APIRouter()

# ============================================
# PETTY CASH FUND ENDPOINTS
# ============================================

@router.post("/petty-cash", response_model=PettyCashResponse)
async def create_petty_cash_fund(
    fund_data: PettyCashCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new petty cash fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:admin")

    try:
        fund = PettyCash(**fund_data.model_dump())
        db.add(fund)
        db.commit()
        db.refresh(fund)

        return fund
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating petty cash fund: {str(e)}"
        )

@router.get("/petty-cash", response_model=PettyCashListResponse)
async def list_petty_cash_funds(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    active_only: bool = Query(True, description="Show only active funds"),
    status_filter: Optional[PettyCashStatus] = Query(None, description="Filter by fund status"),
    custodian_id: Optional[str] = Query(None, description="Filter by custodian ID"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List petty cash funds with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "pettycash:read")

    try:
        # Build query
        query = db.query(PettyCash).filter(PettyCash.deleted_at.is_(None))

        # Apply filters
        if active_only:
            query = query.filter(PettyCash.is_active == True)
        if status_filter:
            query = query.filter(PettyCash.status == status_filter)
        if custodian_id:
            query = query.filter(PettyCash.custodian_id == custodian_id)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        funds = query.order_by(asc(PettyCash.fund_name)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return PettyCashListResponse(
            funds=funds,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing petty cash funds: {str(e)}"
        )

@router.get("/petty-cash/{fund_id}", response_model=PettyCashResponse)
async def get_petty_cash_fund(
    fund_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific petty cash fund by ID"""
    # Check permissions
    await require_permission(current_user, "pettycash:read")

    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    return fund

@router.put("/petty-cash/{fund_id}", response_model=PettyCashResponse)
async def update_petty_cash_fund(
    fund_id: int,
    fund_data: PettyCashUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update a petty cash fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:admin")

    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    try:
        # Update fund fields
        update_data = fund_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fund, field, value)

        fund.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(fund)

        return fund
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating petty cash fund: {str(e)}"
        )

@router.delete("/petty-cash/{fund_id}")
async def delete_petty_cash_fund(
    fund_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete a petty cash fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:admin")

    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    # Check if fund has transactions
    transaction_count = db.query(PettyCashTransaction).filter(
        PettyCashTransaction.petty_cash_id == fund_id
    ).count()

    if transaction_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete fund with existing transactions"
        )

    try:
        fund.deleted_at = datetime.utcnow()
        fund.status = PettyCashStatus.CLOSED
        db.commit()

        return {"message": "Petty cash fund deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting petty cash fund: {str(e)}"
        )

# ============================================
# PETTY CASH TRANSACTION ENDPOINTS
# ============================================

@router.post("/petty-cash/{fund_id}/transactions", response_model=PettyCashTransactionResponse)
async def create_petty_cash_transaction(
    fund_id: int,
    transaction_data: PettyCashTransactionCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new petty cash transaction"""
    # Check permissions
    await require_permission(current_user, "pettycash:transaction")

    # Verify fund exists and is active
    fund = db.query(PettyCash).filter(
        and_(
            PettyCash.id == fund_id,
            PettyCash.deleted_at.is_(None),
            PettyCash.is_active == True
        )
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active petty cash fund not found"
        )

    # Check transaction amount limits
    if fund.max_transaction_amount and transaction_data.amount > fund.max_transaction_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction amount exceeds maximum allowed ({fund.max_transaction_amount})"
        )

    # Check balance for withdrawals/expenses
    if transaction_data.transaction_type in [PettyCashTransactionType.WITHDRAWAL, PettyCashTransactionType.EXPENSE]:
        if fund.current_balance < transaction_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient funds for this transaction"
            )

    try:
        # Calculate new balance
        balance_before = fund.current_balance
        if transaction_data.transaction_type in [PettyCashTransactionType.DEPOSIT, PettyCashTransactionType.REIMBURSEMENT]:
            balance_after = balance_before + transaction_data.amount
        else:
            balance_after = balance_before - transaction_data.amount

        # Create transaction
        transaction = PettyCashTransaction(
            **transaction_data.model_dump(),
            performed_by=current_user.get("user_id"),
            balance_before=balance_before,
            balance_after=balance_after
        )

        # Update fund balance
        fund.current_balance = balance_after
        fund.updated_at = datetime.utcnow()

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return transaction
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating petty cash transaction: {str(e)}"
        )

@router.get("/petty-cash/{fund_id}/transactions", response_model=PettyCashTransactionListResponse)
async def list_petty_cash_transactions(
    fund_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[PettyCashTransactionType] = Query(None, description="Filter by transaction type"),
    start_date: Optional[date] = Query(None, description="Filter transactions from this date"),
    end_date: Optional[date] = Query(None, description="Filter transactions to this date"),
    is_reconciled: Optional[bool] = Query(None, description="Filter by reconciliation status"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List petty cash transactions for a specific fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:read")

    # Verify fund exists
    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    try:
        # Build query
        query = db.query(PettyCashTransaction).filter(
            and_(
                PettyCashTransaction.petty_cash_id == fund_id,
                PettyCashTransaction.deleted_at.is_(None)
            )
        )

        # Apply filters
        if transaction_type:
            query = query.filter(PettyCashTransaction.transaction_type == transaction_type)
        if start_date:
            query = query.filter(PettyCashTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(PettyCashTransaction.transaction_date <= end_date)
        if is_reconciled is not None:
            query = query.filter(PettyCashTransaction.is_reconciled == is_reconciled)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        transactions = query.order_by(desc(PettyCashTransaction.transaction_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return PettyCashTransactionListResponse(
            transactions=transactions,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing petty cash transactions: {str(e)}"
        )

@router.put("/petty-cash/{fund_id}/transactions/{transaction_id}", response_model=PettyCashTransactionResponse)
async def update_petty_cash_transaction(
    fund_id: int,
    transaction_id: int,
    transaction_data: PettyCashTransactionUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update a petty cash transaction"""
    # Check permissions
    await require_permission(current_user, "pettycash:transaction")

    transaction = db.query(PettyCashTransaction).filter(
        and_(
            PettyCashTransaction.id == transaction_id,
            PettyCashTransaction.petty_cash_id == fund_id,
            PettyCashTransaction.deleted_at.is_(None)
        )
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash transaction not found"
        )

    # Check if user can update this transaction
    user_id = current_user.get("user_id")
    if transaction.performed_by != user_id and not await require_permission(current_user, "pettycash:admin", raise_exception=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own transactions"
        )

    try:
        # Update transaction fields
        update_data = transaction_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(transaction, field, value)

        transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(transaction)

        return transaction
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating petty cash transaction: {str(e)}"
        )

@router.post("/petty-cash/{fund_id}/transactions/{transaction_id}/approve", response_model=PettyCashTransactionApprovalResponse)
async def approve_petty_cash_transaction(
    fund_id: int,
    transaction_id: int,
    approval_data: PettyCashTransactionApprovalRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Approve or reject a petty cash transaction"""
    # Check permissions
    await require_permission(current_user, "pettycash:approve")

    transaction = db.query(PettyCashTransaction).filter(
        and_(
            PettyCashTransaction.id == transaction_id,
            PettyCashTransaction.petty_cash_id == fund_id,
            PettyCashTransaction.deleted_at.is_(None)
        )
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash transaction not found"
        )

    if not transaction.requires_approval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction does not require approval"
        )

    if transaction.is_approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction has already been approved"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        if approval_data.action.lower() == "approve":
            transaction.is_approved = True
            transaction.approved_by = user_id
            transaction.approved_at = current_time
        elif approval_data.action.lower() == "reject":
            transaction.is_approved = False
            # Note: You might want to handle rejection differently
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'"
            )

        transaction.approval_notes = approval_data.approval_notes
        transaction.updated_at = current_time
        db.commit()

        return PettyCashTransactionApprovalResponse(
            transaction_id=transaction.id,
            action=approval_data.action,
            approved_by=transaction.approved_by,
            approved_at=transaction.approved_at,
            approval_notes=transaction.approval_notes
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing transaction approval: {str(e)}"
        )

# ============================================
# PETTY CASH RECONCILIATION ENDPOINTS
# ============================================

@router.post("/petty-cash/{fund_id}/reconcile", response_model=PettyCashReconciliationResponse)
async def reconcile_petty_cash_fund(
    fund_id: int,
    reconciliation_data: PettyCashReconciliationRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Reconcile a petty cash fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:reconcile")

    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        # Calculate discrepancy
        book_balance = fund.current_balance
        actual_balance = reconciliation_data.actual_balance
        discrepancy = actual_balance - book_balance

        # Mark unreconciled transactions as reconciled
        unreconciled_transactions = db.query(PettyCashTransaction).filter(
            and_(
                PettyCashTransaction.petty_cash_id == fund_id,
                PettyCashTransaction.is_reconciled == False,
                PettyCashTransaction.transaction_date <= reconciliation_data.reconciliation_date
            )
        ).all()

        transactions_reconciled = len(unreconciled_transactions)

        for transaction in unreconciled_transactions:
            transaction.is_reconciled = True
            transaction.reconciled_date = reconciliation_data.reconciliation_date
            transaction.reconciled_by = user_id

        # Update fund reconciliation info
        fund.last_reconciled_date = reconciliation_data.reconciliation_date
        fund.last_reconciled_by = user_id
        fund.updated_at = current_time

        # If there's a discrepancy, adjust the balance
        if discrepancy != 0:
            fund.current_balance = actual_balance

        db.commit()

        return PettyCashReconciliationResponse(
            petty_cash_id=fund.id,
            reconciliation_date=reconciliation_data.reconciliation_date,
            book_balance=book_balance,
            actual_balance=actual_balance,
            discrepancy=discrepancy,
            discrepancy_reason=reconciliation_data.discrepancy_reason,
            notes=reconciliation_data.notes,
            reconciled_by=user_id,
            reconciled_at=current_time,
            transactions_reconciled=transactions_reconciled
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reconciling petty cash fund: {str(e)}"
        )

# ============================================
# PETTY CASH REPLENISHMENT ENDPOINTS
# ============================================

@router.post("/petty-cash/{fund_id}/replenish", response_model=PettyCashReplenishmentResponse)
async def replenish_petty_cash_fund(
    fund_id: int,
    replenishment_data: PettyCashReplenishmentRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Replenish a petty cash fund"""
    # Check permissions
    await require_permission(current_user, "pettycash:replenish")

    fund = db.query(PettyCash).filter(
        and_(PettyCash.id == fund_id, PettyCash.deleted_at.is_(None))
    ).first()

    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petty cash fund not found"
        )

    # Check maximum balance limit
    if fund.maximum_balance:
        new_balance = fund.current_balance + replenishment_data.amount
        if new_balance > fund.maximum_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replenishment would exceed maximum balance ({fund.maximum_balance})"
            )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        balance_before = fund.current_balance
        balance_after = balance_before + replenishment_data.amount

        # Create a replenishment transaction
        transaction = PettyCashTransaction(
            petty_cash_id=fund.id,
            transaction_number=f"REP-{fund.fund_code or fund.id}-{int(current_time.timestamp())}",
            transaction_date=current_time,
            transaction_type=PettyCashTransactionType.DEPOSIT,
            amount=replenishment_data.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Fund replenishment - {replenishment_data.payment_method}",
            reference_number=replenishment_data.reference_number,
            performed_by=user_id,
            is_approved=True,  # Replenishments are auto-approved
            approved_by=user_id,
            approved_at=current_time,
            notes=replenishment_data.notes
        )

        # Update fund balance
        fund.current_balance = balance_after
        fund.updated_at = current_time

        db.add(transaction)
        db.commit()

        return PettyCashReplenishmentResponse(
            petty_cash_id=fund.id,
            amount=replenishment_data.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            replenishment_date=replenishment_data.replenishment_date,
            payment_method=replenishment_data.payment_method,
            reference_number=replenishment_data.reference_number,
            notes=replenishment_data.notes,
            processed_by=user_id,
            processed_at=current_time
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error replenishing petty cash fund: {str(e)}"
        )

# ============================================
# PETTY CASH SUMMARY ENDPOINTS
# ============================================

@router.get("/petty-cash/summary", response_model=PettyCashSummaryResponse)
async def get_petty_cash_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get petty cash summary and statistics"""
    # Check permissions
    await require_permission(current_user, "pettycash:read")

    try:
        # Get fund statistics
        fund_stats = db.query(
            func.count(PettyCash.id).label('total_funds'),
            func.count(func.nullif(PettyCash.is_active, False)).label('active_funds'),
            func.sum(PettyCash.current_balance).label('total_balance')
        ).filter(PettyCash.deleted_at.is_(None)).first()

        total_funds = fund_stats.total_funds or 0
        active_funds = fund_stats.active_funds or 0
        total_balance = fund_stats.total_balance or 0

        # Get transaction statistics
        transaction_query = db.query(PettyCashTransaction).filter(
            PettyCashTransaction.deleted_at.is_(None)
        )

        if start_date:
            transaction_query = transaction_query.filter(
                PettyCashTransaction.transaction_date >= start_date
            )
        if end_date:
            transaction_query = transaction_query.filter(
                PettyCashTransaction.transaction_date <= end_date
            )

        total_transactions = transaction_query.count()

        # Summary by transaction type
        type_summary = transaction_query.with_entities(
            PettyCashTransaction.transaction_type,
            func.sum(PettyCashTransaction.amount).label('total_amount'),
            func.count(PettyCashTransaction.id).label('count'),
            func.avg(PettyCashTransaction.amount).label('avg_amount')
        ).group_by(PettyCashTransaction.transaction_type).all()

        by_type = [
            PettyCashSummaryByType(
                transaction_type=row.transaction_type,
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in type_summary
        ]

        # Summary by category (for expenses)
        category_summary = transaction_query.filter(
            PettyCashTransaction.expense_category_id.isnot(None)
        ).with_entities(
            PettyCashTransaction.expense_category_id,
            func.sum(PettyCashTransaction.amount).label('total_amount'),
            func.count(PettyCashTransaction.id).label('count')
        ).group_by(PettyCashTransaction.expense_category_id).all()

        by_category = [
            PettyCashSummaryByCategory(
                category_id=row.expense_category_id,
                category_name=None,  # Could join with expense_categories table
                total_amount=row.total_amount or 0,
                count=row.count or 0
            ) for row in category_summary
        ]

        # Fund summaries
        fund_summaries = []
        funds = db.query(PettyCash).filter(
            and_(PettyCash.deleted_at.is_(None), PettyCash.is_active == True)
        ).all()

        for fund in funds:
            last_transaction = db.query(PettyCashTransaction).filter(
                PettyCashTransaction.petty_cash_id == fund.id
            ).order_by(desc(PettyCashTransaction.transaction_date)).first()

            days_since_reconciliation = None
            if fund.last_reconciled_date:
                days_since_reconciliation = (date.today() - fund.last_reconciled_date).days

            fund_summaries.append(PettyCashFundSummary(
                fund_id=fund.id,
                fund_name=fund.fund_name,
                current_balance=fund.current_balance,
                total_transactions=db.query(PettyCashTransaction).filter(
                    PettyCashTransaction.petty_cash_id == fund.id
                ).count(),
                total_expenses=db.query(func.sum(PettyCashTransaction.amount)).filter(
                    and_(
                        PettyCashTransaction.petty_cash_id == fund.id,
                        PettyCashTransaction.transaction_type.in_([
                            PettyCashTransactionType.EXPENSE,
                            PettyCashTransactionType.WITHDRAWAL
                        ])
                    )
                ).scalar() or 0,
                total_deposits=db.query(func.sum(PettyCashTransaction.amount)).filter(
                    and_(
                        PettyCashTransaction.petty_cash_id == fund.id,
                        PettyCashTransaction.transaction_type.in_([
                            PettyCashTransactionType.DEPOSIT,
                            PettyCashTransactionType.REIMBURSEMENT
                        ])
                    )
                ).scalar() or 0,
                last_transaction_date=last_transaction.transaction_date if last_transaction else None,
                days_since_reconciliation=days_since_reconciliation
            ))

        # Additional metrics
        funds_needing_reconciliation = db.query(PettyCash).filter(
            and_(
                PettyCash.deleted_at.is_(None),
                PettyCash.is_active == True,
                or_(
                    PettyCash.last_reconciled_date.is_(None),
                    PettyCash.last_reconciled_date < (date.today() - func.interval('30 days'))
                )
            )
        ).count()

        funds_below_minimum = db.query(PettyCash).filter(
            and_(
                PettyCash.deleted_at.is_(None),
                PettyCash.is_active == True,
                PettyCash.current_balance < PettyCash.minimum_balance
            )
        ).count()

        pending_approvals = db.query(PettyCashTransaction).filter(
            and_(
                PettyCashTransaction.deleted_at.is_(None),
                PettyCashTransaction.requires_approval == True,
                PettyCashTransaction.is_approved == False
            )
        ).count()

        return PettyCashSummaryResponse(
            total_funds=total_funds,
            active_funds=active_funds,
            total_balance=total_balance,
            total_transactions=total_transactions,
            by_type=by_type,
            by_category=by_category,
            fund_summaries=fund_summaries,
            funds_needing_reconciliation=funds_needing_reconciliation,
            funds_below_minimum=funds_below_minimum,
            pending_approvals=pending_approvals
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating petty cash summary: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/petty-cash/health")
async def petty_cash_health():
    """Health check for petty cash module"""
    return {
        "status": "healthy",
        "module": "pettycash",
        "timestamp": datetime.utcnow().isoformat()
    }
