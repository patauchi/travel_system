"""
Inbox Models
SQLAlchemy models for inbox conversations and messages
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

# ============================================
# ENUMS
# ============================================

class ChannelType(str, enum.Enum):
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

class ConversationStatus(str, enum.Enum):
    new = "new"
    open = "open"
    replied = "replied"
    qualified = "qualified"
    archived = "archived"

class Priority(str, enum.Enum):
    high = "high"
    normal = "normal"
    low = "low"

class MessageDirection(str, enum.Enum):
    in_direction = "in"
    out = "out"

class MessageType(str, enum.Enum):
    text = "text"
    image = "image"
    document = "document"
    audio = "audio"
    video = "video"
    location = "location"

class MessageStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"

# ============================================
# INBOX CONVERSATIONS TABLE
# ============================================

class InboxConversation(Base):
    """Inbox conversations from multiple channels"""
    __tablename__ = "inbox_conversations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identification
    external_id = Column(String(255), nullable=True, comment='ID from external platform (WhatsApp, Messenger, etc)')
    channel = Column(SQLEnum(ChannelType), nullable=False)

    # Contact Information
    contact_name = Column(String(255), nullable=True)
    contact_identifier = Column(String(255), nullable=False, comment='Email or phone number')
    contact_metadata = Column(JSONB, nullable=True, comment='Additional contact data from platform')

    # Status
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.new)
    priority = Column(SQLEnum(Priority), default=Priority.normal)
    is_spam = Column(Boolean, default=False)

    # Content
    first_message = Column(Text, nullable=True)
    last_message = Column(Text, nullable=True)
    message_count = Column(Integer, default=1)
    unread_count = Column(Integer, default=0)

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Conversion
    is_lead = Column(Boolean, default=False)
    lead_id = Column(Integer, nullable=True)  # Would reference leads table
    qualified_at = Column(DateTime(timezone=True), nullable=True)
    qualified_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Metadata
    tags = Column(JSONB, nullable=True, comment='Tags for categorization')
    platform_metadata = Column(JSONB, nullable=True, comment='Platform-specific metadata')

    # Timestamps
    last_message_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages = relationship("InboxMessage", back_populates="conversation", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_inbox_channel', 'channel'),
        Index('idx_inbox_status', 'status'),
        Index('idx_inbox_assigned_to', 'assigned_to'),
        Index('idx_inbox_contact_identifier', 'contact_identifier'),
        Index('idx_inbox_created_at', 'created_at'),
        Index('idx_inbox_lead', 'is_lead', 'lead_id'),
        Index('idx_inbox_view', 'status', 'assigned_to', 'created_at'),
        Index('idx_unread', 'status', 'unread_count', 'assigned_to'),
        Index('idx_search', 'contact_identifier', 'contact_name'),
        Index('idx_duplicate_check', 'channel', 'contact_identifier', 'created_at'),
    )

    def __repr__(self):
        try:
            return f"<InboxConversation {self.id}>"
        except:
            return f"<InboxConversation (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "external_id": self.external_id,
            "channel": self.channel.value if self.channel else None,
            "contact_name": self.contact_name,
            "contact_identifier": self.contact_identifier,
            "contact_metadata": self.contact_metadata,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "is_spam": self.is_spam,
            "first_message": self.first_message,
            "last_message": self.last_message,
            "message_count": self.message_count,
            "unread_count": self.unread_count,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "is_lead": self.is_lead,
            "lead_id": self.lead_id,
            "qualified_at": self.qualified_at.isoformat() if self.qualified_at else None,
            "qualified_by": str(self.qualified_by) if self.qualified_by else None,
            "tags": self.tags,
            "platform_metadata": self.platform_metadata,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None
        }

# ============================================
# INBOX MESSAGES TABLE
# ============================================

class InboxMessage(Base):
    """Individual messages within conversations"""
    __tablename__ = "inbox_messages"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationship
    conversation_id = Column(Integer, ForeignKey('inbox_conversations.id', ondelete='CASCADE'), nullable=False)

    # Message Identification
    external_id = Column(String(255), nullable=True, comment='ID from the external platform')
    direction = Column(SQLEnum(MessageDirection), nullable=False, comment='Incoming or outgoing message')
    type = Column(SQLEnum(MessageType), default=MessageType.text)

    # Content
    content = Column(Text, nullable=True)
    media_url = Column(String(500), nullable=True)

    # Status
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.sent)
    status_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    conversation = relationship("InboxConversation", back_populates="messages")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_message_conversation_id', 'conversation_id'),
        Index('idx_message_created_at', 'created_at'),
        Index('idx_message_external_id', 'external_id'),
        Index('idx_conversation_timeline', 'conversation_id', 'created_at'),
    )

    def __repr__(self):
        try:
            return f"<InboxMessage {self.id}>"
        except:
            return f"<InboxMessage (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "external_id": self.external_id,
            "direction": self.direction.value if self.direction else None,
            "type": self.type.value if self.type else None,
            "content": self.content,
            "media_url": self.media_url,
            "status": self.status.value if self.status else None,
            "status_updated_at": self.status_updated_at.isoformat() if self.status_updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

# ============================================
# INBOX QUICK REPLIES TABLE
# ============================================

class InboxQuickReply(Base):
    """Pre-defined quick reply templates"""
    __tablename__ = "inbox_quick_replies"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic fields
    title = Column(String(100), nullable=False, comment='Short title for the quick reply')
    content = Column(Text, nullable=False, comment='The actual message content')
    category = Column(String(50), nullable=True, comment='Category for grouping')
    language = Column(String(10), nullable=True, default='en', comment='Language code (en, es, fr, etc.)')
    shortcuts = Column(JSONB, nullable=True, comment='Keyboard shortcuts for quick access')
    is_active = Column(Boolean, default=True)

    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_quick_reply_category', 'category'),
        Index('idx_quick_reply_language', 'language'),
        Index('idx_quick_reply_usage', 'usage_count'),
    )

    def __repr__(self):
        try:
            return f"<InboxQuickReply {self.id}>"
        except:
            return f"<InboxQuickReply (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "language": self.language or 'en',
            "shortcuts": self.shortcuts,
            "usage_count": self.usage_count if self.usage_count is not None else 0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.utcnow().isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.utcnow().isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }
