"""
Inbox Endpoints
API endpoints for inbox conversations, messages, and quick replies
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from database import get_tenant_db
from .models import InboxConversation, InboxMessage, InboxQuickReply
from .schemas import (
    ConversationCreate, ConversationUpdate, ConversationAssign, ConversationQualify, ConversationResponse,
    MessageCreate, MessageUpdate, MessageResponse,
    QuickReplyCreate, QuickReplyUpdate, QuickReplyResponse,
    ConversationStats
)

# Create routers
conversations_router = APIRouter(prefix="/api/v1/communications/conversations", tags=["Conversations"])
messages_router = APIRouter(prefix="/api/v1/communications/messages", tags=["Messages"])
quick_replies_router = APIRouter(prefix="/api/v1/communications/quick-replies", tags=["Quick Replies"])

# ============================================
# CONVERSATION ENDPOINTS
# ============================================

@conversations_router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Create a new conversation"""
    # Check if conversation already exists
    existing = db.query(InboxConversation).filter(
        InboxConversation.channel == conversation_data.channel,
        InboxConversation.contact_identifier == conversation_data.contact_identifier,
        InboxConversation.archived_at.is_(None)
    ).first()

    if existing:
        return existing

    conversation = InboxConversation(**conversation_data.dict())
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation

@conversations_router.get("/", response_model=List[ConversationResponse])
async def list_conversations(
    tenant_slug: str = Query(..., description="Tenant identifier"),
    channel: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    is_spam: Optional[bool] = None,
    is_lead: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List conversations with filters"""
    query = db.query(InboxConversation)

    if channel:
        query = query.filter(InboxConversation.channel == channel)
    if status:
        query = query.filter(InboxConversation.status == status)
    if assigned_to:
        query = query.filter(InboxConversation.assigned_to == assigned_to)
    if is_spam is not None:
        query = query.filter(InboxConversation.is_spam == is_spam)
    if is_lead is not None:
        query = query.filter(InboxConversation.is_lead == is_lead)

    conversations = query.order_by(desc(InboxConversation.last_message_at)).offset(skip).limit(limit).all()
    return conversations

@conversations_router.get("/stats", response_model=ConversationStats)
async def get_conversation_stats(
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Get conversation statistics"""
    stats = {
        "total_conversations": db.query(InboxConversation).count(),
        "new_conversations": db.query(InboxConversation).filter(
            InboxConversation.status == "new"
        ).count(),
        "open_conversations": db.query(InboxConversation).filter(
            InboxConversation.status == "open"
        ).count(),
        "replied_conversations": db.query(InboxConversation).filter(
            InboxConversation.status == "replied"
        ).count(),
        "qualified_conversations": db.query(InboxConversation).filter(
            InboxConversation.status == "qualified"
        ).count(),
        "archived_conversations": db.query(InboxConversation).filter(
            InboxConversation.archived_at.isnot(None)
        ).count(),
        "total_messages": db.query(InboxMessage).count(),
        "unread_messages": db.query(func.sum(InboxConversation.unread_count)).scalar() or 0,
        "avg_response_time": None  # Would need to calculate based on messages
    }

    return ConversationStats(**stats)

@conversations_router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Get a specific conversation"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

@conversations_router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    update_data: ConversationUpdate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Update a conversation"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(conversation, field, value)

    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)

    return conversation

