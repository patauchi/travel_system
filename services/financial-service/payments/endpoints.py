"""
Payments Module Endpoints
API endpoints for payment management
"""

from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from database import get_tenant_db, get_db, get_schema_from_tenant_id
from shared_auth import get_current_user, get_current_tenant, require_permission
from .models import Payment, PaymentGateway, PaymentAttempt
from .schemas import (
    PaymentCreate, PaymentUpdate, PaymentResponse, PaymentListResponse,
    PaymentGatewayCreate, PaymentGatewayUpdate, PaymentGatewayResponse, PaymentGatewayListResponse,
    PaymentAttemptCreate, PaymentAttemptResponse, PaymentAttemptListResponse,
    PaymentProcessRequest, PaymentProcessResponse, RefundRequest, RefundResponse,
    DisputeCreateRequest, DisputeUpdateRequest, DisputeResponse,
    PaymentSummaryResponse, PaymentSummaryByMethod, PaymentSummaryByStatus, PaymentSummaryByGateway
)
from common.enums import PaymentMethod, PaymentType, TransactionType

router = APIRouter()

# ============================================
# PAYMENT ENDPOINTS
# ============================================

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new payment record"""
    # Check permissions
    await require_permission(current_user, "payments:create")

    try:
        payment = Payment(
            **payment_data.model_dump(),
            processed_by=current_user.get("user_id")
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment: {str(e)}"
        )

@router.get("/payments", response_model=PaymentListResponse)
async def list_payments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    payment_type: Optional[PaymentType] = Query(None, description="Filter by payment type"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    status_filter: Optional[str] = Query(None, description="Filter by payment status"),
    invoice_id: Optional[int] = Query(None, description="Filter by invoice ID"),
    order_id: Optional[int] = Query(None, description="Filter by order ID"),
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    start_date: Optional[date] = Query(None, description="Filter payments from this date"),
    end_date: Optional[date] = Query(None, description="Filter payments to this date"),
    is_refund: Optional[bool] = Query(None, description="Filter by refund status"),
    is_disputed: Optional[bool] = Query(None, description="Filter by dispute status"),
    gateway_code: Optional[str] = Query(None, description="Filter by gateway code"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List payments with filtering and pagination"""
    # Check permissions
    await require_permission(current_user, "payments:read")

    try:
        # Build query
        query = db.query(Payment).filter(Payment.deleted_at.is_(None))

        # Apply filters
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        if payment_type:
            query = query.filter(Payment.payment_type == payment_type)
        if transaction_type:
            query = query.filter(Payment.transaction_type == transaction_type)
        if status_filter:
            query = query.filter(Payment.status == status_filter)
        if invoice_id:
            query = query.filter(Payment.invoice_id == invoice_id)
        if order_id:
            query = query.filter(Payment.order_id == order_id)
        if account_id:
            query = query.filter(Payment.account_id == account_id)
        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)
        if is_refund is not None:
            query = query.filter(Payment.is_refund == is_refund)
        if is_disputed is not None:
            query = query.filter(Payment.is_disputed == is_disputed)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        payments = query.order_by(desc(Payment.payment_date)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return PaymentListResponse(
            payments=payments,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing payments: {str(e)}"
        )

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get a specific payment by ID"""
    # Check permissions
    await require_permission(current_user, "payments:read")

    payment = db.query(Payment).filter(
        and_(Payment.id == payment_id, Payment.deleted_at.is_(None))
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Update an existing payment"""
    # Check permissions
    await require_permission(current_user, "payments:update")

    payment = db.query(Payment).filter(
        and_(Payment.id == payment_id, Payment.deleted_at.is_(None))
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Check if payment can be updated
    if payment.status in ["completed", "settled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update completed or settled payments"
        )

    try:
        # Update payment fields
        update_data = payment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment, field, value)

        payment.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)

        return payment
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating payment: {str(e)}"
        )

# ============================================
# PAYMENT PROCESSING ENDPOINTS
# ============================================

