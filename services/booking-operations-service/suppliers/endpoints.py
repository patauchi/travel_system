"""
Suppliers module endpoints
Contains FastAPI endpoints for supplier management and operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import get_tenant_db
from shared_auth import get_current_user, check_tenant_slug_access
from utils.audit import AuditLogger, AuditAction, get_audit_logger
from .models import Supplier
from .schemas import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
    SupplierListResponse
)

router = APIRouter()


@router.get("/tenants/{tenant_slug}/suppliers", response_model=SupplierListResponse)
async def list_suppliers(
    tenant_slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    supplier_type: Optional[str] = Query(None, description="Filter by supplier type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name, code or email"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    List suppliers with filtering and pagination

    Args:
        tenant_slug: Tenant identifier
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        supplier_type: Filter by supplier type
        status: Filter by status
        is_active: Filter by active status
        search: Search in name, code or email
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of suppliers with pagination info
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build query
    query = db.query(Supplier)

    # Apply filters
    filters = []

    if supplier_type:
        filters.append(Supplier.supplier_type == supplier_type)

    if status:
        filters.append(Supplier.status == status)

    if is_active is not None:
        filters.append(Supplier.is_active == is_active)

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Supplier.name.ilike(search_pattern),
                Supplier.code.ilike(search_pattern),
                Supplier.contact_email.ilike(search_pattern),
                Supplier.legal_name.ilike(search_pattern)
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    suppliers = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": suppliers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/tenants/{tenant_slug}/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    tenant_slug: str,
    supplier_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get a specific supplier by ID

    Args:
        tenant_slug: Tenant identifier
        supplier_id: Supplier ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Supplier details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found"
        )

    return supplier


@router.post("/tenants/{tenant_slug}/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    tenant_slug: str,
    request: Request,
    supplier_data: SupplierCreate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Create a new supplier

    Args:
        tenant_slug: Tenant identifier
        supplier_data: Supplier data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created supplier
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Check if supplier with same code exists
    existing_supplier = db.query(Supplier).filter(
        Supplier.code == supplier_data.code
    ).first()

    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with code {supplier_data.code} already exists"
        )

    # Check if supplier with same tax_id exists (if provided)
    if supplier_data.tax_id:
        existing_tax = db.query(Supplier).filter(
            Supplier.tax_id == supplier_data.tax_id
        ).first()

        if existing_tax:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with tax ID {supplier_data.tax_id} already exists"
            )

    # Create new supplier
    new_supplier = Supplier(**supplier_data.dict())

    # Set timestamps
    new_supplier.created_at = datetime.utcnow()
    new_supplier.updated_at = datetime.utcnow()

    # Add to database
    db.add(new_supplier)

    try:
        db.commit()
        db.refresh(new_supplier)

        # Log audit event
        audit_logger.log_create(
            entity_type="supplier",
            entity_id=new_supplier.id,
            entity_data={
                "id": new_supplier.id,
                "code": new_supplier.code,
                "name": new_supplier.name,
                "type": new_supplier.type.value if new_supplier.type else None,
                "status": new_supplier.status.value if new_supplier.status else None
            },
            user=current_user,
            request_context={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": request.headers.get("x-request-id")
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating supplier: {str(e)}"
        )

    return new_supplier


@router.put("/tenants/{tenant_slug}/suppliers/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    tenant_slug: str,
    supplier_id: int,
    request: Request,
    supplier_update: SupplierUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update an existing supplier

    Args:
        tenant_slug: Tenant identifier
        supplier_id: Supplier ID
        supplier_update: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated supplier
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found"
        )

    # Check if updating code to an existing one
    if supplier_update.code and supplier_update.code != supplier.code:
        existing = db.query(Supplier).filter(
            Supplier.code == supplier_update.code,
            Supplier.id != supplier_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with code {supplier_update.code} already exists"
            )

    # Check if updating tax_id to an existing one
    if supplier_update.tax_id and supplier_update.tax_id != supplier.tax_id:
        existing = db.query(Supplier).filter(
            Supplier.tax_id == supplier_update.tax_id,
            Supplier.id != supplier_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with tax ID {supplier_update.tax_id} already exists"
            )

    # Store old values for audit
    old_values = {
        "code": supplier.code,
        "name": supplier.name,
        "type": supplier.type.value if supplier.type else None,
        "status": supplier.status.value if supplier.status else None,
        "is_active": supplier.is_active
    }

    # Update fields
    update_data = supplier_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    # Update timestamp
    supplier.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(supplier)

        # Log audit event
        new_values = {
            "code": supplier.code,
            "name": supplier.name,
            "type": supplier.type.value if supplier.type else None,
            "status": supplier.status.value if supplier.status else None,
            "is_active": supplier.is_active
        }

        audit_logger.log_update(
            entity_type="supplier",
            entity_id=supplier.id,
            old_data=old_values,
            new_data=new_values,
            user=current_user,
            request_context={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": request.headers.get("x-request-id")
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating supplier: {str(e)}"
        )

    return supplier


@router.delete("/tenants/{tenant_slug}/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_supplier(
    tenant_slug: str,
    supplier_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Delete a supplier

    Args:
        tenant_slug: Tenant identifier
        supplier_id: Supplier ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        No content on success
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found"
        )

    # Check if supplier has related services
    from services.models import Service
    services_count = db.query(Service).filter(Service.supplier_id == supplier_id).count()

    if services_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete supplier with {services_count} associated services. "
                   f"Please delete or reassign services first."
        )

    # Store supplier data for audit
    supplier_data = {
        "id": supplier.id,
        "code": supplier.code,
        "name": supplier.name,
        "type": supplier.type.value if supplier.type else None,
        "status": supplier.status.value if supplier.status else None
    }

    try:
        db.delete(supplier)
        db.commit()

        # Log audit event
        audit_logger.log_delete(
            entity_type="supplier",
            entity_id=supplier_id,
            entity_data=supplier_data,
            user=current_user,
            request_context={
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": request.headers.get("x-request-id")
            }
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting supplier: {str(e)}"
        )

    return None


@router.patch("/tenants/{tenant_slug}/suppliers/{supplier_id}/status")
async def update_supplier_status(
    tenant_slug: str,
    supplier_id: int,
    request: Request,
    status_update: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """
    Update supplier status

    Args:
        tenant_slug: Tenant identifier
        supplier_id: Supplier ID
        status_update: Status update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated supplier
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found"
        )

    # Store old status for audit
    old_status = supplier.status
    old_is_active = supplier.is_active

    # Update status
    new_status = status_update.get("status")
    if new_status:
        supplier.status = new_status

    # Update is_active
    is_active = status_update.get("is_active")
    if is_active is not None:
        supplier.is_active = is_active

    # Update timestamp
    supplier.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(supplier)

        # Log status change if status changed
        if new_status and new_status != old_status:
            audit_logger.log_status_change(
                entity_type="supplier",
                entity_id=supplier.id,
                old_status=old_status,
                new_status=new_status,
                user=current_user,
                reason=status_update.get("reason"),
                request_context={
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_id": request.headers.get("x-request-id")
                }
            )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating supplier status: {str(e)}"
        )

    return {
        "id": supplier.id,
        "code": supplier.code,
        "name": supplier.name,
        "status": supplier.status,
        "is_active": supplier.is_active,
        "updated_at": supplier.updated_at.isoformat()
    }


