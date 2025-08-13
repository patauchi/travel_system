"""
Inbox Schemas
Pydantic schemas for inbox-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================
# ENUMS
# ============================================

class ChannelTypeEnum(str, Enum):
    whatsapp = "whatsapp"
    messenger = "messenger"
    instagram = "instagram"
    email = "email"
    web = "web"
    twilio_whatsapp = "twilio_whatsapp"
    twilio_call = "twilio_call"
    whatsapp_business = "whatsapp_business"
    facebook_messenger = "facebook_messenger"
    personal_whatsapp = "personal_whatsapp"
    gmail = "gmail"
    zendesk = "zendesk"


class ConversationStatusEnum(str, Enum):
    new = "new"
    open = "open"
    replied = "replied"
    qualified = "qualified"
    archived = "archived"


class PriorityEnum(str, Enum):
    high = "high"
    normal = "normal"
    low = "low"


class MessageDirectionEnum(str, Enum):
    in_direction = "in"
    out_direction = "out"


class MessageTypeEnum(str, Enum):
    text = "text"
    image = "image"
    document = "document"
    audio = "audio"
    video = "video"
    location = "location"


class MessageStatusEnum(str, Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


# ============================================
# INBOX CONVERSATION SCHEMAS
# ============================================

class ConversationBase(BaseModel):
    external_id: Optional[str] = Field(None, max_length=255)
    channel: ChannelTypeEnum
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_identifier: str = Field(..., max_length=255)
    contact_metadata: Optional[Dict[str, Any]] = None
    status: ConversationStatusEnum = ConversationStatusEnum.new
    priority: PriorityEnum = PriorityEnum.normal
    tags: Optional[List[str]] = []
    platform_metadata: Optional[Dict[str, Any]] = {}


class ConversationCreate(ConversationBase):
    first_message: Optional[str] = None


class ConversationUpdate(BaseModel):
    contact_name: Optional[str] = Field(None, max_length=255)
    status: Optional[ConversationStatusEnum] = None
    priority: Optional[PriorityEnum] = None
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
    direction: MessageDirectionEnum
    type: MessageTypeEnum = MessageTypeEnum.text
    content: Optional[str] = None
    media_url: Optional[str] = Field(None, max_length=500)


class MessageCreate(MessageBase):
    conversation_id: Optional[int] = None


class MessageUpdate(BaseModel):
    status: MessageStatusEnum


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    status: MessageStatusEnum
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
    is_active: bool = True


class QuickReplyCreate(QuickReplyBase):
    pass


class QuickReplyUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
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
    channel: ChannelTypeEnum
    external_id: Optional[str]
    from_number: Optional[str]
    from_email: Optional[str]
    message: str
    media_urls: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