@conversations_router.post("/{conversation_id}/assign", response_model=ConversationResponse)
async def assign_conversation(
    conversation_id: int,
    assign_data: ConversationAssign,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Assign a conversation to a user"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.assigned_to = assign_data.assigned_to
    conversation.assigned_at = datetime.utcnow()
    conversation.status = "open"
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(conversation)

    return conversation

@conversations_router.post("/{conversation_id}/qualify", response_model=ConversationResponse)
async def qualify_conversation(
    conversation_id: int,
    qualify_data: ConversationQualify,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Qualify a conversation as lead"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.is_lead = qualify_data.is_lead
    conversation.lead_id = qualify_data.lead_id
    conversation.qualified_at = datetime.utcnow()
    conversation.status = "qualified"
    conversation.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(conversation)

    return conversation

@conversations_router.post("/{conversation_id}/mark-read")
async def mark_conversation_read(
    conversation_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Mark all messages in conversation as read"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.unread_count = 0
    db.commit()

    return {"message": "Conversation marked as read"}

@conversations_router.delete("/{conversation_id}")
async def archive_conversation(
    conversation_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Archive a conversation"""
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.archived_at = datetime.utcnow()
    conversation.status = "archived"
    db.commit()

    return {"message": "Conversation archived successfully"}

# ============================================
# MESSAGE ENDPOINTS
# ============================================

@messages_router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Create a new message"""
    # If conversation_id not provided, find or create conversation
    if not message_data.conversation_id:
        # This would need additional logic to determine conversation from context
        raise HTTPException(status_code=400, detail="conversation_id is required")

    # Verify conversation exists
    conversation = db.query(InboxConversation).filter(
        InboxConversation.id == message_data.conversation_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = InboxMessage(**message_data.dict())
    db.add(message)

    # Update conversation
    conversation.last_message = message_data.content[:100] if message_data.content else None
    conversation.last_message_at = datetime.utcnow()
    conversation.message_count += 1

    if message_data.direction == "in":
        conversation.unread_count += 1
        conversation.status = "new" if conversation.status == "new" else "open"
    else:
        conversation.status = "replied"

    db.commit()
    db.refresh(message)

    return message

@messages_router.get("/conversation/{conversation_id}", response_model=List[MessageResponse])
async def list_conversation_messages(
    conversation_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List messages in a conversation"""
    messages = db.query(InboxMessage).filter(
        InboxMessage.conversation_id == conversation_id
    ).order_by(InboxMessage.created_at).offset(skip).limit(limit).all()

    return messages

@messages_router.put("/{message_id}/status", response_model=MessageResponse)
async def update_message_status(
    message_id: int,
    update_data: MessageUpdate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Update message status"""
    message = db.query(InboxMessage).filter(
        InboxMessage.id == message_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    message.status = update_data.status
    message.status_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)

    return message

@messages_router.delete("/{message_id}")
async def delete_message(
    message_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Delete a message"""
    message = db.query(InboxMessage).filter(
        InboxMessage.id == message_id
    ).first()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()

    return {"message": "Message deleted successfully"}

# ============================================
# QUICK REPLY ENDPOINTS
# ============================================

@quick_replies_router.post("/", response_model=QuickReplyResponse, status_code=status.HTTP_201_CREATED)
async def create_quick_reply(
    reply_data: QuickReplyCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Create a new quick reply"""
    quick_reply = InboxQuickReply(**reply_data.dict())
    db.add(quick_reply)
    db.commit()
    db.refresh(quick_reply)

    return quick_reply

@quick_replies_router.get("/", response_model=List[QuickReplyResponse])
async def list_quick_replies(
    tenant_slug: str = Query(..., description="Tenant identifier"),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List quick replies"""
    query = db.query(InboxQuickReply)

    if category:
        query = query.filter(InboxQuickReply.category == category)
    if is_active is not None:
        query = query.filter(InboxQuickReply.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                InboxQuickReply.title.ilike(f"%{search}%"),
                InboxQuickReply.content.ilike(f"%{search}%")
            )
        )

    replies = query.order_by(InboxQuickReply.category, InboxQuickReply.title).all()
    return replies

@quick_replies_router.get("/{reply_id}", response_model=QuickReplyResponse)
async def get_quick_reply(
    reply_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Get a specific quick reply"""
    quick_reply = db.query(InboxQuickReply).filter(
        InboxQuickReply.id == reply_id
    ).first()

    if not quick_reply:
        raise HTTPException(status_code=404, detail="Quick reply not found")

    return quick_reply

@quick_replies_router.put("/{reply_id}", response_model=QuickReplyResponse)
async def update_quick_reply(
    reply_id: int,
    update_data: QuickReplyUpdate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Update a quick reply"""
    quick_reply = db.query(InboxQuickReply).filter(
        InboxQuickReply.id == reply_id
    ).first()

    if not quick_reply:
        raise HTTPException(status_code=404, detail="Quick reply not found")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(quick_reply, field, value)

    quick_reply.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(quick_reply)

    return quick_reply

@quick_replies_router.post("/{reply_id}/use")
async def use_quick_reply(
    reply_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Mark a quick reply as used"""
    quick_reply = db.query(InboxQuickReply).filter(
        InboxQuickReply.id == reply_id
    ).first()

    if not quick_reply:
        raise HTTPException(status_code=404, detail="Quick reply not found")

    quick_reply.usage_count += 1
    quick_reply.last_used_at = datetime.utcnow()
    db.commit()

    return {"message": "Quick reply usage recorded", "content": quick_reply.content}

@quick_replies_router.delete("/{reply_id}")
async def delete_quick_reply(
    reply_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Delete a quick reply"""
    quick_reply = db.query(InboxQuickReply).filter(
        InboxQuickReply.id == reply_id
    ).first()

    if not quick_reply:
        raise HTTPException(status_code=404, detail="Quick reply not found")

    db.delete(quick_reply)
    db.commit()

    return {"message": "Quick reply deleted successfully"}

# Function to include all inbox routers
def include_inbox_routers(app):
    """Include all inbox routers in the FastAPI app"""
    app.include_router(conversations_router)
    app.include_router(messages_router)
    app.include_router(quick_replies_router)
