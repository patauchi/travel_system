"""
Opportunity Models for CRM Service
Opportunity-specific models and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, Date, JSON, Numeric, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from core.models import Base
from core.enums import OpportunityStage, TravelType, BudgetLevel

# ============================================
# OPPORTUNITIES TABLE
# ============================================

class Opportunity(Base):
    """Opportunity management for sales pipeline"""
    __tablename__ = "opportunities"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic information
    name = Column(String(200), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True)
    contact_id = Column(Integer, ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False)  # References users.id
    campaign_id = Column(Integer, nullable=True)  # References campaigns if exists

    # Opportunity information
    stage = Column(SQLEnum(OpportunityStage), default=OpportunityStage.PROSPECTING, index=True)
    probability = Column(Integer, default=25)  # 0-100%
    amount = Column(Numeric(15, 2), nullable=True)
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)

    # Travel Information
    travel_type = Column(SQLEnum(TravelType), nullable=True)
    destinations = Column(JSON, nullable=True)  # Array of destination_ids
    departure_date = Column(Date, nullable=True)
    return_date = Column(Date, nullable=True)
    number_of_adults = Column(Integer, nullable=True)
    number_of_children = Column(Integer, nullable=True)

    # Travel details
    room_configuration = Column(JSON, nullable=True)  # ["1 double", "1 single"]
    budget_level = Column(SQLEnum(BudgetLevel), nullable=True)
    special_requests = Column(Text, nullable=True)

    # Status
    is_closed = Column(Boolean, default=False)
    close_reason = Column(String(255), nullable=True)
    loss_reason = Column(Text, nullable=True)

    # Competition
    competitors = Column(JSON, nullable=True)
    next_steps = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="opportunities")
    contact = relationship("Contact", back_populates="opportunities")
    quotes = relationship("Quote", back_populates="opportunity", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_opportunity_stage_close', 'stage', 'expected_close_date'),
        Index('idx_opportunity_owner_stage', 'owner_id', 'stage'),
        Index('idx_opportunity_departure_stage', 'departure_date', 'stage'),
        Index('idx_opportunity_closed', 'is_closed'),
        Index('idx_opportunity_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Opportunity: {self.name} - {self.stage} (${self.amount or 0})>"
