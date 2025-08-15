"""
Cancellation Policies module schemas
Contains Pydantic schemas for CancellationPolicy data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from common.enums import CancellationPolicyType


class CancellationRuleBase(BaseModel):
    """Base schema for a cancellation rule"""
    hours_before: int = Field(..., ge=0, description="Hours before service")
    refund_percentage: float = Field(..., ge=0, le=100, description="Refund percentage (0-100)")
    fee_amount: Optional[Decimal] = Field(None, ge=0, description="Cancellation fee amount")


class CancellationRuleCreate(CancellationRuleBase):
    """Schema for creating a cancellation rule"""
    pass


class CancellationRuleResponse(CancellationRuleBase):
    """Schema for cancellation rule response"""
    pass


class CancellationPolicyBase(BaseModel):
    """Base schema for Cancellation Policy"""
    name: str = Field(..., min_length=1, max_length=100, description="Policy name")
    code: Optional[str] = Field(None, max_length=50, description="Policy code")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: CancellationPolicyType = Field(CancellationPolicyType.moderate, description="Policy type")
    cancellation_rules: List[CancellationRuleCreate] = Field(..., min_items=1, description="Cancellation rules")
    modification_allowed: bool = Field(True, description="Modifications allowed")
    modification_deadline_hours: Optional[int] = Field(None, ge=0, description="Modification deadline (hours)")
    modification_fee: Optional[Decimal] = Field(None, ge=0, description="Modification fee")
    max_modifications: Optional[int] = Field(None, ge=0, description="Maximum modifications allowed")
    no_show_fee_percentage: Decimal = Field(100, ge=0, le=100, description="No-show fee percentage")
    no_show_fee_amount: Optional[Decimal] = Field(None, ge=0, description="No-show fee amount")
    exceptions: Optional[List[str]] = Field(None, description="Policy exceptions")
    peak_season_rules: Optional[Dict[str, Any]] = Field(None, description="Peak season rules")
    group_size_rules: Optional[Dict[str, Any]] = Field(None, description="Group size rules")
    is_active: bool = Field(True, description="Policy active status")
    is_default: bool = Field(False, description="Default policy status")

    @validator('cancellation_rules')
    def validate_cancellation_rules(cls, v):
        """Validate cancellation rules are properly ordered"""
        if not v:
            raise ValueError('At least one cancellation rule is required')

        # Sort by hours_before to validate ordering
        sorted_rules = sorted(v, key=lambda x: x.hours_before, reverse=True)

        # Check that refund percentages generally decrease as we get closer to service time
        for i in range(len(sorted_rules) - 1):
            current_rule = sorted_rules[i]
            next_rule = sorted_rules[i + 1]

            if current_rule.refund_percentage < next_rule.refund_percentage:
                raise ValueError('Refund percentages should generally decrease as time to service decreases')

        return v

    @validator('modification_deadline_hours')
    def validate_modification_deadline(cls, v, values):
        """Validate modification deadline makes sense"""
        if v is not None and not values.get('modification_allowed', True):
            raise ValueError('Modification deadline cannot be set if modifications are not allowed')
        return v

    @validator('max_modifications')
    def validate_max_modifications(cls, v, values):
        """Validate max modifications makes sense"""
        if v is not None and not values.get('modification_allowed', True):
            raise ValueError('Max modifications cannot be set if modifications are not allowed')
        return v


class CancellationPolicyCreate(CancellationPolicyBase):
    """Schema for creating a new Cancellation Policy"""
    pass


class CancellationPolicyUpdate(BaseModel):
    """Schema for updating a Cancellation Policy"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Policy name")
    code: Optional[str] = Field(None, max_length=50, description="Policy code")
    description: Optional[str] = Field(None, description="Policy description")
    policy_type: Optional[CancellationPolicyType] = Field(None, description="Policy type")
    cancellation_rules: Optional[List[CancellationRuleCreate]] = Field(None, min_items=1, description="Cancellation rules")
    modification_allowed: Optional[bool] = Field(None, description="Modifications allowed")
    modification_deadline_hours: Optional[int] = Field(None, ge=0, description="Modification deadline (hours)")
    modification_fee: Optional[Decimal] = Field(None, ge=0, description="Modification fee")
    max_modifications: Optional[int] = Field(None, ge=0, description="Maximum modifications allowed")
    no_show_fee_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="No-show fee percentage")
    no_show_fee_amount: Optional[Decimal] = Field(None, ge=0, description="No-show fee amount")
    exceptions: Optional[List[str]] = Field(None, description="Policy exceptions")
    peak_season_rules: Optional[Dict[str, Any]] = Field(None, description="Peak season rules")
    group_size_rules: Optional[Dict[str, Any]] = Field(None, description="Group size rules")
    is_active: Optional[bool] = Field(None, description="Policy active status")
    is_default: Optional[bool] = Field(None, description="Default policy status")

    @validator('cancellation_rules')
    def validate_cancellation_rules(cls, v):
        """Validate cancellation rules are properly ordered"""
        if v is not None and len(v) > 0:
            # Sort by hours_before to validate ordering
            sorted_rules = sorted(v, key=lambda x: x.hours_before, reverse=True)

            # Check that refund percentages generally decrease as we get closer to service time
            for i in range(len(sorted_rules) - 1):
                current_rule = sorted_rules[i]
                next_rule = sorted_rules[i + 1]

                if current_rule.refund_percentage < next_rule.refund_percentage:
                    raise ValueError('Refund percentages should generally decrease as time to service decreases')

        return v


