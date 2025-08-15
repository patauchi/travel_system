"""
Inbox Endpoints
API endpoints for inbox conversations, messages, and quick replies
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from database import get_tenant_session
from shared_auth import (
    get_current_user,
    check_tenant_slug_access,
    safe_tenant_session,
    validate_tenant_access
)
from .models import InboxConversation, InboxMessage, InboxQuickReply
from .schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    ConversationAssign, ConversationQualify,
    MessageCreate, MessageUpdate, MessageResponse,
    QuickReplyCreate, QuickReplyUpdate, QuickReplyResponse,
    ConversationStats
)

# Create routers
conversations_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/conversations", tags=["Conversations"])
messages_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/messages", tags=["Messages"])
quick_replies_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/quick-replies", tags=["Quick Replies"])

# ============================================
# CONVERSATION ENDPOINTS
# ============================================

@conversations_router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Create conversation
        conversation = InboxConversation(
            **conversation_data.dict()
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        # Convert to response model while still in session
        return ConversationResponse.from_orm(conversation)

@conversations_router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    status: Optional[str] = None,
    channel: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List conversations with filters"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        query = db.query(InboxConversation)

        # Apply filters
        if status:
            query = query.filter(InboxConversation.status == status)
        if channel:
            query = query.filter(InboxConversation.channel == channel)
        if assigned_to:
            query = query.filter(InboxConversation.assigned_to == assigned_to)
        if priority:
            query = query.filter(InboxConversation.priority == priority)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    InboxConversation.subject.ilike(search_pattern),
                    InboxConversation.tags.contains([search])
                )
            )
        if date_from:
            query = query.filter(InboxConversation.created_at >= date_from)
        if date_to:
            query = query.filter(InboxConversation.created_at <= date_to)

        # Get results with pagination
        conversations = query.order_by(
            desc(InboxConversation.updated_at)
        ).offset(skip).limit(limit).all()

        return conversations

@conversations_router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation statistics"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Get stats
        total = db.query(InboxConversation).count()
        open_count = db.query(InboxConversation).filter(
            InboxConversation.status == 'open'
        ).count()
        pending_count = db.query(InboxConversation).filter(
            InboxConversation.status == 'pending'
        ).count()
        resolved_count = db.query(InboxConversation).filter(
            InboxConversation.status == 'resolved'
        ).count()

        # Average response time (simplified)
        avg_response_time = 3600  # Default to 1 hour

        return ConversationStats(
            total_conversations=total,
            open_conversations=open_count,
            pending_conversations=pending_count,
            resolved_conversations=resolved_count,
            average_response_time=avg_response_time
        )

@conversations_router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return conversation

@conversations_router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(conversation, field, value)

        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

        # Convert to response model while still in session
        return ConversationResponse.from_orm(conversation)

@conversations_router.post("/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation(
    conversation_id: UUID,
    assignment: ConversationAssign,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign a conversation to a user"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.assigned_to = assign_data.assigned_to
        conversation.status = 'assigned'
        conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(conversation)

        # Convert to response model while still in session
        return ConversationResponse.from_orm(conversation)

@conversations_router.post("/{conversation_id}/qualify", response_model=ConversationResponse)
async def qualify_conversation(
    conversation_id: UUID,
    qualification: ConversationQualify,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Qualify a conversation (mark as qualified lead)"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.is_qualified = qualify_data.is_qualified
        if qualify_data.qualification_score:
            conversation.qualification_score = qualify_data.qualification_score
        if qualify_data.notes:
            if not conversation.metadata:
                conversation.metadata = {}
            conversation.metadata['qualification_notes'] = qualify_data.notes

        conversation.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

        # Convert to response model while still in session
        return ConversationResponse.from_orm(conversation)

@conversations_router.post("/{conversation_id}/read", response_model=ConversationResponse)
async def mark_conversation_read(
    conversation_id: int,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a conversation as read"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.is_read = True
        conversation.read_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

        # Convert to response model while still in session
        return ConversationResponse.from_orm(conversation)

@conversations_router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    conversation_update: ConversationUpdate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Update a conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conversation.is_archived = True
        conversation.archived_at = datetime.utcnow()
        db.commit()
        db.refresh(conversation)

        return conversation

# ============================================
# MESSAGE ENDPOINTS
# ============================================

@messages_router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new message in a conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Verify conversation exists
        conversation = db.query(InboxConversation).filter(
            InboxConversation.id == message_data.conversation_id
        ).first()

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Create message
        message = InboxMessage(
            **message_data.dict()
        )
        db.add(message)

        # Update conversation
        conversation.updated_at = datetime.utcnow()
        conversation.message_count = (conversation.message_count or 0) + 1
        conversation.last_message_at = datetime.utcnow()

        # Update status based on message direction
        if message_data.direction == 'in' and conversation.status == 'resolved':
            conversation.status = 'reopened'
        elif message_data.direction == 'out' and conversation.status == 'open':
            conversation.status = 'pending'

        db.commit()
        db.refresh(message)

        # Convert to response model while still in session
        return MessageResponse.from_orm(message)

@messages_router.get("/", response_model=List[MessageResponse])
async def list_messages(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    conversation_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Delete a quick reply"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        query = db.query(InboxMessage)

        if conversation_id:
            query = query.filter(InboxMessage.conversation_id == conversation_id)

        messages = query.order_by(
            desc(InboxMessage.created_at)
        ).offset(skip).limit(limit).all()

        return messages

@messages_router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def list_conversation_messages(
    conversation_id: int,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List all messages in a conversation"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        messages = db.query(InboxMessage).filter(
            InboxMessage.conversation_id == conversation_id
        ).order_by(InboxMessage.created_at).offset(skip).limit(limit).all()

        # Convert to response models while still in session
        return [MessageResponse.from_orm(msg) for msg in messages]

@messages_router.put("/{message_id}", response_model=MessageResponse)
async def update_message_status(
    message_id: int,
    update_data: MessageUpdate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """List messages with optional filters"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        message = db.query(InboxMessage).filter(
            InboxMessage.id == message_id
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        if update_data.status:
            message.status = update_data.status
        if update_data.is_read is not None:
            message.is_read = update_data.is_read

        db.commit()
        db.refresh(message)

        # Convert to response model while still in session
        return MessageResponse.from_orm(message)

