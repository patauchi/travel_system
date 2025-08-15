"""
Tools Module Models
Contains all tool-related models: Note, Task, LogCall, Attachment, Event, etc.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, Date,
    ForeignKey, Table, UniqueConstraint, CheckConstraint, Enum as SQLEnum,
    DECIMAL, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from common.enums import (
    NotePriority, CallType, CallStatus, TaskStatus, TaskPriority,
    DiskType, EventStatus, ChannelType, AssignmentRule
)
from shared_models import Base


class Note(Base):
    """Notes and documentation system - Based on Laravel migration"""
    __tablename__ = "notes"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(191), nullable=True)  # Límite para índices
    content = Column(Text, nullable=False)
    notable_id = Column(BigInteger, nullable=False)
    notable_type = Column(String(50), nullable=False)  # Polimórfico
    priority = Column(SQLEnum(NotePriority), default=NotePriority.MEDIUM)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Índices definidos en la tabla
    __table_args__ = (
        # Índices para performance
        UniqueConstraint('notable_type', 'notable_id', name='idx_notes_notable'),
        UniqueConstraint('assigned_to', 'created_at', name='idx_notes_assigned_created'),
        UniqueConstraint('priority', 'created_at', name='idx_notes_priority_created'),
        UniqueConstraint('created_at', name='idx_notes_created_at'),
        # Índice compuesto para consultas complejas
        UniqueConstraint('notable_type', 'notable_id', 'priority', 'created_at',
                        name='notes_complex_query'),
    )

    def __repr__(self):
        return f"<Note {self.id}: {self.title or 'Untitled'}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "notable_id": self.notable_id,
            "notable_type": self.notable_type,
            "priority": self.priority.value if self.priority else None,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class LogCall(Base):
    """Call logging system - Based on Laravel migration"""
    __tablename__ = "log_calls"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone_number = Column(String(255), nullable=False)
    call_type = Column(SQLEnum(CallType), nullable=False)
    status = Column(SQLEnum(CallStatus), nullable=False)
    notes = Column(Text, nullable=True)
    logacallable_id = Column(BigInteger, nullable=True)  # ID del modelo relacionado
    logacallable_type = Column(String(255), nullable=True)  # Tipo del modelo (Lead, Contact, etc.)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Usuario que hizo/recibió la llamada
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Para soft deletes

    # Índices
    __table_args__ = (
        UniqueConstraint('logacallable_type', 'logacallable_id', name='idx_logacalls_logacallable'),
        UniqueConstraint('phone_number', name='idx_logacalls_phone_number'),
        UniqueConstraint('user_id', name='idx_logacalls_user_id'),
    )

    def __repr__(self):
        return f"<LogCall {self.id}: {self.call_type.value} to {self.phone_number}>"

    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number,
            "call_type": self.call_type.value if self.call_type else None,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "logacallable_id": self.logacallable_id,
            "logacallable_type": self.logacallable_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Task(Base):
    """Task management system - Based on Laravel migration"""
    __tablename__ = "tasks"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.LOW)
    due_date = Column(Date, nullable=True)
    completed_at = Column(Date, nullable=True)
    taskable_id = Column(BigInteger, nullable=True)  # ID del modelo relacionado
    taskable_type = Column(String(255), nullable=True)  # Tipo del modelo (Lead, Contact, etc.)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Usuario asignado
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Usuario que creó la tarea
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Para soft deletes

    # Índices
    __table_args__ = (
        UniqueConstraint('taskable_type', 'taskable_id', name='idx_tasks_taskable'),
        UniqueConstraint('status', name='idx_tasks_status'),
        UniqueConstraint('priority', name='idx_tasks_priority'),
        UniqueConstraint('due_date', name='idx_tasks_due_date'),
        UniqueConstraint('assigned_to', name='idx_tasks_assigned_to'),
    )

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "taskable_id": self.taskable_id,
            "taskable_type": self.taskable_type,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Attachment(Base):
    """File attachment system - Based on Laravel migration"""
    __tablename__ = "attachments"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    original_name = Column(String(255), nullable=False)  # Nombre original del archivo
    file_name = Column(String(255), nullable=False)  # Nombre del archivo en el servidor
    file_path = Column(String(500), nullable=False)  # Ruta completa del archivo
    disk = Column(SQLEnum(DiskType), default=DiskType.PUBLIC)  # Disco de almacenamiento
    description = Column(Text, nullable=True)  # Descripción del archivo
    attachable_id = Column(BigInteger, nullable=True)  # ID del modelo relacionado
    attachable_type = Column(String(255), nullable=True)  # Tipo del modelo (Lead, Quote, etc.)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Usuario que subió el archivo
    is_public = Column(Boolean, default=False)  # Si el archivo es público
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Para soft deletes

    # Índices
    __table_args__ = (
        UniqueConstraint('attachable_type', 'attachable_id', name='idx_attachments_attachable'),
        UniqueConstraint('uploaded_by', name='idx_attachments_uploaded_by'),
        UniqueConstraint('is_public', name='idx_attachments_is_public'),
    )

    def __repr__(self):
        return f"<Attachment {self.id}: {self.original_name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "original_name": self.original_name,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "disk": self.disk.value if self.disk else None,
            "description": self.description,
            "attachable_id": self.attachable_id,
            "attachable_type": self.attachable_type,
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Event(Base):
    """Calendar event system - Based on Laravel migration"""
    __tablename__ = "events"
    __table_args__ = {'extend_existing': True}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    all_day = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    status = Column(SQLEnum(EventStatus), default=EventStatus.SCHEDULED)
    notes = Column(Text, nullable=True)
    eventable_id = Column(BigInteger, nullable=True)  # ID del modelo relacionado
    eventable_type = Column(String(255), nullable=True)  # Tipo del modelo (Lead, Contact, etc.)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)  # Usuario organizador
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Para soft deletes

    # Índices
    __table_args__ = (
        UniqueConstraint('eventable_type', 'eventable_id', name='idx_events_eventable'),
        UniqueConstraint('start_date', name='idx_events_start_date'),
        UniqueConstraint('organizer_id', name='idx_events_organizer_id'),
        UniqueConstraint('status', name='idx_events_status'),
    )

    def __repr__(self):
        return f"<Event {self.id}: {self.title}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "all_day": self.all_day,
            "location": self.location,
            "status": self.status.value if self.status else None,
            "notes": self.notes,
            "eventable_id": self.eventable_id,
            "eventable_type": self.eventable_type,
            "organizer_id": str(self.organizer_id) if self.organizer_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CarbonFootprint(Base):
    """Carbon footprint tracking - Based on Laravel migration"""
    __tablename__ = "carbon_footprints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    quote_id = Column(BigInteger, nullable=False)  # Would need quotes table

    # Emissions data
    total_emissions = Column(DECIMAL(12, 2), nullable=False, comment='Total CO2 emissions in kg')
    offset_cost = Column(DECIMAL(10, 2), nullable=True, comment='Cost of carbon offset in USD')
    offset_included = Column(Boolean, default=False, comment='Whether offset was included in quote')

    # Detailed calculations and metadata
    emissions_metadata = Column(JSONB, nullable=False, default={}, comment='Detailed emissions calculations and breakdown')

    # Tracking
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Índices y constraints
    __table_args__ = (
        UniqueConstraint('quote_id', name='idx_carbon_footprints_quote_id_unique'),
        UniqueConstraint('calculated_at', name='idx_carbon_footprints_calculated_at'),
    )

    def __repr__(self):
        return f"<CarbonFootprint {self.id}: Quote {self.quote_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "quote_id": self.quote_id,
            "total_emissions": float(self.total_emissions) if self.total_emissions else None,
            "offset_cost": float(self.offset_cost) if self.offset_cost else None,
            "offset_included": self.offset_included,
            "emissions_metadata": self.emissions_metadata,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ChannelConfig(Base):
    """Channel configuration for integrations - Based on Laravel migration"""
    __tablename__ = "channel_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Channel Configuration
    name = Column(String(255), nullable=False, comment='Integration name (e.g., "Main WhatsApp", "Support Email")')
    channel = Column(SQLEnum(ChannelType), nullable=False)
    is_active = Column(Boolean, default=True)

    # Configuration JSON for flexibility
    config = Column(JSONB, nullable=False, default={}, comment='Channel-specific configuration (tokens, credentials, etc)')

    # Auto-response Messages
    welcome_message = Column(Text, nullable=True, comment='Auto-response for new conversations')
    offline_message = Column(Text, nullable=True, comment='Auto-response outside business hours')
    business_hours = Column(JSONB, nullable=True, comment='Operating hours per day {"mon": {"start": "09:00", "end": "18:00"}}')

    # Assignment Configuration
    assignment_rule = Column(SQLEnum(AssignmentRule), default=AssignmentRule.MANUAL)
    default_assignee = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Índices
    __table_args__ = (
        Index('idx_channel_configs_channel', 'channel'),
        Index('idx_channel_configs_is_active', 'is_active'),
        Index('idx_channel_configs_created', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<ChannelConfig {self.id}: {self.name}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel.value if self.channel else None,
            "is_active": self.is_active,
            "config": self.config,
            "welcome_message": self.welcome_message,
            "offline_message": self.offline_message,
            "business_hours": self.business_hours,
            "assignment_rule": self.assignment_rule.value if self.assignment_rule else None,
            "default_assignee": str(self.default_assignee) if self.default_assignee else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Review(Base):
    """Reviews system - Based on Laravel migration (empty template)"""
    __tablename__ = "reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # The Laravel migration is empty, so we'll add basic fields
    # These can be extended as needed
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    reviewable_id = Column(BigInteger, nullable=True)  # ID del modelo relacionado
    reviewable_type = Column(String(255), nullable=True)  # Tipo del modelo
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Review {self.id}: {self.rating or 'Unrated'}>"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "rating": self.rating,
            "reviewer_id": str(self.reviewer_id) if self.reviewer_id else None,
            "reviewable_id": self.reviewable_id,
            "reviewable_type": self.reviewable_type,
            "is_approved": self.is_approved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
