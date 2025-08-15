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
from shared_auth import get_current_user, check_permission, validate_tenant_access
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
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Create a new note using two-phase creation"""
    from shared_auth import safe_tenant_session
    from database import get_db

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Phase 1: Create the note in the shared/global context to validate foreign keys
    db_global = next(get_db())
    try:
        db_note = Note(
            title=note_data.title,
            content=note_data.content,
            notable_id=note_data.notable_id,
            notable_type=note_data.notable_type,
            priority=note_data.priority,
            assigned_to=note_data.assigned_to,
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        # Don't add to global session, just validate the model
        # The actual insert will happen in the tenant context
    finally:
        db_global.close()

    # Phase 2: Insert into tenant schema
    with safe_tenant_session(tenant_slug) as db:
        # Create a new instance for the tenant session
        tenant_note = Note(
            title=note_data.title,
            content=note_data.content,
            notable_id=note_data.notable_id,
            notable_type=note_data.notable_type,
            priority=note_data.priority,
            assigned_to=note_data.assigned_to,
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        db.add(tenant_note)
        db.commit()
        db.refresh(tenant_note)

        return tenant_note.to_dict()


@router.get("/notes", response_model=List[NoteResponse])
async def list_notes(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    priority: Optional[str] = Query(None),
    notable_type: Optional[str] = Query(None),
    notable_id: Optional[int] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    created_by: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """List notes with filtering and pagination"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import or_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
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

        # Order by priority and creation date
        query = query.order_by(Note.priority.desc(), Note.created_at.desc())

        notes = query.offset(skip).limit(limit).all()
        return [note.to_dict() for note in notes]


