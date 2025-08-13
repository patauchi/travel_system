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
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"
    EMAIL = "email"
    WEB = "web"
    TWILIO_WHATSAPP = "twilio_whatsapp"
    TWILIO_CALL = "twilio_call"
    WHATSAPP_BUSINESS = "whatsapp_business"
    FACEBOOK_MESSENGER = "facebook_messenger"
    PERSONAL_WHATSAPP = "personal_whatsapp"
    GMAIL = "gmail"
    ZENDESK = "zendesk"

class ConversationStatus(str, enum.Enum):
    NEW = "new"
    OPEN = "open"
    REPLIED = "replied"
    QUALIFIED = "qualified"
    ARCHIVED = "archived"

class Priority(str, enum.Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class MessageDirection(str, enum.Enum):
    IN = "in"
    OUT = "out"

class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

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
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.NEW)
    priority = Column(SQLEnum(Priority), default=Priority.NORMAL)
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
    type = Column(SQLEnum(MessageType), default=MessageType.TEXT)

    # Content
    content = Column(Text, nullable=True)
    media_url = Column(String(500), nullable=True)

    # Status
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT)
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
        Index('idx_quick_reply_active', 'is_active'),
    )
