"""
Chat Endpoints
API endpoints for chat channels, members, and entries
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import json

from database import get_tenant_session
from shared_auth import (
    get_current_user,
    check_tenant_slug_access,
    safe_tenant_session,
    validate_tenant_access
)
from .models import Channel, ChannelMember, ChatEntry, Mention
from .schemas import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelMemberAdd, ChannelMemberUpdate, ChannelMemberResponse,
    ChatEntryCreate, ChatEntryUpdate, ChatEntryResponse,
    MentionResponse, ChannelStats, ReactionAdd
)

# Create routers
channels_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/channels", tags=["Channels"])
chat_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/chat", tags=["Chat"])

# ============================================
# CHANNEL ENDPOINTS
# ============================================

@channels_router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new channel"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if slug already exists
        existing = db.query(Channel).filter(Channel.slug == channel_data.slug).first()
        if existing:
            raise HTTPException(status_code=400, detail="Channel slug already exists")

        # Create channel
        channel = Channel(
            name=channel_data.name,
            slug=channel_data.slug,
            description=channel_data.description,
            type=channel_data.type,
            max_members=channel_data.max_members,
            created_by=current_user_id
        )
        db.add(channel)
        db.flush()

        # Add creator as admin member
        creator_member = ChannelMember(
            channel_id=channel.id,
            user_id=current_user_id,
            role='admin'
        )
        db.add(creator_member)

        # Add initial members if provided
        for user_id in channel_data.initial_members:
            if user_id != current_user_id:
                member = ChannelMember(
                    channel_id=channel.id,
                    user_id=user_id,
                    role='member'
                )
                db.add(member)

        db.commit()
        db.refresh(channel)

        # Add member count
        channel.member_count = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel.id
        ).count()

        return channel

@channels_router.get("/", response_model=List[ChannelResponse])
async def list_channels(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    type: Optional[str] = None,
    is_archived: Optional[bool] = False,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List channels accessible to the user"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Base query - user's channels
        query = db.query(Channel).join(ChannelMember).filter(
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        )

        # Apply filters
        if type:
            query = query.filter(Channel.type == type)

        if is_archived is not None:
            query = query.filter(Channel.is_archived == is_archived)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Channel.name.ilike(search_pattern),
                    Channel.description.ilike(search_pattern)
                )
            )

        # Get results with pagination
        channels = query.offset(skip).limit(limit).all()

        # Add member counts
        for channel in channels:
            channel.member_count = db.query(ChannelMember).filter(
                ChannelMember.channel_id == channel.id,
                ChannelMember.left_at.is_(None)
            ).count()

        return channels

@channels_router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Get channel details"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is a member
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Add member count
        channel.member_count = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel.id,
            ChannelMember.left_at.is_(None)
        ).count()

        return channel

@channels_router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: UUID,
    update_data: ChannelUpdate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Update channel details (admin only)"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is an admin
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.role == 'admin',
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Only channel admins can update")

        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            setattr(channel, field, value)

        db.commit()
        db.refresh(channel)

        return channel

@channels_router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a channel (admin only)"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is an admin
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.role == 'admin',
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Only channel admins can delete")

        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            raise HTTPException(status_code=404, detail="Channel not found")

        # Archive instead of delete
        channel.is_archived = True
        db.commit()

# ============================================
# CHANNEL MEMBER ENDPOINTS
# ============================================

@channels_router.post("/{channel_id}/members", response_model=ChannelMemberResponse)
async def add_channel_member(
    channel_id: int,
    member_data: ChannelMemberAdd,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a member to the channel"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if current user is an admin
        admin_member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.role == 'admin',
            ChannelMember.left_at.is_(None)
        ).first()

        if not admin_member:
            raise HTTPException(status_code=403, detail="Only admins can add members")

        # Check if user is already a member
        existing = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == member_data.user_id
        ).first()

        if existing:
            if existing.left_at:
                # Rejoin the channel
                existing.left_at = None
                existing.role = member_data.role or 'member'
                db.commit()
                db.refresh(existing)
                return existing
            else:
                raise HTTPException(status_code=400, detail="User is already a member")

        # Check channel member limit
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        if channel.max_members:
            current_count = db.query(ChannelMember).filter(
                ChannelMember.channel_id == channel_id,
                ChannelMember.left_at.is_(None)
            ).count()

            if current_count >= channel.max_members:
                raise HTTPException(status_code=400, detail="Channel member limit reached")

        # Add new member
        new_member = ChannelMember(
            channel_id=channel_id,
            user_id=member_data.user_id,
            role=member_data.role or 'member'
        )
        db.add(new_member)
        db.commit()
        db.refresh(new_member)

        return new_member

@channels_router.get("/{channel_id}/members", response_model=List[ChannelMemberResponse])
async def list_channel_members(
    channel_id: int,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """List channel members"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is a member
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        members = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.left_at.is_(None)
        ).all()

        return members

# ============================================
# CHAT ENTRY ENDPOINTS
# ============================================

@chat_router.post("/channels/{channel_id}/messages", response_model=ChatEntryResponse)
async def send_message(
    channel_id: int,
    message_data: ChatEntryCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Send a message to the channel"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is a member
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        # Create chat entry
        chat_entry = ChatEntry(
            channel_id=channel_id,
            user_id=current_user_id,
            message=message_data.message,
            attachments=message_data.attachments,
            metadata=message_data.metadata or {}
        )
        db.add(chat_entry)
        db.flush()

        # Process mentions
        if message_data.mentions:
            for mentioned_user_id in message_data.mentions:
                mention = Mention(
                    chat_entry_id=chat_entry.id,
                    user_id=mentioned_user_id
                )
                db.add(mention)

        # Update channel last activity
        channel = db.query(Channel).filter(Channel.id == channel_id).first()
        channel.last_activity_at = datetime.utcnow()

        db.commit()
        db.refresh(chat_entry)

        return chat_entry

@chat_router.get("/channels/{channel_id}/messages", response_model=List[ChatEntryResponse])
async def list_messages(
    channel_id: int,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    """List channel messages"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Check if user is a member
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        # Get messages
        messages = db.query(ChatEntry).filter(
            ChatEntry.channel_id == channel_id
        ).order_by(
            desc(ChatEntry.created_at)
        ).offset(skip).limit(limit).all()

        return messages

@chat_router.post("/messages/{message_id}/reactions", response_model=dict)
async def add_reaction(
    message_id: int,
    reaction_data: ReactionAdd,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Add a reaction to a message"""
    # Validate tenant access
    validate_tenant_access(current_user, tenant_slug)

    # Get current user ID
    current_user_id = UUID(current_user.get("id"))

    # Get database session
    with safe_tenant_session(tenant_slug) as db:
        # Get the message
        message = db.query(ChatEntry).filter(ChatEntry.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # Check if user is a member of the channel
        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == message.channel_id,
            ChannelMember.user_id == current_user_id,
            ChannelMember.left_at.is_(None)
        ).first()

        if not member:
            raise HTTPException(status_code=403, detail="Not a member of this channel")

        # Add reaction to metadata
        if not message.metadata:
            message.metadata = {}

        if "reactions" not in message.metadata:
            message.metadata["reactions"] = {}

        emoji = reaction_data.emoji
        if emoji not in message.metadata["reactions"]:
            message.metadata["reactions"][emoji] = []

        user_id_str = str(current_user_id)
        if user_id_str not in message.metadata["reactions"][emoji]:
            message.metadata["reactions"][emoji].append(user_id_str)

        db.commit()

        return {"success": True, "reactions": message.metadata.get("reactions", {})}
