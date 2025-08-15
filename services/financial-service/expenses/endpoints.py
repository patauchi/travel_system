"""
Expenses Module Endpoints
API endpoints for expense management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import Expense, ExpenseCategory
from .schemas import (
    ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseListResponse,
    ExpenseCategoryCreate, ExpenseCategoryUpdate, ExpenseCategoryResponse, ExpenseCategoryListResponse,
    ExpenseApprovalRequest, ExpenseApprovalResponse,
    ExpenseReimbursementRequest, ExpenseReimbursementResponse,
    ExpenseSummaryResponse, ExpenseSummaryByCategory, ExpenseSummaryByStatus, ExpenseSummaryByPeriod
)
from common.enums import ExpenseStatus, ExpenseType

router = APIRouter()

# ============================================
# EXPENSE CATEGORY ENDPOINTS
# ============================================

@router.post("/expense-categories", response_model=ExpenseCategoryResponse)
async def create_expense_category(
    category_data: ExpenseCategoryCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new expense category"""
    # Check permissions
    await require_permission(current_user, "expenses:admin")

    try:
        category = ExpenseCategory(**category_data.model_dump())
        db.add(category)
        db.commit()
        db.refresh(category)

        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating expense category: {str(e)}"
        )

@router.get("/expense-categories", response_model=ExpenseCategoryListResponse)
async def list_expense_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    active_only: bool = Query(True, description="Show only active categories"),
    parent_id: Optional[int] = Query(None, description="Filter by parent category ID"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List expense categories"""
    # Check permissions
    await require_permission(current_user, "expenses:read")

    try:
        # Build query
        query = db.query(ExpenseCategory).filter(ExpenseCategory.deleted_at.is_(None))

        # Apply filters
        if active_only:
            query = query.filter(ExpenseCategory.is_active == True)
        if parent_id is not None:
            query = query.filter(ExpenseCategory.parent_id == parent_id)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        categories = query.order_by(asc(ExpenseCategory.name)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return ExpenseCategoryListResponse(
            categories=categories,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing expense categories: {str(e)}"
        )

@router.get("/expense-categories/{category_id}", response_model=ExpenseCategoryResponse)
async def get_expense_category(
    category_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific expense category by ID"""
    # Check permissions
    await require_permission(current_user, "expenses:read")

    category = db.query(ExpenseCategory).filter(
        and_(ExpenseCategory.id == category_id, ExpenseCategory.deleted_at.is_(None))
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )

    return category

@router.put("/expense-categories/{category_id}", response_model=ExpenseCategoryResponse)
async def update_expense_category(
    category_id: int,
    category_data: ExpenseCategoryUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an expense category"""
    # Check permissions
    await require_permission(current_user, "expenses:admin")

    category = db.query(ExpenseCategory).filter(
        and_(ExpenseCategory.id == category_id, ExpenseCategory.deleted_at.is_(None))
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )

    try:
        # Update category fields
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)

        category.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(category)

        return category
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating expense category: {str(e)}"
        )

@router.delete("/expense-categories/{category_id}")
async def delete_expense_category(
    category_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete an expense category"""
    # Check permissions
    await require_permission(current_user, "expenses:admin")

    category = db.query(ExpenseCategory).filter(
        and_(ExpenseCategory.id == category_id, ExpenseCategory.deleted_at.is_(None))
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )

    # Check if category has expenses
    expense_count = db.query(Expense).filter(Expense.category_id == category_id).count()
    if expense_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing expenses"
        )

    try:
        category.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Expense category deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting expense category: {str(e)}"
        )

# ============================================
# EXPENSE ENDPOINTS
# ============================================

