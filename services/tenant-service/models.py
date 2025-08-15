import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, JSON, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

# Enums
class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    tenant_admin = "tenant_admin"

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
    __tablename__ = "central_users"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
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

class Tenant(Base):
    __tablename__ = "central_tenants"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255))
    subdomain = Column(String(100), unique=True, index=True)
    schema_name = Column(String(63), unique=True, nullable=False)
    status = Column(String(50), default=TenantStatus.pending)
    subscription_plan = Column(String(50), default="free")
    max_users = Column(Integer, default=5)
    max_storage_gb = Column(Integer, default=10)
    settings = Column(JSONB, default={})
    tenant_metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    suspended_at = Column(DateTime(timezone=True))
    trial_ends_at = Column(DateTime(timezone=True))
    subscription_ends_at = Column(DateTime(timezone=True))

class TenantUser(Base):
    __tablename__ = "central_tenant_users"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("shared.central_tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("shared.central_users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default=UserRole.tenant_admin)
    is_owner = Column(Boolean, default=False)
    permissions = Column(JSONB, default={})
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    invited_by = Column(String(36), ForeignKey("shared.central_users.id"))
    invitation_token = Column(String(255))
    invitation_accepted_at = Column(DateTime(timezone=True))
    last_active_at = Column(DateTime(timezone=True))

class SubscriptionHistory(Base):
    __tablename__ = "central_subscription_history"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("shared.central_tenants.id", ondelete="CASCADE"), nullable=False)
    plan_from = Column(String(50))
    plan_to = Column(String(50), nullable=False)
    change_type = Column(String(50), nullable=False)
    price_paid = Column(String(20))
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50))
    transaction_id = Column(String(255))
    changed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    changed_by = Column(String(36), ForeignKey("shared.central_users.id"))
    notes = Column(Text)

class FeatureFlag(Base):
    __tablename__ = "central_feature_flags"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)
    tenant_overrides = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class TenantFeature(Base):
    __tablename__ = "central_tenant_features"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("shared.central_tenants.id", ondelete="CASCADE"), nullable=False)
    feature_id = Column(String(36), ForeignKey("shared.central_feature_flags.id", ondelete="CASCADE"), nullable=False)
    is_enabled = Column(Boolean, nullable=False)
    configuration = Column(JSONB, default={})
    enabled_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    enabled_by = Column(String(36), ForeignKey("shared.central_users.id"))

class AuditLog(Base):
    __tablename__ = "central_audit_logs"
    __table_args__ = {"schema": "shared"}

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("shared.central_tenants.id", ondelete="SET NULL"))
    user_id = Column(String(36), ForeignKey("shared.central_users.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSONB, default={})
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
