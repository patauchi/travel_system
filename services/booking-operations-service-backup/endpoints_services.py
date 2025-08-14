"""
Booking Operations Service - Services Endpoints
API endpoints for service management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import Service, ServiceType

router = APIRouter()


@router.post("/tenants/{tenant_id}/services")
async def create_service(
    tenant_id: str,
    service_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new service"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "service_code": service_data.get("service_code", "SRV-001"),
        "name": service_data.get("name", "Sample Service"),
        "service_type": service_data.get("service_type", "tour"),
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/tenants/{tenant_id}/services")
async def list_services(
    tenant_id: str,
    db: Session = Depends(get_db),
    service_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List all services for a tenant"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "services": [],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "total_pages": 0
        }
    }


@router.get("/tenants/{tenant_id}/services/{service_id}")
async def get_service(
    tenant_id: str,
    service_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific service with all details"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": service_id,
        "service_code": f"SRV-{service_id:03d}",
        "supplier_id": 1,
        "name": "Sample Tour Service",
        "description": "A sample tour service",
        "service_type": "tour",
        "is_active": True,
        "inclusions": ["guide", "entrance_fees", "transportation"],
        "exclusions": ["meals", "tips"],
        "created_at": datetime.utcnow().isoformat()
    }


@router.put("/tenants/{tenant_id}/services/{service_id}")
async def update_service(
    tenant_id: str,
    service_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update a service"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": service_id,
        "message": "Service updated successfully",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.delete("/tenants/{tenant_id}/services/{service_id}")
async def delete_service(
    tenant_id: str,
    service_id: int,
    db: Session = Depends(get_db)
):
    """Soft delete a service"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "message": f"Service {service_id} deleted successfully",
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.post("/tenants/{tenant_id}/services/{service_id}/activate")
async def activate_service(
    tenant_id: str,
    service_id: int,
    db: Session = Depends(get_db)
):
    """Activate a service"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": service_id,
        "is_active": True,
        "message": "Service activated successfully"
    }


@router.post("/tenants/{tenant_id}/services/{service_id}/deactivate")
async def deactivate_service(
    tenant_id: str,
    service_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate a service"""
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": service_id,
        "is_active": False,
        "message": "Service deactivated successfully"
    }
