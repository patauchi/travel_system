"""
Industry Models for CRM Service
Industry-specific models and relationships
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from core.models import Base

# ============================================
# INDUSTRIES TABLE
# ============================================

class Industry(Base):
    """Industries for categorizing accounts"""
    __tablename__ = "industries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    code = Column(String(20), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('industries.id'), nullable=True)
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = relationship("Account", back_populates="industry")
    parent = relationship("Industry", remote_side=[id])
    children = relationship("Industry", back_populates="parent")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_industry_code', 'code'),
        Index('idx_industry_active', 'is_active'),
    )

    def __repr__(self):
        return f"<Industry: {self.name}>"
