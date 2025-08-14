"""
Industries Endpoints for CRM Service
API endpoints for industry management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from .models import Industry
from .schemas import (
    IndustryCreate, IndustryUpdate, IndustryResponse,
    IndustryListFilter, IndustryBulkAction, IndustryHierarchy
)

router = APIRouter()

# ============================================
# INDUSTRY CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/industries", response_model=IndustryResponse)
async def create_industry(
    tenant_id: str,
    industry_data: IndustryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new industry"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Check if parent exists (if provided)
        if industry_data.parent_id:
            parent = tenant_db.query(Industry).filter(
                Industry.id == industry_data.parent_id,
                Industry.is_active == True
            ).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent industry not found or inactive"
                )

        # Check for duplicate name or code
        existing = tenant_db.query(Industry).filter(
            or_(
                Industry.name == industry_data.name,
                and_(Industry.code == industry_data.code, industry_data.code.is_not(None))
            )
        ).first()

        if existing:
            if existing.name == industry_data.name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Industry with this name already exists"
                )
            if existing.code == industry_data.code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Industry with this code already exists"
                )

        # Create industry
        industry_dict = industry_data.dict()
        industry = Industry(**industry_dict)
        tenant_db.add(industry)
        tenant_db.commit()

        # Get parent name for response
        parent_name = None
        if industry.parent_id:
            parent = tenant_db.query(Industry).filter(Industry.id == industry.parent_id).first()
            parent_name = parent.name if parent else None

        # Build response
        response_data = {
            "id": industry.id,
            "name": industry.name,
            "code": industry.code,
            "description": industry.description,
            "parent_id": industry.parent_id,
            "is_active": industry.is_active,
            "parent_name": parent_name,
            "children_count": 0,
            "accounts_count": 0,
            "level": 1 if industry.parent_id else 0,
            "created_at": industry.created_at,
            "updated_at": industry.updated_at
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating industry: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/industries", response_model=List[IndustryResponse])
async def list_industries(
    tenant_id: str,
    parent_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List industries with filtering and pagination"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Build query
        query = tenant_db.query(Industry)

        # Apply filters
        if parent_id is not None:
            query = query.filter(Industry.parent_id == parent_id)

        if is_active is not None:
            query = query.filter(Industry.is_active == is_active)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Industry.name.ilike(search_term),
                    Industry.code.ilike(search_term),
                    Industry.description.ilike(search_term)
                )
            )

        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Industry, sort_by)))
        else:
            query = query.order_by(asc(getattr(Industry, sort_by)))

        # Apply pagination
        offset = (page - 1) * page_size
        industries = query.offset(offset).limit(page_size).all()

        # Build response with additional data
        response_data = []
        for industry in industries:
            # Get children count
            children_count = tenant_db.query(Industry).filter(
                Industry.parent_id == industry.id
            ).count()

            # Get accounts count (would need Account model imported)
            accounts_count = 0  # Placeholder

            # Get parent name
            parent_name = None
            if industry.parent_id:
                parent = tenant_db.query(Industry).filter(Industry.id == industry.parent_id).first()
                parent_name = parent.name if parent else None

            industry_data = {
                "id": industry.id,
                "name": industry.name,
                "code": industry.code,
                "description": industry.description,
                "parent_id": industry.parent_id,
                "is_active": industry.is_active,
                "parent_name": parent_name,
                "children_count": children_count,
                "accounts_count": accounts_count,
                "level": 1 if industry.parent_id else 0,
                "created_at": industry.created_at,
                "updated_at": industry.updated_at
            }
            response_data.append(industry_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving industries: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/industries/{industry_id}", response_model=IndustryResponse)
async def get_industry(
    tenant_id: str,
    industry_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific industry by ID"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find industry
        industry = tenant_db.query(Industry).filter(Industry.id == industry_id).first()

        if not industry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Industry not found"
            )

        # Get additional data
        children_count = tenant_db.query(Industry).filter(
            Industry.parent_id == industry.id
        ).count()

        accounts_count = 0  # Placeholder

        parent_name = None
        if industry.parent_id:
            parent = tenant_db.query(Industry).filter(Industry.id == industry.parent_id).first()
            parent_name = parent.name if parent else None

        # Build response
        industry_data = {
            "id": industry.id,
            "name": industry.name,
            "code": industry.code,
            "description": industry.description,
            "parent_id": industry.parent_id,
            "is_active": industry.is_active,
            "parent_name": parent_name,
            "children_count": children_count,
            "accounts_count": accounts_count,
            "level": 1 if industry.parent_id else 0,
            "created_at": industry.created_at,
            "updated_at": industry.updated_at
        }

        return industry_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving industry: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/industries/{industry_id}", response_model=IndustryResponse)
async def update_industry(
    tenant_id: str,
    industry_id: int,
    industry_data: IndustryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a specific industry"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find industry
        industry = tenant_db.query(Industry).filter(Industry.id == industry_id).first()

        if not industry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Industry not found"
            )

        # Check for circular reference if parent_id is being changed
        if industry_data.parent_id is not None and industry_data.parent_id != industry.parent_id:
            if industry_data.parent_id == industry_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Industry cannot be its own parent"
                )

            # Check if new parent exists
            if industry_data.parent_id:
                parent = tenant_db.query(Industry).filter(
                    Industry.id == industry_data.parent_id,
                    Industry.is_active == True
                ).first()
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Parent industry not found or inactive"
                    )

        # Check for duplicate name or code (excluding current record)
        update_data = industry_data.dict(exclude_unset=True)
        if 'name' in update_data or 'code' in update_data:
            conditions = []
            if 'name' in update_data:
                conditions.append(Industry.name == update_data['name'])
            if 'code' in update_data and update_data['code']:
                conditions.append(Industry.code == update_data['code'])

            if conditions:
                existing = tenant_db.query(Industry).filter(
                    or_(*conditions),
                    Industry.id != industry_id
                ).first()

                if existing:
                    if existing.name == update_data.get('name'):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Industry with this name already exists"
                        )
                    if existing.code == update_data.get('code'):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Industry with this code already exists"
                        )

        # Update industry fields
        for field, value in update_data.items():
            setattr(industry, field, value)

        industry.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated industry
        return await get_industry(tenant_id, industry_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating industry: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/industries/{industry_id}")
async def delete_industry(
    tenant_id: str,
    industry_id: int,
    force: bool = Query(False, description="Force delete even if industry has children or accounts"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a specific industry"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find industry
        industry = tenant_db.query(Industry).filter(Industry.id == industry_id).first()

        if not industry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Industry not found"
            )

        # Check for children
        children_count = tenant_db.query(Industry).filter(
            Industry.parent_id == industry_id
        ).count()

        if children_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Industry has {children_count} child industries. Use force=true to delete anyway."
            )

        # Check for associated accounts (placeholder)
        accounts_count = 0  # Would check Account model
        if accounts_count > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Industry has {accounts_count} associated accounts. Use force=true to delete anyway."
            )

        # If force delete, handle children
        if force and children_count > 0:
            # Move children to parent's level or make them root
            children = tenant_db.query(Industry).filter(Industry.parent_id == industry_id).all()
            for child in children:
                child.parent_id = industry.parent_id
                child.updated_at = datetime.utcnow()

        # Delete industry
        tenant_db.delete(industry)
        tenant_db.commit()

        return {
            "message": "Industry deleted successfully",
            "children_moved": children_count if force else 0
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting industry: {str(e)}"
        )

# ============================================
# HIERARCHY OPERATIONS
# ============================================

@router.get("/tenants/{tenant_id}/industries/hierarchy")
async def get_industry_hierarchy(
    tenant_id: str,
    root_only: bool = Query(False, description="Return only root industries"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum hierarchy depth to return"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get industry hierarchy tree"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        def build_hierarchy(parent_id: Optional[int] = None, current_depth: int = 0) -> List[dict]:
            if current_depth >= max_depth:
                return []

            industries = tenant_db.query(Industry).filter(
                Industry.parent_id == parent_id,
                Industry.is_active == True
            ).order_by(Industry.name).all()

            result = []
            for industry in industries:
                children_count = tenant_db.query(Industry).filter(
                    Industry.parent_id == industry.id
                ).count()

                accounts_count = 0  # Placeholder

                industry_data = {
                    "id": industry.id,
                    "name": industry.name,
                    "code": industry.code,
                    "parent_id": industry.parent_id,
                    "level": current_depth,
                    "accounts_count": accounts_count,
                    "children_count": children_count,
                    "is_active": industry.is_active,
                    "children": [] if root_only else build_hierarchy(industry.id, current_depth + 1)
                }
                result.append(industry_data)

            return result

        hierarchy = build_hierarchy()

        return {
            "root_industries": hierarchy,
            "total_levels": max_depth,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving industry hierarchy: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/industries/stats")
async def get_industry_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get industry statistics"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Basic counts
        total_industries = tenant_db.query(Industry).count()
        active_industries = tenant_db.query(Industry).filter(Industry.is_active == True).count()
        inactive_industries = total_industries - active_industries
        root_industries = tenant_db.query(Industry).filter(Industry.parent_id.is_(None)).count()

        # Industries with accounts
        industries_with_accounts = 0  # Placeholder

        return {
            "total_industries": total_industries,
            "active_industries": active_industries,
            "inactive_industries": inactive_industries,
            "root_industries": root_industries,
            "industries_with_accounts": industries_with_accounts,
            "total_accounts": 0  # Placeholder
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving industry statistics: {str(e)}"
        )

# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/industries/bulk-action")
async def bulk_action_industries(
    tenant_id: str,
    bulk_action: IndustryBulkAction,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple industries"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find industries
        industries = tenant_db.query(Industry).filter(
            Industry.id.in_(bulk_action.industry_ids)
        ).all()

        if not industries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No industries found with provided IDs"
            )

        updated_count = 0

        for industry in industries:
            if bulk_action.action == "activate":
                industry.is_active = True
                updated_count += 1
            elif bulk_action.action == "deactivate":
                industry.is_active = False
                updated_count += 1
            elif bulk_action.action == "move_to_parent" and bulk_action.new_parent_id is not None:
                # Validate parent exists and prevent circular reference
                if bulk_action.new_parent_id != industry.id:
                    industry.parent_id = bulk_action.new_parent_id
                    updated_count += 1
            elif bulk_action.action == "delete":
                # Check for children before deleting
                children_count = tenant_db.query(Industry).filter(
                    Industry.parent_id == industry.id
                ).count()
                if children_count == 0:
                    tenant_db.delete(industry)
                    updated_count += 1

            if bulk_action.action != "delete":
                industry.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "message": f"Bulk action '{bulk_action.action}' completed",
            "updated_count": updated_count,
            "total_requested": len(bulk_action.industry_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bulk action: {str(e)}"
        )