@router.get("/tenants/{tenant_slug}/suppliers/search/by-code/{code}")
async def get_supplier_by_code(
    tenant_slug: str,
    code: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get supplier by code

    Args:
        tenant_slug: Tenant identifier
        code: Supplier code
        current_user: Current authenticated user
        db: Database session

    Returns:
        Supplier details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get supplier
    supplier = db.query(Supplier).filter(Supplier.code == code).first()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with code {code} not found"
        )

    return supplier


@router.get("/tenants/{tenant_slug}/suppliers/statistics")
async def get_suppliers_statistics(
    tenant_slug: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get suppliers statistics

    Args:
        tenant_slug: Tenant identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Suppliers statistics
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get statistics
    total_suppliers = db.query(Supplier).count()
    active_suppliers = db.query(Supplier).filter(Supplier.is_active == True).count()

    # Count by type
    type_counts = db.query(
        Supplier.supplier_type,
        func.count(Supplier.id)
    ).group_by(Supplier.supplier_type).all()

    # Count by status
    status_counts = db.query(
        Supplier.status,
        func.count(Supplier.id)
    ).group_by(Supplier.status).all()

    return {
        "total_suppliers": total_suppliers,
        "active_suppliers": active_suppliers,
        "inactive_suppliers": total_suppliers - active_suppliers,
        "by_type": {type_name: count for type_name, count in type_counts if type_name},
        "by_status": {status_name: count for status_name, count in status_counts if status_name},
        "generated_at": datetime.utcnow().isoformat()
    }
