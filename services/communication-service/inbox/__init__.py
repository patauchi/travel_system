"""
Inbox Module
Handles inbox conversations, messages, and quick replies
"""

from .models import InboxConversation, InboxMessage, InboxQuickReply
from .schemas import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageUpdate, MessageResponse,
    QuickReplyCreate, QuickReplyUpdate, QuickReplyResponse,
    ConversationStats, IncomingWebhook
)
from .endpoints import (
    conversations_router,
    messages_router,
    quick_replies_router
)

__all__ = [
    # Models
    'InboxConversation',
    'InboxMessage',
    'InboxQuickReply',

    # Schemas
    'ConversationCreate',
    'ConversationUpdate',
    'ConversationResponse',
    'MessageCreate',
    'MessageUpdate',
    'MessageResponse',
    'QuickReplyCreate',
    'QuickReplyUpdate',
    'QuickReplyResponse',
    'ConversationStats',
    'IncomingWebhook',

    # Endpoints
    'conversations_router',
    'messages_router',
    'quick_replies_router'
]