@router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new expense"""
    # Check permissions
    await require_permission(current_user, "expenses:create")

    # Verify category exists
    category = db.query(ExpenseCategory).filter(
        and_(ExpenseCategory.id == expense_data.category_id, ExpenseCategory.deleted_at.is_(None))
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense category not found"
        )

    try:
        expense = Expense(**expense_data.model_dump())
        expense.employee_id = current_user.get("user_id")  # Set current user as employee
        db.add(expense)
        db.commit()
        db.refresh(expense)

        return expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating expense: {str(e)}"
        )

@router.get("/expenses", response_model=ExpenseListResponse)
async def list_expenses(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_filter: Optional[ExpenseStatus] = Query(None, description="Filter by expense status"),
    expense_type: Optional[ExpenseType] = Query(None, description="Filter by expense type"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    employee_id: Optional[str] = Query(None, description="Filter by employee ID"),
    start_date: Optional[date] = Query(None, description="Filter expenses from this date"),
    end_date: Optional[date] = Query(None, description="Filter expenses to this date"),
    is_reimbursable: Optional[bool] = Query(None, description="Filter by reimbursable status"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List expenses with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "expenses:read")

    try:
        # Build query
        query = db.query(Expense).filter(Expense.deleted_at.is_(None))

        # Apply filters
        if status_filter:
            query = query.filter(Expense.status == status_filter)
        if expense_type:
            query = query.filter(Expense.expense_type == expense_type)
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        if employee_id:
            query = query.filter(Expense.employee_id == employee_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        if is_reimbursable is not None:
            query = query.filter(Expense.is_reimbursable == is_reimbursable)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        expenses = query.order_by(desc(Expense.expense_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return ExpenseListResponse(
            expenses=expenses,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing expenses: {str(e)}"
        )

@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific expense by ID"""
    # Check permissions
    await require_permission(current_user, "expenses:read")

    expense = db.query(Expense).filter(
        and_(Expense.id == expense_id, Expense.deleted_at.is_(None))
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    return expense

@router.put("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an existing expense"""
    # Check permissions
    await require_permission(current_user, "expenses:update")

    expense = db.query(Expense).filter(
        and_(Expense.id == expense_id, Expense.deleted_at.is_(None))
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    # Check if user can update this expense
    user_id = current_user.get("user_id")
    if expense.employee_id != user_id and not await require_permission(current_user, "expenses:admin", raise_exception=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own expenses"
        )

    try:
        # Update expense fields
        update_data = expense_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)

        expense.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(expense)

        return expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating expense: {str(e)}"
        )

@router.delete("/expenses/{expense_id}")
async def delete_expense(
    expense_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete an expense"""
    # Check permissions
    await require_permission(current_user, "expenses:delete")

    expense = db.query(Expense).filter(
        and_(Expense.id == expense_id, Expense.deleted_at.is_(None))
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    # Check if user can delete this expense
    user_id = current_user.get("user_id")
    if expense.employee_id != user_id and not await require_permission(current_user, "expenses:admin", raise_exception=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own expenses"
        )

    try:
        expense.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Expense deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting expense: {str(e)}"
        )

# ============================================
# EXPENSE APPROVAL ENDPOINTS
# ============================================

@router.post("/expenses/{expense_id}/approve", response_model=ExpenseApprovalResponse)
async def approve_expense(
    expense_id: int,
    approval_data: ExpenseApprovalRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Approve or reject an expense"""
    # Check permissions
    await require_permission(current_user, "expenses:approve")

    expense = db.query(Expense).filter(
        and_(Expense.id == expense_id, Expense.deleted_at.is_(None))
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    if expense.status not in [ExpenseStatus.pending]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is not in a state that can be approved/rejected"
        )

    try:
        user_id = current_user.get("user_id")
        current_time = datetime.utcnow()

        if approval_data.action.lower() == "approve":
            expense.status = ExpenseStatus.approved
            expense.approved_by = user_id
            expense.approved_at = current_time
        elif approval_data.action.lower() == "reject":
            expense.status = ExpenseStatus.rejected
            expense.rejected_at = current_time
            expense.rejection_reason = approval_data.rejection_reason
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'"
            )

        expense.updated_at = current_time
        db.commit()

        return ExpenseApprovalResponse(
            expense_id=expense.id,
            action=approval_data.action,
            approved_by=expense.approved_by,
            approved_at=expense.approved_at,
            rejected_at=expense.rejected_at,
            notes=approval_data.notes,
            rejection_reason=expense.rejection_reason
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing expense approval: {str(e)}"
        )

@router.post("/expenses/{expense_id}/reimburse", response_model=ExpenseReimbursementResponse)
async def reimburse_expense(
    expense_id: int,
    reimbursement_data: ExpenseReimbursementRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Process expense reimbursement"""
    # Check permissions
    await require_permission(current_user, "expenses:reimburse")

    expense = db.query(Expense).filter(
        and_(Expense.id == expense_id, Expense.deleted_at.is_(None))
    ).first()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    if expense.status != ExpenseStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense must be approved before reimbursement"
        )

    if not expense.is_reimbursable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense is not marked as reimbursable"
        )

    try:
        expense.status = ExpenseStatus.reimbursed
        expense.reimbursed_amount = reimbursement_data.amount
        expense.reimbursement_date = reimbursement_data.reimbursement_date
        expense.payment_method = reimbursement_data.payment_method
        expense.payment_reference = reimbursement_data.payment_reference
        expense.updated_at = datetime.utcnow()

        db.commit()

        return ExpenseReimbursementResponse(
            expense_id=expense.id,
            reimbursed_amount=expense.reimbursed_amount,
            reimbursement_date=expense.reimbursement_date,
            payment_method=expense.payment_method,
            payment_reference=expense.payment_reference,
            notes=reimbursement_data.notes,
            processed_by=current_user.get("user_id"),
            processed_at=expense.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing expense reimbursement: {str(e)}"
        )

# ============================================
# EXPENSE REPORTING ENDPOINTS
# ============================================

@router.get("/expenses/summary", response_model=ExpenseSummaryResponse)
async def get_expense_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get expense summary and statistics"""
    # Check permissions
    await require_permission(current_user, "expenses:read")

    try:
        # Build base query
        query = db.query(Expense).filter(Expense.deleted_at.is_(None))

        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)

        # Get total expenses
        total_result = query.with_entities(
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).first()

        total_expenses = total_result.total_amount or 0
        total_count = total_result.count or 0

        # Get summary by status
        status_summary = query.with_entities(
            Expense.status,
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).group_by(Expense.status).all()

        by_status = [
            ExpenseSummaryByStatus(
                status=row.status,
                total_amount=row.total_amount or 0,
                count=row.count or 0
            ) for row in status_summary
        ]

        # Get summary by category
        category_summary = query.join(ExpenseCategory).with_entities(
            Expense.category_id,
            ExpenseCategory.name.label('category_name'),
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count'),
            func.avg(Expense.total_amount).label('avg_amount')
        ).group_by(Expense.category_id, ExpenseCategory.name).all()

        by_category = [
            ExpenseSummaryByCategory(
                category_id=row.category_id,
                category_name=row.category_name,
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0
            ) for row in category_summary
        ]

        # Get pending approval amounts
        pending_result = query.filter(Expense.status == ExpenseStatus.pending).with_entities(
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).first()

        pending_approval_amount = pending_result.total_amount or 0
        pending_approval_count = pending_result.count or 0

        # Get reimbursable amounts
        reimbursable_result = query.filter(
            and_(Expense.is_reimbursable == True, Expense.status == ExpenseStatus.approved)
        ).with_entities(
            func.sum(Expense.total_amount).label('total_amount'),
            func.count(Expense.id).label('count')
        ).first()

        reimbursable_amount = reimbursable_result.total_amount or 0
        reimbursable_count = reimbursable_result.count or 0

        return ExpenseSummaryResponse(
            total_expenses=total_expenses,
            total_count=total_count,
            by_status=by_status,
            by_category=by_category,
            by_period=[],  # Can be implemented later if needed
            pending_approval_amount=pending_approval_amount,
            pending_approval_count=pending_approval_count,
            reimbursable_amount=reimbursable_amount,
            reimbursable_count=reimbursable_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating expense summary: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/expenses/health")
async def expenses_health():
    """Health check for expenses module"""
    return {
        "status": "healthy",
        "module": "expenses",
        "timestamp": datetime.utcnow().isoformat()
    }
