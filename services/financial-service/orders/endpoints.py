"""
Orders Module Endpoints
API endpoints for order management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import Order, OrderLine, PassengerDocument
from .schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderListResponse,
    OrderLineCreate, OrderLineUpdate, OrderLineResponse, OrderLineListResponse,
    PassengerDocumentCreate, PassengerDocumentUpdate, PassengerDocumentResponse,
    PassengerDocumentListResponse
)
from common.enums import OrderStatus, PaymentStatus

router = APIRouter()

# ============================================
# ORDER ENDPOINTS
# ============================================

@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new order"""
    # Check permissions
    await require_permission(current_user, "orders:create")

    try:
        # Create order
        order = Order(**order_data.model_dump(exclude={'order_lines'}))
        db.add(order)
        db.flush()  # Get the order ID

        # Create order lines if provided
        if order_data.order_lines:
            for line_data in order_data.order_lines:
                order_line = OrderLine(
                    order_id=order.id,
                    **line_data.model_dump()
                )
                db.add(order_line)

        db.commit()
        db.refresh(order)

        return order
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )

@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    order_status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    payment_status: Optional[PaymentStatus] = Query(None, description="Filter by payment status"),
    order_number: Optional[str] = Query(None, description="Filter by order number"),
    start_date: Optional[date] = Query(None, description="Filter orders from this date"),
    end_date: Optional[date] = Query(None, description="Filter orders to this date"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List orders with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "orders:read")

    try:
        # Build query
        query = db.query(Order).filter(Order.deleted_at.is_(None))

        # Apply filters
        if order_status:
            query = query.filter(Order.order_status == order_status)
        if payment_status:
            query = query.filter(Order.payment_status == payment_status)
        if order_number:
            query = query.filter(Order.order_number.ilike(f"%{order_number}%"))
        if start_date:
            query = query.filter(Order.order_date >= start_date)
        if end_date:
            query = query.filter(Order.order_date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return OrderListResponse(
            orders=orders,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing orders: {str(e)}"
        )

@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific order by ID"""
    # Check permissions
    await require_permission(current_user, "orders:read")

    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    return order

@router.put("/orders/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an existing order"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    try:
        # Update order fields
        update_data = order_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)

        return order
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order: {str(e)}"
        )

@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete an order"""
    # Check permissions
    await require_permission(current_user, "orders:delete")

    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    try:
        order.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Order deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting order: {str(e)}"
        )

# ============================================
# ORDER LINE ENDPOINTS
# ============================================

@router.post("/orders/{order_id}/lines", response_model=OrderLineResponse)
async def create_order_line(
    order_id: int,
    line_data: OrderLineCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new order line"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    # Verify order exists
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    try:
        order_line = OrderLine(
            order_id=order_id,
            **line_data.model_dump()
        )
        db.add(order_line)
        db.commit()
        db.refresh(order_line)

        return order_line
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order line: {str(e)}"
        )

@router.get("/orders/{order_id}/lines", response_model=OrderLineListResponse)
async def list_order_lines(
    order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List order lines for a specific order"""
    # Check permissions
    await require_permission(current_user, "orders:read")

    # Verify order exists
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Get order lines
    query = db.query(OrderLine).filter(OrderLine.order_id == order_id)
    total = query.count()

    order_lines = query.order_by(asc(OrderLine.line_number)).offset(skip).limit(limit).all()

    pages = (total + limit - 1) // limit

    return OrderLineListResponse(
        order_lines=order_lines,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages
    )

@router.put("/orders/{order_id}/lines/{line_id}", response_model=OrderLineResponse)
async def update_order_line(
    order_id: int,
    line_id: int,
    line_data: OrderLineUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an order line"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    order_line = db.query(OrderLine).filter(
        and_(OrderLine.id == line_id, OrderLine.order_id == order_id)
    ).first()

    if not order_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order line not found"
        )

    try:
        update_data = line_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order_line, field, value)

        order_line.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order_line)

        return order_line
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating order line: {str(e)}"
        )

@router.delete("/orders/{order_id}/lines/{line_id}")
async def delete_order_line(
    order_id: int,
    line_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Delete an order line"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    order_line = db.query(OrderLine).filter(
        and_(OrderLine.id == line_id, OrderLine.order_id == order_id)
    ).first()

    if not order_line:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order line not found"
        )

    try:
        db.delete(order_line)
        db.commit()

        return {"message": "Order line deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting order line: {str(e)}"
        )

# ============================================
# PASSENGER DOCUMENT ENDPOINTS
# ============================================

@router.post("/orders/{order_id}/documents", response_model=PassengerDocumentResponse)
async def create_passenger_document(
    order_id: int,
    document_data: PassengerDocumentCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a passenger document for an order"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    # Verify order exists
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    try:
        document = PassengerDocument(**document_data.model_dump())
        db.add(document)
        db.commit()
        db.refresh(document)

        return document
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating passenger document: {str(e)}"
        )

@router.get("/orders/{order_id}/documents", response_model=PassengerDocumentListResponse)
async def list_passenger_documents(
    order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List passenger documents for an order"""
    # Check permissions
    await require_permission(current_user, "orders:read")

    # Verify order exists
    order = db.query(Order).filter(
        and_(Order.id == order_id, Order.deleted_at.is_(None))
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    query = db.query(PassengerDocument).filter(
        and_(PassengerDocument.order_id == order_id, PassengerDocument.deleted_at.is_(None))
    )
    total = query.count()

    documents = query.order_by(desc(PassengerDocument.created_at)).offset(skip).limit(limit).all()

    pages = (total + limit - 1) // limit

    return PassengerDocumentListResponse(
        documents=documents,
        total=total,
        page=(skip // limit) + 1,
        size=limit,
        pages=pages
    )

@router.put("/orders/{order_id}/documents/{document_id}", response_model=PassengerDocumentResponse)
async def update_passenger_document(
    order_id: int,
    document_id: int,
    document_data: PassengerDocumentUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update a passenger document"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    document = db.query(PassengerDocument).filter(
        and_(
            PassengerDocument.id == document_id,
            PassengerDocument.order_id == order_id,
            PassengerDocument.deleted_at.is_(None)
        )
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger document not found"
        )

    try:
        update_data = document_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(document, field, value)

        document.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(document)

        return document
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating passenger document: {str(e)}"
        )

@router.delete("/orders/{order_id}/documents/{document_id}")
async def delete_passenger_document(
    order_id: int,
    document_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Soft delete a passenger document"""
    # Check permissions
    await require_permission(current_user, "orders:update")

    document = db.query(PassengerDocument).filter(
        and_(
            PassengerDocument.id == document_id,
            PassengerDocument.order_id == order_id,
            PassengerDocument.deleted_at.is_(None)
        )
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passenger document not found"
        )

    try:
        document.deleted_at = datetime.utcnow()
        db.commit()

        return {"message": "Passenger document deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting passenger document: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/orders/health")
async def orders_health():
    """Health check for orders module"""
    return {
        "status": "healthy",
        "module": "orders",
        "timestamp": datetime.utcnow().isoformat()
    }
