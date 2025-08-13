"""
Communication Service - Communication Endpoints
API endpoints for sending emails, SMS, WhatsApp messages and managing templates
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
import json
import logging

from database import get_tenant_db, get_db, get_schema_from_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# ENUMS
# ============================================

class CommunicationType(str, Enum):
    """Types of communications"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"


class CommunicationStatus(str, Enum):
    """Communication delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"


class TemplateType(str, Enum):
    """Template types"""
    BOOKING_CONFIRMATION = "booking_confirmation"
    PAYMENT_RECEIPT = "payment_receipt"
    INVOICE = "invoice"
    REMINDER = "reminder"
    WELCOME = "welcome"
    RESET_PASSWORD = "reset_password"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    CUSTOM = "custom"


# ============================================
# SCHEMAS
# ============================================

class EmailRequest(BaseModel):
    """Email sending request"""
    to: List[EmailStr] = Field(..., min_items=1, max_items=50)
    cc: Optional[List[EmailStr]] = Field(None, max_items=10)
    bcc: Optional[List[EmailStr]] = Field(None, max_items=10)
    subject: str = Field(..., min_length=1, max_length=200)
    body_html: Optional[str] = None
    body_text: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    attachments: Optional[List[Dict[str, str]]] = None
    reply_to: Optional[EmailStr] = None
    headers: Optional[Dict[str, str]] = None
    track_opens: bool = Field(default=True)
    track_clicks: bool = Field(default=True)
    send_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('body_html', 'body_text', 'template_id')
    def validate_content(cls, v, values):
        has_html = values.get('body_html')
        has_text = values.get('body_text')
        has_template = values.get('template_id')

        if not any([has_html, has_text, has_template]):
            raise ValueError('Must provide either body_html, body_text, or template_id')
        return v


class SMSRequest(BaseModel):
    """SMS sending request"""
    to: List[str] = Field(..., min_items=1, max_items=100, description="Phone numbers in E.164 format")
    message: str = Field(..., min_length=1, max_length=1600)
    sender_id: Optional[str] = Field(None, max_length=11)
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    send_at: Optional[datetime] = None
    validity_period: Optional[int] = Field(None, ge=60, le=86400, description="Message validity in seconds")
    metadata: Optional[Dict[str, Any]] = None

    @validator('to')
    def validate_phone_numbers(cls, v):
        # Basic validation for E.164 format
        for phone in v:
            if not phone.startswith('+'):
                raise ValueError(f'Phone number {phone} must be in E.164 format (starting with +)')
            if len(phone) < 10 or len(phone) > 15:
                raise ValueError(f'Phone number {phone} invalid length')
        return v


class WhatsAppRequest(BaseModel):
    """WhatsApp message request"""
    to: str = Field(..., description="Phone number in E.164 format")
    message_type: str = Field("text", pattern="^(text|template|media|location|contact)$")
    text: Optional[str] = Field(None, max_length=4096)
    template_name: Optional[str] = None
    template_language: Optional[str] = Field("en", max_length=5)
    template_data: Optional[Dict[str, Any]] = None
    media_url: Optional[str] = None
    media_caption: Optional[str] = Field(None, max_length=1024)
    location: Optional[Dict[str, float]] = None  # {latitude, longitude, name, address}
    buttons: Optional[List[Dict[str, str]]] = None
    send_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BulkCommunicationRequest(BaseModel):
    """Bulk communication request"""
    communication_type: CommunicationType
    recipients: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    template_id: str
    default_data: Optional[Dict[str, Any]] = None
    personalization: Optional[Dict[str, Dict[str, Any]]] = None
    send_at: Optional[datetime] = None
    batch_size: int = Field(100, ge=1, le=500)
    delay_between_batches: int = Field(1, ge=0, le=60, description="Delay in seconds")
    metadata: Optional[Dict[str, Any]] = None


class TemplateCreate(BaseModel):
    """Template creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    type: TemplateType
    communication_type: CommunicationType
    subject: Optional[str] = Field(None, max_length=200)
    content_html: Optional[str] = None
    content_text: str
    variables: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = Field(default=True)


class CommunicationHistoryFilter(BaseModel):
    """Filters for communication history"""
    communication_type: Optional[CommunicationType] = None
    status: Optional[CommunicationStatus] = None
    recipient: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    template_id: Optional[str] = None