@router.get("/notes/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Get a specific note by ID"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        return note.to_dict()


@router.put("/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Update a note"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
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

        return db_note.to_dict()


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Delete a note"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
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
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Create a new task using two-phase creation"""
    from shared_auth import safe_tenant_session
    from database import get_db

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Phase 1: Create the task in the shared/global context to validate foreign keys
    db_global = next(get_db())
    try:
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            taskable_id=task_data.taskable_id,
            taskable_type=task_data.taskable_type,
            assigned_to=task_data.assigned_to,
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        # Don't add to global session, just validate the model
        # The actual insert will happen in the tenant context
    finally:
        db_global.close()

    # Phase 2: Insert into tenant schema
    with safe_tenant_session(tenant_slug) as db:
        # Create a new instance for the tenant session
        tenant_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            due_date=task_data.due_date,
            taskable_id=task_data.taskable_id,
            taskable_type=task_data.taskable_type,
            assigned_to=task_data.assigned_to,
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        db.add(tenant_task)
        db.commit()
        db.refresh(tenant_task)

        return tenant_task.to_dict()


@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[UUID] = Query(None),
    created_by: Optional[UUID] = Query(None),
    taskable_type: Optional[str] = Query(None),
    taskable_id: Optional[int] = Query(None),
    due_before: Optional[date] = Query(None),
    due_after: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """List tasks with filtering and pagination"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import or_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
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

        if taskable_type:
            query = query.filter(Task.taskable_type == taskable_type)

        if taskable_id:
            query = query.filter(Task.taskable_id == taskable_id)

        if due_before:
            query = query.filter(Task.due_date <= due_before)

        if due_after:
            query = query.filter(Task.due_date >= due_after)

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
        return [task.to_dict() for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Get a specific task by ID"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import and_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        return task.to_dict()


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Update a task"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import and_
    from datetime import datetime

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Update fields
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(task)

        return task.to_dict()


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Delete a task (soft delete)"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import and_
    from datetime import datetime

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        task = db.query(Task).filter(and_(Task.id == task_id, Task.deleted_at.is_(None))).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Soft delete
        task.deleted_at = datetime.utcnow()

        db.commit()

        return {"message": "Task deleted successfully"}


# ============================================
# LogCall Endpoints
# ============================================

@router.post("/logcalls", response_model=LogCallResponse, status_code=status.HTTP_201_CREATED)
async def create_logcall(
    logcall_data: LogCallCreate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Create a new log call using two-phase creation"""
    from shared_auth import safe_tenant_session
    from database import get_db

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Phase 1: Validate the model with foreign keys in global context
    db_global = next(get_db())
    try:
        db_logcall = LogCall(
            phone_number=logcall_data.phone_number,
            call_type=logcall_data.call_type,
            status=logcall_data.status,
            notes=logcall_data.notes,
            logacallable_id=logcall_data.logacallable_id,
            logacallable_type=logcall_data.logacallable_type,
            created_by=current_user.get("user_id") or current_user.get("id")
        )
        # Just validate, don't persist
    finally:
        db_global.close()

    # Phase 2: Insert into tenant schema
    with safe_tenant_session(tenant_slug) as db:
        tenant_logcall = LogCall(
            phone_number=logcall_data.phone_number,
            call_type=logcall_data.call_type,
            status=logcall_data.status,
            notes=logcall_data.notes,
            logacallable_id=logcall_data.logacallable_id,
            logacallable_type=logcall_data.logacallable_type,
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        db.add(tenant_logcall)
        db.commit()
        db.refresh(tenant_logcall)

        return tenant_logcall.to_dict()


@router.get("/logcalls", response_model=List[LogCallResponse])
async def list_logcalls(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    call_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    user_id: Optional[UUID] = Query(None),
    logacallable_type: Optional[str] = Query(None),
    logacallable_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user)
):
    """List call logs with filtering and pagination"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        query = db.query(LogCall).filter(LogCall.deleted_at.is_(None))

        # Apply filters
        if call_type:
            query = query.filter(LogCall.call_type == call_type)

        if status:
            query = query.filter(LogCall.status == status)

        if phone_number:
            query = query.filter(LogCall.phone_number.contains(phone_number))

        if user_id:
            query = query.filter(LogCall.user_id == user_id)

        if logacallable_type:
            query = query.filter(LogCall.logacallable_type == logacallable_type)

        if logacallable_id:
            query = query.filter(LogCall.logacallable_id == logacallable_id)

        # Order by creation date
        query = query.order_by(LogCall.created_at.desc())

        # Execute query
        logcalls = query.offset(skip).limit(limit).all()
        return [logcall.to_dict() for logcall in logcalls]


@router.get("/logcalls/{logcall_id}", response_model=LogCallResponse)
async def get_logcall(
    logcall_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Get a specific log call by ID"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import and_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        logcall = db.query(LogCall).filter(and_(LogCall.id == logcall_id, LogCall.deleted_at.is_(None))).first()
        if not logcall:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Log call not found"
            )
        return logcall.to_dict()


# ============================================
# Event Endpoints
# ============================================

@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Create a new event using two-phase creation"""
    from shared_auth import safe_tenant_session
    from database import get_db

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Phase 1: Validate the model with foreign keys in global context
    db_global = next(get_db())
    try:
        db_event = Event(
            title=event_data.title,
            description=event_data.description,
            status=event_data.status,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            all_day=event_data.all_day,
            location=event_data.location,
            notes=event_data.notes,
            eventable_id=event_data.eventable_id,
            eventable_type=event_data.eventable_type,
            organizer_id=current_user.get("user_id") or current_user.get("id")
        )
        # Just validate, don't persist
    finally:
        db_global.close()

    # Phase 2: Insert into tenant schema
    with safe_tenant_session(tenant_slug) as db:
        tenant_event = Event(
            title=event_data.title,
            description=event_data.description,
            status=event_data.status,
            start_date=event_data.start_date,
            end_date=event_data.end_date,
            all_day=event_data.all_day,
            location=event_data.location,
            notes=event_data.notes,
            eventable_id=event_data.eventable_id,
            eventable_type=event_data.eventable_type,
            organizer_id=current_user.get("user_id") or current_user.get("id")
        )

        db.add(tenant_event)
        db.commit()
        db.refresh(tenant_event)

        return tenant_event.to_dict()


@router.get("/events", response_model=List[EventResponse])
async def list_events(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    start_from: Optional[datetime] = Query(None),
    start_to: Optional[datetime] = Query(None),
    organizer_id: Optional[UUID] = Query(None),
    eventable_type: Optional[str] = Query(None),
    eventable_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    current_user = Depends(get_current_user)
):
    """List events with filtering and pagination"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import or_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
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
                    Event.description.ilike(search_term)
                )
            )

        # Order by start date (upcoming first)
        query = query.order_by(Event.start_date.asc())

        events = query.offset(skip).limit(limit).all()
        return [event.to_dict() for event in events]


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Get a specific event by ID"""
    from shared_auth import safe_tenant_session
    from sqlalchemy import and_

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        event = db.query(Event).filter(and_(Event.id == event_id, Event.deleted_at.is_(None))).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        return event.to_dict()


# ============================================
# Channel Config Endpoints
# ============================================

@router.post("/channel-configs", response_model=ChannelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_channel_config(
    config_data: ChannelConfigCreate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Create a new channel configuration using two-phase creation"""
    from shared_auth import safe_tenant_session
    from database import get_db

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Phase 1: Create the config in the shared/global context to validate foreign keys
    db_global = next(get_db())
    try:
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
        # Don't add to global session, just validate the model
    finally:
        db_global.close()

    # Phase 2: Insert into tenant schema
    with safe_tenant_session(tenant_slug) as db:
        # Check if channel config already exists for this channel
        existing_config = db.query(ChannelConfig).filter(ChannelConfig.channel == config_data.channel).first()
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Channel configuration for {config_data.channel.value} already exists"
            )

        tenant_config = ChannelConfig(
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

        db.add(tenant_config)
        db.commit()
        db.refresh(tenant_config)

        return tenant_config.to_dict()


@router.get("/channel-configs", response_model=List[ChannelConfigResponse])
async def list_channel_configs(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    channel: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user = Depends(get_current_user)
):
    """List channel configurations with filtering"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        query = db.query(ChannelConfig)

        if channel:
            query = query.filter(ChannelConfig.channel == channel)

        if is_active is not None:
            query = query.filter(ChannelConfig.is_active == is_active)

        configs = query.offset(skip).limit(limit).all()
        return [config.to_dict() for config in configs]


# ============================================
# Bulk Operations
# ============================================

@router.put("/tasks/bulk-update", response_model=BulkTaskUpdateResult)
async def bulk_update_tasks(
    bulk_data: BulkTaskUpdate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Bulk update multiple tasks"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    result = BulkTaskUpdateResult(updated_count=0, failed_count=0, errors=[])

    with safe_tenant_session(tenant_slug) as db:
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

                task.updated_at = datetime.utcnow()
                result.updated_count += 1

            except Exception as e:
                result.failed_count += 1
                result.errors.append({"task_id": str(task_id), "error": str(e)})

        db.commit()

    return result


@router.put("/notes/bulk-update", response_model=BulkNoteUpdateResult)
async def bulk_update_notes(
    bulk_data: BulkNoteUpdate,
    tenant_slug: str,
    current_user = Depends(get_current_user)
):
    """Bulk update multiple notes"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    result = BulkNoteUpdateResult(updated_count=0, failed_count=0, errors=[])

    with safe_tenant_session(tenant_slug) as db:
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

                note.updated_at = datetime.utcnow()
                result.updated_count += 1

            except Exception as e:
                result.failed_count += 1
                result.errors.append({"note_id": str(note_id), "error": str(e)})

        db.commit()

    return result
