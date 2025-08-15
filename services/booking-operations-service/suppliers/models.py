"""
Suppliers module models
Contains the Supplier model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey,
    Enum as SQLEnum, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import SupplierType, SupplierStatus

# ============================================
# SUPPLIERS TABLE
# ============================================

class Supplier(Base):
    """Supplier management for travel services"""
    __tablename__ = "suppliers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic Information
    code = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    type = Column(SQLEnum(SupplierType), default=SupplierType.company)

    # Contact Information (JSON fields)
    contact_info = Column(JSON, nullable=True)  # {phones, emails, websites, social_media}
    address = Column(JSON, nullable=True)  # {street, city, state, country, postal_code, coordinates}

    # Financial Information
    banking_info = Column(JSON, nullable=True)  # {accounts, swift, payment_methods}

    # Certifications and Compliance
    certifications = Column(JSON, nullable=True)  # {licenses, insurance, quality_seals}

    # Service Configuration
    allowed_services = Column(JSON, nullable=True)  # {ticket, tour, restaurant, equipment, guide, transport, transfer}
    allowed_destinations = Column(JSON, nullable=True)  # destination ids {1, 3, 5, 9}

    # Status and Rating
    status = Column(SQLEnum(SupplierStatus), default=SupplierStatus.active, index=True)
    ratings = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00

    # Additional Data
    supplier_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    services = relationship("Service", back_populates="supplier", cascade="all, delete-orphan")

    # Table arguments for indexes and constraints
    __table_args__ = (
        UniqueConstraint('code', 'deleted_at', name='uq_supplier_code_deleted'),
        Index('idx_supplier_code', 'code'),
        Index('idx_supplier_status', 'status'),
        Index('idx_supplier_name_status', 'name', 'status'),
        Index('idx_supplier_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Supplier(id={self.id}, code='{self.code}', name='{self.name}', status='{self.status}')>"
