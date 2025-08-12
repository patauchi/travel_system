from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime
import uuid

# Enums
class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    tenant_admin = "tenant_admin"
    tenant_user = "tenant_user"
    tenant_viewer = "tenant_viewer"

class TenantStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    trial = "trial"
    expired = "expired"
    pending = "pending"

class SubscriptionPlan(str, enum.Enum):
    free = "free"
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"

# Models
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant_associations = relationship("TenantUser", foreign_keys="TenantUser.user_id", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.user_id", back_populates="user")
    api_keys_created = relationship("ApiKey", foreign_keys="ApiKey.created_by_id", back_populates="created_by")

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None
        }

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    subdomain = Column(String(100), unique=True, index=True)
    schema_name = Column(String(63), unique=True, nullable=False)
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.pending)
    subscription_plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.free)
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)
    settings = Column(JSONB, default={})
    tenant_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    suspended_at = Column(DateTime(timezone=True))
    trial_ends_at = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))

    # Relationships
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant")
    feature_flags = relationship("TenantFeature", back_populates="tenant", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="tenant", cascade="all, delete-orphan")
    subscription_history = relationship("SubscriptionHistory", back_populates="tenant", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tenant {self.slug}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "slug": self.slug,
            "name": self.name,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "status": self.status.value if self.status else None,
            "subscription_plan": self.subscription_plan.value if self.subscription_plan else None,
            "max_users": self.max_users,
            "max_storage_gb": self.max_storage_gb,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None
        }

class TenantUser(Base):
    __tablename__ = "tenant_users"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("shared.users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.tenant_user)
    is_owner = Column(Boolean, default=False)
    permissions = Column(JSONB, default={})
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("shared.users.id"))
    invitation_token = Column(String(255))
    invitation_accepted_at = Column(DateTime(timezone=True))
    last_active_at = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    user = relationship("User", foreign_keys=[user_id], back_populates="tenant_associations")
    inviter = relationship("User", foreign_keys=[invited_by])

    def __repr__(self):
        return f"<TenantUser {self.user_id} in {self.tenant_id}>"

class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_prefix = Column(String(10), nullable=False, index=True)
    scopes = Column(JSONB, default=[])
    rate_limit = Column(Integer, default=1000)
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("shared.users.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    revoked_at = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    created_by = relationship("User", back_populates="api_keys_created")

    def __repr__(self):
        return f"<ApiKey {self.name} for {self.tenant_id}>"

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="SET NULL"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("shared.users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSONB, default={})
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)
    tenant_overrides = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant_features = relationship("TenantFeature", back_populates="feature", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FeatureFlag {self.name}>"

class TenantFeature(Base):
    __tablename__ = "tenant_features"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="CASCADE"), nullable=False)
    feature_id = Column(UUID(as_uuid=True), ForeignKey("shared.feature_flags.id", ondelete="CASCADE"), nullable=False)
    is_enabled = Column(Boolean, nullable=False)
    configuration = Column(JSONB, default={})
    enabled_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    enabled_by = Column(UUID(as_uuid=True), ForeignKey("shared.users.id"))

    # Relationships
    tenant = relationship("Tenant", back_populates="feature_flags")
    feature = relationship("FeatureFlag", back_populates="tenant_features")
    enabler = relationship("User")

    def __repr__(self):
        return f"<TenantFeature {self.feature_id} for {self.tenant_id}>"

class SubscriptionHistory(Base):
    __tablename__ = "subscription_history"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="CASCADE"), nullable=False)
    plan_from = Column(SQLEnum(SubscriptionPlan))
    plan_to = Column(SQLEnum(SubscriptionPlan), nullable=False)
    change_type = Column(String(50), nullable=False)  # upgrade, downgrade, renewal, cancellation
    price_paid = Column(String(20))  # Using String to avoid decimal precision issues
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50))
    transaction_id = Column(String(255))
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("shared.users.id"))
    notes = Column(Text)

    # Relationships
    tenant = relationship("Tenant", back_populates="subscription_history")
    changer = relationship("User")

    def __repr__(self):
        return f"<SubscriptionHistory {self.tenant_id} {self.change_type}>"

class Webhook(Base):
    __tablename__ = "webhooks"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("shared.tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    events = Column(JSONB, nullable=False, default=[])
    headers = Column(JSONB, default={})
    secret = Column(String(255))
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_triggered_at = Column(DateTime(timezone=True))

    # Relationships
    tenant = relationship("Tenant", back_populates="webhooks")
    logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Webhook {self.name} for {self.tenant_id}>"

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    __table_args__ = {"schema": "shared"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("shared.webhooks.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False)
    response_status = Column(Integer)
    response_body = Column(Text)
    attempts = Column(Integer, default=1)
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    webhook = relationship("Webhook", back_populates="logs")

    def __repr__(self):
        return f"<WebhookLog {self.event_type} for {self.webhook_id}>"

class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = {"schema": "shared"}

    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("shared.users.id"))

    # Relationships
    updater = relationship("User")

    def __repr__(self):
        return f"<SystemSetting {self.key}>"
