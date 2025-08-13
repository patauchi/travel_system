"""
Extended API Endpoints for System Service
Handles CRUD operations for extended models (notes, tasks, events, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from uuid import UUID
import logging

from dependencies import get_tenant_db_session
from models_extended import (
    Note, LogCall, Task, Attachment, Event,
    CarbonFootprint, ChannelConfig, Review
)
from schemas_extended import (
    NoteCreate, NoteUpdate, NoteResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    EventCreate, EventUpdate, EventResponse,
    LogCallCreate, LogCallUpdate, LogCallResponse,
    AttachmentCreate, AttachmentResponse,
    CarbonFootprintCreate, CarbonFootprintResponse,
    ChannelConfigCreate, ChannelConfigUpdate, ChannelConfigResponse,
    ReviewCreate, ReviewUpdate, ReviewResponse
)
from utils import verify_tenant_access, get_current_user

logger = logging.getLogger(__name__)

# Create routers for each domain
notes_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/notes", tags=["Notes"])
tasks_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/tasks", tags=["Tasks"])
events_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/events", tags=["Events"])
logcalls_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/logcalls", tags=["Call Logs"])
attachments_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/attachments", tags=["Attachments"])
carbon_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/carbon-footprints", tags=["Carbon Footprints"])
channels_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/channel-configs", tags=["Channel Configs"])
reviews_router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/reviews", tags=["Reviews"])

# ============================================
# NOTES ENDPOINTS
# ============================================

@notes_router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    tenant_slug: str,
    note_data: NoteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Create a new note"""
    verify_tenant_access(tenant_slug, current_user)

    note = Note(
        **note_data.dict(),
        created_by=UUID(current_user["user_id"])
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note

@notes_router.get("/", response_model=List[NoteResponse])
async def list_notes(
    tenant_slug: str,
    notable_type: Optional[str] = None,
    notable_id: Optional[int] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List notes with optional filters"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(Note)

    if notable_type:
        query = query.filter(Note.notable_type == notable_type)
    if notable_id:
        query = query.filter(Note.notable_id == notable_id)
    if priority:
        query = query.filter(Note.priority == priority)
    if assigned_to:
        query = query.filter(Note.assigned_to == assigned_to)

    notes = query.order_by(desc(Note.created_at)).offset(skip).limit(limit).all()
    return notes

@notes_router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    tenant_slug: str,
    note_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get a specific note"""
    verify_tenant_access(tenant_slug, current_user)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note

@notes_router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    tenant_slug: str,
    note_id: int,
    note_update: NoteUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Update a note"""
    verify_tenant_access(tenant_slug, current_user)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    for field, value in note_update.dict(exclude_unset=True).items():
        setattr(note, field, value)

    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)

    return note

@notes_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    tenant_slug: str,
    note_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Delete a note"""
    verify_tenant_access(tenant_slug, current_user)

    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()

# ============================================
# TASKS ENDPOINTS
# ============================================

@tasks_router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    tenant_slug: str,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Create a new task"""
    verify_tenant_access(tenant_slug, current_user)

    task = Task(
        **task_data.dict(),
        created_by=UUID(current_user["user_id"])
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@tasks_router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    tenant_slug: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[UUID] = None,
    due_before: Optional[date] = None,
    taskable_type: Optional[str] = None,
    taskable_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List tasks with optional filters"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(Task).filter(Task.deleted_at.is_(None))

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if due_before:
        query = query.filter(Task.due_date <= due_before)
    if taskable_type:
        query = query.filter(Task.taskable_type == taskable_type)
    if taskable_id:
        query = query.filter(Task.taskable_id == taskable_id)

    tasks = query.order_by(Task.due_date, desc(Task.priority)).offset(skip).limit(limit).all()
    return tasks

@tasks_router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    tenant_slug: str,
    task_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get a specific task"""
    verify_tenant_access(tenant_slug, current_user)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

@tasks_router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    tenant_slug: str,
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Update a task"""
    verify_tenant_access(tenant_slug, current_user)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)

    # If task is being completed, set completed_at
    if task_update.status == "completed" and not task.completed_at:
        task.completed_at = date.today()

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)

    return task

