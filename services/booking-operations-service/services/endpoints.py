"""
Services module endpoints
Contains FastAPI endpoints for service management and operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from database import get_tenant_db
from shared_auth import get_current_user, check_tenant_slug_access
from .models import Service, ServiceAvailability, ServiceDailyCapacity
from .schemas import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceListResponse,
    ServiceAvailability as ServiceAvailabilitySchema
)
from suppliers.models import Supplier
from common.enums import ServiceType, OperationModel

router = APIRouter()


@router.get("/tenants/{tenant_slug}/services", response_model=ServiceListResponse)
async def list_services(
    tenant_slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    service_type: Optional[ServiceType] = Query(None, description="Filter by service type"),
    operation_model: Optional[OperationModel] = Query(None, description="Filter by operation model"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    search: Optional[str] = Query(None, description="Search in name, code or description"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    List services with filtering and pagination

    Args:
        tenant_slug: Tenant identifier
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        supplier_id: Filter by supplier ID
        service_type: Filter by service type
        operation_model: Filter by operation model
        is_active: Filter by active status
        is_featured: Filter by featured status
        min_price: Minimum price filter
        max_price: Maximum price filter
        search: Search in name, code or description
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of services with pagination info
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build query with supplier join
    query = db.query(Service).options(joinedload(Service.supplier))

    # Apply filters
    filters = []

    if supplier_id:
        filters.append(Service.supplier_id == supplier_id)

    if service_type:
        filters.append(Service.service_type == service_type)

    if operation_model:
        filters.append(Service.operation_model == operation_model)

    if is_active is not None:
        filters.append(Service.is_active == is_active)

    if is_featured is not None:
        filters.append(Service.is_featured == is_featured)

    if search:
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Service.name.ilike(search_pattern),
                Service.code.ilike(search_pattern),
                Service.description.ilike(search_pattern)
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    services = query.offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return {
        "items": services,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }


@router.get("/tenants/{tenant_slug}/services/{service_id}", response_model=ServiceResponse)
async def get_service(
    tenant_slug: str,
    service_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get a specific service by ID

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Service details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get service with supplier
    service = db.query(Service).options(
        joinedload(Service.supplier)
    ).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    return service


@router.post("/tenants/{tenant_slug}/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    tenant_slug: str,
    service_data: ServiceCreate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Create a new service

    Args:
        tenant_slug: Tenant identifier
        service_data: Service data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created service
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Verify supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == service_data.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {service_data.supplier_id} not found"
        )

    # Check if service with same code exists for this supplier
    existing_service = db.query(Service).filter(
        Service.supplier_id == service_data.supplier_id,
        Service.code == service_data.code
    ).first()

    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service with code {service_data.code} already exists for supplier {supplier.name}"
        )

    # Validate min/max participants
    if service_data.min_participants and service_data.max_participants:
        if service_data.min_participants > service_data.max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum participants cannot be greater than maximum participants"
            )

    # Create new service
    new_service = Service(**service_data.dict())

    # Set timestamps
    new_service.created_at = datetime.utcnow()
    new_service.updated_at = datetime.utcnow()

    # Add to database
    db.add(new_service)

    try:
        db.commit()
        db.refresh(new_service)

        # Load supplier relationship
        db.refresh(new_service)
        new_service.supplier  # Force load the relationship

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating service: {str(e)}"
        )

    return new_service


@router.put("/tenants/{tenant_slug}/services/{service_id}", response_model=ServiceResponse)
async def update_service(
    tenant_slug: str,
    service_id: int,
    service_update: ServiceUpdate = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update an existing service

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        service_update: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated service
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get service
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    # If updating supplier, verify it exists
    if service_update.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == service_update.supplier_id).first()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {service_update.supplier_id} not found"
            )

    # Check if updating code to an existing one
    if service_update.code and service_update.code != service.code:
        supplier_id = service_update.supplier_id or service.supplier_id
        existing = db.query(Service).filter(
            Service.supplier_id == supplier_id,
            Service.code == service_update.code,
            Service.id != service_id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Service with code {service_update.code} already exists for this supplier"
            )

    # Validate min/max participants
    update_data = service_update.dict(exclude_unset=True)
    min_participants = update_data.get('min_participants', service.min_participants)
    max_participants = update_data.get('max_participants', service.max_participants)

    if min_participants and max_participants:
        if min_participants > max_participants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum participants cannot be greater than maximum participants"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(service, field, value)

    # Update timestamp
    service.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(service)

        # Load supplier relationship
        service.supplier  # Force load the relationship

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating service: {str(e)}"
        )

    return service


@router.delete("/tenants/{tenant_slug}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    tenant_slug: str,
    service_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Delete a service

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        No content on success
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get service
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    # Check if service has active bookings
    # TODO: Implement when BookingLine has service_id field
    # from bookings.models import BookingLine
    # active_bookings = db.query(BookingLine).join(
    #     Service, BookingLine.service_id == Service.id
    # ).filter(
    #     Service.id == service_id,
    #     BookingLine.booking_status != 'cancelled'
    # ).count()

    # if active_bookings > 0:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=f"Cannot delete service with {active_bookings} active bookings"
    #     )

    # Soft delete
    service.deleted_at = datetime.utcnow()
    service.is_active = False

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting service: {str(e)}"
        )

    return None


@router.patch("/tenants/{tenant_slug}/services/{service_id}/status")
async def update_service_status(
    tenant_slug: str,
    service_id: int,
    status_update: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update service status

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        status_update: Status update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated service status
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get service
    service = db.query(Service).filter(Service.id == service_id).first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    # Update status fields
    if 'is_active' in status_update:
        service.is_active = status_update['is_active']

    if 'is_featured' in status_update:
        service.is_featured = status_update['is_featured']

    # Update timestamp
    service.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(service)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating service status: {str(e)}"
        )

    return {
        "id": service.id,
        "code": service.code,
        "name": service.name,
        "is_active": service.is_active,
        "is_featured": service.is_featured,
        "updated_at": service.updated_at.isoformat()
    }


@router.get("/tenants/{tenant_slug}/services/{service_id}/availability")
async def get_service_availability(
    tenant_slug: str,
    service_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get service availability for a date range

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        start_date: Start date
        end_date: End date
        current_user: Current authenticated user
        db: Database session

    Returns:
        Service availability for each date
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after or equal to start date"
        )

    # Get availability for date range
    availability_data = db.query(ServiceDailyCapacity).filter(
        ServiceDailyCapacity.service_id == service_id,
        ServiceDailyCapacity.service_date >= start_date,
        ServiceDailyCapacity.service_date <= end_date
    ).all()

    # Build response
    availability_list = []
    current_date = start_date

    while current_date <= end_date:
        # Find availability for this date
        day_availability = next(
            (a for a in availability_data if a.service_date == current_date),
            None
        )

        if day_availability:
            availability_list.append({
                "date": current_date.isoformat(),
                "total_capacity": day_availability.total_capacity,
                "booked_capacity": day_availability.booked_capacity,
                "available_capacity": day_availability.available_capacity,
                "is_available": day_availability.is_available,
                "is_blocked": day_availability.is_blocked,
                "block_reason": day_availability.block_reason
            })
        else:
            # Default availability if not set
            availability_list.append({
                "date": current_date.isoformat(),
                "total_capacity": service.max_participants or 999,
                "booked_capacity": 0,
                "available_capacity": service.max_participants or 999,
                "is_available": True,
                "is_blocked": False,
                "block_reason": None
            })

        current_date += timedelta(days=1)

    return {
        "service_id": service_id,
        "service_name": service.name,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "availability": availability_list
    }


@router.post("/tenants/{tenant_slug}/services/{service_id}/availability")
async def update_service_availability(
    tenant_slug: str,
    service_id: int,
    availability_update: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update service availability for specific dates

    Args:
        tenant_slug: Tenant identifier
        service_id: Service ID
        availability_update: Availability update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated availability
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Verify service exists
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with ID {service_id} not found"
        )

    # Parse dates
    service_date = datetime.strptime(availability_update['date'], '%Y-%m-%d').date()

    # Get or create daily capacity record
    daily_capacity = db.query(ServiceDailyCapacity).filter(
        ServiceDailyCapacity.service_id == service_id,
        ServiceDailyCapacity.service_date == service_date
    ).first()

    if not daily_capacity:
        daily_capacity = ServiceDailyCapacity(
            service_id=service_id,
            service_date=service_date,
            total_capacity=availability_update.get('total_capacity', service.max_participants or 999),
            booked_capacity=0,
            available_capacity=availability_update.get('total_capacity', service.max_participants or 999)
        )
        db.add(daily_capacity)

    # Update fields
    if 'total_capacity' in availability_update:
        daily_capacity.total_capacity = availability_update['total_capacity']
        daily_capacity.available_capacity = daily_capacity.total_capacity - daily_capacity.booked_capacity

    if 'is_available' in availability_update:
        daily_capacity.is_available = availability_update['is_available']

    if 'is_blocked' in availability_update:
        daily_capacity.is_blocked = availability_update['is_blocked']
        if availability_update['is_blocked']:
            daily_capacity.block_reason = availability_update.get('block_reason', 'Manual block')
        else:
            daily_capacity.block_reason = None

    # Update timestamps
    daily_capacity.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(daily_capacity)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating availability: {str(e)}"
        )

    return {
        "service_id": service_id,
        "date": service_date.isoformat(),
        "total_capacity": daily_capacity.total_capacity,
        "booked_capacity": daily_capacity.booked_capacity,
        "available_capacity": daily_capacity.available_capacity,
        "is_available": daily_capacity.is_available,
        "is_blocked": daily_capacity.is_blocked,
        "block_reason": daily_capacity.block_reason
    }


@router.get("/tenants/{tenant_slug}/services/search/by-code/{code}")
async def get_service_by_code(
    tenant_slug: str,
    code: str,
    supplier_id: Optional[int] = Query(None, description="Supplier ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get service by code

    Args:
        tenant_slug: Tenant identifier
        code: Service code
        supplier_id: Optional supplier ID filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        Service details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build query
    query = db.query(Service).options(joinedload(Service.supplier))
    query = query.filter(Service.code == code)

    if supplier_id:
        query = query.filter(Service.supplier_id == supplier_id)

    service = query.first()

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service with code {code} not found"
        )

    return service


@router.get("/tenants/{tenant_slug}/services/statistics")
async def get_services_statistics(
    tenant_slug: str,
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get services statistics

    Args:
        tenant_slug: Tenant identifier
        supplier_id: Optional supplier filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        Services statistics
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build base query
    query = db.query(Service)
    if supplier_id:
        query = query.filter(Service.supplier_id == supplier_id)

    # Get statistics
    total_services = query.count()
    active_services = query.filter(Service.is_active == True).count()
    featured_services = query.filter(Service.is_featured == True).count()

    # Count by type
    type_counts = db.query(
        Service.service_type,
        func.count(Service.id)
    ).group_by(Service.service_type)

    if supplier_id:
        type_counts = type_counts.filter(Service.supplier_id == supplier_id)

    type_counts = type_counts.all()

    # Count by operation model
    model_counts = db.query(
        Service.operation_model,
        func.count(Service.id)
    ).group_by(Service.operation_model)

    if supplier_id:
        model_counts = model_counts.filter(Service.supplier_id == supplier_id)

    model_counts = model_counts.all()

    # Get suppliers with most services
    top_suppliers = db.query(
        Supplier.id,
        Supplier.name,
        func.count(Service.id).label('service_count')
    ).join(Service).group_by(
        Supplier.id, Supplier.name
    ).order_by(func.count(Service.id).desc()).limit(5).all()

    return {
        "total_services": total_services,
        "active_services": active_services,
        "inactive_services": total_services - active_services,
        "featured_services": featured_services,
        "by_type": {
            type_name.value if type_name else "unknown": count
            for type_name, count in type_counts
        },
        "by_operation_model": {
            model.value if model else "unknown": count
            for model, count in model_counts
        },
        "top_suppliers": [
            {"id": s.id, "name": s.name, "service_count": s.service_count}
            for s in top_suppliers
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
