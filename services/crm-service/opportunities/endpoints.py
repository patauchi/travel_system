"""
Opportunities Endpoints for CRM Service
API endpoints for opportunity management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from core.enums import OpportunityStage
from .models import Opportunity
from .schemas import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    OpportunityListFilter, OpportunityBulkAction, OpportunityConvert
)

router = APIRouter()

# ============================================
# OPPORTUNITY CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/opportunities", response_model=OpportunityResponse)
async def create_opportunity(
    tenant_id: str,
    opportunity_data: OpportunityCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new opportunity"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Create opportunity
        opportunity_dict = opportunity_data.dict()
        opportunity_dict["owner_id"] = current_user["user_id"]

        opportunity = Opportunity(**opportunity_dict)
        tenant_db.add(opportunity)
        tenant_db.commit()

        # Return response
        response_data = {
            **opportunity_dict,
            "id": opportunity.id,
            "created_at": opportunity.created_at,
            "updated_at": opportunity.updated_at,
            "is_closed": opportunity.is_closed,
            "actual_close_date": opportunity.actual_close_date,
            "close_reason": opportunity.close_reason,
            "loss_reason": opportunity.loss_reason
        }

        return response_data

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating opportunity: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/opportunities", response_model=List[OpportunityResponse])
async def list_opportunities(
    tenant_id: str,
    stage: Optional[List[OpportunityStage]] = Query(None),
    owner_id: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List opportunities with filtering and pagination"""
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
        query = tenant_db.query(Opportunity).filter(
            Opportunity.deleted_at.is_(None)
        )

        # Apply filters
        if stage:
            query = query.filter(Opportunity.stage.in_(stage))

        if owner_id:
            query = query.filter(Opportunity.owner_id == owner_id)

        if account_id:
            query = query.filter(Opportunity.account_id == account_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(Opportunity.name.ilike(search_term))

        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Opportunity, sort_by)))
        else:
            query = query.order_by(asc(getattr(Opportunity, sort_by)))

        # Apply pagination
        offset = (page - 1) * page_size
        opportunities = query.offset(offset).limit(page_size).all()

        # Build response
        response_data = []
        for opp in opportunities:
            opp_data = {
                "id": opp.id,
                "name": opp.name,
                "stage": opp.stage,
                "probability": opp.probability,
                "amount": opp.amount,
                "expected_close_date": opp.expected_close_date,
                "actual_close_date": opp.actual_close_date,
                "travel_type": opp.travel_type,
                "destinations": opp.destinations,
                "departure_date": opp.departure_date,
                "return_date": opp.return_date,
                "number_of_adults": opp.number_of_adults,
                "number_of_children": opp.number_of_children,
                "room_configuration": opp.room_configuration,
                "budget_level": opp.budget_level,
                "special_requests": opp.special_requests,
                "competitors": opp.competitors,
                "next_steps": opp.next_steps,
                "account_id": opp.account_id,
                "contact_id": opp.contact_id,
                "owner_id": opp.owner_id,
                "campaign_id": opp.campaign_id,
                "is_closed": opp.is_closed,
                "close_reason": opp.close_reason,
                "loss_reason": opp.loss_reason,
                "created_at": opp.created_at,
                "updated_at": opp.updated_at,
                "deleted_at": opp.deleted_at
            }
            response_data.append(opp_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving opportunities: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    tenant_id: str,
    opportunity_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific opportunity by ID"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find opportunity
        opportunity = tenant_db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.deleted_at.is_(None)
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found"
            )

        # Build response
        opp_data = {
            "id": opportunity.id,
            "name": opportunity.name,
            "stage": opportunity.stage,
            "probability": opportunity.probability,
            "amount": opportunity.amount,
            "expected_close_date": opportunity.expected_close_date,
            "actual_close_date": opportunity.actual_close_date,
            "travel_type": opportunity.travel_type,
            "destinations": opportunity.destinations,
            "departure_date": opportunity.departure_date,
            "return_date": opportunity.return_date,
            "number_of_adults": opportunity.number_of_adults,
            "number_of_children": opportunity.number_of_children,
            "room_configuration": opportunity.room_configuration,
            "budget_level": opportunity.budget_level,
            "special_requests": opportunity.special_requests,
            "competitors": opportunity.competitors,
            "next_steps": opportunity.next_steps,
            "account_id": opportunity.account_id,
            "contact_id": opportunity.contact_id,
            "owner_id": opportunity.owner_id,
            "campaign_id": opportunity.campaign_id,
            "is_closed": opportunity.is_closed,
            "close_reason": opportunity.close_reason,
            "loss_reason": opportunity.loss_reason,
            "created_at": opportunity.created_at,
            "updated_at": opportunity.updated_at,
            "deleted_at": opportunity.deleted_at
        }

        return opp_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving opportunity: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    tenant_id: str,
    opportunity_id: int,
    opportunity_data: OpportunityUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a specific opportunity"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find opportunity
        opportunity = tenant_db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.deleted_at.is_(None)
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found"
            )

        # Update opportunity fields
        update_data = opportunity_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(opportunity, field, value)

        opportunity.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated opportunity
        return await get_opportunity(tenant_id, opportunity_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating opportunity: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/opportunities/{opportunity_id}")
async def delete_opportunity(
    tenant_id: str,
    opportunity_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Soft delete a specific opportunity"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find opportunity
        opportunity = tenant_db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.deleted_at.is_(None)
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found"
            )

        # Soft delete
        opportunity.deleted_at = datetime.utcnow()
        opportunity.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {"message": "Opportunity deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting opportunity: {str(e)}"
        )

# ============================================
# OPPORTUNITY CONVERSION
# ============================================

@router.post("/tenants/{tenant_id}/opportunities/{opportunity_id}/convert")
async def convert_opportunity(
    tenant_id: str,
    opportunity_id: int,
    convert_data: OpportunityConvert,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Convert an opportunity to won/lost"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find opportunity
        opportunity = tenant_db.query(Opportunity).filter(
            Opportunity.id == opportunity_id,
            Opportunity.deleted_at.is_(None)
        ).first()

        if not opportunity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Opportunity not found"
            )

        if opportunity.is_closed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opportunity is already closed"
            )

        # Update opportunity
        if convert_data.close_as_won:
            opportunity.stage = OpportunityStage.closed_won
            opportunity.probability = 100
        else:
            opportunity.stage = OpportunityStage.closed_lost
            opportunity.probability = 0

        opportunity.is_closed = True
        opportunity.actual_close_date = convert_data.actual_close_date or date.today()
        opportunity.close_reason = convert_data.close_reason

        if convert_data.final_amount is not None:
            opportunity.amount = convert_data.final_amount

        opportunity.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {
            "opportunity_id": opportunity_id,
            "status": "won" if convert_data.close_as_won else "lost",
            "closed_date": opportunity.actual_close_date,
            "final_amount": opportunity.amount,
            "message": f"Opportunity {('won' if convert_data.close_as_won else 'lost')} successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting opportunity: {str(e)}"
        )

