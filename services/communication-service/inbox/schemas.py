"""
Inbox Schemas
Pydantic schemas for inbox-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from common.enums import (
    ChannelType,
    ConversationStatus,
    Priority,
    MessageDirection,
    MessageType,
    MessageStatus
)


# Note: Enums are now imported from common.enums


# ============================================
# INBOX CONVERSATION SCHEMAS
# ============================================

class ConversationBase(BaseModel):
    external_id: Optional[str] = Field(None, max_length=255)
    channel: ChannelType
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_identifier: str = Field(..., max_length=255)
    contact_metadata: Optional[Dict[str, Any]] = None
    status: ConversationStatus = ConversationStatus.new
    priority: Priority = Priority.normal
    tags: Optional[List[str]] = []
    platform_metadata: Optional[Dict[str, Any]] = {}


class ConversationCreate(ConversationBase):
    first_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    contact_name: Optional[str] = Field(None, max_length=255)
    status: Optional[ConversationStatus] = None
    priority: Optional[Priority] = None
    is_spam: Optional[bool] = None
    tags: Optional[List[str]] = None
    platform_metadata: Optional[Dict[str, Any]] = None


class ConversationAssign(BaseModel):
    assigned_to: UUID


class ConversationQualify(BaseModel):
    is_lead: bool = True
    lead_id: Optional[int] = None


class ConversationResponse(ConversationBase):
    id: int
    is_spam: bool
    first_message: Optional[str]
    last_message: Optional[str]
    message_count: int
    unread_count: int
    assigned_to: Optional[UUID]
    assigned_at: Optional[datetime]
    is_lead: bool
    lead_id: Optional[int]
    qualified_at: Optional[datetime]
    qualified_by: Optional[UUID]
    last_message_at: datetime
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# INBOX MESSAGE SCHEMAS
# ============================================

class MessageBase(BaseModel):
    external_id: Optional[str] = Field(None, max_length=255)
    direction: MessageDirection
    type: MessageType = MessageType.text
    content: Optional[str] = None
    media_url: Optional[str] = Field(None, max_length=500)


class MessageCreate(MessageBase):
    conversation_id: Optional[int] = None


class MessageUpdate(BaseModel):
    status: MessageStatus


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    status: MessageStatus
    status_updated_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# QUICK REPLY SCHEMAS
# ============================================

class QuickReplyBase(BaseModel):
    title: str = Field(..., max_length=100)
    content: str
    category: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    shortcuts: Optional[List[str]] = None
    is_active: bool = True


class QuickReplyCreate(QuickReplyBase):
    pass


class QuickReplyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    shortcuts: Optional[List[str]] = None
    is_active: Optional[bool] = None


class QuickReplyResponse(QuickReplyBase):
    id: int
    usage_count: int
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================
# STATS AND ANALYTICS
# ============================================

class ConversationStats(BaseModel):
    total_conversations: int
    new_conversations: int
    open_conversations: int
    replied_conversations: int
    qualified_conversations: int
    archived_conversations: int
    avg_response_time: Optional[float]
    total_messages: int
    unread_messages: int


# ============================================
# WEBHOOK PAYLOADS
# ============================================

class IncomingWebhook(BaseModel):
    channel: ChannelType
    external_id: Optional[str]
    from_number: Optional[str]
    from_email: Optional[str]
    message: str
    media_urls: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
