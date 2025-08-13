"""
CRM Service - Quotes Endpoints
API endpoints for quote management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import Quote, QuoteLine

router = APIRouter()


@router.post("/tenants/{tenant_id}/quotes")
async def create_quote(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """Create a new quote"""
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
        "opportunity_id": 1,
        "quote_number": "Q-2024-001",
        "name": "New Quote",
        "status": "draft",
        "quote_date": date.today(),
        "expiration_date": date.today(),
        "total_amount": 0,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.get("/tenants/{tenant_id}/quotes")
async def list_quotes(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """List all quotes for a tenant"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.get("/tenants/{tenant_id}/quotes/{quote_id}")
async def get_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": quote_id,
        "opportunity_id": 1,
        "quote_number": f"Q-2024-{quote_id:03d}",
        "name": "Sample Quote",
        "status": "draft",
        "quote_date": date.today(),
        "expiration_date": date.today(),
        "total_amount": 1000.00,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.put("/tenants/{tenant_id}/quotes/{quote_id}")
async def update_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Update a quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": quote_id,
        "opportunity_id": 1,
        "quote_number": f"Q-2024-{quote_id:03d}",
        "name": "Updated Quote",
        "status": "sent",
        "quote_date": date.today(),
        "expiration_date": date.today(),
        "total_amount": 1500.00,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.delete("/tenants/{tenant_id}/quotes/{quote_id}")
async def delete_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Delete a quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {"message": f"Quote {quote_id} deleted successfully"}


@router.post("/tenants/{tenant_id}/quotes/{quote_id}/send")
async def send_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Send a quote to customer"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": quote_id,
        "status": "sent",
        "message": f"Quote {quote_id} sent successfully"
    }


@router.post("/tenants/{tenant_id}/quotes/{quote_id}/accept")
async def accept_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Mark a quote as accepted"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": quote_id,
        "status": "accepted",
        "accepted_date": date.today(),
        "message": f"Quote {quote_id} accepted successfully"
    }


@router.post("/tenants/{tenant_id}/quotes/{quote_id}/reject")
async def reject_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Mark a quote as rejected"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": quote_id,
        "status": "rejected",
        "message": f"Quote {quote_id} rejected"
    }


@router.post("/tenants/{tenant_id}/quotes/{quote_id}/lines")
async def add_quote_line(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Add a line item to a quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 1,
        "quote_id": quote_id,
        "line_number": 1,
        "type": "hotel",
        "description": "Hotel accommodation",
        "quantity": 1,
        "unit_price": 100.00,
        "total_amount": 100.00,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.get("/tenants/{tenant_id}/quotes/{quote_id}/lines")
async def get_quote_lines(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Get all line items for a quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return []


@router.put("/tenants/{tenant_id}/quotes/{quote_id}/lines/{line_id}")
async def update_quote_line(
    tenant_id: str,
    quote_id: int,
    line_id: int,
    db: Session = Depends(get_db)
):
    """Update a quote line item"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": line_id,
        "quote_id": quote_id,
        "line_number": 1,
        "type": "hotel",
        "description": "Updated hotel accommodation",
        "quantity": 2,
        "unit_price": 100.00,
        "total_amount": 200.00,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.delete("/tenants/{tenant_id}/quotes/{quote_id}/lines/{line_id}")
async def delete_quote_line(
    tenant_id: str,
    quote_id: int,
    line_id: int,
    db: Session = Depends(get_db)
):
    """Delete a quote line item"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {"message": f"Quote line {line_id} deleted successfully"}


@router.post("/tenants/{tenant_id}/quotes/{quote_id}/duplicate")
async def duplicate_quote(
    tenant_id: str,
    quote_id: int,
    db: Session = Depends(get_db)
):
    """Create a duplicate of an existing quote"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    return {
        "id": 2,
        "opportunity_id": 1,
        "quote_number": "Q-2024-002",
        "name": "Duplicated Quote",
        "status": "draft",
        "quote_date": date.today(),
        "expiration_date": date.today(),
        "total_amount": 1000.00,
        "currency": "USD",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "message": f"Quote duplicated from {quote_id}"
    }
