"""
Quotes Endpoints for CRM Service
API endpoints for quote management with authentication
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user_from_token, check_tenant_access
from core.enums import QuoteStatus
from .models import Quote, QuoteLine
from .schemas import (
    QuoteCreate, QuoteUpdate, QuoteResponse,
    QuoteLineCreate, QuoteLineUpdate, QuoteLineResponse,
    QuoteListFilter, QuoteBulkAction, QuoteAccept
)

router = APIRouter()

# ============================================
# QUOTE CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/quotes", response_model=QuoteResponse)
async def create_quote(
    tenant_id: str,
    quote_data: QuoteCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new quote"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Auto-generate quote number if not provided
        quote_dict = quote_data.dict()
        if not quote_dict.get("quote_number"):
            # Simple quote number generation
            count = tenant_db.query(Quote).filter(Quote.deleted_at.is_(None)).count()
            quote_dict["quote_number"] = f"Q-{count + 1:06d}"

        quote = Quote(**quote_dict)
        tenant_db.add(quote)
        tenant_db.commit()

        # Return response
        response_data = {
            **quote_dict,
            "id": quote.id,
            "created_at": quote.created_at,
            "updated_at": quote.updated_at,
            "accepted_date": quote.accepted_date,
            "subtotal": quote.subtotal,
            "tax_amount": quote.tax_amount,
            "discount_amount": quote.discount_amount,
            "total_amount": quote.total_amount
        }

        return response_data

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/quotes", response_model=List[QuoteResponse])
async def list_quotes(
    tenant_id: str,
    status: Optional[List[QuoteStatus]] = Query(None),
    opportunity_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List quotes with filtering and pagination"""
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
        query = tenant_db.query(Quote).filter(
            Quote.deleted_at.is_(None)
        )

        # Apply filters
        if status:
            query = query.filter(Quote.status.in_(status))

        if opportunity_id:
            query = query.filter(Quote.opportunity_id == opportunity_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Quote.name.ilike(search_term),
                    Quote.quote_number.ilike(search_term)
                )
            )

        # Apply sorting
        if sort_order == "desc":
            query = query.order_by(desc(getattr(Quote, sort_by)))
        else:
            query = query.order_by(asc(getattr(Quote, sort_by)))

        # Apply pagination
        offset = (page - 1) * page_size
        quotes = query.offset(offset).limit(page_size).all()

        # Build response
        response_data = []
        for quote in quotes:
            quote_data = {
                "id": quote.id,
                "opportunity_id": quote.opportunity_id,
                "quote_number": quote.quote_number,
                "name": quote.name,
                "status": quote.status,
                "is_primary": quote.is_primary,
                "quote_date": quote.quote_date,
                "expiration_date": quote.expiration_date,
                "accepted_date": quote.accepted_date,
                "subtotal": quote.subtotal,
                "tax_amount": quote.tax_amount,
                "discount_amount": quote.discount_amount,
                "total_amount": quote.total_amount,
                "currency": quote.currency,
                "payment_terms": quote.payment_terms,
                "special_instructions": quote.special_instructions,
                "internal_notes": quote.internal_notes,
                "created_at": quote.created_at,
                "updated_at": quote.updated_at,
                "deleted_at": quote.deleted_at
            }
            response_data.append(quote_data)

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quotes: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    tenant_id: str,
    quote_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific quote by ID"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find quote
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Build response
        quote_data = {
            "id": quote.id,
            "opportunity_id": quote.opportunity_id,
            "quote_number": quote.quote_number,
            "name": quote.name,
            "status": quote.status,
            "is_primary": quote.is_primary,
            "quote_date": quote.quote_date,
            "expiration_date": quote.expiration_date,
            "accepted_date": quote.accepted_date,
            "subtotal": quote.subtotal,
            "tax_amount": quote.tax_amount,
            "discount_amount": quote.discount_amount,
            "total_amount": quote.total_amount,
            "currency": quote.currency,
            "payment_terms": quote.payment_terms,
            "special_instructions": quote.special_instructions,
            "internal_notes": quote.internal_notes,
            "created_at": quote.created_at,
            "updated_at": quote.updated_at,
            "deleted_at": quote.deleted_at
        }

        return quote_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quote: {str(e)}"
        )

