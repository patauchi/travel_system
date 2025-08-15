"""
Common Enums for System Service
Centralizes all enum definitions used across the system service modules.
"""

import enum


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class PermissionAction(str, enum.Enum):
    """Available permission actions"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    EXPORT = "export"
    IMPORT = "import"


class ResourceType(str, enum.Enum):
    """Types of resources that can be accessed"""
    USER = "user"
    ROLE = "role"
    PROJECT = "project"
    DOCUMENT = "document"
    REPORT = "report"
    SETTING = "setting"
    AUDIT = "audit"
    API = "api"
    WEBHOOK = "webhook"
    WORKFLOW = "workflow"


class TaskStatus(str, enum.Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotePriority(str, enum.Enum):
    """Note priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CallType(str, enum.Enum):
    """Call direction types"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class CallStatus(str, enum.Enum):
    """Call completion status"""
    ANSWERED = "answered"
    MISSED = "missed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"


class DiskType(str, enum.Enum):
    """Storage disk types"""
    PUBLIC = "public"
    AWS = "aws"


class EventStatus(str, enum.Enum):
    """Event status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class ChannelType(str, enum.Enum):
    """Communication channel types"""
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


class AssignmentRule(str, enum.Enum):
    """Assignment rules for tasks and channels"""
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    MANUAL = "manual"
    BY_SKILL = "by_skill"
