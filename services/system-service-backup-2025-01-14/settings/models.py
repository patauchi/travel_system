"""
Settings Module Models
Contains settings and audit log models for system configuration and tracking
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, Table, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from datetime import datetime
import uuid

from shared_models import Base


class Setting(Base):
    """Tenant-specific settings"""
    __tablename__ = "settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSONB, nullable=False)
    value_type = Column(String(50))  # string, number, boolean, json
    display_name = Column(String(255))
    description = Column(Text)
    is_public = Column(Boolean, default=False)  # Visible to all users
    is_encrypted = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # System settings cannot be deleted
    validation_rules = Column(JSONB)  # JSON schema for validation
    allowed_values = Column(JSONB)  # List of allowed values
    default_value = Column(JSONB)
    meta_data = Column(JSONB, default={})
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))

    # Unique constraint on category + key
    __table_args__ = (
        UniqueConstraint('category', 'key', name='_category_key_uc'),
    )

    def __repr__(self):
        return f"<Setting {self.category}.{self.key}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "value_type": self.value_type,
            "display_name": self.display_name,
            "description": self.description,
            "is_public": self.is_public,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AuditLog(Base):
    """Tenant-specific audit logs"""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), index=True)
    resource_id = Column(String(255))
    resource_name = Column(String(255))
    changes = Column(JSONB)  # Before/after values
    result = Column(String(50))  # success, failure, partial
    error_message = Column(Text)
    ip_address = Column(INET)
    user_agent = Column(Text)
    session_id = Column(UUID(as_uuid=True))
    request_id = Column(String(100))
    duration_ms = Column(Integer)  # Request duration in milliseconds
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "changes": self.changes,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
