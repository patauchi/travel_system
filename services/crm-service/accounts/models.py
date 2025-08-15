"""
Account Models for CRM Service
Account-specific models and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from core.models import Base
from core.enums import AccountType, AccountStatus, PaymentMethod, RiskLevel

# ============================================
# ACCOUNTS TABLE
# ============================================

class Account(Base):
    """Account management for businesses and individual customers"""
    __tablename__ = "accounts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey('actors.id', ondelete='CASCADE'), nullable=False)
    industry_id = Column(Integer, ForeignKey('industries.id', ondelete='SET NULL'), nullable=True)

    # Account specific fields
    account_type = Column(SQLEnum(AccountType), nullable=False, index=True)
    account_status = Column(SQLEnum(AccountStatus), default=AccountStatus.prospect, index=True)
    parent_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    is_following = Column(Boolean, default=False)

    # Business Information (for business accounts)
    tax_id = Column(String(50), nullable=True)
    business_license = Column(String(100), nullable=True)
    credit_limit = Column(Numeric(15, 2), nullable=True)
    payment_terms = Column(String(50), nullable=True)
    payment_method = Column(SQLEnum(PaymentMethod), nullable=True)

    # Additional business information
    company_owner = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    employee_count = Column(Integer, nullable=True)
    time_zone = Column(String(50), nullable=True)

    # Banking information
    bank_name = Column(String(100), nullable=True)
    bank_account = Column(String(50), nullable=True)
    swift_code = Column(String(20), nullable=True)

    # Metrics
    total_bookings = Column(Integer, default=0)
    lifetime_value = Column(Numeric(15, 2), default=0)
    last_booking_date = Column(Date, nullable=True)
    first_booking_date = Column(Date, nullable=True)

    # Segmentation information
    customer_segment = Column(String(50), nullable=True)
    loyalty_points = Column(Integer, default=0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.low)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor = relationship("Actor", back_populates="account")
    industry = relationship("Industry", back_populates="accounts")
    parent = relationship("Account", remote_side=[id], foreign_keys=[parent_account_id])
    subsidiaries = relationship("Account", back_populates="parent", foreign_keys=[parent_account_id])
    contacts = relationship("Contact", back_populates="account", foreign_keys="Contact.account_id")
    opportunities = relationship("Opportunity", back_populates="account")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_account_type_status', 'account_type', 'account_status'),
        Index('idx_account_segment_ltv', 'customer_segment', 'lifetime_value'),
        Index('idx_account_last_booking', 'last_booking_date'),
        Index('idx_account_deleted', 'deleted_at'),
    )

    def __repr__(self):
        name = self.actor.company_name or f"{self.actor.first_name} {self.actor.last_name}".strip()
        return f"<Account({self.account_type}): {name} - {self.account_status}>"
