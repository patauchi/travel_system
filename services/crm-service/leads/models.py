"""
Lead Models for CRM Service
Lead-specific models and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from core.models import Base
from core.enums import LeadStatus, InterestLevel

# ============================================
# LEADS TABLE
# ============================================

class Lead(Base):
    """Lead management for potential customers"""
    __tablename__ = "leads"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(Integer, ForeignKey('actors.id', ondelete='CASCADE'), nullable=False)

    # Lead specific fields
    lead_source = Column(String(100), nullable=True, index=True)
    lead_status = Column(SQLEnum(LeadStatus), default=LeadStatus.new, index=True)
    conversion_probability = Column(Integer, nullable=True)  # 0-100%
    expected_close_date = Column(Date, nullable=True)
    estimated_value = Column(Numeric(15, 2), nullable=True)

    # Conversion Information
    converted_date = Column(DateTime(timezone=True), nullable=True)
    interest_level = Column(SQLEnum(InterestLevel), default=InterestLevel.low)
    inquiry_type = Column(String(255), nullable=True)
    last_contacted_at = Column(Date, nullable=True)
    is_qualified = Column(Boolean, default=False)
    disqualification_reason = Column(Text, nullable=True)
    referral_source = Column(Text, nullable=True)

    # Owner and conversion references
    lead_owner_id = Column(UUID(as_uuid=True), nullable=True)  # References users.id
    converted_contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    converted_account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    converted_opportunity_id = Column(Integer, ForeignKey('opportunities.id', ondelete='SET NULL'), nullable=True)

    # Travel specific information
    travel_interests = Column(JSON, nullable=True)
    preferred_travel_date = Column(Date, nullable=True)
    number_of_travelers = Column(Integer, nullable=True)
    special_requirements = Column(Text, nullable=True)

    # Management fields
    follow_up_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    campaign_id = Column(String(255), nullable=True)
    score = Column(Integer, default=0, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    actor = relationship("Actor", back_populates="lead")
    converted_contact = relationship("Contact", foreign_keys=[converted_contact_id])
    converted_account = relationship("Account", foreign_keys=[converted_account_id])
    converted_opportunity = relationship("Opportunity", foreign_keys=[converted_opportunity_id])

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_lead_status_created', 'lead_status', 'created_at'),
        Index('idx_lead_probability_close', 'conversion_probability', 'expected_close_date'),
        Index('idx_lead_converted_date', 'converted_date'),
        Index('idx_lead_score_interest', 'score', 'interest_level'),
        Index('idx_lead_follow_up', 'follow_up_date'),
        Index('idx_lead_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Lead: {self.actor.first_name} {self.actor.last_name} - {self.lead_status}>"