class CancellationPolicyResponse(CancellationPolicyBase):
    """Schema for Cancellation Policy response"""
    id: int = Field(..., description="Cancellation policy ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    cancellation_rules: List[CancellationRuleResponse] = Field(..., description="Cancellation rules")

    model_config = ConfigDict(from_attributes=True)


class CancellationPolicyListResponse(BaseModel):
    """Schema for Cancellation Policy list response"""
    policies: List[CancellationPolicyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class CancellationCalculationRequest(BaseModel):
    """Schema for cancellation calculation request"""
    policy_id: int = Field(..., description="Cancellation policy ID")
    hours_before_service: int = Field(..., ge=0, description="Hours before service starts")
    booking_amount: Decimal = Field(..., gt=0, description="Total booking amount")
    group_size: Optional[int] = Field(None, ge=1, description="Group size")
    is_peak_season: bool = Field(False, description="Is peak season")


class CancellationCalculationResponse(BaseModel):
    """Schema for cancellation calculation response"""
    policy_name: str = Field(..., description="Policy name")
    policy_type: str = Field(..., description="Policy type")
    hours_before_service: int = Field(..., description="Hours before service")
    original_amount: Decimal = Field(..., description="Original booking amount")
    refund_percentage: float = Field(..., description="Refund percentage")
    refund_amount: Decimal = Field(..., description="Refund amount")
    cancellation_fee: Decimal = Field(..., description="Cancellation fee")
    net_refund: Decimal = Field(..., description="Net refund amount")
    can_modify: bool = Field(..., description="Can modify booking")
    modification_fee: Optional[Decimal] = Field(None, description="Modification fee if applicable")
    applied_rules: Dict[str, Any] = Field(..., description="Applied policy rules")

    model_config = ConfigDict(from_attributes=True)


class ModificationCheckRequest(BaseModel):
    """Schema for modification check request"""
    policy_id: int = Field(..., description="Cancellation policy ID")
    hours_before_service: int = Field(..., ge=0, description="Hours before service starts")
    current_modifications_count: int = Field(0, ge=0, description="Current number of modifications")


class ModificationCheckResponse(BaseModel):
    """Schema for modification check response"""
    policy_name: str = Field(..., description="Policy name")
    can_modify: bool = Field(..., description="Can modify booking")
    modification_allowed: bool = Field(..., description="Modifications allowed by policy")
    within_deadline: bool = Field(..., description="Within modification deadline")
    within_max_modifications: bool = Field(..., description="Within maximum modifications limit")
    modification_fee: Optional[Decimal] = Field(None, description="Modification fee")
    deadline_hours: Optional[int] = Field(None, description="Modification deadline hours")
    max_modifications: Optional[int] = Field(None, description="Maximum modifications allowed")
    current_modifications: int = Field(..., description="Current modifications count")

    model_config = ConfigDict(from_attributes=True)


class PolicyTemplateResponse(BaseModel):
    """Schema for predefined policy template"""
    name: str = Field(..., description="Template name")
    policy_type: CancellationPolicyType = Field(..., description="Policy type")
    description: str = Field(..., description="Template description")
    recommended_for: List[str] = Field(..., description="Recommended service types")
    template_rules: List[CancellationRuleResponse] = Field(..., description="Template rules")

    model_config = ConfigDict(from_attributes=True)


class PolicyComparisonRequest(BaseModel):
    """Schema for policy comparison request"""
    policy_ids: List[int] = Field(..., min_items=2, max_items=5, description="Policy IDs to compare")
    scenario_hours: List[int] = Field(..., min_items=1, description="Hours before service scenarios")
    booking_amount: Decimal = Field(100.0, gt=0, description="Booking amount for comparison")


class PolicyComparisonResponse(BaseModel):
    """Schema for policy comparison response"""
    policies: List[Dict[str, Any]] = Field(..., description="Policy comparison data")
    scenarios: List[Dict[str, Any]] = Field(..., description="Scenario comparisons")
    recommendations: List[str] = Field(..., description="Recommendations")

    model_config = ConfigDict(from_attributes=True)
