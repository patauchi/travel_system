"""
Destinations module models
Contains the Destination model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Numeric, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base

# ============================================
# DESTINATIONS TABLE
# ============================================

class Destination(Base):
    """Travel destinations"""
    __tablename__ = "destinations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign Keys
    country_id = Column(Integer, ForeignKey('countries.id'), nullable=False)
    parent_destination_id = Column(Integer, ForeignKey('destinations.id'), nullable=True)

    # Destination Information
    code = Column(String(20), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # city, region, area, district, landmark

    # Geographic Information
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    altitude_meters = Column(Integer, nullable=True)
    timezone = Column(String(50), nullable=True)

    # Description
    description = Column(Text, nullable=True)
    highlights = Column(JSON, nullable=True)
    best_time_to_visit = Column(JSON, nullable=True)  # {months: [1,2,3], notes: "..."}

    # Travel Information
    airport_codes = Column(JSON, nullable=True)  # ["LIM", "CUZ"]
    nearest_airport_distance_km = Column(Numeric(10, 2), nullable=True)
    requires_special_permit = Column(Boolean, default=False)

    # Tourism Data
    tourism_rating = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00
    safety_rating = Column(Numeric(3, 2), nullable=True)
    popularity_score = Column(Integer, nullable=True)  # 1-100

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Metadata
    destination_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    country = relationship("Country", back_populates="destinations")
    parent_destination = relationship("Destination", remote_side=[id])

    # Table arguments for indexes
    __table_args__ = (
        UniqueConstraint('code', 'deleted_at', name='uq_destination_code_deleted'),
        Index('idx_destination_country', 'country_id'),
        Index('idx_destination_parent', 'parent_destination_id'),
        Index('idx_destination_type', 'type'),
        Index('idx_destination_active', 'is_active'),
        Index('idx_destination_featured', 'is_featured'),
    )

    def __repr__(self):
        return f"<Destination(id={self.id}, code='{self.code}', name='{self.name}', type='{self.type}')>"
