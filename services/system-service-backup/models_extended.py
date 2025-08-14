"""
Extended Models for System Service
Based on Laravel migrations from services-references
These models represent additional tenant-specific tables that extend the base system.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, Date,
    ForeignKey, Table, UniqueConstraint, CheckConstraint, Enum as SQLEnum,
    DECIMAL, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import enum

# Import Base from existing models
from models import Base

# ============================================
# ENUMS
# ============================================

class NotePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CallType(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class CallStatus(str, enum.Enum):
    ANSWERED = "answered"
    MISSED = "missed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class DiskType(str, enum.Enum):
    PUBLIC = "public"
    AWS = "aws"

class EventStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"

class ChannelType(str, enum.Enum):
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
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    MANUAL = "manual"
    BY_SKILL = "by_skill"

# ============================================
# NOTES MODEL
# ============================================

class Note(Base):
    """Notes and documentation system - Based on Laravel migration"""
    __tablename__ = "notes"

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
    # soft_deletes would be handled at application level or with a deleted_at column

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

# ============================================
# LOGACALLS MODEL
# ============================================

class LogCall(Base):
    """Call logging and tracking system - Based on Laravel migration"""
    __tablename__ = "logacalls"

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

# ============================================
# TASKS MODEL
# ============================================

class Task(Base):
    """Task management system - Based on Laravel migration"""
    __tablename__ = "tasks"

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

# ============================================
# ATTACHMENTS MODEL
# ============================================

class Attachment(Base):
    """File attachment system - Based on Laravel migration"""
    __tablename__ = "attachments"

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

# ============================================
# EVENTS MODEL
# ============================================

class Event(Base):
    """Event management system - Based on Laravel migration"""
    __tablename__ = "events"

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

# ============================================
# CARBON FOOTPRINTS MODEL
# ============================================

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

# ============================================
# CHANNEL CONFIGS MODEL
# ============================================

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
        UniqueConstraint('channel', name='idx_channel_configs_channel'),
        UniqueConstraint('is_active', name='idx_channel_configs_is_active'),
        UniqueConstraint('channel', 'is_active', name='idx_channel_configs_channel_active'),
    )

# ============================================
# REVIEWS MODEL
# ============================================

class Review(Base):
    """Reviews system - Based on Laravel migration (empty template)"""
    __tablename__ = "reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # The Laravel migration is empty, so we'll add basic fields
    # These can be extended as needed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
