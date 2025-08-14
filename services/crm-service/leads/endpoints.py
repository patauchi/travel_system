"""
Leads Endpoints for CRM Service
API endpoints for lead management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from core.models import Actor
from core.enums import ActorType, LeadStatus
from .models import Lead
from .schemas import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListFilter,
    LeadConvert, LeadBulkAction
)

router = APIRouter()

# ============================================
# LEAD CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/leads", response_model=LeadResponse)
async def create_lead(
    tenant_id: str,
    lead_data: LeadCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Create a new lead with actor information

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Create actor first
        actor_data = {
            "type": ActorType.LEAD,
            "first_name": lead_data.first_name,
            "last_name": lead_data.last_name,
            "company_name": lead_data.company_name,
            "email": lead_data.email,
            "phone": lead_data.phone,
            "mobile": lead_data.mobile,
            "title": lead_data.title,
            "street": lead_data.street,
            "city": lead_data.city,
            "state": lead_data.state,
            "postal_code": lead_data.postal_code,
            "country": lead_data.country,
            "status": "active"
        }

        actor = Actor(**actor_data)
        tenant_db.add(actor)
        tenant_db.flush()  # Get actor ID

        # Create lead
        lead_dict = lead_data.dict(exclude={
            'first_name', 'last_name', 'company_name', 'email',
            'phone', 'mobile', 'title', 'street', 'city',
            'state', 'postal_code', 'country'
        })
        lead_dict["actor_id"] = actor.id
        lead_dict["lead_owner_id"] = current_user["user_id"]

        lead = Lead(**lead_dict)
        tenant_db.add(lead)
        tenant_db.commit()

        # Return response with actor data
        response_data = {
            **lead_dict,
            "id": lead.id,
            "actor_id": actor.id,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
            "actor_first_name": actor.first_name,
            "actor_last_name": actor.last_name,
            "actor_company_name": actor.company_name,
            "actor_email": actor.email,
            "actor_phone": actor.phone,
            "actor_mobile": actor.mobile
        }

        return response_data

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lead: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/leads", response_model=List[LeadResponse])
async def list_leads(
    tenant_id: str,
    lead_status: Optional[List[LeadStatus]] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    List leads with filtering and pagination

    Requires authentication and tenant access
    """
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
        query = tenant_db.query(Lead).join(Actor).filter(
            Lead.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        )

        # Apply filters
        if lead_status:
            query = query.filter(Lead.lead_status.in_(lead_status))

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Actor.first_name.ilike(search_term),
                    Actor.last_name.ilike(search_term),
                    Actor.company_name.ilike(search_term),
                    Actor.email.ilike(search_term),
                    Actor.phone.ilike(search_term)
                )
            )

        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Lead, sort_by)))
        else:
            query = query.order_by(asc(getattr(Lead, sort_by)))

        # Apply pagination
        offset = (page - 1) * page_size
        leads = query.offset(offset).limit(page_size).all()

        # Build response
        response_data = []
        for lead in leads:
            lead_data = {
                "id": lead.id,
                "actor_id": lead.actor_id,
                "lead_source": lead.lead_source,
                "lead_status": lead.lead_status,
                "conversion_probability": lead.conversion_probability,
                "expected_close_date": lead.expected_close_date,
                "estimated_value": lead.estimated_value,
                "interest_level": lead.interest_level,
                "inquiry_type": lead.inquiry_type,
                "last_contacted_at": lead.last_contacted_at,
                "is_qualified": lead.is_qualified,
                "disqualification_reason": lead.disqualification_reason,
                "referral_source": lead.referral_source,
                "travel_interests": lead.travel_interests,
                "preferred_travel_date": lead.preferred_travel_date,
                "number_of_travelers": lead.number_of_travelers,
                "special_requirements": lead.special_requirements,
                "follow_up_date": lead.follow_up_date,
                "notes": lead.notes,
                "campaign_id": lead.campaign_id,
                "score": lead.score,
                "lead_owner_id": lead.lead_owner_id,
                "converted_date": lead.converted_date,
                "converted_contact_id": lead.converted_contact_id,
                "converted_account_id": lead.converted_account_id,
                "converted_opportunity_id": lead.converted_opportunity_id,
                "created_at": lead.created_at,
                "updated_at": lead.updated_at,
                "deleted_at": lead.deleted_at,
                "actor_first_name": lead.actor.first_name,
                "actor_last_name": lead.actor.last_name,
                "actor_company_name": lead.actor.company_name,
                "actor_email": lead.actor.email,
                "actor_phone": lead.actor.phone,
                "actor_mobile": lead.actor.mobile
            }
            response_data.append(lead_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving leads: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    tenant_id: str,
    lead_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get a specific lead by ID

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find lead
        lead = tenant_db.query(Lead).join(Actor).filter(
            Lead.id == lead_id,
            Lead.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        ).first()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Build response
        lead_data = {
            "id": lead.id,
            "actor_id": lead.actor_id,
            "lead_source": lead.lead_source,
            "lead_status": lead.lead_status,
            "conversion_probability": lead.conversion_probability,
            "expected_close_date": lead.expected_close_date,
            "estimated_value": lead.estimated_value,
            "interest_level": lead.interest_level,
            "inquiry_type": lead.inquiry_type,
            "last_contacted_at": lead.last_contacted_at,
            "is_qualified": lead.is_qualified,
            "disqualification_reason": lead.disqualification_reason,
            "referral_source": lead.referral_source,
            "travel_interests": lead.travel_interests,
            "preferred_travel_date": lead.preferred_travel_date,
            "number_of_travelers": lead.number_of_travelers,
            "special_requirements": lead.special_requirements,
            "follow_up_date": lead.follow_up_date,
            "notes": lead.notes,
            "campaign_id": lead.campaign_id,
            "score": lead.score,
            "lead_owner_id": lead.lead_owner_id,
            "converted_date": lead.converted_date,
            "converted_contact_id": lead.converted_contact_id,
            "converted_account_id": lead.converted_account_id,
            "converted_opportunity_id": lead.converted_opportunity_id,
            "created_at": lead.created_at,
            "updated_at": lead.updated_at,
            "deleted_at": lead.deleted_at,
            "actor_first_name": lead.actor.first_name,
            "actor_last_name": lead.actor.last_name,
            "actor_company_name": lead.actor.company_name,
            "actor_email": lead.actor.email,
            "actor_phone": lead.actor.phone,
            "actor_mobile": lead.actor.mobile
        }

        return lead_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lead: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    tenant_id: str,
    lead_id: int,
    lead_data: LeadUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Update a specific lead

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find lead
        lead = tenant_db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.deleted_at.is_(None)
        ).first()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Update lead fields
        update_data = lead_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lead, field, value)

        lead.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated lead
        return await get_lead(tenant_id, lead_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lead: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/leads/{lead_id}")
async def delete_lead(
    tenant_id: str,
    lead_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Soft delete a specific lead

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find lead
        lead = tenant_db.query(Lead).filter(
            Lead.id == lead_id,
            Lead.deleted_at.is_(None)
        ).first()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        # Soft delete
        lead.deleted_at = datetime.utcnow()
        lead.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {"message": "Lead deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting lead: {str(e)}"
        )

# ============================================
# LEAD CONVERSION
# ============================================

@router.post("/tenants/{tenant_id}/leads/{lead_id}/convert")
async def convert_lead(
    tenant_id: str,
    lead_id: int,
    convert_data: LeadConvert,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Convert a lead to contact/account/opportunity

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find lead
        lead = tenant_db.query(Lead).join(Actor).filter(
            Lead.id == lead_id,
            Lead.deleted_at.is_(None)
        ).first()

        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead not found"
            )

        if lead.lead_status == LeadStatus.CONVERTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead is already converted"
            )

        # Update lead status
        lead.lead_status = LeadStatus.CONVERTED
        lead.converted_date = datetime.utcnow()
        lead.updated_at = datetime.utcnow()

        conversion_result = {
            "lead_id": lead_id,
            "converted_at": lead.converted_date,
            "created_entities": []
        }

        # TODO: Implement actual contact/account/opportunity creation
        # This would require importing and using the respective modules

        if convert_data.create_contact:
            conversion_result["created_entities"].append("contact")

        if convert_data.create_account:
            conversion_result["created_entities"].append("account")

        if convert_data.create_opportunity:
            conversion_result["created_entities"].append("opportunity")

        tenant_db.commit()

        return conversion_result

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting lead: {str(e)}"
        )

# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/leads/bulk-action")
async def bulk_action_leads(
    tenant_id: str,
    bulk_action: LeadBulkAction,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Perform bulk actions on multiple leads

    Requires authentication and tenant access
    """
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find leads
        leads = tenant_db.query(Lead).filter(
            Lead.id.in_(bulk_action.lead_ids),
            Lead.deleted_at.is_(None)
        ).all()

        if not leads:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No leads found with provided IDs"
            )

        updated_count = 0

        for lead in leads:
            if bulk_action.action == "assign" and bulk_action.lead_owner_id:
                lead.lead_owner_id = bulk_action.lead_owner_id
                updated_count += 1
            elif bulk_action.action == "update_status" and bulk_action.lead_status:
                lead.lead_status = bulk_action.lead_status
                updated_count += 1
            elif bulk_action.action == "score" and bulk_action.score_adjustment is not None:
                new_score = max(0, min(100, lead.score + bulk_action.score_adjustment))
                lead.score = new_score
                updated_count += 1
            elif bulk_action.action == "delete":
                lead.deleted_at = datetime.utcnow()
                updated_count += 1

            lead.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "message": f"Bulk action '{bulk_action.action}' completed",
            "updated_count": updated_count,
            "total_requested": len(bulk_action.lead_ids)
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing bulk action: {str(e)}"
        )

# ============================================
# STATISTICS
# ============================================

@router.get("/tenants/{tenant_id}/leads/stats")
async def get_lead_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get lead statistics

    Requires authentication and tenant access
    """
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
        total_leads = tenant_db.query(Lead).filter(Lead.deleted_at.is_(None)).count()
        new_leads = tenant_db.query(Lead).filter(
            Lead.lead_status == LeadStatus.NEW,
            Lead.deleted_at.is_(None)
        ).count()
        qualified_leads = tenant_db.query(Lead).filter(
            Lead.is_qualified == True,
            Lead.deleted_at.is_(None)
        ).count()
        converted_leads = tenant_db.query(Lead).filter(
            Lead.lead_status == LeadStatus.CONVERTED,
            Lead.deleted_at.is_(None)
        ).count()

        # Calculate conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0

        return {
            "total_leads": total_leads,
            "new_leads": new_leads,
            "qualified_leads": qualified_leads,
            "converted_leads": converted_leads,
            "conversion_rate": round(conversion_rate, 2),
            "qualification_rate": round((qualified_leads / total_leads * 100) if total_leads > 0 else 0, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving lead statistics: {str(e)}"
        )