@router.post("/payments/process", response_model=PaymentProcessResponse)
async def process_payment(
    payment_request: PaymentProcessRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Process a new payment"""
    # Check permissions
    await require_permission(current_user, "payments:process")

    try:
        # Select gateway
        gateway_query = db.query(PaymentGateway).filter(
            and_(
                PaymentGateway.is_active == True,
                PaymentGateway.deleted_at.is_(None)
            )
        )

        if payment_request.gateway_code:
            gateway = gateway_query.filter(
                PaymentGateway.gateway_code == payment_request.gateway_code
            ).first()
        else:
            gateway = gateway_query.order_by(asc(PaymentGateway.priority)).first()

        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No available payment gateway found"
            )

        # Validate payment method support
        payment_method = payment_request.payment_method
        if payment_method == PaymentMethod.credit_card and not gateway.supports_credit_cards:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gateway does not support credit cards"
            )
        elif payment_method == PaymentMethod.debit_card and not gateway.supports_debit_cards:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gateway does not support debit cards"
            )
        elif payment_method == PaymentMethod.bank_transfer and not gateway.supports_bank_transfer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gateway does not support bank transfers"
            )

        # Check amount limits
        if gateway.min_transaction_amount and payment_request.amount < gateway.min_transaction_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount below minimum limit of {gateway.min_transaction_amount}"
            )

        if gateway.max_transaction_amount and payment_request.amount > gateway.max_transaction_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Amount exceeds maximum limit of {gateway.max_transaction_amount}"
            )

        # Create payment record
        payment_number = f"PAY-{datetime.now().strftime('%Y%m%d')}-{datetime.now().microsecond}"

        payment = Payment(
            invoice_id=payment_request.invoice_id,
            order_id=payment_request.order_id,
            payment_number=payment_number,
            payment_date=date.today(),
            amount=payment_request.amount,
            currency=payment_request.currency,
            payment_method=payment_request.payment_method,
            payment_type=PaymentType.full if payment_request.amount else PaymentType.partial,
            processed_by=current_user.get("user_id"),
            status="processing"
        )

        db.add(payment)
        db.flush()  # Get payment ID

        # Create payment attempt record
        attempt = PaymentAttempt(
            payment_id=payment.id,
            gateway_id=gateway.id,
            invoice_id=payment_request.invoice_id,
            order_id=payment_request.order_id,
            attempt_number=1,
            attempt_date=datetime.utcnow(),
            amount=payment_request.amount,
            currency=payment_request.currency,
            status="processing"
        )

        db.add(attempt)

        # Here you would integrate with the actual payment gateway
        # For now, we'll simulate payment processing
        import random
        processing_time_ms = random.randint(500, 3000)
        success = random.choice([True, True, True, False])  # 75% success rate

        if success:
            # Simulate successful payment
            transaction_id = f"TXN-{datetime.now().microsecond}"
            gateway_transaction_id = f"GTW-{datetime.now().microsecond}"
            authorization_code = f"AUTH-{random.randint(100000, 999999)}"

            # Calculate fees
            gateway_fee = (payment_request.amount * gateway.transaction_fee_percent / 100) + gateway.transaction_fee_fixed
            net_amount = payment_request.amount - gateway_fee

            # Update payment
            payment.status = "completed"
            payment.transaction_id = transaction_id
            payment.gateway_transaction_id = gateway_transaction_id
            payment.authorization_code = authorization_code
            payment.gateway_fee = gateway_fee
            payment.net_amount = net_amount
            payment.is_verified = True
            payment.verified_at = datetime.utcnow()
            payment.verified_by = current_user.get("user_id")

            # Update attempt
            attempt.status = "success"
            attempt.gateway_transaction_id = gateway_transaction_id
            attempt.gateway_response_code = "00"
            attempt.gateway_response_message = "Transaction successful"
            attempt.processing_time_ms = processing_time_ms

            db.commit()

            return PaymentProcessResponse(
                payment_id=payment.id,
                status="completed",
                success=True,
                transaction_id=transaction_id,
                gateway_transaction_id=gateway_transaction_id,
                authorization_code=authorization_code,
                amount=payment_request.amount,
                currency=payment_request.currency,
                gateway_fee=gateway_fee,
                net_amount=net_amount,
                processing_time_ms=processing_time_ms,
                retry_eligible=False
            )
        else:
            # Simulate failed payment
            error_messages = [
                "Insufficient funds",
                "Card declined",
                "Invalid card number",
                "Expired card",
                "Transaction limit exceeded"
            ]
            error_message = random.choice(error_messages)
            decline_reason = error_message.lower().replace(" ", "_")

            # Update payment
            payment.status = "failed"

            # Update attempt
            attempt.status = "failed"
            attempt.gateway_response_code = "05"
            attempt.gateway_response_message = error_message
            attempt.error_message = error_message
            attempt.decline_reason = decline_reason
            attempt.processing_time_ms = processing_time_ms
            attempt.retry_eligible = True

            db.commit()

            return PaymentProcessResponse(
                payment_id=payment.id,
                status="failed",
                success=False,
                amount=payment_request.amount,
                currency=payment_request.currency,
                decline_reason=decline_reason,
                error_message=error_message,
                retry_eligible=True,
                processing_time_ms=processing_time_ms
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing payment: {str(e)}"
        )

@router.post("/payments/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: int,
    refund_request: RefundRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Process a payment refund"""
    # Check permissions
    await require_permission(current_user, "payments:refund")

    payment = db.query(Payment).filter(
        and_(Payment.id == payment_id, Payment.deleted_at.is_(None))
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund completed payments"
        )

    if payment.is_refund:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot refund a refund transaction"
        )

    # Determine refund amount
    refund_amount = refund_request.amount or payment.amount

    if refund_amount > payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed original payment amount"
        )

    try:
        # Create refund payment record
        refund_payment_number = f"REF-{payment.payment_number}-{datetime.now().microsecond}"

        # Get gateway info for fees
        gateway = db.query(PaymentGateway).join(PaymentAttempt).filter(
            PaymentAttempt.payment_id == payment_id
        ).first()

        refund_fee = 0
        if gateway:
            refund_fee = (refund_amount * gateway.refund_fee_percent / 100) + gateway.refund_fee_fixed

        net_refund = refund_amount - refund_fee

        refund_payment = Payment(
            payment_number=refund_payment_number,
            payment_date=date.today(),
            amount=refund_amount,
            currency=payment.currency,
            payment_method=payment.payment_method,
            payment_type=PaymentType.refund,
            transaction_type=TransactionType.refund,
            is_refund=True,
            refund_reason=refund_request.reason,
            original_payment_id=payment_id,
            refund_fee=refund_fee,
            net_amount=net_refund,
            processed_by=current_user.get("user_id"),
            status="completed",
            notes=refund_request.notes
        )

        db.add(refund_payment)
        db.commit()
        db.refresh(refund_payment)

        return RefundResponse(
            refund_payment_id=refund_payment.id,
            original_payment_id=payment_id,
            refund_amount=refund_amount,
            refund_fee=refund_fee,
            net_refund=net_refund,
            status="completed",
            expected_settlement_days=gateway.refund_time_days if gateway else None
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing refund: {str(e)}"
        )

