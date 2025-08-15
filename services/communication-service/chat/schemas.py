"""
Chat Schemas
Pydantic schemas for chat-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from common.enums import (
    ChatChannelType,
    MemberRole,
    NotificationLevel,
    EntryType,
    MentionType
)


# Note: Enums are now imported from common.enums


# ============================================
# CHANNEL SCHEMAS
# ============================================

class ChannelBase(BaseModel):
    name: str = Field(..., max_length=255)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    type: str = "public"
    max_members: Optional[int] = None

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['public', 'private', 'direct']
        if v not in valid_types:
            raise ValueError(f'type must be one of {valid_types}')
        return v


class ChannelCreate(ChannelBase):
    initial_members: Optional[List[UUID]] = []


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
    created_by: Optional[UUID]
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime]
    member_count: Optional[int] = 0
    unread_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ============================================
# CHANNEL MEMBER SCHEMAS
# ============================================

class ChannelMemberBase(BaseModel):
    user_id: UUID
    role: MemberRole = MemberRole.member
    nickname: Optional[str] = Field(None, max_length=100)


class ChannelMemberAdd(ChannelMemberBase):
    pass


class ChannelMemberUpdate(BaseModel):
    role: Optional[MemberRole] = None
    nickname: Optional[str] = Field(None, max_length=100)
    is_muted: Optional[bool] = None
    notification_level: Optional[NotificationLevel] = None


class ChannelMemberResponse(ChannelMemberBase):
    id: int
    channel_id: int
    is_muted: bool
    notification_level: NotificationLevel
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
    content: str = Field(..., min_length=1)
    type: EntryType = EntryType.message
    attachments: Optional[List[Dict[str, Any]]] = []
    reply_to_id: Optional[int] = None


class ChatEntryCreate(ChatEntryBase):
    mentions: Optional[List[UUID]] = []


class ChatEntryUpdate(BaseModel):
    content: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ReactionAdd(BaseModel):
    emoji: str = Field(..., max_length=10)


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
    mentions: Optional[List['MentionResponse']] = []

    class Config:
        from_attributes = True


# ============================================
# MENTION SCHEMAS
# ============================================

class MentionResponse(BaseModel):
    id: int
    entry_id: int
    mentioned_user_id: UUID
    mention_type: MentionType
    position_start: Optional[int]
    position_end: Optional[int]
    is_read: bool
    notified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# TYPING INDICATOR SCHEMAS
# ============================================

class TypingIndicator(BaseModel):
    channel_id: int
    user_id: UUID
    is_typing: bool


# ============================================
# PRESENCE SCHEMAS
# ============================================

class UserPresence(BaseModel):
    user_id: UUID
    status: str = Field(default='online')  # online, away, busy, offline
    last_seen: Optional[datetime]
    custom_status: Optional[str] = Field(None, max_length=100)


# ============================================
# SEARCH SCHEMAS
# ============================================

class ChatSearchRequest(BaseModel):
    query: str
    channel_ids: Optional[List[int]] = None
    user_ids: Optional[List[UUID]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    has_attachments: Optional[bool] = None
    limit: int = Field(default=50, ge=1, le=200)


class ChatSearchResult(BaseModel):
    entry: ChatEntryResponse
    channel_name: str
    relevance_score: Optional[float]


# ============================================
# STATS AND ANALYTICS
# ============================================

class ChannelStats(BaseModel):
    total_channels: int
    active_channels: int
    total_members: int
    total_messages: int
    active_users_today: int
    messages_today: int
    avg_messages_per_channel: Optional[float]


class UserChatStats(BaseModel):
    user_id: UUID
    total_messages: int
    channels_count: int
    mentions_received: int
    reactions_given: int
    reactions_received: int
    last_active: Optional[datetime]


# ============================================
# NOTIFICATION SCHEMAS
# ============================================

class ChatNotification(BaseModel):
    type: str  # message, mention, reaction, channel_invite
    channel_id: int
    entry_id: Optional[int]
    from_user_id: UUID
    content: Optional[str]
    timestamp: datetime


# ============================================
# PAGINATION
# ============================================

class PaginatedChatEntries(BaseModel):
    entries: List[ChatEntryResponse]
    total: int
    has_more: bool
    next_cursor: Optional[str]


# ============================================
# WEBHOOK PAYLOADS
# ============================================

class ChatWebhookPayload(BaseModel):
    event: str  # message_created, message_edited, message_deleted, member_joined, member_left
    timestamp: datetime
    channel_id: int
    data: Dict[str, Any]


# Update forward references
ChatEntryResponse.model_rebuild()
