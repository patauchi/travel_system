"""
Cancellation Policies module models
Contains the CancellationPolicy model and related database definitions
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, ForeignKey,
    Enum as SQLEnum, JSON, Numeric, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from models_base import Base
from common.enums import CancellationPolicyType


class CancellationPolicy(Base):
    """Cancellation policies for services"""
    __tablename__ = "cancellation_policies"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Policy Information
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    policy_type = Column(SQLEnum(CancellationPolicyType), default=CancellationPolicyType.moderate)

    # Cancellation Rules (JSON structure for flexibility)
    cancellation_rules = Column(JSON, nullable=False)
    """ Example structure:
    [
        {
            "hours_before": 72,
            "refund_percentage": 100,
            "fee_amount": 0
        },
        {
            "hours_before": 48,
            "refund_percentage": 50,
            "fee_amount": 25
        },
        {
            "hours_before": 24,
            "refund_percentage": 0,
            "fee_amount": 50
        }
    ]
    """

    # Modification Rules
    modification_allowed = Column(Boolean, default=True)
    modification_deadline_hours = Column(Integer, nullable=True)
    modification_fee = Column(Numeric(10, 2), nullable=True)
    max_modifications = Column(Integer, nullable=True)

    # No-show Policy
    no_show_fee_percentage = Column(Numeric(5, 2), default=100)
    no_show_fee_amount = Column(Numeric(10, 2), nullable=True)

    # Special Conditions
    exceptions = Column(JSON, nullable=True)  # Weather, strikes, etc.
    peak_season_rules = Column(JSON, nullable=True)  # Different rules for peak season
    group_size_rules = Column(JSON, nullable=True)  # Different rules based on group size

    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    services = relationship("Service", back_populates="cancellation_policy")

    # Table arguments for indexes
    __table_args__ = (
        Index('idx_cancellation_policy_code', 'code'),
        Index('idx_cancellation_policy_type', 'policy_type'),
        Index('idx_cancellation_policy_active', 'is_active'),
        Index('idx_cancellation_policy_default', 'is_default'),
        Index('idx_cancellation_policy_deleted', 'deleted_at'),
    )

    def __repr__(self):
        return f"<CancellationPolicy(id={self.id}, code='{self.code}', name='{self.name}', type='{self.policy_type}')>"

    def get_refund_percentage(self, hours_before_service: int) -> float:
        """
        Calculate refund percentage based on hours before service

        Args:
            hours_before_service: Hours before the service starts

        Returns:
            Refund percentage (0-100)
        """
        if not self.cancellation_rules:
            return 0.0

        # Sort rules by hours_before in descending order
        sorted_rules = sorted(self.cancellation_rules, key=lambda x: x.get('hours_before', 0), reverse=True)

        for rule in sorted_rules:
            if hours_before_service >= rule.get('hours_before', 0):
                return float(rule.get('refund_percentage', 0))

        # If no rule matches, return 0% refund
        return 0.0

    def get_cancellation_fee(self, hours_before_service: int) -> float:
        """
        Calculate cancellation fee based on hours before service

        Args:
            hours_before_service: Hours before the service starts

        Returns:
            Cancellation fee amount
        """
        if not self.cancellation_rules:
            return 0.0

        # Sort rules by hours_before in descending order
        sorted_rules = sorted(self.cancellation_rules, key=lambda x: x.get('hours_before', 0), reverse=True)

        for rule in sorted_rules:
            if hours_before_service >= rule.get('hours_before', 0):
                return float(rule.get('fee_amount', 0))

        # If no rule matches, return maximum fee (usually from the most restrictive rule)
        if sorted_rules:
            return float(sorted_rules[-1].get('fee_amount', 0))

        return 0.0

    def can_modify(self, hours_before_service: int) -> bool:
        """
        Check if modification is allowed based on hours before service

        Args:
            hours_before_service: Hours before the service starts

        Returns:
            True if modification is allowed, False otherwise
        """
        if not self.modification_allowed:
            return False

        if self.modification_deadline_hours is None:
            return True

        return hours_before_service >= self.modification_deadline_hours

    def is_flexible_policy(self) -> bool:
        """Check if this is a flexible cancellation policy"""
        return self.policy_type == CancellationPolicyType.flexible

    def is_strict_policy(self) -> bool:
        """Check if this is a strict cancellation policy"""
        return self.policy_type in [
            CancellationPolicyType.strict,
            CancellationPolicyType.super_strict,
            CancellationPolicyType.non_refundable
        ]
