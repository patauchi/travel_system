"""
Countries module models
Contains the Country model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base

# ============================================
# COUNTRIES TABLE
# ============================================

class Country(Base):
    """Countries reference table"""
    __tablename__ = "countries"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Country Information
    code = Column(String(2), nullable=False, unique=True)  # ISO 3166-1 alpha-2
    code3 = Column(String(3), nullable=False, unique=True)  # ISO 3166-1 alpha-3
    name = Column(String(100), nullable=False)
    official_name = Column(String(200), nullable=True)
    native_name = Column(String(100), nullable=True)

    # Geographic Information
    continent = Column(String(50), nullable=True)
    region = Column(String(100), nullable=True)
    subregion = Column(String(100), nullable=True)
    capital = Column(String(100), nullable=True)

    # Additional Information
    currency_code = Column(String(3), nullable=True)
    phone_code = Column(String(10), nullable=True)
    timezone_codes = Column(JSON, nullable=True)  # Array of timezone codes
    languages = Column(JSON, nullable=True)  # Array of language codes

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    destinations = relationship("Destination", back_populates="country", cascade="all, delete-orphan")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_country_code', 'code'),
        Index('idx_country_active', 'is_active'),
        Index('idx_country_continent', 'continent'),
    )

    def __repr__(self):
        return f"<Country(id={self.id}, code='{self.code}', name='{self.name}')>"
