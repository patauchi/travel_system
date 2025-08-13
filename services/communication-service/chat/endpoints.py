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

from database import get_tenant_db
from .models import Channel, ChannelMember, ChatEntry, Mention
from .schemas import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelMemberAdd, ChannelMemberUpdate, ChannelMemberResponse,
    ChatEntryCreate, ChatEntryUpdate, ChatEntryResponse,
    MentionResponse, ChannelStats, ReactionAdd
)

# Create routers
channels_router = APIRouter(prefix="/api/v1/communications/channels", tags=["Channels"])
chat_router = APIRouter(prefix="/api/v1/communications/chat", tags=["Chat"])

# ============================================
# CHANNEL ENDPOINTS
# ============================================

@channels_router.post("/", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),  # In production, get from auth
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Create a new channel"""
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
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    type: Optional[str] = None,
    is_archived: Optional[bool] = False,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List channels accessible to the user"""
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
        query = query.filter(
            or_(
                Channel.name.ilike(f"%{search}%"),
                Channel.description.ilike(f"%{search}%")
            )
        )

    channels = query.order_by(desc(Channel.updated_at)).offset(skip).limit(limit).all()

    # Add member count and unread count for each channel
    for channel in channels:
        channel.member_count = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel.id,
            ChannelMember.left_at.is_(None)
        ).count()

        member = db.query(ChannelMember).filter(
            ChannelMember.channel_id == channel.id,
            ChannelMember.user_id == current_user_id
        ).first()
        channel.unread_count = member.unread_count if member else 0

    return channels

@channels_router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Get a specific channel"""
    # Verify user is a member
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

    channel.member_count = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel.id,
        ChannelMember.left_at.is_(None)
    ).count()
    channel.unread_count = member.unread_count

    return channel

@channels_router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    update_data: ChannelUpdate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Update a channel (admin/moderator only)"""
    # Verify user is an admin or moderator
    member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.role.in_(['admin', 'moderator'])
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(channel, field, value)

    channel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(channel)

    return channel

@channels_router.delete("/{channel_id}")
async def delete_channel(
    channel_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Delete a channel (admin only)"""
    # Verify user is an admin
    member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.role == 'admin'
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only channel admin can delete the channel")

    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")

    db.delete(channel)
    db.commit()

    return {"message": "Channel deleted successfully"}

# ============================================
# CHANNEL MEMBER ENDPOINTS
# ============================================

@channels_router.post("/{channel_id}/members", response_model=ChannelMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_channel_member(
    channel_id: int,
    member_data: ChannelMemberAdd,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Add a member to a channel"""
    # Verify current user is a member with appropriate permissions
    current_member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.role.in_(['admin', 'moderator'])
    ).first()

    if not current_member:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Check if user is already a member
    existing = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == member_data.user_id
    ).first()

    if existing:
        if existing.left_at:
            # Rejoin the channel
            existing.left_at = None
            existing.joined_at = datetime.utcnow()
            existing.role = member_data.role
            db.commit()
            db.refresh(existing)
            return existing
        else:
            raise HTTPException(status_code=400, detail="User is already a member")

    # Add new member
    new_member = ChannelMember(
        channel_id=channel_id,
        **member_data.dict()
    )
    db.add(new_member)

    # Create system entry for member joining
    join_entry = ChatEntry(
        channel_id=channel_id,
        user_id=member_data.user_id,
        type='join',
        content=f"joined the channel"
    )
    db.add(join_entry)

    db.commit()
    db.refresh(new_member)

    return new_member

@channels_router.get("/{channel_id}/members", response_model=List[ChannelMemberResponse])
async def list_channel_members(
    channel_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List members of a channel"""
    # Verify current user is a member
    is_member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.left_at.is_(None)
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    members = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.left_at.is_(None)
    ).order_by(ChannelMember.role, ChannelMember.joined_at).all()

    return members

# ============================================
# CHAT ENTRY ENDPOINTS
# ============================================

@chat_router.post("/channels/{channel_id}/messages", response_model=ChatEntryResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    channel_id: int,
    message_data: ChatEntryCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Send a message to a channel"""
    # Verify user is a member
    member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.left_at.is_(None)
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    # Check if channel is read-only
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if channel.is_read_only and member.role not in ['admin', 'moderator']:
        raise HTTPException(status_code=403, detail="Channel is read-only")

    # Create message
    message_dict = message_data.dict(exclude={'mentions'})
    entry = ChatEntry(
        channel_id=channel_id,
        user_id=current_user_id,
        **message_dict
    )
    db.add(entry)
    db.flush()

    # Handle mentions
    if message_data.mentions:
        for mentioned_user_id in message_data.mentions:
            mention = Mention(
                entry_id=entry.id,
                mentioned_user_id=mentioned_user_id,
                mention_type='user'
            )
            db.add(mention)

    # Update channel's updated_at
    channel.updated_at = datetime.utcnow()

    # Update unread counts for other members
    db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id != current_user_id,
        ChannelMember.left_at.is_(None)
    ).update({"unread_count": ChannelMember.unread_count + 1})

    db.commit()
    db.refresh(entry)

    # Load mentions for response
    entry.mentions = db.query(Mention).filter(Mention.entry_id == entry.id).all()

    return entry

@chat_router.get("/channels/{channel_id}/messages", response_model=List[ChatEntryResponse])
async def list_messages(
    channel_id: int,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """List messages in a channel"""
    # Verify user is a member
    member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.left_at.is_(None)
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    entries = db.query(ChatEntry).filter(
        ChatEntry.channel_id == channel_id,
        ChatEntry.is_deleted == False
    ).order_by(desc(ChatEntry.created_at)).offset(skip).limit(limit).all()

    # Mark messages as read
    if entries:
        member.last_read_at = datetime.utcnow()
        member.last_read_entry_id = entries[0].id
        member.unread_count = 0
        db.commit()

    # Reverse to get chronological order
    entries.reverse()

    return entries

@chat_router.post("/messages/{message_id}/reactions", response_model=ChatEntryResponse)
async def add_reaction(
    message_id: int,
    reaction_data: ReactionAdd,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user_id: UUID = Query(...),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Add a reaction to a message"""
    entry = db.query(ChatEntry).filter(ChatEntry.id == message_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify user is a member of the channel
    member = db.query(ChannelMember).filter(
        ChannelMember.channel_id == entry.channel_id,
        ChannelMember.user_id == current_user_id,
        ChannelMember.left_at.is_(None)
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this channel")

    # Add or update reactions
    if not entry.reactions:
        entry.reactions = {}

    emoji = reaction_data.emoji
    user_id_str = str(current_user_id)

    if emoji not in entry.reactions:
        entry.reactions[emoji] = []

    if user_id_str not in entry.reactions[emoji]:
        entry.reactions[emoji].append(user_id_str)
    else:
        # Remove reaction if already exists (toggle)
        entry.reactions[emoji].remove(user_id_str)
        if not entry.reactions[emoji]:
            del entry.reactions[emoji]

    db.commit()
    db.refresh(entry)

    return entry

# Function to include all chat routers
def include_chat_routers(app):
    """Include all chat routers in the FastAPI app"""
    app.include_router(channels_router)
    app.include_router(chat_router)
