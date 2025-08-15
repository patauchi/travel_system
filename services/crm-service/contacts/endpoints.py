"""
Contacts Endpoints for CRM Service
API endpoints for contact management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from core.models import Actor
from core.enums import ActorType, ContactStatus
from .models import Contact
from .schemas import (
    ContactCreate, ContactUpdate, ContactResponse, ContactListFilter,
    ContactBulkAction
)

router = APIRouter()

# ============================================
# CONTACT CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/contacts", response_model=ContactResponse)
async def create_contact(
    tenant_id: str,
    contact_data: ContactCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Create a new contact with actor information

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
            "type": ActorType.contact,
            "first_name": contact_data.first_name,
            "last_name": contact_data.last_name,
            "company_name": contact_data.company_name,
            "email": contact_data.email,
            "phone": contact_data.phone,
            "mobile": contact_data.mobile,
            "title": contact_data.title,
            "street": contact_data.street,
            "city": contact_data.city,
            "state": contact_data.state,
            "postal_code": contact_data.postal_code,
            "country": contact_data.country,
            "status": "active"
        }

        actor = Actor(**actor_data)
        tenant_db.add(actor)
        tenant_db.flush()  # Get actor ID

        # Create contact
        contact_dict = contact_data.dict(exclude={
            'first_name', 'last_name', 'company_name', 'email',
            'phone', 'mobile', 'title', 'street', 'city',
            'state', 'postal_code', 'country'
        })
        contact_dict["actor_id"] = actor.id

        contact = Contact(**contact_dict)
        tenant_db.add(contact)
        tenant_db.commit()

        # Return response with actor data
        response_data = {
            **contact_dict,
            "id": contact.id,
            "actor_id": actor.id,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "actor_first_name": actor.first_name,
            "actor_last_name": actor.last_name,
            "actor_company_name": actor.company_name,
            "actor_email": actor.email,
            "actor_phone": actor.phone,
            "actor_mobile": actor.mobile,
            "actor_title": actor.title
        }

        return response_data

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating contact: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/contacts", response_model=List[ContactResponse])
async def list_contacts(
    tenant_id: str,
    contact_status: Optional[List[ContactStatus]] = Query(None),
    account_id: Optional[int] = Query(None),
    is_primary_contact: Optional[bool] = Query(None),
    department: Optional[str] = Query(None),
    passport_expiring_days: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    List contacts with filtering and pagination

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
        query = tenant_db.query(Contact).join(Actor).filter(
            Contact.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        )

        # Apply filters
        if contact_status:
            query = query.filter(Contact.contact_status.in_(contact_status))

        if account_id:
            query = query.filter(Contact.account_id == account_id)

        if is_primary_contact is not None:
            query = query.filter(Contact.is_primary_contact == is_primary_contact)

        if department:
            query = query.filter(Contact.department.ilike(f"%{department}%"))

        if passport_expiring_days is not None:
            expiry_date = date.today() + timedelta(days=passport_expiring_days)
            query = query.filter(
                Contact.passport_expiry.is_not(None),
                Contact.passport_expiry <= expiry_date
            )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Actor.first_name.ilike(search_term),
                    Actor.last_name.ilike(search_term),
                    Actor.company_name.ilike(search_term),
                    Actor.email.ilike(search_term),
                    Actor.phone.ilike(search_term),
                    Contact.department.ilike(search_term)
                )
            )

        # Apply sorting
        if sort_by in ['first_name', 'last_name', 'company_name']:
            sort_field = getattr(Actor, sort_by)
        else:
            sort_field = getattr(Contact, sort_by)

        if sort_order == "desc":
            query = query.order_by(desc(sort_field))
        else:
            query = query.order_by(asc(sort_field))

        # Apply pagination
        offset = (page - 1) * page_size
        contacts = query.offset(offset).limit(page_size).all()

        # Build response
        response_data = []
        for contact in contacts:
            # Get manager name if reports_to is set
            manager_name = None
            if contact.reports_to:
                manager_contact = tenant_db.query(Contact).join(Actor).filter(
                    Contact.id == contact.reports_to
                ).first()
                if manager_contact:
                    manager_name = f"{manager_contact.actor.first_name} {manager_contact.actor.last_name}".strip()

            contact_data = {
                "id": contact.id,
                "actor_id": contact.actor_id,
                "account_id": contact.account_id,
                "passenger_id": contact.passenger_id,
                "contact_status": contact.contact_status,
                "is_primary_contact": contact.is_primary_contact,
                "department": contact.department,
                "reports_to": contact.reports_to,
                "passport_number": contact.passport_number,
                "passport_expiry": contact.passport_expiry,
                "visa_requirements": contact.visa_requirements,
                "dietary_restrictions": contact.dietary_restrictions,
                "accessibility_needs": contact.accessibility_needs,
                "date_of_birth": contact.date_of_birth,
                "gender": contact.gender,
                "email_opt_in": contact.email_opt_in,
                "sms_opt_in": contact.sms_opt_in,
                "preferred_communication": contact.preferred_communication,
                "created_at": contact.created_at,
                "updated_at": contact.updated_at,
                "deleted_at": contact.deleted_at,
                "actor_first_name": contact.actor.first_name,
                "actor_last_name": contact.actor.last_name,
                "actor_company_name": contact.actor.company_name,
                "actor_email": contact.actor.email,
                "actor_phone": contact.actor.phone,
                "actor_mobile": contact.actor.mobile,
                "actor_title": contact.actor.title,
                "manager_name": manager_name
            }
            response_data.append(contact_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contacts: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(
    tenant_id: str,
    contact_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get a specific contact by ID

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

        # Find contact
        contact = tenant_db.query(Contact).join(Actor).filter(
            Contact.id == contact_id,
            Contact.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        ).first()

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )

        # Get manager name if reports_to is set
        manager_name = None
        if contact.reports_to:
            manager_contact = tenant_db.query(Contact).join(Actor).filter(
                Contact.id == contact.reports_to
            ).first()
            if manager_contact:
                manager_name = f"{manager_contact.actor.first_name} {manager_contact.actor.last_name}".strip()

        # Build response
        contact_data = {
            "id": contact.id,
            "actor_id": contact.actor_id,
            "account_id": contact.account_id,
            "passenger_id": contact.passenger_id,
            "contact_status": contact.contact_status,
            "is_primary_contact": contact.is_primary_contact,
            "department": contact.department,
            "reports_to": contact.reports_to,
            "passport_number": contact.passport_number,
            "passport_expiry": contact.passport_expiry,
            "visa_requirements": contact.visa_requirements,
            "dietary_restrictions": contact.dietary_restrictions,
            "accessibility_needs": contact.accessibility_needs,
            "date_of_birth": contact.date_of_birth,
            "gender": contact.gender,
            "email_opt_in": contact.email_opt_in,
            "sms_opt_in": contact.sms_opt_in,
            "preferred_communication": contact.preferred_communication,
            "created_at": contact.created_at,
            "updated_at": contact.updated_at,
            "deleted_at": contact.deleted_at,
            "actor_first_name": contact.actor.first_name,
            "actor_last_name": contact.actor.last_name,
            "actor_company_name": contact.actor.company_name,
            "actor_email": contact.actor.email,
            "actor_phone": contact.actor.phone,
            "actor_mobile": contact.actor.mobile,
            "actor_title": contact.actor.title,
            "manager_name": manager_name
        }

        return contact_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contact: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    tenant_id: str,
    contact_id: int,
    contact_data: ContactUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Update a specific contact

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

        # Find contact
        contact = tenant_db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.deleted_at.is_(None)
        ).first()

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )

        # Update contact fields
        update_data = contact_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        contact.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated contact
        return await get_contact(tenant_id, contact_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating contact: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/contacts/{contact_id}")
async def delete_contact(
    tenant_id: str,
    contact_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Soft delete a specific contact

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

        # Find contact
        contact = tenant_db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.deleted_at.is_(None)
        ).first()

        if not contact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contact not found"
            )

        # Soft delete
        contact.deleted_at = datetime.utcnow()
        contact.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {"message": "Contact deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting contact: {str(e)}"
        )

# ============================================
# BULK OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/contacts/bulk-action")
async def bulk_action_contacts(
    tenant_id: str,
    bulk_action: ContactBulkAction,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Perform bulk actions on multiple contacts

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

        # Find contacts
        contacts = tenant_db.query(Contact).filter(
            Contact.id.in_(bulk_action.contact_ids),
            Contact.deleted_at.is_(None)
        ).all()

        if not contacts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No contacts found with provided IDs"
            )

        updated_count = 0

        for contact in contacts:
            if bulk_action.action == "update_status" and bulk_action.contact_status:
                contact.contact_status = bulk_action.contact_status
                updated_count += 1
            elif bulk_action.action == "assign_account" and bulk_action.account_id is not None:
                contact.account_id = bulk_action.account_id
                updated_count += 1
            elif bulk_action.action == "update_communication_prefs":
                if bulk_action.email_opt_in is not None:
                    contact.email_opt_in = bulk_action.email_opt_in
                if bulk_action.sms_opt_in is not None:
                    contact.sms_opt_in = bulk_action.sms_opt_in
                if bulk_action.preferred_communication:
                    contact.preferred_communication = bulk_action.preferred_communication
                updated_count += 1
            elif bulk_action.action == "delete":
                contact.deleted_at = datetime.utcnow()
                updated_count += 1

            contact.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "message": f"Bulk action '{bulk_action.action}' completed",
            "updated_count": updated_count,
            "total_requested": len(bulk_action.contact_ids)
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
# STATISTICS & REPORTING
# ============================================

@router.get("/tenants/{tenant_id}/contacts/stats")
async def get_contact_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get contact statistics

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
        total_contacts = tenant_db.query(Contact).filter(Contact.deleted_at.is_(None)).count()
        active_contacts = tenant_db.query(Contact).filter(
            Contact.contact_status == ContactStatus.active,
            Contact.deleted_at.is_(None)
        ).count()
        primary_contacts = tenant_db.query(Contact).filter(
            Contact.is_primary_contact == True,
            Contact.deleted_at.is_(None)
        ).count()

        # Communication preferences
        email_opt_in = tenant_db.query(Contact).filter(
            Contact.email_opt_in == True,
            Contact.deleted_at.is_(None)
        ).count()
        sms_opt_in = tenant_db.query(Contact).filter(
            Contact.sms_opt_in == True,
            Contact.deleted_at.is_(None)
        ).count()

        # Passport expiring soon (next 90 days)
        expiry_date = date.today() + timedelta(days=90)
        passports_expiring = tenant_db.query(Contact).filter(
            Contact.passport_expiry.is_not(None),
            Contact.passport_expiry <= expiry_date,
            Contact.deleted_at.is_(None)
        ).count()

        return {
            "total_contacts": total_contacts,
            "active_contacts": active_contacts,
            "primary_contacts": primary_contacts,
            "email_opt_in": email_opt_in,
            "sms_opt_in": sms_opt_in,
            "passports_expiring_90_days": passports_expiring,
            "email_opt_in_rate": round((email_opt_in / total_contacts * 100) if total_contacts > 0 else 0, 2),
            "sms_opt_in_rate": round((sms_opt_in / total_contacts * 100) if total_contacts > 0 else 0, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contact statistics: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/contacts/passport-expiring")
async def get_contacts_with_expiring_passports(
    tenant_id: str,
    days: int = Query(90, ge=1, le=365),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get contacts with passports expiring in specified days

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

        expiry_date = date.today() + timedelta(days=days)

        contacts = tenant_db.query(Contact).join(Actor).filter(
            Contact.passport_expiry.is_not(None),
            Contact.passport_expiry <= expiry_date,
            Contact.deleted_at.is_(None)
        ).order_by(Contact.passport_expiry).all()

        response_data = []
        for contact in contacts:
            days_until_expiry = (contact.passport_expiry - date.today()).days
            contact_data = {
                "id": contact.id,
                "actor_first_name": contact.actor.first_name,
                "actor_last_name": contact.actor.last_name,
                "actor_email": contact.actor.email,
                "passport_number": contact.passport_number,
                "passport_expiry": contact.passport_expiry,
                "days_until_expiry": days_until_expiry,
                "status": "expired" if days_until_expiry < 0 else "expiring_soon"
            }
            response_data.append(contact_data)

        return {
            "contacts_with_expiring_passports": response_data,
            "total_count": len(response_data),
            "search_criteria": f"passports expiring within {days} days"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving contacts with expiring passports: {str(e)}"
        )
