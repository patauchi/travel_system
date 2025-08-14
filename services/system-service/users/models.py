"""
Users Module Models
Contains all user-related models: User, Role, Permission, Team, UserSession, etc.
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, Table, UniqueConstraint, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from datetime import datetime
import uuid

from common.enums import UserStatus, PermissionAction, ResourceType
from shared_models import Base

# Association Tables
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('granted_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('granted_by', UUID(as_uuid=True))
)

user_permissions = Table(
    'user_permissions',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
    Column('is_granted', Boolean, default=True),  # Can be False to explicitly deny
    Column('granted_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('granted_by', UUID(as_uuid=True)),
    Column('expires_at', DateTime(timezone=True))
)

user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('assigned_by', UUID(as_uuid=True)),
    Column('expires_at', DateTime(timezone=True))
)

team_members = Table(
    'team_members',
    Base.metadata,
    Column('team_id', UUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), default=datetime.utcnow),
    Column('role', String(50))  # team-specific role like 'lead', 'member'
)


class Role(Base):
    """Roles define a set of permissions that can be assigned to users"""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority roles override lower ones
    max_users = Column(Integer)  # Optional limit on users with this role
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))

    # Relationships
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="roles")

    def __repr__(self):
        return f"<Role {self.name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_system": self.is_system,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Permission(Base):
    """Granular permissions for resources and actions"""
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(SQLEnum(ResourceType), nullable=False)
    action = Column(SQLEnum(PermissionAction), nullable=False)
    description = Column(Text)
    conditions = Column(JSONB)  # Optional conditions for the permission
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    # Unique constraint on resource + action
    __table_args__ = (
        UniqueConstraint('resource', 'action', name='_resource_action_uc'),
    )

    def __repr__(self):
        return f"<Permission {self.name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "resource": self.resource.value if self.resource else None,
            "action": self.action.value if self.action else None,
            "description": self.description,
            "is_active": self.is_active
        }


class User(Base):
    """Tenant-specific users"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Personal Information
    first_name = Column(String(100))
    last_name = Column(String(100))
    full_name = Column(String(255))
    phone = Column(String(50))
    phone_secondary = Column(String(50))
    avatar_url = Column(Text)
    bio = Column(Text)

    # Organization Information
    title = Column(String(100))
    department = Column(String(100))
    employee_id = Column(String(50), unique=True)
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    currency = Column(String(3), default='USD')
    date_format = Column(String(20), default='YYYY-MM-DD')
    time_format = Column(String(10), default='24h')

    # Status and Security
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    phone_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))

    # Notifications
    notification_preferences = Column(JSONB, default={})
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)

    # Two-Factor Authentication
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))

    # Metadata
    metadata_json = Column(JSONB, default={})
    tags = Column(JSONB, default=[])

    # Audit Fields
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True))
    updated_by = Column(UUID(as_uuid=True))
    deleted_at = Column(DateTime(timezone=True))  # Soft delete
    deleted_by = Column(UUID(as_uuid=True))

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    teams = relationship("Team", secondary=team_members, back_populates="members")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "department": self.department,
            "title": self.title,
            "status": self.status.value if self.status else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Team(Base):
    """Teams or departments within a tenant"""
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    description = Column(Text)
    parent_team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'))
    team_lead_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    meta_data = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members = relationship("User", secondary=team_members, back_populates="teams")
    subteams = relationship("Team", backref="parent_team", remote_side=[id])

    def __repr__(self):
        return f"<Team {self.name}>"


class UserSession(Base):
    """Active user sessions"""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token_hash = Column(String(255), unique=True, index=True)
    ip_address = Column(INET)
    user_agent = Column(Text)
    device_info = Column(JSONB)
    location = Column(JSONB)  # Geo-location info
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self):
        return f"<UserSession {self.id}>"


class PasswordResetToken(Base):
    """Password reset tokens for users"""
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(INET)
    user_agent = Column(Text)

    def __repr__(self):
        return f"<PasswordResetToken {self.id}>"


class EmailVerificationToken(Base):
    """Email verification tokens"""
    __tablename__ = "email_verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(255), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<EmailVerificationToken {self.id}>"


class ApiKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False)
    key_prefix = Column(String(10), nullable=False, index=True)  # First few chars for identification
    scopes = Column(JSONB, default=[])  # List of allowed scopes
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    last_used_ip = Column(INET)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True))
    revoked_by = Column(UUID(as_uuid=True))
    revoke_reason = Column(Text)

    def __repr__(self):
        return f"<ApiKey {self.name}>"
