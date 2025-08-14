"""
Tools Module Endpoints
API endpoints for tools-related operations (notes, tasks, calls, attachments, events, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, date

from database import get_db
from shared_auth import get_current_user, require_permission, get_current_tenant
from .models import Note, Task, LogCall, Attachment, Event, CarbonFootprint, ChannelConfig, Review
from .schemas import (
    NoteCreate, NoteUpdate, NoteResponse, NoteFilter,
    TaskCreate, TaskUpdate, TaskResponse, TaskFilter,
    LogCallCreate, LogCallUpdate, LogCallResponse, LogCallFilter,
    AttachmentCreate, AttachmentUpdate, AttachmentResponse,
    EventCreate, EventUpdate, EventResponse, EventFilter,
    CarbonFootprintCreate, CarbonFootprintUpdate, CarbonFootprintResponse,
    ChannelConfigCreate, ChannelConfigUpdate, ChannelConfigResponse,
    ReviewCreate, ReviewUpdate, ReviewResponse,
    BulkTaskUpdate, BulkTaskUpdateResult, BulkNoteUpdate, BulkNoteUpdateResult
)

router = APIRouter()

# ============================================
# Note Endpoints
# ============================================

@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new note"""
    db_note = Note(
        title=note_data.title,
        content=note_data.content,
        notable_id=note_data.notable_id,
        notable_type=note_data.notable_type,
        priority=note_data.priority,
        assigned_to=note_data.assigned_to,
        created_by=current_user.id
    )

    db.add(db_note)
    db.commit()
    db.refresh(db_note)

    return db_note


@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    priority: Optional[str] = Query(None),
    notable_type: Optional[str] = Query(None),
    notable_id: Optional[int] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    created_by: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List notes with filtering and pagination"""
    query = db.query(Note)

    # Apply filters
    if priority:
        query = query.filter(Note.priority == priority)

    if notable_type:
        query = query.filter(Note.notable_type == notable_type)

    if notable_id:
        query = query.filter(Note.notable_id == notable_id)

    if assigned_to:
        query = query.filter(Note.assigned_to == assigned_to)

    if created_by:
        query = query.filter(Note.created_by == created_by)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term)
            )
        )

    # Order by most recent first
    query = query.order_by(Note.created_at.desc())

    notes = query.offset(skip).limit(limit).all()
    return notes


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific note by ID"""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Update fields
    update_data = note_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_note, field, value)

    db.commit()
    db.refresh(db_note)

    return db_note


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete a note"""
    db_note = db.query(Note).filter(Note.id == note_id).first()
    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    db.delete(db_note)
    db.commit()


# ============================================
# Task Endpoints
# ============================================

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new task"""
    db_task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        taskable_id=task_data.taskable_id,
        taskable_type=task_data.taskable_type,
        assigned_to=task_data.assigned_to,
        created_by=current_user.id
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    created_by: Optional[UUID] = Query(None),
    due_from: Optional[date] = Query(None),
    due_to: Optional[date] = Query(None),
    taskable_type: Optional[str] = Query(None),
    taskable_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List tasks with filtering and pagination"""
    query = db.query(Task).filter(Task.deleted_at.is_(None))

    # Apply filters
    if status:
        query = query.filter(Task.status == status)

    if priority:
        query = query.filter(Task.priority == priority)

    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)

    if created_by:
        query = query.filter(Task.created_by == created_by)

    if due_from:
        query = query.filter(Task.due_date >= due_from)

    if due_to:
        query = query.filter(Task.due_date <= due_to)

    if taskable_type:
        query = query.filter(Task.taskable_type == taskable_type)

    if taskable_id:
        query = query.filter(Task.taskable_id == taskable_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term)
            )
        )

    # Order by priority and due date
    query = query.order_by(Task.priority.desc(), Task.due_date.asc())

    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific task by ID"""
    task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a task"""
    db_task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update fields
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)

    return db_task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Soft delete a task"""
    db_task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
    if not db_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Soft delete
    db_task.deleted_at = datetime.utcnow()
    db.commit()


# ============================================
# LogCall Endpoints
# ============================================