@router.put("/tenants/{tenant_id}/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    tenant_id: str,
    quote_id: int,
    quote_data: QuoteUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a specific quote"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find quote
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Update quote fields
        update_data = quote_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(quote, field, value)

        quote.updated_at = datetime.utcnow()
        tenant_db.commit()

        # Return updated quote
        return await get_quote(tenant_id, quote_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating quote: {str(e)}"
        )

@router.delete("/tenants/{tenant_id}/quotes/{quote_id}")
async def delete_quote(
    tenant_id: str,
    quote_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Soft delete a specific quote"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find quote
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Soft delete
        quote.deleted_at = datetime.utcnow()
        quote.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {"message": "Quote deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting quote: {str(e)}"
        )

# ============================================
# QUOTE LINE OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/quotes/{quote_id}/lines", response_model=QuoteLineResponse)
async def create_quote_line(
    tenant_id: str,
    quote_id: int,
    line_data: QuoteLineCreate,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new quote line"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Verify quote exists
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Create quote line
        line_dict = line_data.dict()
        line_dict["quote_id"] = quote_id

        # Calculate amounts
        discount_amount = (line_dict["unit_price"] * line_dict["quantity"]) * (line_dict.get("discount_percent", 0) / 100)
        subtotal = (line_dict["unit_price"] * line_dict["quantity"]) - discount_amount
        tax_amount = subtotal * (line_dict.get("tax_rate", 0) / 100)
        total_amount = subtotal + tax_amount

        line_dict.update({
            "discount_amount": discount_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount
        })

        quote_line = QuoteLine(**line_dict)
        tenant_db.add(quote_line)
        tenant_db.commit()

        return quote_line

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating quote line: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/quotes/{quote_id}/lines", response_model=List[QuoteLineResponse])
async def list_quote_lines(
    tenant_id: str,
    quote_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """List quote lines for a specific quote"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Verify quote exists
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        # Get quote lines
        quote_lines = tenant_db.query(QuoteLine).filter(
            QuoteLine.quote_id == quote_id
        ).order_by(QuoteLine.line_number).all()

        return quote_lines

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quote lines: {str(e)}"
        )

# ============================================
# QUOTE ACTIONS
# ============================================

@router.post("/tenants/{tenant_id}/quotes/{quote_id}/accept")
async def accept_quote(
    tenant_id: str,
    quote_id: int,
    accept_data: QuoteAccept,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Accept a quote"""
    try:
        # Check tenant access
        if not check_tenant_access(current_user, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied for this tenant"
            )

        # Get tenant database session
        tenant_db = get_tenant_db(tenant_id, db)

        # Find quote
        quote = tenant_db.query(Quote).filter(
            Quote.id == quote_id,
            Quote.deleted_at.is_(None)
        ).first()

        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quote not found"
            )

        if quote.status == QuoteStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quote is already accepted"
            )

        # Update quote
        quote.status = QuoteStatus.ACCEPTED
        quote.accepted_date = accept_data.accepted_date or date.today()
        quote.updated_at = datetime.utcnow()
        tenant_db.commit()

        return {
            "quote_id": quote_id,
            "status": "accepted",
            "accepted_date": quote.accepted_date,
            "message": "Quote accepted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting quote: {str(e)}"
        )

@router.get("/tenants/{tenant_id}/quotes/stats")
async def get_quote_stats(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get quote statistics"""
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
        total_quotes = tenant_db.query(Quote).filter(Quote.deleted_at.is_(None)).count()

        accepted_quotes = tenant_db.query(Quote).filter(
            Quote.status == QuoteStatus.ACCEPTED,
            Quote.deleted_at.is_(None)
        ).count()

        # Calculate total value
        total_value = tenant_db.query(func.sum(Quote.total_amount)).filter(
            Quote.deleted_at.is_(None),
            Quote.total_amount.is_not(None)
        ).scalar() or 0

        # Calculate acceptance rate
        acceptance_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0

        return {
            "total_quotes": total_quotes,
            "accepted_quotes": accepted_quotes,
            "total_value": float(total_value),
            "acceptance_rate": round(acceptance_rate, 2),
            "average_quote_value": round(float(total_value) / total_quotes, 2) if total_quotes > 0 else 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving quote statistics: {str(e)}"
        )
