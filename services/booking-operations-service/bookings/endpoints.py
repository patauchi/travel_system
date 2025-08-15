"""
Bookings module endpoints
Contains FastAPI endpoints for booking management and operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import get_tenant_db
from shared_auth import get_current_user, check_tenant_slug_access
from .models import Booking, BookingLine, BookingPassenger
from .schemas import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse,
    BookingLineCreate,
    BookingLineUpdate,
    BookingLineResponse,
    BookingPassengerCreate,
    BookingPassengerUpdate,
    BookingPassengerResponse
)
from common.enums import BookingOverallStatus, BookingLineStatus

router = APIRouter()


@router.get("/tenants/{tenant_slug}/bookings", response_model=BookingListResponse)
async def list_bookings(
    tenant_slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    overall_status: Optional[BookingOverallStatus] = Query(None, description="Filter by overall status"),
    booking_date_from: Optional[datetime] = Query(None, description="Filter by booking date from"),
    booking_date_to: Optional[datetime] = Query(None, description="Filter by booking date to"),
    service_date_from: Optional[datetime] = Query(None, description="Filter by service date from"),
    service_date_to: Optional[datetime] = Query(None, description="Filter by service date to"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    search: Optional[str] = Query(None, description="Search in booking reference, customer name or email"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    List bookings with filtering and pagination

    Args:
        tenant_slug: Tenant identifier
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        overall_status: Filter by overall status
        booking_date_from: Filter by booking date from
        booking_date_to: Filter by booking date to
        service_date_from: Filter by service date from
        service_date_to: Filter by service date to
        customer_email: Filter by customer email
        search: Search in booking reference, customer name or email
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of bookings with pagination info
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build query
    query = db.query(Booking)

    # Apply filters
    filters = []

    if overall_status:
        filters.append(Booking.overall_status == overall_status)

    if booking_date_from:
        filters.append(Booking.booking_date >= booking_date_from)

    if booking_date_to:
        filters.append(Booking.booking_date <= booking_date_to)

    if service_date_from:
        filters.append(Booking.service_date >= service_date_from)

    if service_date_to:
        filters.append(Booking.service_date <= service_date_to)

    if customer_email:
        filters.append(Booking.customer_email == customer_email)

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Booking.booking_reference.ilike(search_pattern),
                Booking.external_reference.ilike(search_pattern),
                Booking.customer_name.ilike(search_pattern),
                Booking.customer_email.ilike(search_pattern)
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    bookings = query.order_by(Booking.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": bookings,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/tenants/{tenant_slug}/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(
    tenant_slug: str,
    booking_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get a specific booking by ID

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Booking details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking with related data
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    return booking


@router.post("/tenants/{tenant_slug}/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    tenant_slug: str,
    booking_data: BookingCreate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Create a new booking

    Args:
        tenant_slug: Tenant identifier
        booking_data: Booking data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created booking
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Check if booking with same reference exists
    if booking_data.booking_reference:
        existing = db.query(Booking).filter(
            Booking.booking_reference == booking_data.booking_reference
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking with reference {booking_data.booking_reference} already exists"
            )

    # Create new booking
    new_booking = Booking(**booking_data.dict())

    # Set timestamps
    new_booking.created_at = datetime.utcnow()
    new_booking.updated_at = datetime.utcnow()

    # Add to database
    db.add(new_booking)

    try:
        db.commit()
        db.refresh(new_booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating booking: {str(e)}"
        )

    return new_booking


@router.put("/tenants/{tenant_slug}/bookings/{booking_id}", response_model=BookingResponse)
async def update_booking(
    tenant_slug: str,
    booking_id: int,
    booking_update: BookingUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update an existing booking

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        booking_update: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated booking
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    # Check if updating reference to an existing one
    if booking_update.booking_reference and booking_update.booking_reference != booking.booking_reference:
        existing = db.query(Booking).filter(
            Booking.booking_reference == booking_update.booking_reference,
            Booking.id != booking_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking with reference {booking_update.booking_reference} already exists"
            )

    # Update fields
    update_data = booking_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)

    # Update timestamp
    booking.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking: {str(e)}"
        )

    return booking


@router.delete("/tenants/{tenant_slug}/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(
    tenant_slug: str,
    booking_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Delete a booking

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        No content on success
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    # Soft delete - just mark as deleted
    booking.deleted_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting booking: {str(e)}"
        )

    return None


@router.patch("/tenants/{tenant_slug}/bookings/{booking_id}/status")
async def update_booking_status(
    tenant_slug: str,
    booking_id: int,
    status_update: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update booking status

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        status_update: Status update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated booking
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    # Update status
    new_status = status_update.get("overall_status")
    if new_status:
        try:
            booking.overall_status = BookingOverallStatus(new_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {new_status}"
            )

    # Update timestamp
    booking.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating booking status: {str(e)}"
        )

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "overall_status": booking.overall_status.value if booking.overall_status else None,
        "updated_at": booking.updated_at.isoformat()
    }


@router.post("/tenants/{tenant_slug}/bookings/{booking_id}/cancel")
async def cancel_booking(
    tenant_slug: str,
    booking_id: int,
    cancellation_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Cancel a booking

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        cancellation_data: Cancellation details
        current_user: Current authenticated user
        db: Database session

    Returns:
        Cancelled booking
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    # Check if already cancelled
    if booking.overall_status == BookingOverallStatus.cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already cancelled"
        )

    # Update booking status
    booking.overall_status = BookingOverallStatus.cancelled
    booking.cancellation_reason = cancellation_data.get("reason", "Customer request")
    booking.cancelled_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()

    # Cancel all booking lines
    for line in booking.booking_lines:
        line.booking_status = BookingLineStatus.cancelled
        line.cancellation_reason = cancellation_data.get("reason", "Booking cancelled")
        line.cancelled_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling booking: {str(e)}"
        )

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "overall_status": booking.overall_status.value,
        "cancellation_reason": booking.cancellation_reason,
        "cancelled_at": booking.cancelled_at.isoformat() if booking.cancelled_at else None
    }


@router.post("/tenants/{tenant_slug}/bookings/{booking_id}/confirm")
async def confirm_booking(
    tenant_slug: str,
    booking_id: int,
    confirmation_data: Dict[str, Any] = Body(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Confirm a booking

    Args:
        tenant_slug: Tenant identifier
        booking_id: Booking ID
        confirmation_data: Confirmation details
        current_user: Current authenticated user
        db: Database session

    Returns:
        Confirmed booking
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} not found"
        )

    # Check if already confirmed
    if booking.overall_status == BookingOverallStatus.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking is already confirmed"
        )

    # Update booking status
    booking.overall_status = BookingOverallStatus.confirmed
    booking.confirmed_at = datetime.utcnow()
    booking.updated_at = datetime.utcnow()

    # Confirm all booking lines
    for line in booking.booking_lines:
        if line.booking_status == BookingLineStatus.pending:
            line.booking_status = BookingLineStatus.confirmed
            line.confirmed_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(booking)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error confirming booking: {str(e)}"
        )

    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "overall_status": booking.overall_status.value,
        "confirmed_at": booking.confirmed_at.isoformat() if booking.confirmed_at else None
    }


@router.get("/tenants/{tenant_slug}/bookings/search/by-reference/{reference}")
async def get_booking_by_reference(
    tenant_slug: str,
    reference: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get booking by reference

    Args:
        tenant_slug: Tenant identifier
        reference: Booking reference
        current_user: Current authenticated user
        db: Database session

    Returns:
        Booking details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get booking
    booking = db.query(Booking).filter(
        or_(
            Booking.booking_reference == reference,
            Booking.external_reference == reference
        )
    ).first()

    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with reference {reference} not found"
        )

    return booking


@router.get("/tenants/{tenant_slug}/bookings/statistics")
async def get_bookings_statistics(
    tenant_slug: str,
    date_from: Optional[datetime] = Query(None, description="Statistics from date"),
    date_to: Optional[datetime] = Query(None, description="Statistics to date"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get bookings statistics

    Args:
        tenant_slug: Tenant identifier
        date_from: Statistics from date
        date_to: Statistics to date
        current_user: Current authenticated user
        db: Database session

    Returns:
        Bookings statistics
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build base query
    query = db.query(Booking)

    # Apply date filters
    if date_from:
        query = query.filter(Booking.booking_date >= date_from)
    if date_to:
        query = query.filter(Booking.booking_date <= date_to)

    # Get statistics
    total_bookings = query.count()

    # Count by status
    status_counts = db.query(
        Booking.overall_status,
        func.count(Booking.id)
    ).group_by(Booking.overall_status)

    if date_from:
        status_counts = status_counts.filter(Booking.booking_date >= date_from)
    if date_to:
        status_counts = status_counts.filter(Booking.booking_date <= date_to)

    status_counts = status_counts.all()

    # Calculate total revenue
    total_revenue = query.filter(
        Booking.overall_status != BookingOverallStatus.cancelled
    ).with_entities(func.sum(Booking.total_amount)).scalar() or 0

    # Count bookings by month
    monthly_counts = db.query(
        func.date_trunc('month', Booking.booking_date).label('month'),
        func.count(Booking.id).label('count')
    ).group_by('month').order_by('month')

    if date_from:
        monthly_counts = monthly_counts.filter(Booking.booking_date >= date_from)
    if date_to:
        monthly_counts = monthly_counts.filter(Booking.booking_date <= date_to)

    monthly_data = [
        {"month": month.isoformat(), "count": count}
        for month, count in monthly_counts.all()
    ]

    return {
        "total_bookings": total_bookings,
        "total_revenue": float(total_revenue),
        "by_status": {
            status.value if status else "unknown": count
            for status, count in status_counts
        },
        "monthly_bookings": monthly_data,
        "date_range": {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None
        },
        "generated_at": datetime.utcnow().isoformat()
    }
