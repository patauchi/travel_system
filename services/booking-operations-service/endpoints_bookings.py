"""
Booking Operations Service - Bookings Endpoints
API endpoints for booking management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from models import (
    Booking, BookingLine, BookingPassenger,
    BookingOverallStatus, BookingLineStatus
)

router = APIRouter()


# ============================================
# BOOKING CRUD OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/bookings")
async def create_booking(
    tenant_id: str,
    booking_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Create a new booking from an order

    Args:
        tenant_id: UUID of the tenant
        booking_data: Booking information
        db: Database session

    Returns:
        Created booking information
    """
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
        # Create new booking
        booking = Booking(
            order_id=booking_data.get("order_id"),
            booking_number=booking_data.get("booking_number", f"BK-{datetime.now().year}-{datetime.now().strftime('%m%d%H%M%S')}"),
            overall_status=BookingOverallStatus.PENDING,
            total_services=booking_data.get("total_services", 0),
            total_passengers=booking_data.get("total_passengers", 0),
            adults_count=booking_data.get("adults_count", 0),
            children_count=booking_data.get("children_count", 0),
            infants_count=booking_data.get("infants_count", 0),
            travel_start_date=booking_data.get("travel_start_date"),
            travel_end_date=booking_data.get("travel_end_date"),
            special_requirements=booking_data.get("special_requirements"),
            total_amount=booking_data.get("total_amount", 0),
            currency=booking_data.get("currency", "USD"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(booking)
        tenant_db.commit()
        tenant_db.refresh(booking)

        return {
            "id": booking.id,
            "booking_number": booking.booking_number,
            "order_id": booking.order_id,
            "overall_status": booking.overall_status,
            "travel_start_date": booking.travel_start_date,
            "travel_end_date": booking.travel_end_date,
            "total_passengers": booking.total_passengers,
            "total_amount": float(booking.total_amount),
            "currency": booking.currency,
            "created_at": booking.created_at.isoformat()
        }

    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/bookings")
async def list_bookings(
    tenant_id: str,
    db: Session = Depends(get_db),
    # Pagination
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    # Filters
    status: Optional[BookingOverallStatus] = Query(None, description="Filter by booking status"),
    booking_number: Optional[str] = Query(None, description="Filter by booking number"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    customer_name: Optional[str] = Query(None, description="Search by customer name"),
    travel_date_from: Optional[date] = Query(None, description="Travel start date from"),
    travel_date_to: Optional[date] = Query(None, description="Travel start date to"),
    created_from: Optional[datetime] = Query(None, description="Created date from"),
    created_to: Optional[datetime] = Query(None, description="Created date to"),
    min_amount: Optional[float] = Query(None, description="Minimum total amount"),
    max_amount: Optional[float] = Query(None, description="Maximum total amount"),
    # Sorting
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List bookings with advanced filtering, pagination and sorting

    Args:
        tenant_id: UUID of the tenant
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        Various filter parameters

    Returns:
        List of bookings matching the criteria
    """
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
        query = tenant_db.query(Booking)

        # Apply filters
        if status:
            query = query.filter(Booking.overall_status == status)

        if booking_number:
            query = query.filter(Booking.booking_number.ilike(f"%{booking_number}%"))

        if order_id:
            query = query.filter(Booking.order_id == order_id)

        if customer_name:
            query = query.filter(
                or_(
                    Booking.primary_contact_name.ilike(f"%{customer_name}%"),
                    Booking.booking_number.ilike(f"%{customer_name}%")
                )
            )

        if travel_date_from:
            query = query.filter(Booking.travel_start_date >= travel_date_from)

        if travel_date_to:
            query = query.filter(Booking.travel_start_date <= travel_date_to)

        if created_from:
            query = query.filter(Booking.created_at >= created_from)

        if created_to:
            query = query.filter(Booking.created_at <= created_to)

        if min_amount is not None:
            query = query.filter(Booking.total_amount >= min_amount)

        if max_amount is not None:
            query = query.filter(Booking.total_amount <= max_amount)

        # Get total count before pagination
        total_count = query.count()

        # Apply sorting
        if hasattr(Booking, sort_by):
            order_column = getattr(Booking, sort_by)
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(Booking.created_at.desc())

        # Apply pagination
        bookings = query.offset(skip).limit(limit).all()

        # Format response
        results = []
        for booking in bookings:
            results.append({
                "id": booking.id,
                "booking_number": booking.booking_number,
                "order_id": booking.order_id,
                "overall_status": booking.overall_status.value if booking.overall_status else None,
                "travel_start_date": booking.travel_start_date.isoformat() if booking.travel_start_date else None,
                "travel_end_date": booking.travel_end_date.isoformat() if booking.travel_end_date else None,
                "total_passengers": booking.total_passengers,
                "adults_count": booking.adults_count,
                "children_count": booking.children_count,
                "infants_count": booking.infants_count,
                "total_services": booking.total_services,
                "confirmed_services": booking.confirmed_services,
                "pending_services": booking.pending_services,
                "total_amount": float(booking.total_amount) if booking.total_amount else 0,
                "currency": booking.currency,
                "primary_contact_name": booking.primary_contact_name,
                "created_at": booking.created_at.isoformat() if booking.created_at else None,
                "updated_at": booking.updated_at.isoformat() if booking.updated_at else None
            })

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "data": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching bookings: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/bookings/{booking_id}")
async def get_booking(
    tenant_id: str,
    booking_id: int = Path(..., description="Booking ID"),
    db: Session = Depends(get_db),
    include_lines: bool = Query(True, description="Include booking lines"),
    include_passengers: bool = Query(True, description="Include passenger details")
):
    """
    Get detailed information about a specific booking

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking
        include_lines: Whether to include booking lines
        include_passengers: Whether to include passenger information

    Returns:
        Detailed booking information
    """
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
        # Fetch booking
        booking = tenant_db.query(Booking).filter(Booking.id == booking_id).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Build response
        response = {
            "id": booking.id,
            "booking_number": booking.booking_number,
            "order_id": booking.order_id,
            "overall_status": booking.overall_status.value if booking.overall_status else None,
            "travel_start_date": booking.travel_start_date.isoformat() if booking.travel_start_date else None,
            "travel_end_date": booking.travel_end_date.isoformat() if booking.travel_end_date else None,
            "total_passengers": booking.total_passengers,
            "adults_count": booking.adults_count,
            "children_count": booking.children_count,
            "infants_count": booking.infants_count,
            "total_services": booking.total_services,
            "confirmed_services": booking.confirmed_services,
            "pending_services": booking.pending_services,
            "cancelled_services": booking.cancelled_services,
            "total_amount": float(booking.total_amount) if booking.total_amount else 0,
            "paid_amount": float(booking.paid_amount) if booking.paid_amount else 0,
            "pending_amount": float(booking.pending_amount) if booking.pending_amount else 0,
            "currency": booking.currency,
            "primary_contact_name": booking.primary_contact_name,
            "primary_contact_email": booking.primary_contact_email,
            "primary_contact_phone": booking.primary_contact_phone,
            "special_requirements": booking.special_requirements,
            "internal_notes": booking.internal_notes,
            "customer_notes": booking.customer_notes,
            "created_at": booking.created_at.isoformat() if booking.created_at else None,
            "updated_at": booking.updated_at.isoformat() if booking.updated_at else None,
            "created_by": str(booking.created_by) if booking.created_by else None,
            "updated_by": str(booking.updated_by) if booking.updated_by else None
        }

        # Include booking lines if requested
        if include_lines:
            booking_lines = tenant_db.query(BookingLine).filter(
                BookingLine.booking_id == booking_id
            ).all()

            response["booking_lines"] = [
                {
                    "id": line.id,
                    "order_line_id": line.order_line_id,
                    "booking_status": line.booking_status.value if line.booking_status else None,
                    "supplier_reference": line.supplier_reference,
                    "booking_method": line.booking_method,
                    "booked_at": line.booked_at.isoformat() if line.booked_at else None,
                    "confirmed_at": line.confirmed_at.isoformat() if line.confirmed_at else None,
                    "cancelled_at": line.cancelled_at.isoformat() if line.cancelled_at else None,
                    "risk_level": line.risk_level.value if line.risk_level else None
                }
                for line in booking_lines
            ]

        # Include passengers if requested
        if include_passengers:
            booking_passengers = tenant_db.query(BookingPassenger).filter(
                BookingPassenger.booking_id == booking_id
            ).all()

            response["passengers"] = [
                {
                    "id": bp.id,
                    "passenger_id": bp.passenger_id,
                    "is_lead_passenger": bp.is_lead_passenger,
                    "passenger_type": bp.passenger_type.value if bp.passenger_type else None,
                    "special_requirements": bp.special_requirements
                }
                for bp in booking_passengers
            ]

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching booking: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.put("/tenants/{tenant_id}/bookings/{booking_id}")
async def update_booking(
    tenant_id: str,
    booking_id: int = Path(..., description="Booking ID"),
    booking_update: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """
    Update booking information

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking to update
        booking_update: Fields to update

    Returns:
        Updated booking information
    """
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
        # Fetch booking
        booking = tenant_db.query(Booking).filter(Booking.id == booking_id).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Update allowed fields
        allowed_fields = [
            "overall_status", "special_requirements", "internal_notes",
            "customer_notes", "primary_contact_name", "primary_contact_email",
            "primary_contact_phone", "travel_start_date", "travel_end_date"
        ]

        for field, value in booking_update.items():
            if field in allowed_fields and hasattr(booking, field):
                # Handle enum fields
                if field == "overall_status" and value:
                    value = BookingOverallStatus(value)
                # Handle date fields
                elif field in ["travel_start_date", "travel_end_date"] and value:
                    value = datetime.fromisoformat(value) if isinstance(value, str) else value

                setattr(booking, field, value)

        booking.updated_at = datetime.utcnow()

        tenant_db.commit()
        tenant_db.refresh(booking)

        return {
            "id": booking.id,
            "booking_number": booking.booking_number,
            "overall_status": booking.overall_status.value if booking.overall_status else None,
            "message": "Booking updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.delete("/tenants/{tenant_id}/bookings/{booking_id}")
async def delete_booking(
    tenant_id: str,
    booking_id: int = Path(..., description="Booking ID"),
    db: Session = Depends(get_db),
    soft_delete: bool = Query(True, description="Soft delete instead of hard delete")
):
    """
    Delete or cancel a booking

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking to delete
        soft_delete: If true, marks as cancelled instead of deleting

    Returns:
        Confirmation message
    """
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
        # Fetch booking
        booking = tenant_db.query(Booking).filter(Booking.id == booking_id).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        if soft_delete:
            # Soft delete - mark as cancelled
            booking.overall_status = BookingOverallStatus.CANCELLED
            booking.updated_at = datetime.utcnow()
            tenant_db.commit()

            return {
                "message": f"Booking {booking_id} has been cancelled",
                "booking_number": booking.booking_number,
                "status": "cancelled"
            }
        else:
            # Hard delete
            tenant_db.delete(booking)
            tenant_db.commit()

            return {
                "message": f"Booking {booking_id} has been deleted",
                "booking_number": booking.booking_number,
                "status": "deleted"
            }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting booking: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/bookings/search")
async def search_bookings(
    tenant_id: str,
    q: str = Query(..., min_length=2, description="Search query"),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Maximum results to return")
):
    """
    Search bookings by multiple fields

    Args:
        tenant_id: UUID of the tenant
        q: Search query string
        limit: Maximum number of results

    Returns:
        List of bookings matching the search criteria
    """
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
        # Build search query
        search_term = f"%{q}%"

        bookings = tenant_db.query(Booking).filter(
            or_(
                Booking.booking_number.ilike(search_term),
                Booking.primary_contact_name.ilike(search_term),
                Booking.primary_contact_email.ilike(search_term),
                Booking.primary_contact_phone.ilike(search_term),
                Booking.special_requirements.ilike(search_term),
                Booking.customer_notes.ilike(search_term)
            )
        ).limit(limit).all()

        # Format results
        results = []
        for booking in bookings:
            results.append({
                "id": booking.id,
                "booking_number": booking.booking_number,
                "primary_contact_name": booking.primary_contact_name,
                "travel_start_date": booking.travel_start_date.isoformat() if booking.travel_start_date else None,
                "overall_status": booking.overall_status.value if booking.overall_status else None,
                "total_amount": float(booking.total_amount) if booking.total_amount else 0
            })

        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching bookings: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/bookings/statistics")
async def get_booking_statistics(
    tenant_id: str,
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None, description="Statistics from date"),
    date_to: Optional[date] = Query(None, description="Statistics to date")
):
    """
    Get booking statistics and analytics

    Args:
        tenant_id: UUID of the tenant
        date_from: Start date for statistics
        date_to: End date for statistics

    Returns:
        Booking statistics and metrics
    """
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
        # Base query
        query = tenant_db.query(Booking)

        # Apply date filters
        if date_from:
            query = query.filter(Booking.created_at >= date_from)
        if date_to:
            query = query.filter(Booking.created_at <= date_to)

        # Get statistics
        total_bookings = query.count()

        # Status breakdown
        status_counts = {}
        for status in BookingOverallStatus:
            count = query.filter(Booking.overall_status == status).count()
            status_counts[status.value] = count

        # Financial statistics
        total_revenue = tenant_db.query(func.sum(Booking.total_amount)).scalar() or 0
        total_paid = tenant_db.query(func.sum(Booking.paid_amount)).scalar() or 0
        total_pending = tenant_db.query(func.sum(Booking.pending_amount)).scalar() or 0

        # Passenger statistics
        total_passengers = tenant_db.query(func.sum(Booking.total_passengers)).scalar() or 0
        total_adults = tenant_db.query(func.sum(Booking.adults_count)).scalar() or 0
        total_children = tenant_db.query(func.sum(Booking.children_count)).scalar() or 0
        total_infants = tenant_db.query(func.sum(Booking.infants_count)).scalar() or 0

        # Service statistics
        total_services = tenant_db.query(func.sum(Booking.total_services)).scalar() or 0
        confirmed_services = tenant_db.query(func.sum(Booking.confirmed_services)).scalar() or 0
        pending_services = tenant_db.query(func.sum(Booking.pending_services)).scalar() or 0

        return {
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "totals": {
                "bookings": total_bookings,
                "passengers": int(total_passengers),
                "services": int(total_services)
            },
            "status_breakdown": status_counts,
            "financial": {
                "total_revenue": float(total_revenue),
                "total_paid": float(total_paid),
                "total_pending": float(total_pending)
            },
            "passengers": {
                "total": int(total_passengers),
                "adults": int(total_adults),
                "children": int(total_children),
                "infants": int(total_infants)
            },
            "services": {
                "total": int(total_services),
                "confirmed": int(confirmed_services),
                "pending": int(pending_services)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching statistics: {str(e)}"
        )
    finally:
        tenant_db.close()
async def list_bookings(
    tenant_id: str,
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    date_from: Optional[date] = Query(None, description="Filter bookings from this date"),
    date_to: Optional[date] = Query(None, description="Filter bookings until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List bookings for a tenant with optional filters

    Args:
        tenant_id: UUID of the tenant
        db: Database session
        status_filter: Optional status filter
        date_from: Optional start date filter
        date_to: Optional end date filter
        page: Page number for pagination
        page_size: Number of items per page

    Returns:
        List of bookings with pagination info
    """
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
        query = tenant_db.query(Booking).filter(Booking.deleted_at.is_(None))

        # Apply filters
        if status_filter:
            query = query.filter(Booking.overall_status == status_filter)

        if date_from:
            query = query.filter(Booking.travel_start_date >= date_from)

        if date_to:
            query = query.filter(Booking.travel_start_date <= date_to)

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        bookings = query.order_by(Booking.created_at.desc()).offset(offset).limit(page_size).all()

        # Format response
        booking_list = []
        for booking in bookings:
            booking_list.append({
                "id": booking.id,
                "booking_number": booking.booking_number,
                "order_id": booking.order_id,
                "overall_status": booking.overall_status,
                "travel_start_date": booking.travel_start_date.isoformat() if booking.travel_start_date else None,
                "travel_end_date": booking.travel_end_date.isoformat() if booking.travel_end_date else None,
                "total_services": booking.total_services,
                "confirmed_services": booking.confirmed_services,
                "total_passengers": booking.total_passengers,
                "total_amount": float(booking.total_amount),
                "currency": booking.currency,
                "created_at": booking.created_at.isoformat()
            })

        return {
            "bookings": booking_list,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing bookings: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/bookings/{booking_id}")
async def get_booking(
    tenant_id: str,
    booking_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific booking

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking
        db: Database session

    Returns:
        Detailed booking information
    """
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
        # Get booking with related data
        booking = tenant_db.query(Booking).filter(
            and_(
                Booking.id == booking_id,
                Booking.deleted_at.is_(None)
            )
        ).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Get booking lines
        booking_lines = []
        for line in booking.booking_lines:
            booking_lines.append({
                "id": line.id,
                "order_line_id": line.order_line_id,
                "booking_status": line.booking_status,
                "supplier_confirmation_code": line.supplier_confirmation_code,
                "service_confirmed_start": line.service_confirmed_start.isoformat() if line.service_confirmed_start else None,
                "service_confirmed_end": line.service_confirmed_end.isoformat() if line.service_confirmed_end else None,
                "risk_level": line.risk_level
            })

        # Get passengers
        passengers = []
        for bp in booking.booking_passengers:
            passengers.append({
                "passenger_id": bp.passenger_id,
                "is_lead_passenger": bp.is_lead_passenger,
                "passenger_type": bp.passenger_type,
                "documents_received": bp.documents_received,
                "documents_verified": bp.documents_verified,
                "checked_in": bp.checked_in
            })

        return {
            "id": booking.id,
            "booking_number": booking.booking_number,
            "order_id": booking.order_id,
            "overall_status": booking.overall_status,
            "travel_start_date": booking.travel_start_date.isoformat() if booking.travel_start_date else None,
            "travel_end_date": booking.travel_end_date.isoformat() if booking.travel_end_date else None,
            "total_services": booking.total_services,
            "confirmed_services": booking.confirmed_services,
            "cancelled_services": booking.cancelled_services,
            "pending_services": booking.pending_services,
            "total_passengers": booking.total_passengers,
            "adults_count": booking.adults_count,
            "children_count": booking.children_count,
            "infants_count": booking.infants_count,
            "documents_complete": booking.documents_complete,
            "special_requirements": booking.special_requirements,
            "total_amount": float(booking.total_amount),
            "total_paid": float(booking.total_paid),
            "currency": booking.currency,
            "booking_lines": booking_lines,
            "passengers": passengers,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting booking: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.put("/tenants/{tenant_id}/bookings/{booking_id}")
async def update_booking(
    tenant_id: str,
    booking_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Update a booking

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking
        update_data: Fields to update
        db: Database session

    Returns:
        Updated booking information
    """
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
        # Get booking
        booking = tenant_db.query(Booking).filter(
            and_(
                Booking.id == booking_id,
                Booking.deleted_at.is_(None)
            )
        ).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Update allowed fields
        allowed_fields = [
            "overall_status", "special_requirements", "dietary_restrictions",
            "emergency_contacts", "documents_complete", "metadata"
        ]

        for field, value in update_data.items():
            if field in allowed_fields and hasattr(booking, field):
                setattr(booking, field, value)

        booking.updated_at = datetime.utcnow()

        tenant_db.commit()
        tenant_db.refresh(booking)

        return {
            "id": booking.id,
            "booking_number": booking.booking_number,
            "overall_status": booking.overall_status,
            "updated_at": booking.updated_at.isoformat(),
            "message": "Booking updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# BOOKING LINE OPERATIONS
# ============================================

@router.post("/tenants/{tenant_id}/bookings/{booking_id}/lines")
async def create_booking_line(
    tenant_id: str,
    booking_id: int,
    line_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Create a new booking line for a booking

    Args:
        tenant_id: UUID of the tenant
        booking_id: ID of the booking
        line_data: Booking line information
        db: Database session

    Returns:
        Created booking line information
    """
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
        # Verify booking exists
        booking = tenant_db.query(Booking).filter(
            and_(
                Booking.id == booking_id,
                Booking.deleted_at.is_(None)
            )
        ).first()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {booking_id} not found"
            )

        # Create booking line
        booking_line = BookingLine(
            booking_id=booking_id,
            order_line_id=line_data.get("order_line_id"),
            booking_status=BookingLineStatus.PENDING,
            booking_method=line_data.get("booking_method"),
            booking_requested_at=datetime.utcnow(),
            risk_level=line_data.get("risk_level", "low"),
            booking_notes=line_data.get("booking_notes"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        tenant_db.add(booking_line)

        # Update booking service count
        booking.total_services += 1
        booking.pending_services += 1
        booking.updated_at = datetime.utcnow()

        tenant_db.commit()
        tenant_db.refresh(booking_line)

        return {
            "id": booking_line.id,
            "booking_id": booking_line.booking_id,
            "order_line_id": booking_line.order_line_id,
            "booking_status": booking_line.booking_status,
            "created_at": booking_line.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking line: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.put("/tenants/{tenant_id}/booking-lines/{line_id}/confirm")
async def confirm_booking_line(
    tenant_id: str,
    line_id: int,
    confirmation_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Confirm a booking line with supplier

    Args:
        tenant_id: UUID of the tenant
        line_id: ID of the booking line
        confirmation_data: Confirmation details
        db: Database session

    Returns:
        Updated booking line information
    """
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
        # Get booking line with booking
        booking_line = tenant_db.query(BookingLine).filter(
            and_(
                BookingLine.id == line_id,
                BookingLine.deleted_at.is_(None)
            )
        ).first()

        if not booking_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking line {line_id} not found"
            )

        # Update confirmation details
        booking_line.booking_status = BookingLineStatus.CONFIRMED
        booking_line.supplier_confirmation_code = confirmation_data.get("supplier_confirmation_code")
        booking_line.supplier_booking_reference = confirmation_data.get("supplier_booking_reference")
        booking_line.confirmed_at = datetime.utcnow()
        booking_line.confirmed_with = confirmation_data.get("confirmed_with")
        booking_line.supplier_response = confirmation_data.get("supplier_response")
        booking_line.voucher_number = confirmation_data.get("voucher_number")
        booking_line.updated_at = datetime.utcnow()

        # Update booking counters
        booking = booking_line.booking
        booking.confirmed_services += 1
        booking.pending_services -= 1

        # Check if all services are confirmed
        if booking.confirmed_services == booking.total_services:
            booking.overall_status = BookingOverallStatus.CONFIRMED
        elif booking.confirmed_services > 0:
            booking.overall_status = BookingOverallStatus.IN_PROGRESS

        booking.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "id": booking_line.id,
            "booking_status": booking_line.booking_status,
            "supplier_confirmation_code": booking_line.supplier_confirmation_code,
            "confirmed_at": booking_line.confirmed_at.isoformat(),
            "message": "Booking line confirmed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming booking line: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.put("/tenants/{tenant_id}/booking-lines/{line_id}/cancel")
async def cancel_booking_line(
    tenant_id: str,
    line_id: int,
    cancellation_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Cancel a booking line

    Args:
        tenant_id: UUID of the tenant
        line_id: ID of the booking line
        cancellation_data: Cancellation details
        db: Database session

    Returns:
        Updated booking line information
    """
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
        # Get booking line
        booking_line = tenant_db.query(BookingLine).filter(
            and_(
                BookingLine.id == line_id,
                BookingLine.deleted_at.is_(None)
            )
        ).first()

        if not booking_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking line {line_id} not found"
            )

        # Update cancellation details
        previous_status = booking_line.booking_status
        booking_line.booking_status = BookingLineStatus.CANCELLED
        booking_line.cancelled_at = datetime.utcnow()
        booking_line.cancellation_reason = cancellation_data.get("cancellation_reason")
        booking_line.cancellation_code = cancellation_data.get("cancellation_code")
        booking_line.cancellation_fee = cancellation_data.get("cancellation_fee")
        booking_line.updated_at = datetime.utcnow()

        # Update booking counters
        booking = booking_line.booking
        booking.cancelled_services += 1

        if previous_status == BookingLineStatus.CONFIRMED:
            booking.confirmed_services -= 1
        elif previous_status in [BookingLineStatus.PENDING, BookingLineStatus.CONFIRMING]:
            booking.pending_services -= 1

        # Update overall status
        if booking.cancelled_services == booking.total_services:
            booking.overall_status = BookingOverallStatus.CANCELLED
        elif booking.cancelled_services > 0:
            booking.overall_status = BookingOverallStatus.PARTIALLY_CANCELLED

        booking.updated_at = datetime.utcnow()

        tenant_db.commit()

        return {
            "id": booking_line.id,
            "booking_status": booking_line.booking_status,
            "cancelled_at": booking_line.cancelled_at.isoformat(),
            "cancellation_fee": float(booking_line.cancellation_fee) if booking_line.cancellation_fee else None,
            "message": "Booking line cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        tenant_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling booking line: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# BOOKING STATISTICS
# ============================================

@router.get("/tenants/{tenant_id}/bookings/statistics")
async def get_booking_statistics(
    tenant_id: str,
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """
    Get booking statistics for a tenant

    Args:
        tenant_id: UUID of the tenant
        db: Database session
        date_from: Start date for statistics
        date_to: End date for statistics

    Returns:
        Booking statistics
    """
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
        # Base query
        query = tenant_db.query(Booking).filter(Booking.deleted_at.is_(None))

        # Apply date filters
        if date_from:
            query = query.filter(Booking.created_at >= date_from)
        if date_to:
            query = query.filter(Booking.created_at <= date_to)

        # Get statistics
        total_bookings = query.count()

        status_counts = {}
        for status in BookingOverallStatus:
            count = query.filter(Booking.overall_status == status).count()
            status_counts[status] = count

        # Get booking lines statistics
        line_query = tenant_db.query(BookingLine).join(Booking).filter(
            Booking.deleted_at.is_(None)
        )

        if date_from:
            line_query = line_query.filter(BookingLine.created_at >= date_from)
        if date_to:
            line_query = line_query.filter(BookingLine.created_at <= date_to)

        total_services = line_query.count()
        confirmed_services = line_query.filter(
            BookingLine.booking_status == BookingLineStatus.CONFIRMED
        ).count()

        # Get financial summary
        financial_summary = query.with_entities(
            func.sum(Booking.total_amount).label("total_amount"),
            func.sum(Booking.total_paid).label("total_paid"),
            func.sum(Booking.total_commission).label("total_commission")
        ).first()

        return {
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "bookings": {
                "total": total_bookings,
                "by_status": status_counts
            },
            "services": {
                "total": total_services,
                "confirmed": confirmed_services,
                "confirmation_rate": (confirmed_services / total_services * 100) if total_services > 0 else 0
            },
            "financial": {
                "total_amount": float(financial_summary[0] or 0),
                "total_paid": float(financial_summary[1] or 0),
                "total_commission": float(financial_summary[2] or 0)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting booking statistics: {str(e)}"
        )
    finally:
        tenant_db.close()
