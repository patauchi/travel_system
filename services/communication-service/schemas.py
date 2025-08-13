"""
Pydantic Schemas for Communication Service
Request/Response models for API endpoints
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
# CHANNEL SCHEMAS
# ============================================

class ChannelBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    type: str = Field(default='public', max_length=50)
    max_members: Optional[int] = None


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_archived: Optional[bool] = None
    is_read_only: Optional[bool] = None
    max_members: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class ChannelResponse(ChannelBase):
    id: int
    is_archived: bool
    is_read_only: bool
    created_by: UUID
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]
    member_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ============================================
# CHANNEL MEMBER SCHEMAS
# ============================================

class ChannelMemberBase(BaseModel):
    user_id: UUID
    role: str = Field(default='member', max_length=50)
    nickname: Optional[str] = Field(None, max_length=100)


class ChannelMemberAdd(ChannelMemberBase):
    pass


class ChannelMemberUpdate(BaseModel):
    role: Optional[str] = Field(None, max_length=50)
    nickname: Optional[str] = Field(None, max_length=100)
    is_muted: Optional[bool] = None
    notification_level: Optional[str] = Field(None, max_length=50)


class ChannelMemberResponse(ChannelMemberBase):
    id: int
    channel_id: int
    is_muted: bool
    notification_level: str
    last_read_at: Optional[datetime]
    last_read_entry_id: Optional[int]
    unread_count: int
    joined_at: datetime
    left_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================
# CHAT ENTRY SCHEMAS
# ============================================

class ChatEntryBase(BaseModel):
    type: str = Field(default='message', max_length=50)
    content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    reply_to_id: Optional[int] = None


class ChatEntryCreate(ChatEntryBase):
    mentions: Optional[List[UUID]] = []


class ChatEntryUpdate(BaseModel):
    content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ChatEntryResponse(ChatEntryBase):
    id: int
    channel_id: int
    user_id: Optional[UUID]
    edited_at: Optional[datetime]
    edited_by: Optional[UUID]
    edit_history: Optional[List[Dict[str, Any]]]
    is_pinned: bool
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    reactions: Optional[Dict[str, List[str]]]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# MENTION SCHEMAS
# ============================================

class MentionResponse(BaseModel):
    id: int
    entry_id: int
    mentioned_user_id: UUID
    mention_type: str
    position: Optional[int]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# PAGINATION
# ============================================

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int = 1
    per_page: int = 100
    pages: int = 1


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


class ChannelStats(BaseModel):
    total_channels: int
    active_channels: int
    total_members: int
    total_messages: int
    active_users_today: int


# ============================================
# WEBHOOK PAYLOADS
# ============================================

class WebhookPayload(BaseModel):
    event: str
    timestamp: datetime
    data: Dict[str, Any]


class IncomingWebhook(BaseModel):
    channel: ChannelTypeEnum
    external_id: Optional[str]
    from_number: Optional[str]
    from_email: Optional[str]
    message: str
    media_urls: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}
