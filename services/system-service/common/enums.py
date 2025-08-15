"""
Common Enums for System Service
Centralizes all enum definitions used across the system service modules.
"""

import enum


class UserStatus(str, enum.Enum):
    """User account status"""
    active = "active"
    inactive = "inactive"
    suspended = "suspended"
    pending = "pending"


class PermissionAction(str, enum.Enum):
    """Available permission actions"""
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"
    execute = "execute"
    approve = "approve"
    export = "export"
    import_action = "import"


class ResourceType(str, enum.Enum):
    """Types of resources that can be accessed"""
    user = "user"
    role = "role"
    project = "project"
    document = "document"
    report = "report"
    setting = "setting"
    audit = "audit"
    api = "api"
    webhook = "webhook"
    workflow = "workflow"


class TaskStatus(str, enum.Enum):
    """Task execution status"""
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority levels"""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class NotePriority(str, enum.Enum):
    """Note priority levels"""
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class CallType(str, enum.Enum):
    """Call direction types"""
    incoming = "incoming"
    outgoing = "outgoing"


class CallStatus(str, enum.Enum):
    """Call completion status"""
    answered = "answered"
    missed = "missed"
    busy = "busy"
    no_answer = "no_answer"
    failed = "failed"


class DiskType(str, enum.Enum):
    """Storage disk types"""
    public = "public"
    aws = "aws"


class EventStatus(str, enum.Enum):
    """Event status"""
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    postponed = "postponed"


class ChannelType(str, enum.Enum):
    """Communication channel types"""
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


class AssignmentRule(str, enum.Enum):
    """Assignment rules for tasks and channels"""
    round_robin = "round_robin"
    load_balanced = "load_balanced"
    manual = "manual"
    by_skill = "by_skill"
