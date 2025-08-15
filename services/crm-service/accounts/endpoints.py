"""
Accounts Endpoints for CRM Service
API endpoints for account management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from core.models import Actor
from core.enums import ActorType, AccountStatus
from .models import Account
from .schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountListFilter,
    AccountBulkAction
)

router = APIRouter()

# ============================================
# ACCOUNT CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/accounts", response_model=AccountResponse)
async def create_account(
    tenant_id: str,
    account_data: AccountCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new account with actor information"""
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
            "type": ActorType.account_business if account_data.account_type == "business" else ActorType.account_person,
            "first_name": account_data.first_name,
            "last_name": account_data.last_name,
            "company_name": account_data.company_name,
            "email": account_data.email,
            "phone": account_data.phone,
            "mobile": account_data.mobile,
            "title": account_data.title,
            "street": account_data.street,
            "city": account_data.city,
            "state": account_data.state,
            "postal_code": account_data.postal_code,
            "country": account_data.country,
            "website": account_data.website,
            "annual_revenue": account_data.annual_revenue,
            "number_of_employees": account_data.number_of_employees,
            "status": "active"
        }

        actor = Actor(**actor_data)
        tenant_db.add(actor)
        tenant_db.flush()

        # Create account
        account_dict = account_data.dict(exclude={
            'first_name', 'last_name', 'company_name', 'email',
            'phone', 'mobile', 'title', 'street', 'city',
            'state', 'postal_code', 'country', 'website',
            'annual_revenue', 'number_of_employees'
        })
        account_dict["actor_id"] = actor.id

        account = Account(**account_dict)
        tenant_db.add(account)
        tenant_db.commit()

        # Return response
        response_data = {
            **account_dict,
            "id": account.id,
            "actor_id": actor.id,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
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
            detail=f"Error creating account: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/accounts", response_model=List[AccountResponse])
async def list_accounts(
    tenant_id: str,
    account_status: Optional[List[AccountStatus]] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List accounts with filtering and pagination"""
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
        query = tenant_db.query(Account).join(Actor).filter(
            Account.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        )

        # Apply filters
        if account_status:
            query = query.filter(Account.account_status.in_(account_status))

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
            query = query.order_by(desc(getattr(Account, sort_by)))
        else:
            query = query.order_by(asc(getattr(Account, sort_by)))

        # Apply pagination
        offset = (page - 1) * page_size
        accounts = query.offset(offset).limit(page_size).all()

        # Build response
        response_data = []
        for account in accounts:
            account_data = {
                "id": account.id,
                "actor_id": account.actor_id,
                "account_type": account.account_type,
                "account_status": account.account_status,
                "parent_account_id": account.parent_account_id,
                "is_following": account.is_following,
                "tax_id": account.tax_id,
                "business_license": account.business_license,
                "credit_limit": account.credit_limit,
                "payment_terms": account.payment_terms,
                "payment_method": account.payment_method,
                "company_owner": account.company_owner,
                "employee_count": account.employee_count,
                "time_zone": account.time_zone,
                "bank_name": account.bank_name,
                "bank_account": account.bank_account,
                "swift_code": account.swift_code,
                "total_bookings": account.total_bookings,
                "lifetime_value": account.lifetime_value,
                "last_booking_date": account.last_booking_date,
                "first_booking_date": account.first_booking_date,
                "customer_segment": account.customer_segment,
                "loyalty_points": account.loyalty_points,
                "risk_level": account.risk_level,
                "industry_id": account.industry_id,
                "created_at": account.created_at,
                "updated_at": account.updated_at,
                "deleted_at": account.deleted_at,
                "actor_first_name": account.actor.first_name,
                "actor_last_name": account.actor.last_name,
                "actor_company_name": account.actor.company_name,
                "actor_email": account.actor.email,
                "actor_phone": account.actor.phone,
                "actor_mobile": account.actor.mobile
            }
            response_data.append(account_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving accounts: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    tenant_id: str,
    account_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific account by ID"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find account
        account = tenant_db.query(Account).join(Actor).filter(
            Account.id == account_id,
            Account.deleted_at.is_(None),
            Actor.deleted_at.is_(None)
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Build response
        account_data = {
            "id": account.id,
            "actor_id": account.actor_id,
            "account_type": account.account_type,
            "account_status": account.account_status,
            "parent_account_id": account.parent_account_id,
            "is_following": account.is_following,
            "tax_id": account.tax_id,
            "business_license": account.business_license,
            "credit_limit": account.credit_limit,
            "payment_terms": account.payment_terms,
            "payment_method": account.payment_method,
            "company_owner": account.company_owner,
            "employee_count": account.employee_count,
            "time_zone": account.time_zone,
            "bank_name": account.bank_name,
            "bank_account": account.bank_account,
            "swift_code": account.swift_code,
            "total_bookings": account.total_bookings,
            "lifetime_value": account.lifetime_value,
            "last_booking_date": account.last_booking_date,
            "first_booking_date": account.first_booking_date,
            "customer_segment": account.customer_segment,
            "loyalty_points": account.loyalty_points,
            "risk_level": account.risk_level,
            "industry_id": account.industry_id,
            "created_at": account.created_at,
            "updated_at": account.updated_at,
            "deleted_at": account.deleted_at,
            "actor_first_name": account.actor.first_name,
            "actor_last_name": account.actor.last_name,
            "actor_company_name": account.actor.company_name,
            "actor_email": account.actor.email,
            "actor_phone": account.actor.phone,
            "actor_mobile": account.actor.mobile
        }

        return account_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/accounts/{account_id}", response_model=AccountResponse)
async def update_account(
    tenant_id: str,
    account_id: int,
    account_data: AccountUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a specific account"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find account
        account = tenant_db.query(Account).filter(
            Account.id == account_id,
            Account.deleted_at.is_(None)
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Update account fields
        update_data = account_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        account.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated account
        return await get_account(tenant_id, account_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating account: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/accounts/{account_id}")
async def delete_account(
    tenant_id: str,
    account_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Soft delete a specific account"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find account
        account = tenant_db.query(Account).filter(
            Account.id == account_id,
            Account.deleted_at.is_(None)
        ).first()

        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Soft delete
        account.deleted_at = datetime.utcnow()
        account.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {"message": "Account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/accounts/stats")
async def get_account_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get account statistics"""
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
        total_accounts = tenant_db.query(Account).filter(Account.deleted_at.is_(None)).count()
        active_accounts = tenant_db.query(Account).filter(
            Account.account_status == AccountStatus.active,
            Account.deleted_at.is_(None)
        ).count()
        customer_accounts = tenant_db.query(Account).filter(
            Account.account_status == AccountStatus.customer,
            Account.deleted_at.is_(None)
        ).count()

        return {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "customer_accounts": customer_accounts,
            "prospect_accounts": total_accounts - customer_accounts,
            "conversion_rate": round((customer_accounts / total_accounts * 100) if total_accounts > 0 else 0, 2)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account statistics: {str(e)}"
        )
