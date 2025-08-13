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


# ============================================
# INBOX SPECIFIC ENUMS
# ============================================

class ConversationStatus(str, Enum):
    """Status of inbox conversations"""
    NEW = "new"
    OPEN = "open"
    REPLIED = "replied"
    QUALIFIED = "qualified"
    ARCHIVED = "archived"


class Priority(str, Enum):
    """Priority levels for conversations"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class MessageDirection(str, Enum):
    """Direction of messages"""
    IN = "in"
    OUT = "out"


class MessageType(str, Enum):
    """Types of messages"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"


class MessageStatus(str, Enum):
    """Status of messages"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# ============================================
# CHAT SPECIFIC ENUMS
# ============================================

class ChatChannelType(str, Enum):
    """Types of chat channels"""
    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"


class MemberRole(str, Enum):
    """Roles of channel members"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class NotificationLevel(str, Enum):
    """Notification levels for channel members"""
    ALL = "all"
    MENTIONS = "mentions"
    NONE = "none"


class EntryType(str, Enum):
    """Types of chat entries"""
    MESSAGE = "message"
    JOIN = "join"
    LEAVE = "leave"
    SYSTEM = "system"


class MentionType(str, Enum):
    """Types of mentions"""
    USER = "user"
    EVERYONE = "everyone"
    HERE = "here"


# ============================================
# COMMUNICATION SERVICE ENUMS
# ============================================

class CommunicationType(str, Enum):
    """Types of communication"""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    PUSH = "push"
    IN_APP = "in_app"


class CommunicationStatus(str, Enum):
    """Status of communication attempts"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class TemplateType(str, Enum):
    """Types of communication templates"""
    WELCOME = "welcome"
    VERIFICATION = "verification"
    RESET_PASSWORD = "reset_password"
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_REMINDER = "booking_reminder"
    PAYMENT_RECEIPT = "payment_receipt"
    PROMOTIONAL = "promotional"
    TRANSACTIONAL = "transactional"
    NOTIFICATION = "notification"


# ============================================
# WEBHOOK ENUMS
# ============================================

class WebhookEvent(str, Enum):
    """Types of webhook events"""
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_READ = "message_read"
    MESSAGE_FAILED = "message_failed"
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_ARCHIVED = "conversation_archived"
    CHANNEL_CREATED = "channel_created"
    CHANNEL_UPDATED = "channel_updated"
    CHANNEL_DELETED = "channel_deleted"
    MEMBER_JOINED = "member_joined"
    MEMBER_LEFT = "member_left"
    ENTRY_CREATED = "entry_created"
    ENTRY_EDITED = "entry_edited"
    ENTRY_DELETED = "entry_deleted"
