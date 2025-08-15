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

    def __repr__(self):
        try:
            return f"<Channel {self.id}>"
        except:
            return f"<Channel (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "type": self.type,
            "is_archived": self.is_archived,
            "is_read_only": self.is_read_only,
            "max_members": self.max_members,
            "created_by": str(self.created_by) if self.created_by else None,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None
        }

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

    def __repr__(self):
        try:
            return f"<ChannelMember {self.id}>"
        except:
            return f"<ChannelMember (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "role": self.role,
            "nickname": self.nickname,
            "is_muted": self.is_muted,
            "notification_level": self.notification_level,
            "last_read_at": self.last_read_at.isoformat() if self.last_read_at else None,
            "last_read_entry_id": self.last_read_entry_id,
            "unread_count": self.unread_count,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "left_at": self.left_at.isoformat() if self.left_at else None
        }

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
    reply_to = relationship("ChatEntry", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_entry_channel', 'channel_id'),
        Index('idx_entry_user', 'user_id'),
        Index('idx_entry_created', 'created_at'),
        Index('idx_entry_reply', 'reply_to_id'),
        Index('idx_entry_type', 'type'),
    )

    def __repr__(self):
        try:
            return f"<ChatEntry {self.id}>"
        except:
            return f"<ChatEntry (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "type": self.type,
            "content": self.content,
            "attachments": self.attachments,
            "reply_to_id": self.reply_to_id,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "edited_by": str(self.edited_by) if self.edited_by else None,
            "edit_history": self.edit_history,
            "is_pinned": self.is_pinned,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "reactions": self.reactions,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

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
    mentioned_by = Column(UUID(as_uuid=True), nullable=True)  # References users.id but no FK constraint

    # Mention info
    mention_type = Column(String(20), default='user')  # user, channel, everyone, here
    position_start = Column(Integer, nullable=True)  # Start position in message content
    position_end = Column(Integer, nullable=True)  # End position in message content

    # Notification tracking
    is_read = Column(Boolean, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    entry = relationship("ChatEntry", back_populates="mentions")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_mention_entry_id', 'entry_id'),
        Index('idx_mention_user_id', 'mentioned_user_id'),
        Index('idx_mention_created_at', 'created_at'),
    )

    def __repr__(self):
        try:
            return f"<Mention {self.id}>"
        except:
            return f"<Mention (detached)>"

    def to_dict(self):
        return {
            "id": self.id,
            "entry_id": self.entry_id,
            "mentioned_user_id": str(self.mentioned_user_id) if self.mentioned_user_id else None,
            "mentioned_by": str(self.mentioned_by) if self.mentioned_by else None,
            "mention_type": self.mention_type,
            "position_start": self.position_start,
            "position_end": self.position_end,
            "is_read": self.is_read,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
