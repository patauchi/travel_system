"""
Chat Module
Handles chat channels, members, entries, and mentions
"""

from .models import Channel, ChannelMember, ChatEntry, Mention
from .schemas import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    ChannelMemberAdd, ChannelMemberUpdate, ChannelMemberResponse,
    ChatEntryCreate, ChatEntryUpdate, ChatEntryResponse,
    MentionResponse, ChannelStats, ReactionAdd,
    ChatSearchRequest, ChatSearchResult, PaginatedChatEntries,
    TypingIndicator, UserPresence, UserChatStats,
    ChatNotification, ChatWebhookPayload
)
from .endpoints import (
    channels_router,
    chat_router
)

__all__ = [
    # Models
    'Channel',
    'ChannelMember',
    'ChatEntry',
    'Mention',

    # Schemas
    'ChannelCreate',
    'ChannelUpdate',
    'ChannelResponse',
    'ChannelMemberAdd',
    'ChannelMemberUpdate',
    'ChannelMemberResponse',
    'ChatEntryCreate',
    'ChatEntryUpdate',
    'ChatEntryResponse',
    'MentionResponse',
    'ChannelStats',
    'ReactionAdd',
    'ChatSearchRequest',
    'ChatSearchResult',
    'PaginatedChatEntries',
    'TypingIndicator',
    'UserPresence',
    'UserChatStats',
    'ChatNotification',
    'ChatWebhookPayload',

    # Endpoints
    'channels_router',
    'chat_router'
]
