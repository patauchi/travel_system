"""
CRM Service - Leads Endpoints
API endpoints for lead management
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import Lead, Actor
from schemas_leads import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListFilter,
    LeadConvert, LeadBulkAction
)

router = APIRouter()


@router.post("/tenants/{tenant_id}/leads", response_model=LeadResponse)
async def create_lead(
    tenant_id: str,
    lead_data: LeadCreate,
    db: Session = Depends(get_db)
):
    """Create a new lead"""
    # Get tenant schema
    schema_name = get_schema_from_tenant_id(tenant_id, db)
    if not schema_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )

    # Placeholder for now
    return {
        "id": 1,
        "actor_id": 1,
        "lead_status": "new",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "actor": {
            "id": 1,
            "type": "lead",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    }


@router.get("/tenants/{tenant_id}/leads", response_model=Dict[str, Any])
async def list_leads(
    tenant_id: str,
    db: Session = Depends(get_db),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    # Filters
    status: Optional[str] = Query(None, description="Filter by lead status"),
    source: Optional[str] = Query(None, description="Filter by lead source"),
    rating: Optional[str] = Query(None, description="Filter by lead rating"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned user"),
    search: Optional[str] = Query(None, description="Search in name, email, company"),
    created_from: Optional[datetime] = Query(None, description="Created date from"),
    created_to: Optional[datetime] = Query(None, description="Created date to"),
    follow_up_from: Optional[date] = Query(None, description="Follow up date from"),
    follow_up_to: Optional[date] = Query(None, description="Follow up date to"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum lead score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum lead score"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List all leads for a tenant with advanced filtering"""
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
        query = tenant_db.query(Lead)

        # Apply filters
        if status:
            query = query.filter(Lead.status == status)

        if source:
            query = query.filter(Lead.source == source)

        if rating:
            query = query.filter(Lead.rating == rating)

        if assigned_to:
            query = query.filter(Lead.assigned_to == assigned_to)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Lead.first_name.ilike(search_term),
                    Lead.last_name.ilike(search_term),
                    Lead.email.ilike(search_term),
                    Lead.company.ilike(search_term),
                    Lead.phone.ilike(search_term)
                )
            )

        if created_from:
            query = query.filter(Lead.created_at >= created_from)

        if created_to:
            query = query.filter(Lead.created_at <= created_to)

        if follow_up_from:
            query = query.filter(Lead.follow_up_date >= follow_up_from)

        if follow_up_to:
            query = query.filter(Lead.follow_up_date <= follow_up_to)

        if min_score is not None:
            query = query.filter(Lead.score >= min_score)

        if max_score is not None:
            query = query.filter(Lead.score <= max_score)

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        if hasattr(Lead, sort_by):
            order_column = getattr(Lead, sort_by)
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(Lead.created_at.desc())

        # Apply pagination
        leads = query.offset(skip).limit(limit).all()

        # Format response
        results = [LeadResponse.from_orm(lead) for lead in leads]

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching leads: {str(e)}"
        )
    finally:
        tenant_db.close()