# ============================================
# STATISTICS
# ============================================

@router.get("/tenants/{tenant_id}/opportunities/stats")
async def get_opportunity_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get opportunity statistics"""
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
        total_opportunities = tenant_db.query(Opportunity).filter(
            Opportunity.deleted_at.is_(None)
        ).count()

        open_opportunities = tenant_db.query(Opportunity).filter(
            Opportunity.is_closed == False,
            Opportunity.deleted_at.is_(None)
        ).count()

        closed_won = tenant_db.query(Opportunity).filter(
            Opportunity.stage == OpportunityStage.closed_won,
            Opportunity.deleted_at.is_(None)
        ).count()

        closed_lost = tenant_db.query(Opportunity).filter(
            Opportunity.stage == OpportunityStage.closed_lost,
            Opportunity.deleted_at.is_(None)
        ).count()

        # Calculate pipeline value
        pipeline_value = tenant_db.query(func.sum(Opportunity.amount)).filter(
            Opportunity.is_closed == False,
            Opportunity.deleted_at.is_(None),
            Opportunity.amount.is_not(None)
        ).scalar() or 0

        # Calculate win rate
        total_closed = closed_won + closed_lost
        win_rate = (closed_won / total_closed * 100) if total_closed > 0 else 0

        return {
            "total_opportunities": total_opportunities,
            "open_opportunities": open_opportunities,
            "closed_won": closed_won,
            "closed_lost": closed_lost,
            "total_pipeline_value": float(pipeline_value),
            "win_rate": round(win_rate, 2),
            "average_deal_size": round(float(pipeline_value) / open_opportunities, 2) if open_opportunities > 0 else 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving opportunity statistics: {str(e)}"
        )

# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/opportunities/bulk-action")
async def bulk_action_opportunities(
    tenant_id: str,
    bulk_action: OpportunityBulkAction,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Perform bulk actions on multiple opportunities"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find opportunities
        opportunities = tenant_db.query(Opportunity).filter(
            Opportunity.id.in_(bulk_action.opportunity_ids),
            Opportunity.deleted_at.is_(None)
        ).all()

        if not opportunities:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No opportunities found with provided IDs"
            )

        updated_count = 0

        for opportunity in opportunities:
            if bulk_action.action == "update_stage" and bulk_action.stage:
                opportunity.stage = bulk_action.stage
                updated_count += 1
            elif bulk_action.action == "assign_owner" and bulk_action.owner_id:
                opportunity.owner_id = bulk_action.owner_id
                updated_count += 1
            elif bulk_action.action == "update_probability" and bulk_action.probability is not None:
                opportunity.probability = bulk_action.probability
                updated_count += 1
            elif bulk_action.action == "close_won":
                opportunity.stage = OpportunityStage.closed_won
                opportunity.is_closed = True
                opportunity.probability = 100
                opportunity.actual_close_date = date.today()
                if bulk_action.close_reason:
                    opportunity.close_reason = bulk_action.close_reason
                updated_count += 1
            elif bulk_action.action == "close_lost":
                opportunity.stage = OpportunityStage.closed_lost
                opportunity.is_closed = True
                opportunity.probability = 0
                opportunity.actual_close_date = date.today()
                if bulk_action.loss_reason:
                    opportunity.loss_reason = bulk_action.loss_reason
                updated_count += 1
            elif bulk_action.action == "delete":
                opportunity.deleted_at = datetime.utcnow()
                updated_count += 1

            opportunity.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "message": f"Bulk action '{bulk_action.action}' completed",
            "updated_count": updated_count,
            "total_requested": len(bulk_action.opportunity_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bulk action: {str(e)}"
        )