# ============================================
# PAYMENT GATEWAY ENDPOINTS
# ============================================

@router.post("/payment-gateways", response_model=PaymentGatewayResponse)
async def create_payment_gateway(
    gateway_data: PaymentGatewayCreate,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a new payment gateway configuration"""
    # Check permissions
    await require_permission(current_user, "payments:admin")

    try:
        # Note: In production, sensitive fields like api_key, api_secret should be encrypted
        gateway = PaymentGateway(**gateway_data.model_dump())
        db.add(gateway)
        db.commit()
        db.refresh(gateway)

        return gateway
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating payment gateway: {str(e)}"
        )

@router.get("/payment-gateways", response_model=PaymentGatewayListResponse)
async def list_payment_gateways(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True, description="Show only active gateways"),
    gateway_type: Optional[str] = Query(None, description="Filter by gateway type"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """List payment gateways"""
    # Check permissions
    await require_permission(current_user, "payments:read")

    try:
        # Build query
        query = db.query(PaymentGateway).filter(PaymentGateway.deleted_at.is_(None))

        # Apply filters
        if active_only:
            query = query.filter(PaymentGateway.is_active == True)
        if gateway_type:
            query = query.filter(PaymentGateway.gateway_type == gateway_type)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        gateways = query.order_by(asc(PaymentGateway.priority)).offset(skip).limit(limit).all()

        # Calculate pagination info
        pages = (total + limit - 1) // limit

        return PaymentGatewayListResponse(
            gateways=gateways,
            total=total,
            page=(skip // limit) + 1,
            size=limit,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing payment gateways: {str(e)}"
        )

# ============================================
# DISPUTE ENDPOINTS
# ============================================

@router.post("/payments/{payment_id}/dispute", response_model=DisputeResponse)
async def create_dispute(
    payment_id: int,
    dispute_data: DisputeCreateRequest,
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Create a dispute for a payment"""
    # Check permissions
    await require_permission(current_user, "payments:dispute")

    payment = db.query(Payment).filter(
        and_(Payment.id == payment_id, Payment.deleted_at.is_(None))
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.is_disputed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already disputed"
        )

    try:
        # Update payment with dispute information
        payment.is_disputed = True
        payment.dispute_date = datetime.utcnow()
        payment.dispute_reason = dispute_data.dispute_reason
        payment.dispute_amount = dispute_data.dispute_amount
        payment.dispute_status = "open"
        payment.updated_at = datetime.utcnow()

        db.commit()

        return DisputeResponse(
            payment_id=payment_id,
            dispute_amount=dispute_data.dispute_amount,
            dispute_reason=dispute_data.dispute_reason,
            dispute_status="open",
            dispute_date=payment.dispute_date,
            evidence_files=dispute_data.evidence_files,
            notes=dispute_data.notes
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating dispute: {str(e)}"
        )

# ============================================
# SUMMARY ENDPOINTS
# ============================================

@router.get("/payments/summary", response_model=PaymentSummaryResponse)
async def get_payment_summary(
    start_date: Optional[date] = Query(None, description="Start date for summary"),
    end_date: Optional[date] = Query(None, description="End date for summary"),
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Get payment summary and statistics"""
    # Check permissions
    await require_permission(current_user, "payments:read")

    try:
        # Build base query
        query = db.query(Payment).filter(Payment.deleted_at.is_(None))

        if start_date:
            query = query.filter(Payment.payment_date >= start_date)
        if end_date:
            query = query.filter(Payment.payment_date <= end_date)

        # Get total metrics
        total_result = query.with_entities(
            func.count(Payment.id).label('count'),
            func.sum(Payment.amount).label('total_amount'),
            func.sum(func.case([(Payment.is_refund == True, Payment.amount)], else_=0)).label('total_refunds'),
            func.sum(func.coalesce(Payment.gateway_fee, 0)).label('total_fees'),
            func.sum(func.coalesce(Payment.net_amount, Payment.amount)).label('net_amount')
        ).first()

        total_payments = total_result.count or 0
        total_amount = total_result.total_amount or 0
        total_refunds = total_result.total_refunds or 0
        total_fees = total_result.total_fees or 0
        net_amount = total_result.net_amount or 0

        # Success rate
        successful_payments = query.filter(Payment.status == 'completed').count()
        success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0

        # Summary by payment method
        method_summary = query.with_entities(
            Payment.payment_method,
            func.sum(Payment.amount).label('total_amount'),
            func.count(Payment.id).label('count'),
            func.avg(Payment.amount).label('avg_amount'),
            func.count(func.case([(Payment.status == 'completed', 1)])).label('success_count')
        ).group_by(Payment.payment_method).all()

        by_method = [
            PaymentSummaryByMethod(
                payment_method=row.payment_method,
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                avg_amount=row.avg_amount or 0,
                success_rate=(row.success_count / row.count * 100) if row.count > 0 else 0
            ) for row in method_summary
        ]

        # Summary by status
        status_summary = query.with_entities(
            Payment.status,
            func.sum(Payment.amount).label('total_amount'),
            func.count(Payment.id).label('count')
        ).group_by(Payment.status).all()

        by_status = [
            PaymentSummaryByStatus(
                status=row.status,
                total_amount=row.total_amount or 0,
                count=row.count or 0
            ) for row in status_summary
        ]

        # Summary by gateway (simplified)
        gateway_summary = query.join(PaymentAttempt).join(PaymentGateway).with_entities(
            PaymentGateway.gateway_name,
            PaymentGateway.gateway_code,
            func.sum(Payment.amount).label('total_amount'),
            func.count(Payment.id).label('count'),
            func.count(func.case([(Payment.status == 'completed', 1)])).label('success_count'),
            func.avg(PaymentAttempt.processing_time_ms).label('avg_processing_time')
        ).group_by(PaymentGateway.gateway_name, PaymentGateway.gateway_code).all()

        by_gateway = [
            PaymentSummaryByGateway(
                gateway_name=row.gateway_name,
                gateway_code=row.gateway_code,
                total_amount=row.total_amount or 0,
                count=row.count or 0,
                success_rate=(row.success_count / row.count * 100) if row.count > 0 else 0,
                avg_processing_time_ms=int(row.avg_processing_time) if row.avg_processing_time else None
            ) for row in gateway_summary
        ]

        # Dispute metrics
        dispute_result = query.filter(Payment.is_disputed == True).with_entities(
            func.count(Payment.id).label('count'),
            func.sum(Payment.dispute_amount).label('amount')
        ).first()

        dispute_count = dispute_result.count or 0
        dispute_amount = dispute_result.amount or 0

        # Failed payment metrics
        failed_payment_count = query.filter(Payment.status == 'failed').count()

        return PaymentSummaryResponse(
            total_payments=total_payments,
            total_amount=total_amount,
            total_refunds=total_refunds,
            total_fees=total_fees,
            net_amount=net_amount,
            success_rate=success_rate,
            by_method=by_method,
            by_status=by_status,
            by_gateway=by_gateway,
            dispute_count=dispute_count,
            dispute_amount=dispute_amount,
            chargeback_count=0,  # Would need separate tracking
            chargeback_amount=0,  # Would need separate tracking
            avg_processing_time_ms=None,  # Could be calculated from attempts
            failed_payment_count=failed_payment_count,
            retry_success_rate=0  # Would need retry attempt tracking
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating payment summary: {str(e)}"
        )

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/payments/health")
async def payments_health():
    """Health check for payments module"""
    return {
        "status": "healthy",
        "module": "payments",
        "timestamp": datetime.utcnow().isoformat()
    }
