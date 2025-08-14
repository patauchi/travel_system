"""
Pydantic Schemas for Extended Models
Request/Response models for API endpoints
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum

# ============================================
# ENUMS
# ============================================

class NotePriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class TaskStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class TaskPriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class CallTypeEnum(str, Enum):
    incoming = "incoming"
    outgoing = "outgoing"

class CallStatusEnum(str, Enum):
    answered = "answered"
    missed = "missed"
    busy = "busy"
    no_answer = "no_answer"
    failed = "failed"

class EventStatusEnum(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    postponed = "postponed"

class DiskTypeEnum(str, Enum):
    public = "public"
    aws = "aws"

class ChannelTypeEnum(str, Enum):
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

class AssignmentRuleEnum(str, Enum):
    round_robin = "round_robin"
    load_balanced = "load_balanced"
    manual = "manual"
    by_skill = "by_skill"

# ============================================
# NOTE SCHEMAS
# ============================================

class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=191)
    content: str
    notable_id: int
    notable_type: str = Field(..., max_length=50)
    priority: NotePriorityEnum = NotePriorityEnum.medium
    assigned_to: Optional[UUID] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=191)
    content: Optional[str] = None
    priority: Optional[NotePriorityEnum] = None
    assigned_to: Optional[UUID] = None

class NoteResponse(NoteBase):
    id: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# TASK SCHEMAS
# ============================================

class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.pending
    priority: TaskPriorityEnum = TaskPriorityEnum.low
    due_date: Optional[date] = None
    taskable_id: Optional[int] = None
    taskable_type: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[UUID] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    completed_at: Optional[date] = None

class TaskResponse(TaskBase):
    id: UUID
    completed_at: Optional[date] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# EVENT SCHEMAS
# ============================================

class EventBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    all_day: bool = False
    location: Optional[str] = Field(None, max_length=255)
    status: EventStatusEnum = EventStatusEnum.scheduled
    notes: Optional[str] = None
    eventable_id: Optional[int] = None
    eventable_type: Optional[str] = Field(None, max_length=255)

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[EventStatusEnum] = None
    notes: Optional[str] = None

class EventResponse(EventBase):
    id: int
    organizer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# LOGCALL SCHEMAS
# ============================================

class LogCallBase(BaseModel):
    phone_number: str = Field(..., max_length=255)
    call_type: CallTypeEnum
    status: CallStatusEnum
    notes: Optional[str] = None
    logacallable_id: Optional[int] = None
    logacallable_type: Optional[str] = Field(None, max_length=255)

class LogCallCreate(LogCallBase):
    pass

class LogCallUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=255)
    call_type: Optional[CallTypeEnum] = None
    status: Optional[CallStatusEnum] = None
    notes: Optional[str] = None

class LogCallResponse(LogCallBase):
    id: int
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# ATTACHMENT SCHEMAS
# ============================================

class AttachmentBase(BaseModel):
    description: Optional[str] = None
    attachable_id: Optional[int] = None
    attachable_type: Optional[str] = Field(None, max_length=255)
    is_public: bool = False

class AttachmentCreate(AttachmentBase):
    # File will be handled separately as UploadFile
    pass

class AttachmentResponse(AttachmentBase):
    id: int
    original_name: str
    file_name: str
    file_path: str
    disk: DiskTypeEnum
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================
# CARBON FOOTPRINT SCHEMAS
# ============================================

class CarbonFootprintBase(BaseModel):
    quote_id: int
    total_emissions: float = Field(..., description="Total CO2 emissions in kg")
    offset_cost: Optional[float] = Field(None, description="Cost of carbon offset in USD")
    offset_included: bool = Field(False, description="Whether offset was included in quote")
    emissions_metadata: Dict[str, Any] = Field(default_factory=dict, description="Detailed emissions calculations")

class CarbonFootprintCreate(CarbonFootprintBase):
    calculated_at: datetime

class CarbonFootprintResponse(CarbonFootprintBase):
    id: int
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# CHANNEL CONFIG SCHEMAS
# ============================================

class ChannelConfigBase(BaseModel):
    name: str = Field(..., max_length=255, description="Integration name")
    channel: ChannelTypeEnum
    is_active: bool = True
    config: Dict[str, Any] = Field(default_factory=dict, description="Channel-specific configuration")
    welcome_message: Optional[str] = Field(None, description="Auto-response for new conversations")
    offline_message: Optional[str] = Field(None, description="Auto-response outside business hours")
    business_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours per day")
    assignment_rule: AssignmentRuleEnum = AssignmentRuleEnum.manual
    default_assignee: Optional[UUID] = None

class ChannelConfigCreate(ChannelConfigBase):
    pass

class ChannelConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    channel: Optional[ChannelTypeEnum] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    welcome_message: Optional[str] = None
    offline_message: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    assignment_rule: Optional[AssignmentRuleEnum] = None
    default_assignee: Optional[UUID] = None

class ChannelConfigResponse(ChannelConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# REVIEW SCHEMAS
# ============================================

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None
    reviewable_id: int
    reviewable_type: str = Field(..., max_length=50, description="Type of entity being reviewed")
    is_verified: bool = False
    would_recommend: Optional[bool] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None
    is_verified: Optional[bool] = None
    would_recommend: Optional[bool] = None

class ReviewResponse(ReviewBase):
    id: int
    reviewer_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# BULK OPERATIONS
# ============================================

class BulkDeleteRequest(BaseModel):
    ids: List[int] = Field(..., min_items=1, max_items=100)

class BulkUpdateRequest(BaseModel):
    ids: List[int] = Field(..., min_items=1, max_items=100)
    updates: Dict[str, Any]

class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_ids: List[int] = []
    errors: List[Dict[str, Any]] = []

# ============================================
# PAGINATION
# ============================================

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int
