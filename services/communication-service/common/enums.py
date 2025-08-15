"""
Common Enums
Shared enums used across communication service modules
"""

from enum import Enum


# ============================================
# CHANNEL ENUMS (Used by both inbox and chat)
# ============================================

class ChannelType(str, Enum):
    """Types of communication channels"""
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


# ============================================
# INBOX SPECIFIC ENUMS
# ============================================

class ConversationStatus(str, Enum):
    """Status of inbox conversations"""
    new = "new"
    open = "open"
    replied = "replied"
    qualified = "qualified"
    archived = "archived"


class Priority(str, Enum):
    """Priority levels for conversations"""
    high = "high"
    normal = "normal"
    low = "low"


class MessageDirection(str, Enum):
    """Direction of messages"""
    in_direction = "in"
    out = "out"


class MessageType(str, Enum):
    """Types of messages"""
    text = "text"
    image = "image"
    document = "document"
    audio = "audio"
    video = "video"
    location = "location"


class MessageStatus(str, Enum):
    """Status of messages"""
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


# ============================================
# CHAT SPECIFIC ENUMS
# ============================================

class ChatChannelType(str, Enum):
    """Types of chat channels"""
    public = "public"
    private = "private"
    direct = "direct"


class MemberRole(str, Enum):
    """Roles of channel members"""
    admin = "admin"
    moderator = "moderator"
    member = "member"


class NotificationLevel(str, Enum):
    """Notification levels for channel members"""
    all = "all"
    mentions = "mentions"
    none = "none"


class EntryType(str, Enum):
    """Types of chat entries"""
    message = "message"
    join = "join"
    leave = "leave"
    system = "system"


class MentionType(str, Enum):
    """Types of mentions"""
    user = "user"
    everyone = "everyone"
    here = "here"


# ============================================
# COMMUNICATION SERVICE ENUMS
# ============================================

class CommunicationType(str, Enum):
    """Types of communication"""
    email = "email"
    sms = "sms"
    whatsapp = "whatsapp"
    push = "push"
    in_app = "in_app"


class CommunicationStatus(str, Enum):
    """Status of communication attempts"""
    pending = "pending"
    sending = "sending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"
    bounced = "bounced"
    complained = "complained"


class TemplateType(str, Enum):
    """Types of communication templates"""
    welcome = "welcome"
    verification = "verification"
    reset_password = "reset_password"
    booking_confirmation = "booking_confirmation"
    booking_reminder = "booking_reminder"
    payment_receipt = "payment_receipt"
    promotional = "promotional"
    transactional = "transactional"
    notification = "notification"


# ============================================
# WEBHOOK ENUMS
# ============================================

class WebhookEvent(str, Enum):
    """Types of webhook events"""
    message_received = "message_received"
    message_sent = "message_sent"
    message_delivered = "message_delivered"
    message_read = "message_read"
    message_failed = "message_failed"
    conversation_created = "conversation_created"
    conversation_updated = "conversation_updated"
    conversation_archived = "conversation_archived"
    channel_created = "channel_created"
    channel_updated = "channel_updated"
    channel_deleted = "channel_deleted"
    member_joined = "member_joined"
    member_left = "member_left"
    entry_created = "entry_created"
    entry_edited = "entry_edited"
    entry_deleted = "entry_deleted"