@messages_router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Update message status"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        message = db.query(InboxMessage).filter(
            InboxMessage.id == message_id
        ).first()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        db.delete(message)
        db.commit()

# ============================================
# QUICK REPLY ENDPOINTS
# ============================================

@quick_replies_router.post("/", response_model=QuickReplyResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_reply(
    reply_data: QuickReplyCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a quick reply template"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if title already exists (use title as unique identifier)
        existing = db.query(InboxQuickReply).filter(
            InboxQuickReply.title == reply_data.title
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Title already exists")

        quick_reply = InboxQuickReply(
            **reply_data.dict()
        )
        db.add(quick_reply)
        db.commit()
        db.refresh(quick_reply)

        # Convert to response model while still in session
        return QuickReplyResponse.from_orm(quick_reply)

@quick_replies_router.get("/", response_model=List[QuickReplyResponse])
async def list_quick_replies(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    category: Optional[str] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Delete a message"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        query = db.query(InboxQuickReply)

        # Apply filters
        if category:
            query = query.filter(InboxQuickReply.category == category)
        if is_active is not None:
            query = query.filter(InboxQuickReply.is_active == is_active)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    InboxQuickReply.title.ilike(search_pattern),
                    InboxQuickReply.content.ilike(search_pattern)
                )
            )

        quick_replies = query.order_by(
            InboxQuickReply.category, InboxQuickReply.title
        ).offset(skip).limit(limit).all()

        return quick_replies

@quick_replies_router.get("/{reply_id}", response_model=QuickReplyResponse)
async def get_quick_reply(
    reply_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific quick reply"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        quick_reply = db.query(InboxQuickReply).filter(
            InboxQuickReply.id == reply_id
        ).first()

        if not quick_reply:
            raise HTTPException(status_code=404, detail="Quick reply not found")

        return quick_reply

@quick_replies_router.put("/{reply_id}", response_model=QuickReplyResponse)
async def update_quick_reply(
    reply_id: UUID,
    update_data: QuickReplyUpdate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """List quick reply templates with filters"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        quick_reply = db.query(InboxQuickReply).filter(
            InboxQuickReply.id == reply_id
        ).first()

        if not quick_reply:
            raise HTTPException(status_code=404, detail="Quick reply not found")

        # Check if new title conflicts
        if update_data.title and update_data.title != quick_reply.title:
            existing = db.query(InboxQuickReply).filter(
                InboxQuickReply.title == update_data.title,
                InboxQuickReply.id != reply_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Title already exists")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(quick_reply, field, value)

        quick_reply.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(quick_reply)

        # Convert to response model while still in session
        return QuickReplyResponse.from_orm(quick_reply)

@quick_replies_router.delete("/{reply_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quick_reply(
    reply_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Update a quick reply"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        quick_reply = db.query(InboxQuickReply).filter(
            InboxQuickReply.id == reply_id
        ).first()

        if not quick_reply:
            raise HTTPException(status_code=404, detail="Quick reply not found")

        db.delete(quick_reply)
        db.commit()
