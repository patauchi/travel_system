"""
Chat Models
SQLAlchemy models for chat channels, members, and entries
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# ============================================
# CHANNELS TABLE (for chat feature)
# ============================================

class Channel(Base):
    """Chat channels for internal communication"""
    __tablename__ = "channels"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Channel info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), default='public')  # public, private, direct

    # Settings
    is_archived = Column(Boolean, default=False)
    is_read_only = Column(Boolean, default=False)
    max_members = Column(Integer, nullable=True)

    # Creator
    created_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Metadata
    settings = Column(JSONB, default={})

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    entries = relationship("ChatEntry", back_populates="channel", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_channel_slug', 'slug'),
        Index('idx_channel_type', 'type'),
        Index('idx_channel_archived', 'is_archived'),
    )

# ============================================
# CHANNEL MEMBERS TABLE
# ============================================

class ChannelMember(Base):
    """Members of chat channels"""
    __tablename__ = "channel_members"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    channel_id = Column(Integer, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Member info
    role = Column(String(50), default='member')  # admin, moderator, member
    nickname = Column(String(100), nullable=True)

    # Settings
    is_muted = Column(Boolean, default=False)
    notification_level = Column(String(50), default='all')  # all, mentions, none

    # Status
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    last_read_entry_id = Column(Integer, nullable=True)
    unread_count = Column(Integer, default=0)

    # Timestamps
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    left_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    channel = relationship("Channel", back_populates="members")

    # Table arguments for unique constraint and indexes
    __table_args__ = (
        UniqueConstraint('channel_id', 'user_id', name='uq_channel_member'),
        Index('idx_member_channel', 'channel_id'),
        Index('idx_member_user', 'user_id'),
        Index('idx_member_role', 'role'),
    )

# ============================================
# CHAT ENTRIES TABLE
# ============================================

class ChatEntry(Base):
    """Messages/entries in chat channels"""
    __tablename__ = "chat_entries"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    channel_id = Column(Integer, ForeignKey('channels.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Message content
    type = Column(String(50), default='message')  # message, join, leave, system
    content = Column(Text, nullable=True)

    # Attachments
    attachments = Column(JSONB, nullable=True)  # Array of attachment objects

    # Reply
    reply_to_id = Column(Integer, ForeignKey('chat_entries.id', ondelete='SET NULL'), nullable=True)

    # Edit history
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edited_by = Column(UUID(as_uuid=True), nullable=True)
    edit_history = Column(JSONB, nullable=True)

    # Status
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)

    # Reactions
    reactions = Column(JSONB, nullable=True)  # {emoji: [user_ids]}

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    channel = relationship("Channel", back_populates="entries")
    mentions = relationship("Mention", back_populates="entry", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_entry_channel', 'channel_id'),
        Index('idx_entry_user', 'user_id'),
        Index('idx_entry_created', 'created_at'),
        Index('idx_entry_type', 'type'),
        Index('idx_entry_reply', 'reply_to_id'),
        Index('idx_channel_timeline', 'channel_id', 'created_at'),
    )

# ============================================
# MENTIONS TABLE
# ============================================

class Mention(Base):
    """User mentions in chat entries"""
    __tablename__ = "mentions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    entry_id = Column(Integer, ForeignKey('chat_entries.id', ondelete='CASCADE'), nullable=False)
    mentioned_user_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Mention info
    mention_type = Column(String(50), default='user')  # user, everyone, here
    position = Column(Integer, nullable=True)  # Position in text where mention appears

    # Read status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    entry = relationship("ChatEntry", back_populates="mentions")

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('entry_id', 'mentioned_user_id', name='uq_entry_mention'),
        Index('idx_mention_entry', 'entry_id'),
        Index('idx_mention_user', 'mentioned_user_id'),
        Index('idx_mention_unread', 'mentioned_user_id', 'is_read'),
    )
