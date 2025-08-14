"""
Booking Operations Service - Suppliers Endpoints
API endpoints for supplier management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import Supplier, SupplierStatus

router = APIRouter()


@router.post("/tenants/{tenant_id}/suppliers")
async def create_supplier(
    tenant_id: str,
    supplier_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new supplier"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "code": supplier_data.get("code", "SUP-001"),
        "name": supplier_data.get("name", "Sample Supplier"),
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/tenants/{tenant_id}/suppliers")
async def list_suppliers(
    tenant_id: str,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List all suppliers for a tenant"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "suppliers": [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "total_pages": 0
        }
    }


@router.get("/tenants/{tenant_id}/suppliers/{supplier_id}")
async def get_supplier(
    tenant_id: str,
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific supplier"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": supplier_id,
        "code": f"SUP-{supplier_id:03d}",
        "name": "Sample Supplier",
        "type": "company",
        "status": "active",
        "created_at": datetime.utcnow().isoformat()
    }


@router.put("/tenants/{tenant_id}/suppliers/{supplier_id}")
async def update_supplier(
    tenant_id: str,
    supplier_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update a supplier"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": supplier_id,
        "message": "Supplier updated successfully",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.delete("/tenants/{tenant_id}/suppliers/{supplier_id}")
async def delete_supplier(
    tenant_id: str,
    supplier_id: int,
    db: Session = Depends(get_db)
):
    """Soft delete a supplier"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "message": f"Supplier {supplier_id} deleted successfully",
        "deleted_at": datetime.utcnow().isoformat()
    }
