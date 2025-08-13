"""
Financial Service - Expenses Endpoints
API endpoints for expense management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import Expense, ExpenseCategory, PettyCash, PettyCashTransaction, Voucher

router = APIRouter()


@router.post("/tenants/{tenant_id}/expenses")
async def create_expense(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create a new expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Placeholder implementation
    return {
        "id": 1,
        "expense_number": "EXP-2024-001",
        "expense_date": date.today(),
        "expense_type": "travel",
        "description": "Business travel expense",
        "amount": 500.00,
        "total_amount": 500.00,
        "currency": "USD",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.get("/tenants/{tenant_id}/expenses")
async def list_expenses(
    tenant_id: str,
    status: Optional[str] = Query(None),
    expense_type: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """List all expenses for a tenant"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.get("/tenants/{tenant_id}/expenses/{expense_id}")
async def get_expense(
    tenant_id: str,
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": expense_id,
        "expense_number": f"EXP-2024-{expense_id:03d}",
        "expense_date": date.today(),
        "expense_type": "travel",
        "description": "Business travel expense",
        "amount": 500.00,
        "total_amount": 500.00,
        "currency": "USD",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.put("/tenants/{tenant_id}/expenses/{expense_id}")
async def update_expense(
    tenant_id: str,
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Update an expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": expense_id,
        "expense_number": f"EXP-2024-{expense_id:03d}",
        "expense_date": date.today(),
        "expense_type": "travel",
        "description": "Updated business travel expense",
        "amount": 550.00,
        "total_amount": 550.00,
        "currency": "USD",
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.post("/tenants/{tenant_id}/expenses/{expense_id}/approve")
async def approve_expense(
    tenant_id: str,
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Approve an expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": expense_id,
        "status": "approved",
        "approved_at": datetime.utcnow(),
        "message": f"Expense {expense_id} approved successfully"
    }


@router.post("/tenants/{tenant_id}/expenses/{expense_id}/reject")
async def reject_expense(
    tenant_id: str,
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Reject an expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": expense_id,
        "status": "rejected",
        "rejected_at": datetime.utcnow(),
        "rejection_reason": "Missing receipt",
        "message": f"Expense {expense_id} rejected"
    }


@router.delete("/tenants/{tenant_id}/expenses/{expense_id}")
async def delete_expense(
    tenant_id: str,
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Delete an expense"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {"message": f"Expense {expense_id} deleted successfully"}


# Expense Categories endpoints
@router.get("/tenants/{tenant_id}/expense-categories")
async def list_expense_categories(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """List all expense categories"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.post("/tenants/{tenant_id}/expense-categories")
async def create_expense_category(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create a new expense category"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "name": "Travel",
        "code": "TRAVEL",
        "description": "Travel related expenses",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# Petty Cash endpoints
@router.get("/tenants/{tenant_id}/petty-cash")
async def list_petty_cash_funds(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """List all petty cash funds"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.post("/tenants/{tenant_id}/petty-cash")
async def create_petty_cash_fund(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create a new petty cash fund"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "fund_name": "Office Petty Cash",
        "fund_code": "PC-001",
        "initial_amount": 1000.00,
        "current_balance": 1000.00,
        "status": "open",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.post("/tenants/{tenant_id}/petty-cash/{fund_id}/transactions")
async def create_petty_cash_transaction(
    tenant_id: str,
    fund_id: int,
    db: Session = Depends(get_db)
):
    """Create a petty cash transaction"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "petty_cash_id": fund_id,
        "transaction_number": "PCT-2024-001",
        "transaction_date": datetime.utcnow(),
        "transaction_type": "expense",
        "amount": 50.00,
        "balance_before": 1000.00,
        "balance_after": 950.00,
        "description": "Office supplies",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# Voucher endpoints
@router.get("/tenants/{tenant_id}/vouchers")
async def list_vouchers(
    tenant_id: str,
    status: Optional[str] = Query(None),
    voucher_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all vouchers"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.post("/tenants/{tenant_id}/vouchers")
async def create_voucher(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create a new voucher"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "voucher_number": "VCH-2024-001",
        "voucher_date": date.today(),
        "voucher_type": "payment",
        "payee_name": "Supplier ABC",
        "amount": 1000.00,
        "currency": "USD",
        "purpose": "Payment for services",
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.post("/tenants/{tenant_id}/vouchers/{voucher_id}/approve")
async def approve_voucher(
    tenant_id: str,
    voucher_id: int,
    db: Session = Depends(get_db)
):
    """Approve a voucher"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": voucher_id,
        "status": "approved",
        "is_approved": True,
        "approved_date": datetime.utcnow(),
        "message": f"Voucher {voucher_id} approved successfully"
    }


@router.get("/tenants/{tenant_id}/expenses/summary")
async def get_expense_summary(
    tenant_id: str,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get expense summary report"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "total_expenses": 0,
        "approved": 0,
        "pending": 0,
        "rejected": 0,
        "by_category": {},
        "by_type": {},
        "by_month": {},
        "top_expenses": []
    }
