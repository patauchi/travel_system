"""
Tools Module Schemas
Pydantic schemas for tools-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from uuid import UUID
import re

from common.enums import (
    NotePriority, CallType, CallStatus, TaskStatus, TaskPriority,
    DiskType, EventStatus, ChannelType, AssignmentRule
)


# ============================================
# Note Schemas
# ============================================

class NoteBase(BaseModel):
    title: Optional[str] = Field(None, max_length=191)
    content: str = Field(..., min_length=1)
    notable_id: int = Field(..., gt=0)
    notable_type: str = Field(..., min_length=1, max_length=50)
    priority: NotePriority = Field(default=NotePriority.medium)
    assigned_to: Optional[UUID] = None

    @validator('notable_type')
    def validate_notable_type(cls, v):
        # Convert to lowercase for consistency
        return v.lower()


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=191)
    content: Optional[str] = Field(None, min_length=1)
    priority: Optional[NotePriority] = None
    assigned_to: Optional[UUID] = None


class NoteResponse(BaseModel):
    id: int
    title: Optional[str]
    content: str
    notable_id: int
    notable_type: str
    priority: NotePriority
    assigned_to: Optional[UUID]
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Task Schemas
# ============================================

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = Field(default=TaskStatus.pending)
    priority: TaskPriority = Field(default=TaskPriority.low)
    due_date: Optional[date] = None
    taskable_id: Optional[int] = Field(None, gt=0)
    taskable_type: Optional[str] = Field(None, max_length=255)
    assigned_to: Optional[UUID] = None

    @validator('taskable_type')
    def validate_taskable_type(cls, v):
        if v:
            return v.lower()
        return v


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    completed_at: Optional[date] = None

    @validator('completed_at', pre=True, always=True)
    def set_completed_at(cls, v, values):
        # Auto-set completed_at when status changes to completed
        if 'status' in values and values['status'] == TaskStatus.completed and v is None:
            return date.today()
        elif 'status' in values and values['status'] != TaskStatus.completed:
            return None
        return v


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    completed_at: Optional[date]
    taskable_id: Optional[int]
    taskable_type: Optional[str]
    assigned_to: Optional[UUID]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# LogCall Schemas
# ============================================

class LogCallBase(BaseModel):
    phone_number: str = Field(..., min_length=1, max_length=255)
    call_type: CallType
    status: CallStatus
    notes: Optional[str] = None
    logacallable_id: Optional[int] = Field(None, gt=0)
    logacallable_type: Optional[str] = Field(None, max_length=255)

    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic phone number validation
        if not re.match(r'^[\+\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

    @validator('logacallable_type')
    def validate_logacallable_type(cls, v):
        if v:
            return v.lower()
        return v


class LogCallCreate(LogCallBase):
    pass


class LogCallUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, min_length=1, max_length=255)
    call_type: Optional[CallType] = None
    status: Optional[CallStatus] = None
    notes: Optional[str] = None

    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v and not re.match(r'^[\+\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v


class LogCallResponse(BaseModel):
    id: int
    phone_number: str
    call_type: CallType
    status: CallStatus
    notes: Optional[str]
    logacallable_id: Optional[int]
    logacallable_type: Optional[str]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Attachment Schemas
# ============================================

class AttachmentBase(BaseModel):
    original_name: str = Field(..., min_length=1, max_length=255)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    disk: DiskType = Field(default=DiskType.public)
    description: Optional[str] = None
    attachable_id: Optional[int] = Field(None, gt=0)
    attachable_type: Optional[str] = Field(None, max_length=255)
    is_public: bool = Field(default=False)

    @validator('attachable_type')
    def validate_attachable_type(cls, v):
        if v:
            return v.lower()
        return v


class AttachmentCreate(AttachmentBase):
    pass


class AttachmentUpdate(BaseModel):
    description: Optional[str] = None
    is_public: Optional[bool] = None


class AttachmentResponse(BaseModel):
    id: int
    original_name: str
    file_name: str
    file_path: str
    disk: DiskType
    description: Optional[str]
    attachable_id: Optional[int]
    attachable_type: Optional[str]
    uploaded_by: Optional[UUID]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Event Schemas
# ============================================

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    all_day: bool = Field(default=False)
    location: Optional[str] = Field(None, max_length=255)
    status: EventStatus = Field(default=EventStatus.scheduled)
    notes: Optional[str] = None
    eventable_id: Optional[int] = Field(None, gt=0)
    eventable_type: Optional[str] = Field(None, max_length=255)

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('eventable_type')
    def validate_eventable_type(cls, v):
        if v:
            return v.lower()
        return v


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=255)
    status: Optional[EventStatus] = None
    notes: Optional[str] = None

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and values['start_date'] and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    start_date: datetime
    end_date: Optional[datetime]
    all_day: bool
    location: Optional[str]
    status: EventStatus
    notes: Optional[str]
    eventable_id: Optional[int]
    eventable_type: Optional[str]
    organizer_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Carbon Footprint Schemas
# ============================================

class CarbonFootprintBase(BaseModel):
    quote_id: int = Field(..., gt=0)
    total_emissions: float = Field(..., gt=0)
    offset_cost: Optional[float] = Field(None, ge=0)
    offset_included: bool = Field(default=False)
    emissions_metadata: Dict[str, Any] = Field(default={})

    @validator('total_emissions', 'offset_cost')
    def validate_decimal_precision(cls, v):
        if v is not None:
            # Ensure proper decimal precision for financial calculations
            return round(float(v), 2)
        return v


class CarbonFootprintCreate(CarbonFootprintBase):
    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class CarbonFootprintUpdate(BaseModel):
    total_emissions: Optional[float] = Field(None, gt=0)
    offset_cost: Optional[float] = Field(None, ge=0)
    offset_included: Optional[bool] = None
    emissions_metadata: Optional[Dict[str, Any]] = None

    @validator('total_emissions', 'offset_cost')
    def validate_decimal_precision(cls, v):
        if v is not None:
            return round(float(v), 2)
        return v


class CarbonFootprintResponse(BaseModel):
    id: int
    quote_id: int
    total_emissions: float
    offset_cost: Optional[float]
    offset_included: bool
    emissions_metadata: Dict[str, Any]
    calculated_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Channel Config Schemas
# ============================================

class ChannelConfigBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    channel: ChannelType
    is_active: bool = Field(default=True)
    config: Dict[str, Any] = Field(default={})
    welcome_message: Optional[str] = None
    offline_message: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    assignment_rule: AssignmentRule = Field(default=AssignmentRule.manual)
    default_assignee: Optional[UUID] = None

    @validator('business_hours')
    def validate_business_hours(cls, v):
        if v:
            # Basic validation for business hours structure
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            for day, hours in v.items():
                if day not in days:
                    raise ValueError(f'Invalid day: {day}')
                if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
                    raise ValueError(f'Invalid hours format for {day}')
        return v


class ChannelConfigCreate(ChannelConfigBase):
    pass


class ChannelConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    welcome_message: Optional[str] = None
    offline_message: Optional[str] = None
    business_hours: Optional[Dict[str, Any]] = None
    assignment_rule: Optional[AssignmentRule] = None
    default_assignee: Optional[UUID] = None

    @validator('business_hours')
    def validate_business_hours(cls, v):
        if v:
            days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            for day, hours in v.items():
                if day not in days:
                    raise ValueError(f'Invalid day: {day}')
                if not isinstance(hours, dict) or 'start' not in hours or 'end' not in hours:
                    raise ValueError(f'Invalid hours format for {day}')
        return v


class ChannelConfigResponse(BaseModel):
    id: int
    name: str
    channel: ChannelType
    is_active: bool
    config: Dict[str, Any]
    welcome_message: Optional[str]
    offline_message: Optional[str]
    business_hours: Optional[Dict[str, Any]]
    assignment_rule: AssignmentRule
    default_assignee: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Review Schemas
# ============================================

class ReviewBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    reviewable_id: Optional[int] = Field(None, gt=0)
    reviewable_type: Optional[str] = Field(None, max_length=255)

    @validator('reviewable_type')
    def validate_reviewable_type(cls, v):
        if v:
            return v.lower()
        return v


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    is_approved: Optional[bool] = None


class ReviewResponse(BaseModel):
    id: int
    title: Optional[str]
    content: Optional[str]
    rating: Optional[int]
    reviewer_id: Optional[UUID]
    reviewable_id: Optional[int]
    reviewable_type: Optional[str]
    is_approved: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Filter and Query Schemas
# ============================================

class ToolsFilter(BaseModel):
    """Common filters for tools endpoints"""
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    assigned_to: Optional[UUID] = None
    created_by: Optional[UUID] = None
    search: Optional[str] = None


class NoteFilter(ToolsFilter):
    priority: Optional[NotePriority] = None
    notable_type: Optional[str] = None
    notable_id: Optional[int] = None


class TaskFilter(ToolsFilter):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_from: Optional[date] = None
    due_to: Optional[date] = None
    taskable_type: Optional[str] = None
    taskable_id: Optional[int] = None


class LogCallFilter(ToolsFilter):
    call_type: Optional[CallType] = None
    status: Optional[CallStatus] = None
    phone_number: Optional[str] = None
    logacallable_type: Optional[str] = None
    logacallable_id: Optional[int] = None


class EventFilter(ToolsFilter):
    status: Optional[EventStatus] = None
    start_from: Optional[datetime] = None
    start_to: Optional[datetime] = None
    eventable_type: Optional[str] = None
    eventable_id: Optional[int] = None


# ============================================
# Bulk Operations Schemas
# ============================================

class BulkTaskUpdate(BaseModel):
    task_ids: List[int] = Field(..., min_items=1)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[UUID] = None


class BulkTaskUpdateResult(BaseModel):
    updated_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []


class BulkNoteUpdate(BaseModel):
    note_ids: List[int] = Field(..., min_items=1)
    priority: Optional[NotePriority] = None
    assigned_to: Optional[UUID] = None


class BulkNoteUpdateResult(BaseModel):
    updated_count: int
    failed_count: int
    errors: List[Dict[str, str]] = []