@router.post("/logcalls", response_model=LogCallResponse, status_code=status.HTTP_201_CREATED)
async def create_logcall(
    logcall_data: LogCallCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new call log"""
    db_logcall = LogCall(
        phone_number=logcall_data.phone_number,
        call_type=logcall_data.call_type,
        status=logcall_data.status,
        notes=logcall_data.notes,
        logacallable_id=logcall_data.logacallable_id,
        logacallable_type=logcall_data.logacallable_type,
        user_id=current_user.id
    )

    db.add(db_logcall)
    db.commit()
    db.refresh(db_logcall)

    return db_logcall


@router.get("/logcalls", response_model=List[LogCallResponse])
async def list_logcalls(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    call_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    logacallable_type: Optional[str] = Query(None),
    logacallable_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List call logs with filtering and pagination"""
    query = db.query(LogCall).filter(LogCall.deleted_at.is_(None))

    # Apply filters
    if call_type:
        query = query.filter(LogCall.call_type == call_type)

    if status:
        query = query.filter(LogCall.status == status)

    if phone_number:
        query = query.filter(LogCall.phone_number.ilike(f"%{phone_number}%"))

    if user_id:
        query = query.filter(LogCall.user_id == user_id)

    if logacallable_type:
        query = query.filter(LogCall.logacallable_type == logacallable_type)

    if logacallable_id:
        query = query.filter(LogCall.logacallable_id == logacallable_id)

    # Order by most recent first
    query = query.order_by(LogCall.created_at.desc())

    logcalls = query.offset(skip).limit(limit).all()
    return logcalls


@router.get("/logcalls/{logcall_id}", response_model=LogCallResponse)
async def get_logcall(
    logcall_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific call log by ID"""
    logcall = db.query(LogCall).filter(and_(LogCall.id == logcall_id, LogCall.deleted_at.is_(None))).first()
    if not logcall:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call log not found"
        )
    return logcall


# ============================================
# Event Endpoints
# ============================================

@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new event"""
    db_event = Event(
        title=event_data.title,
        description=event_data.description,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        all_day=event_data.all_day,
        location=event_data.location,
        status=event_data.status,
        notes=event_data.notes,
        eventable_id=event_data.eventable_id,
        eventable_type=event_data.eventable_type,
        organizer_id=current_user.id
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/events", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    start_from: Optional[datetime] = Query(None),
    start_to: Optional[datetime] = Query(None),
    organizer_id: Optional[UUID] = Query(None),
    eventable_type: Optional[str] = Query(None),
    eventable_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List events with filtering and pagination"""
    query = db.query(Event).filter(Event.deleted_at.is_(None))

    # Apply filters
    if status:
        query = query.filter(Event.status == status)

    if start_from:
        query = query.filter(Event.start_date >= start_from)

    if start_to:
        query = query.filter(Event.start_date <= start_to)

    if organizer_id:
        query = query.filter(Event.organizer_id == organizer_id)

    if eventable_type:
        query = query.filter(Event.eventable_type == eventable_type)

    if eventable_id:
        query = query.filter(Event.eventable_id == eventable_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term),
                Event.location.ilike(search_term)
            )
        )

    # Order by start date
    query = query.order_by(Event.start_date.asc())

    events = query.offset(skip).limit(limit).all()
    return events


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific event by ID"""
    event = db.query(Event).filter(and_(Event.id == event_id, Event.deleted_at.is_(None))).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return event


# ============================================
# Channel Config Endpoints
# ============================================

@router.post("/channel-configs", response_model=ChannelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_config(
    config_data: ChannelConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new channel configuration"""
    # Check if channel config already exists for this channel
    existing_config = db.query(ChannelConfig).filter(ChannelConfig.channel == config_data.channel).first()
    if existing_config:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Channel configuration for {config_data.channel.value} already exists"
        )

    db_config = ChannelConfig(
        name=config_data.name,
        channel=config_data.channel,
        is_active=config_data.is_active,
        config=config_data.config,
        welcome_message=config_data.welcome_message,
        offline_message=config_data.offline_message,
        business_hours=config_data.business_hours,
        assignment_rule=config_data.assignment_rule,
        default_assignee=config_data.default_assignee
    )

    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config


@router.get("/channel-configs", response_model=List[ChannelConfigResponse])
async def list_channel_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List channel configurations with filtering and pagination"""
    query = db.query(ChannelConfig)

    # Apply filters
    if channel:
        query = query.filter(ChannelConfig.channel == channel)

    if is_active is not None:
        query = query.filter(ChannelConfig.is_active == is_active)

    configs = query.offset(skip).limit(limit).all()
    return configs


# ============================================
# Bulk Operations
# ============================================

@router.put("/tasks/bulk-update", response_model=BulkTaskUpdateResult)
async def bulk_update_tasks(
    bulk_data: BulkTaskUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Bulk update multiple tasks"""
    result = BulkTaskUpdateResult(updated_count=0, failed_count=0, errors=[])

    for task_id in bulk_data.task_ids:
        try:
            task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
            if not task:
                result.failed_count += 1
                result.errors.append({"task_id": str(task_id), "error": "Task not found"})
                continue

            # Update fields if provided
            if bulk_data.status is not None:
                task.status = bulk_data.status
            if bulk_data.priority is not None:
                task.priority = bulk_data.priority
            if bulk_data.assigned_to is not None:
                task.assigned_to = bulk_data.assigned_to

            result.updated_count += 1

        except Exception as e:
            result.failed_count += 1
            result.errors.append({"task_id": str(task_id), "error": str(e)})

    db.commit()
    return result


@router.put("/notes/bulk-update", response_model=BulkNoteUpdateResult)
async def bulk_update_notes(
    bulk_data: BulkNoteUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Bulk update multiple notes"""
    result = BulkNoteUpdateResult(updated_count=0, failed_count=0, errors=[])

    for note_id in bulk_data.note_ids:
        try:
            note = db.query(Note).filter(Note.id == note_id).first()
            if not note:
                result.failed_count += 1
                result.errors.append({"note_id": str(note_id), "error": "Note not found"})
                continue

            # Update fields if provided
            if bulk_data.priority is not None:
                note.priority = bulk_data.priority
            if bulk_data.assigned_to is not None:
                note.assigned_to = bulk_data.assigned_to

            result.updated_count += 1

        except Exception as e:
            result.failed_count += 1
            result.errors.append({"note_id": str(note_id), "error": str(e)})

    db.commit()
    return result