# ============================================
# EMAIL ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/communications/emails")
async def send_email(
    tenant_id: str,
    email_request: EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send email to one or multiple recipients

    Supports both template-based and custom content emails
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
        # Create communication record
        communication_id = f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
        # For now, we'll simulate the sending process

        # Add to background task for async processing
        background_tasks.add_task(
            process_email_sending,
            communication_id,
            email_request.dict(),
            tenant_id
        )

        return {
            "communication_id": communication_id,
            "status": "queued",
            "recipients_count": len(email_request.to),
            "scheduled_at": email_request.send_at,
            "message": "Email queued for sending"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# SMS ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/communications/sms")
async def send_sms(
    tenant_id: str,
    sms_request: SMSRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send SMS to one or multiple recipients

    Phone numbers must be in E.164 format (+1234567890)
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
        # Create communication record
        communication_id = f"SMS-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # TODO: Integrate with actual SMS service (Twilio, MessageBird, etc.)

        # Add to background task for async processing
        background_tasks.add_task(
            process_sms_sending,
            communication_id,
            sms_request.dict(),
            tenant_id
        )

        return {
            "communication_id": communication_id,
            "status": "queued",
            "recipients_count": len(sms_request.to),
            "scheduled_at": sms_request.send_at,
            "message": "SMS queued for sending"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending SMS: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# WHATSAPP ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/communications/whatsapp")
async def send_whatsapp(
    tenant_id: str,
    whatsapp_request: WhatsAppRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send WhatsApp message

    Supports text, template, media, location, and contact messages
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
        # Create communication record
        communication_id = f"WA-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # TODO: Integrate with WhatsApp Business API

        # Add to background task for async processing
        background_tasks.add_task(
            process_whatsapp_sending,
            communication_id,
            whatsapp_request.dict(),
            tenant_id
        )

        return {
            "communication_id": communication_id,
            "status": "queued",
            "recipient": whatsapp_request.to,
            "message_type": whatsapp_request.message_type,
            "scheduled_at": whatsapp_request.send_at,
            "message": "WhatsApp message queued for sending"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending WhatsApp message: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# BULK COMMUNICATION ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/communications/bulk")
async def send_bulk_communication(
    tenant_id: str,
    bulk_request: BulkCommunicationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Send bulk communications (email, SMS, or WhatsApp)

    Processes in batches with configurable delays
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
        # Create bulk job record
        job_id = f"BULK-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Calculate batches
        total_recipients = len(bulk_request.recipients)
        batch_count = (total_recipients + bulk_request.batch_size - 1) // bulk_request.batch_size

        # Add to background task for async processing
        background_tasks.add_task(
            process_bulk_communication,
            job_id,
            bulk_request.dict(),
            tenant_id
        )

        return {
            "job_id": job_id,
            "status": "queued",
            "communication_type": bulk_request.communication_type,
            "total_recipients": total_recipients,
            "batch_count": batch_count,
            "batch_size": bulk_request.batch_size,
            "scheduled_at": bulk_request.send_at,
            "message": "Bulk communication job queued"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bulk communication job: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# TEMPLATE ENDPOINTS
# ============================================

@router.post("/tenants/{tenant_id}/communications/templates")
async def create_template(
    tenant_id: str,
    template_data: TemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new communication template
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
        # TODO: Save template to database
        template_id = f"TPL-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return {
            "template_id": template_id,
            "name": template_data.name,
            "type": template_data.type,
            "communication_type": template_data.communication_type,
            "is_active": template_data.is_active,
            "created_at": datetime.utcnow().isoformat(),
            "message": "Template created successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating template: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/communications/templates")
async def list_templates(
    tenant_id: str,
    db: Session = Depends(get_db),
    communication_type: Optional[CommunicationType] = Query(None),
    template_type: Optional[TemplateType] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List available communication templates
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
        # TODO: Fetch templates from database with filters

        # Mock response for now
        templates = [
            {
                "template_id": "TPL-001",
                "name": "Booking Confirmation",
                "type": "booking_confirmation",
                "communication_type": "email",
                "subject": "Your Booking is Confirmed!",
                "is_active": True,
                "variables": ["customer_name", "booking_number", "travel_date"],
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "template_id": "TPL-002",
                "name": "Payment Reminder",
                "type": "reminder",
                "communication_type": "sms",
                "is_active": True,
                "variables": ["customer_name", "amount", "due_date"],
                "created_at": datetime.utcnow().isoformat()
            }
        ]

        return {
            "total": len(templates),
            "skip": skip,
            "limit": limit,
            "data": templates
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching templates: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# COMMUNICATION HISTORY ENDPOINTS
# ============================================

@router.get("/tenants/{tenant_id}/communications/history")
async def get_communication_history(
    tenant_id: str,
    db: Session = Depends(get_db),
    communication_type: Optional[CommunicationType] = Query(None),
    status: Optional[CommunicationStatus] = Query(None),
    recipient: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    template_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$")
):
    """
    Get communication history with filtering
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
        # TODO: Fetch communication history from database

        # Mock response for now
        history = [
            {
                "communication_id": "EMAIL-20240115120000",
                "type": "email",
                "status": "delivered",
                "recipient": "customer@example.com",
                "subject": "Booking Confirmation",
                "template_id": "TPL-001",
                "sent_at": datetime.utcnow().isoformat(),
                "delivered_at": datetime.utcnow().isoformat(),
                "metadata": {}
            }
        ]

        return {
            "total": len(history),
            "skip": skip,
            "limit": limit,
            "data": history
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching communication history: {str(e)}"
        )
    finally:
        tenant_db.close()


@router.get("/tenants/{tenant_id}/communications/{communication_id}")
async def get_communication_details(
    tenant_id: str,
    communication_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific communication
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
        # TODO: Fetch communication details from database

        # Mock response for now
        return {
            "communication_id": communication_id,
            "type": "email",
            "status": "delivered",
            "recipient": "customer@example.com",
            "subject": "Booking Confirmation",
            "content": "Your booking has been confirmed...",
            "template_id": "TPL-001",
            "created_at": datetime.utcnow().isoformat(),
            "sent_at": datetime.utcnow().isoformat(),
            "delivered_at": datetime.utcnow().isoformat(),
            "opened_at": None,
            "clicked_at": None,
            "metadata": {},
            "events": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "queued",
                    "details": {}
                },
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "sent",
                    "details": {}
                },
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event": "delivered",
                    "details": {}
                }
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching communication details: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# STATISTICS ENDPOINTS
# ============================================

@router.get("/tenants/{tenant_id}/communications/statistics")
async def get_communication_statistics(
    tenant_id: str,
    db: Session = Depends(get_db),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    group_by: str = Query("day", pattern="^(day|week|month)$")
):
    """
    Get communication statistics and analytics
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
        # TODO: Calculate statistics from database

        # Mock response for now
        return {
            "period": {
                "from": date_from.isoformat() if date_from else None,
                "to": date_to.isoformat() if date_to else None
            },
            "summary": {
                "total_sent": 1250,
                "total_delivered": 1200,
                "total_opened": 800,
                "total_clicked": 300,
                "total_failed": 50
            },
            "by_type": {
                "email": {
                    "sent": 500,
                    "delivered": 480,
                    "opened": 400,
                    "clicked": 200
                },
                "sms": {
                    "sent": 600,
                    "delivered": 590,
                    "failed": 10
                },
                "whatsapp": {
                    "sent": 150,
                    "delivered": 130,
                    "read": 100
                }
            },
            "delivery_rate": 96.0,
            "open_rate": 66.7,
            "click_rate": 25.0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )
    finally:
        tenant_db.close()


# ============================================
# BACKGROUND TASKS
# ============================================

async def process_email_sending(communication_id: str, email_data: dict, tenant_id: str):
    """Background task to process email sending"""
    logger.info(f"Processing email {communication_id} for tenant {tenant_id}")
    # TODO: Implement actual email sending logic
    # 1. Connect to email service provider
    # 2. Send email
    # 3. Update communication record with status
    # 4. Handle errors and retries


async def process_sms_sending(communication_id: str, sms_data: dict, tenant_id: str):
    """Background task to process SMS sending"""
    logger.info(f"Processing SMS {communication_id} for tenant {tenant_id}")
    # TODO: Implement actual SMS sending logic
    # 1. Connect to SMS service provider
    # 2. Send SMS
    # 3. Update communication record with status
    # 4. Handle errors and retries


async def process_whatsapp_sending(communication_id: str, whatsapp_data: dict, tenant_id: str):
    """Background task to process WhatsApp sending"""
    logger.info(f"Processing WhatsApp message {communication_id} for tenant {tenant_id}")
    # TODO: Implement actual WhatsApp sending logic
    # 1. Connect to WhatsApp Business API
    # 2. Send message
    # 3. Update communication record with status
    # 4. Handle errors and retries


async def process_bulk_communication(job_id: str, bulk_data: dict, tenant_id: str):
    """Background task to process bulk communication"""
    logger.info(f"Processing bulk job {job_id} for tenant {tenant_id}")
    # TODO: Implement bulk sending logic
    # 1. Process recipients in batches
    # 2. Apply delays between batches
    # 3. Track individual sending status
    # 4. Update job status
