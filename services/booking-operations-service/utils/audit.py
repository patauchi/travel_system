"""
Audit trail module for Booking Operations Service
Tracks all changes to critical entities
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import json
from fastapi import Depends

from database import get_tenant_db
from models_base import Base


class AuditAction(str, Enum):
    """Audit action types"""
    create = "CREATE"
    update = "UPDATE"
    delete = "DELETE"
    soft_delete = "SOFT_DELETE"
    restore = "RESTORE"
    status_change = "STATUS_CHANGE"
    cancel = "CANCEL"
    confirm = "CONFIRM"
    approve = "APPROVE"
    reject = "REJECT"
    login = "LOGIN"
    logout = "LOGOUT"
    export = "EXPORT"
    import_action = "IMPORT"


class AuditLog(Base):
    """Audit log table for tracking all changes"""
    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Entity information
    entity_type = Column(String(50), nullable=False)  # booking, service, supplier, etc.
    entity_id = Column(Integer, nullable=False)  # ID of the entity
    entity_name = Column(String(255), nullable=True)  # Human-readable name/reference

    # Action information
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, etc.
    action_description = Column(Text, nullable=True)  # Detailed description

    # User information
    user_id = Column(String(100), nullable=True)  # User who performed the action
    user_email = Column(String(255), nullable=True)
    user_name = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Change details
    old_values = Column(JSON, nullable=True)  # Previous values (for updates)
    new_values = Column(JSON, nullable=True)  # New values
    changed_fields = Column(JSON, nullable=True)  # List of changed field names

    # Context information
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)  # Browser/client info
    request_id = Column(String(100), nullable=True)  # Unique request identifier
    session_id = Column(String(100), nullable=True)  # Session identifier

    # Additional metadata
    audit_metadata = Column(JSON, nullable=True)  # Any additional context
    tags = Column(JSON, nullable=True)  # Tags for categorization

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        {'extend_existing': True}
    )


class AuditLogger:
    """Utility class for logging audit events"""

    def __init__(self, db: Session):
        """
        Initialize audit logger

        Args:
            db: Database session
        """
        self.db = db

    def log_action(
        self,
        entity_type: str,
        entity_id: int,
        action: AuditAction,
        user: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        request_context: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event

        Args:
            entity_type: Type of entity (booking, service, etc.)
            entity_id: ID of the entity
            action: Action performed
            user: User information
            old_values: Previous values (for updates)
            new_values: New values
            description: Human-readable description
            metadata: Additional metadata
            request_context: Request context (IP, user agent, etc.)

        Returns:
            Created audit log entry
        """
        # Calculate changed fields
        changed_fields = None
        if old_values and new_values:
            changed_fields = self._get_changed_fields(old_values, new_values)

        # Extract entity name if available
        entity_name = None
        if new_values:
            entity_name = new_values.get('name') or new_values.get('reference') or new_values.get('code')
        elif old_values:
            entity_name = old_values.get('name') or old_values.get('reference') or old_values.get('code')

        # Create audit log entry
        audit_log = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
            action=action.value if isinstance(action, Enum) else action,
            action_description=description,
            user_id=user.get('id') if user else None,
            user_email=user.get('email') if user else None,
            user_name=user.get('username') or user.get('full_name') if user else None,
            user_role=user.get('role') if user else None,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=request_context.get('ip_address') if request_context else None,
            user_agent=request_context.get('user_agent') if request_context else None,
            request_id=request_context.get('request_id') if request_context else None,
            session_id=request_context.get('session_id') if request_context else None,
            audit_metadata=metadata,
            created_at=datetime.utcnow()
        )

        self.db.add(audit_log)

        try:
            self.db.commit()
            return audit_log
        except Exception as e:
            self.db.rollback()
            # Log error but don't fail the main operation
            print(f"Failed to create audit log: {str(e)}")
            return None

    def log_create(
        self,
        entity_type: str,
        entity_id: int,
        entity_data: Dict[str, Any],
        user: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log entity creation

        Args:
            entity_type: Type of entity
            entity_id: ID of created entity
            entity_data: Created entity data
            user: User information
            **kwargs: Additional parameters

        Returns:
            Audit log entry
        """
        return self.log_action(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.create,
            user=user,
            new_values=entity_data,
            description=f"Created {entity_type} #{entity_id}",
            **kwargs
        )

    def log_update(
        self,
        entity_type: str,
        entity_id: int,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        user: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log entity update

        Args:
            entity_type: Type of entity
            entity_id: ID of updated entity
            old_data: Previous entity data
            new_data: Updated entity data
            user: User information
            **kwargs: Additional parameters

        Returns:
            Audit log entry
        """
        changed_fields = self._get_changed_fields(old_data, new_data)

        return self.log_action(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.update,
            user=user,
            old_values=old_data,
            new_values=new_data,
            description=f"Updated {entity_type} #{entity_id}: {', '.join(changed_fields) if changed_fields else 'no changes'}",
            **kwargs
        )

    def log_delete(
        self,
        entity_type: str,
        entity_id: int,
        entity_data: Dict[str, Any],
        user: Optional[Dict[str, Any]] = None,
        soft_delete: bool = False,
        **kwargs
    ) -> AuditLog:
        """
        Log entity deletion

        Args:
            entity_type: Type of entity
            entity_id: ID of deleted entity
            entity_data: Deleted entity data
            user: User information
            soft_delete: Whether this is a soft delete
            **kwargs: Additional parameters

        Returns:
            Audit log entry
        """
        return self.log_action(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.soft_delete if soft_delete else AuditAction.delete,
            user=user,
            old_values=entity_data,
            description=f"{'Soft deleted' if soft_delete else 'Deleted'} {entity_type} #{entity_id}",
            **kwargs
        )

    def log_status_change(
        self,
        entity_type: str,
        entity_id: int,
        old_status: str,
        new_status: str,
        user: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """
        Log status change

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            old_status: Previous status
            new_status: New status
            user: User information
            reason: Reason for status change
            **kwargs: Additional parameters

        Returns:
            Audit log entry
        """
        description = f"Status changed from {old_status} to {new_status}"
        if reason:
            description += f": {reason}"

        return self.log_action(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.status_change,
            user=user,
            old_values={"status": old_status},
            new_values={"status": new_status},
            description=description,
            audit_metadata={"reason": reason} if reason else None,
            **kwargs
        )

    def get_entity_history(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit history for an entity

        Args:
            entity_type: Type of entity
            entity_id: ID of entity
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        return self.db.query(AuditLog).filter(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id
        ).order_by(
            AuditLog.created_at.desc()
        ).limit(limit).offset(offset).all()

    def get_user_activity(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get activity log for a user

        Args:
            user_id: User ID
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records

        Returns:
            List of audit log entries
        """
        query = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        )

        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        return query.order_by(
            AuditLog.created_at.desc()
        ).limit(limit).all()

    def search_audit_logs(
        self,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search_text: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Search audit logs with filters

        Args:
            entity_type: Filter by entity type
            action: Filter by action
            user_id: Filter by user
            start_date: Start date filter
            end_date: End date filter
            search_text: Search in description
            limit: Maximum number of records
            offset: Offset for pagination

        Returns:
            List of audit log entries
        """
        query = self.db.query(AuditLog)

        if entity_type:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action:
            query = query.filter(AuditLog.action == action)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        if search_text:
            query = query.filter(
                AuditLog.action_description.ilike(f"%{search_text}%")
            )

        return query.order_by(
            AuditLog.created_at.desc()
        ).limit(limit).offset(offset).all()

    def _get_changed_fields(
        self,
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ) -> List[str]:
        """
        Get list of changed fields between old and new values

        Args:
            old_values: Previous values
            new_values: New values

        Returns:
            List of changed field names
        """
        changed = []

        # Check for modified fields
        for key in new_values:
            if key in old_values:
                if self._normalize_value(old_values[key]) != self._normalize_value(new_values[key]):
                    changed.append(key)
            else:
                changed.append(key)  # New field

        # Check for removed fields
        for key in old_values:
            if key not in new_values:
                changed.append(f"-{key}")  # Removed field

        return changed

    def _normalize_value(self, value: Any) -> Any:
        """
        Normalize value for comparison

        Args:
            value: Value to normalize

        Returns:
            Normalized value
        """
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (dict, list)):
            return json.dumps(value, sort_keys=True, default=str)
        else:
            return str(value) if value is not None else None


def get_audit_logger(db: Session = Depends(get_tenant_db)) -> AuditLogger:
    """
    Dependency to get audit logger instance

    Args:
        db: Database session

    Returns:
        AuditLogger instance
    """
    return AuditLogger(db)


# Export classes and functions
__all__ = [
    'AuditAction',
    'AuditLog',
    'AuditLogger',
    'get_audit_logger'
]