@tasks_router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    tenant_slug: str,
    task_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Soft delete a task"""
    verify_tenant_access(tenant_slug, current_user)

    task = db.query(Task).filter(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.deleted_at = datetime.utcnow()
    db.commit()

# ============================================
# EVENTS ENDPOINTS
# ============================================

@events_router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    tenant_slug: str,
    event_data: EventCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Create a new event"""
    verify_tenant_access(tenant_slug, current_user)

    event = Event(
        **event_data.dict(),
        organizer_id=UUID(current_user["user_id"])
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event

@events_router.get("/", response_model=List[EventResponse])
async def list_events(
    tenant_slug: str,
    start_after: Optional[datetime] = None,
    end_before: Optional[datetime] = None,
    status: Optional[str] = None,
    organizer_id: Optional[UUID] = None,
    eventable_type: Optional[str] = None,
    eventable_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List events with optional filters"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(Event).filter(Event.deleted_at.is_(None))

    if start_after:
        query = query.filter(Event.start_date >= start_after)
    if end_before:
        query = query.filter(Event.end_date <= end_before)
    if status:
        query = query.filter(Event.status == status)
    if organizer_id:
        query = query.filter(Event.organizer_id == organizer_id)
    if eventable_type:
        query = query.filter(Event.eventable_type == eventable_type)
    if eventable_id:
        query = query.filter(Event.eventable_id == eventable_id)

    events = query.order_by(Event.start_date).offset(skip).limit(limit).all()
    return events

@events_router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    tenant_slug: str,
    event_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get a specific event"""
    verify_tenant_access(tenant_slug, current_user)

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.deleted_at.is_(None)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event

@events_router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    tenant_slug: str,
    event_id: int,
    event_update: EventUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Update an event"""
    verify_tenant_access(tenant_slug, current_user)

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.deleted_at.is_(None)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for field, value in event_update.dict(exclude_unset=True).items():
        setattr(event, field, value)

    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)

    return event

@events_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    tenant_slug: str,
    event_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Soft delete an event"""
    verify_tenant_access(tenant_slug, current_user)

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.deleted_at.is_(None)
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    event.deleted_at = datetime.utcnow()
    db.commit()

# ============================================
# LOGCALLS ENDPOINTS
# ============================================

@logcalls_router.post("/", response_model=LogCallResponse, status_code=status.HTTP_201_CREATED)
async def create_log_call(
    tenant_slug: str,
    call_data: LogCallCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Log a new call"""
    verify_tenant_access(tenant_slug, current_user)

    log_call = LogCall(
        **call_data.dict(),
        user_id=UUID(current_user["user_id"])
    )

    db.add(log_call)
    db.commit()
    db.refresh(log_call)

    return log_call

@logcalls_router.get("/", response_model=List[LogCallResponse])
async def list_log_calls(
    tenant_slug: str,
    phone_number: Optional[str] = None,
    call_type: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[UUID] = None,
    logacallable_type: Optional[str] = None,
    logacallable_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List call logs with optional filters"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(LogCall).filter(LogCall.deleted_at.is_(None))

    if phone_number:
        query = query.filter(LogCall.phone_number.contains(phone_number))
    if call_type:
        query = query.filter(LogCall.call_type == call_type)
    if status:
        query = query.filter(LogCall.status == status)
    if user_id:
        query = query.filter(LogCall.user_id == user_id)
    if logacallable_type:
        query = query.filter(LogCall.logacallable_type == logacallable_type)
    if logacallable_id:
        query = query.filter(LogCall.logacallable_id == logacallable_id)

    calls = query.order_by(desc(LogCall.created_at)).offset(skip).limit(limit).all()
    return calls

@logcalls_router.get("/{call_id}", response_model=LogCallResponse)
async def get_log_call(
    tenant_slug: str,
    call_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get a specific call log"""
    verify_tenant_access(tenant_slug, current_user)

    call = db.query(LogCall).filter(
        LogCall.id == call_id,
        LogCall.deleted_at.is_(None)
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call log not found")

    return call

@logcalls_router.put("/{call_id}", response_model=LogCallResponse)
async def update_log_call(
    tenant_slug: str,
    call_id: int,
    call_update: LogCallUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Update a call log"""
    verify_tenant_access(tenant_slug, current_user)

    call = db.query(LogCall).filter(
        LogCall.id == call_id,
        LogCall.deleted_at.is_(None)
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call log not found")

    for field, value in call_update.dict(exclude_unset=True).items():
        setattr(call, field, value)

    call.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(call)

    return call

@logcalls_router.delete("/{call_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_call(
    tenant_slug: str,
    call_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Soft delete a call log"""
    verify_tenant_access(tenant_slug, current_user)

    call = db.query(LogCall).filter(
        LogCall.id == call_id,
        LogCall.deleted_at.is_(None)
    ).first()

    if not call:
        raise HTTPException(status_code=404, detail="Call log not found")

    call.deleted_at = datetime.utcnow()
    db.commit()

# ============================================
# ATTACHMENTS ENDPOINTS
# ============================================

@attachments_router.post("/", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(
    tenant_slug: str,
    file: UploadFile = File(...),
    attachable_type: Optional[str] = None,
    attachable_id: Optional[int] = None,
    description: Optional[str] = None,
    is_public: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Upload a new attachment"""
    verify_tenant_access(tenant_slug, current_user)

    # TODO: Implement actual file storage (S3, local disk, etc.)
    # For now, we'll just store the metadata

    attachment = Attachment(
        original_name=file.filename,
        file_name=file.filename,  # In production, generate unique filename
        file_path=f"/storage/{tenant_slug}/{file.filename}",  # Example path
        disk="public",
        description=description,
        attachable_type=attachable_type,
        attachable_id=attachable_id,
        uploaded_by=UUID(current_user["user_id"]),
        is_public=is_public
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment

@attachments_router.get("/", response_model=List[AttachmentResponse])
async def list_attachments(
    tenant_slug: str,
    attachable_type: Optional[str] = None,
    attachable_id: Optional[int] = None,
    uploaded_by: Optional[UUID] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List attachments with optional filters"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(Attachment).filter(Attachment.deleted_at.is_(None))

    if attachable_type:
        query = query.filter(Attachment.attachable_type == attachable_type)
    if attachable_id:
        query = query.filter(Attachment.attachable_id == attachable_id)
    if uploaded_by:
        query = query.filter(Attachment.uploaded_by == uploaded_by)
    if is_public is not None:
        query = query.filter(Attachment.is_public == is_public)

    attachments = query.order_by(desc(Attachment.created_at)).offset(skip).limit(limit).all()
    return attachments

@attachments_router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(
    tenant_slug: str,
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get attachment metadata"""
    verify_tenant_access(tenant_slug, current_user)

    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.deleted_at.is_(None)
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return attachment

@attachments_router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    tenant_slug: str,
    attachment_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Soft delete an attachment"""
    verify_tenant_access(tenant_slug, current_user)

    attachment = db.query(Attachment).filter(
        Attachment.id == attachment_id,
        Attachment.deleted_at.is_(None)
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # TODO: Delete actual file from storage

    attachment.deleted_at = datetime.utcnow()
    db.commit()

# ============================================
# CHANNEL CONFIGS ENDPOINTS
# ============================================

@channels_router.post("/", response_model=ChannelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_config(
    tenant_slug: str,
    config_data: ChannelConfigCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Create a new channel configuration"""
    verify_tenant_access(tenant_slug, current_user)

    # Check permissions - only admins should configure channels
    # TODO: Implement permission check

    config = ChannelConfig(**config_data.dict())

    db.add(config)
    db.commit()
    db.refresh(config)

    return config

@channels_router.get("/", response_model=List[ChannelConfigResponse])
async def list_channel_configs(
    tenant_slug: str,
    channel: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """List channel configurations"""
    verify_tenant_access(tenant_slug, current_user)

    query = db.query(ChannelConfig)

    if channel:
        query = query.filter(ChannelConfig.channel == channel)
    if is_active is not None:
        query = query.filter(ChannelConfig.is_active == is_active)

    configs = query.order_by(ChannelConfig.name).all()
    return configs

@channels_router.get("/{config_id}", response_model=ChannelConfigResponse)
async def get_channel_config(
    tenant_slug: str,
    config_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Get a specific channel configuration"""
    verify_tenant_access(tenant_slug, current_user)

    config = db.query(ChannelConfig).filter(ChannelConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Channel configuration not found")

    return config

@channels_router.put("/{config_id}", response_model=ChannelConfigResponse)
async def update_channel_config(
    tenant_slug: str,
    config_id: int,
    config_update: ChannelConfigUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Update a channel configuration"""
    verify_tenant_access(tenant_slug, current_user)

    config = db.query(ChannelConfig).filter(ChannelConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Channel configuration not found")

    for field, value in config_update.dict(exclude_unset=True).items():
        setattr(config, field, value)

    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)

    return config

@channels_router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel_config(
    tenant_slug: str,
    config_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_tenant_db_session)
):
    """Delete a channel configuration"""
    verify_tenant_access(tenant_slug, current_user)

    config = db.query(ChannelConfig).filter(ChannelConfig.id == config_id).first()

    if not config:
        raise HTTPException(status_code=404, detail="Channel configuration not found")

    db.delete(config)
    db.commit()

# Function to include all routers in the main app
def include_extended_routers(app):
    """Include all extended routers in the FastAPI app"""
    app.include_router(notes_router)
    app.include_router(tasks_router)
    app.include_router(events_router)
    app.include_router(logcalls_router)
    app.include_router(attachments_router)
    app.include_router(channels_router)
    # Carbon footprints and reviews can be added similarly
