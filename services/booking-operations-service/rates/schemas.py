"""
Rates module schemas
Contains Pydantic schemas for Rate data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from common.enums import RateType, PricingModel, SeasonType, PassengerType


# ============================================
# RATE SCHEMAS
# ============================================

class RateBase(BaseModel):
    """Base schema for Rate"""
    service_id: int = Field(..., description="Service ID")
    rate_code: Optional[str] = Field(None, max_length=50, description="Rate code")
    name: str = Field(..., min_length=1, max_length=200, description="Rate name")
    description: Optional[str] = Field(None, description="Rate description")
    pricing_model: PricingModel = Field(..., description="Pricing model")
    valid_from: date = Field(..., description="Valid from date")
    valid_to: date = Field(..., description="Valid to date")
    season_type: SeasonType = Field(SeasonType.LOW, description="Season type")
    applicable_days: Optional[List[int]] = Field(None, description="Applicable days of week (1-7)")
    blocked_dates: Optional[List[str]] = Field(None, description="Blocked dates (ISO format)")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    is_active: bool = Field(True, description="Active status")
    is_promotional: bool = Field(False, description="Promotional rate")
    priority: int = Field(0, description="Priority order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('valid_to')
    def validate_date_range(cls, v, values):
        valid_from = values.get('valid_from')
        if valid_from and v < valid_from:
            raise ValueError('Valid to date must be after valid from date')
        return v

    @validator('applicable_days')
    def validate_applicable_days(cls, v):
        if v is not None:
            for day in v:
                if not (1 <= day <= 7):
                    raise ValueError('Day must be between 1 (Monday) and 7 (Sunday)')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        return v.upper()


class RateCreate(RateBase):
    """Schema for creating a new Rate"""
    pass


class RateUpdate(BaseModel):
    """Schema for updating a Rate"""
    rate_code: Optional[str] = Field(None, max_length=50, description="Rate code")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Rate name")
    description: Optional[str] = Field(None, description="Rate description")
    pricing_model: Optional[PricingModel] = Field(None, description="Pricing model")
    valid_from: Optional[date] = Field(None, description="Valid from date")
    valid_to: Optional[date] = Field(None, description="Valid to date")
    season_type: Optional[SeasonType] = Field(None, description="Season type")
    applicable_days: Optional[List[int]] = Field(None, description="Applicable days of week")
    blocked_dates: Optional[List[str]] = Field(None, description="Blocked dates")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Currency code")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_promotional: Optional[bool] = Field(None, description="Promotional rate")
    priority: Optional[int] = Field(None, description="Priority order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RateResponse(RateBase):
    """Schema for Rate response"""
    id: int = Field(..., description="Rate ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RATE VARIANT SCHEMAS
# ============================================

class RateVariantBase(BaseModel):
    """Base schema for Rate Variant"""
    rate_id: int = Field(..., description="Rate ID")
    variant_code: str = Field(..., min_length=1, max_length=50, description="Variant code")
    variant_name: str = Field(..., min_length=1, max_length=255, description="Variant name")
    description: Optional[str] = Field(None, description="Variant description")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Variant specifications")
    is_default: bool = Field(False, description="Is default variant")
    is_active: bool = Field(True, description="Active status")
    display_order: int = Field(0, description="Display order")


class RateVariantCreate(RateVariantBase):
    """Schema for creating a Rate Variant"""
    pass


class RateVariantUpdate(BaseModel):
    """Schema for updating a Rate Variant"""
    variant_code: Optional[str] = Field(None, min_length=1, max_length=50, description="Variant code")
    variant_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Variant name")
    description: Optional[str] = Field(None, description="Variant description")
    specifications: Optional[Dict[str, Any]] = Field(None, description="Variant specifications")
    is_default: Optional[bool] = Field(None, description="Is default variant")
    is_active: Optional[bool] = Field(None, description="Active status")
    display_order: Optional[int] = Field(None, description="Display order")


class RateVariantResponse(RateVariantBase):
    """Schema for Rate Variant response"""
    id: int = Field(..., description="Rate variant ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RATE PASSENGER PRICE SCHEMAS
# ============================================

class RatePassengerPriceBase(BaseModel):
    """Base schema for Rate Passenger Price"""
    rate_id: int = Field(..., description="Rate ID")
    variant_id: Optional[int] = Field(None, description="Variant ID")
    passenger_category: PassengerType = Field(PassengerType.ADULT, description="Passenger category")
    nationality_type: str = Field("all", description="Nationality type")
    price: Optional[Decimal] = Field(None, ge=0, description="Absolute price")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    requires_documentation: bool = Field(False, description="Requires documentation")
    documentation_types: Optional[List[str]] = Field(None, description="Required documentation types")
    special_conditions: Optional[Dict[str, Any]] = Field(None, description="Special conditions")
    min_age_override: Optional[int] = Field(None, ge=0, description="Minimum age override")
    max_age_override: Optional[int] = Field(None, ge=0, description="Maximum age override")
    min_passengers: int = Field(1, ge=1, description="Minimum passengers")
    max_passengers: Optional[int] = Field(None, ge=1, description="Maximum passengers")
    requires_adult_supervision: bool = Field(False, description="Requires adult supervision")
    is_active: bool = Field(True, description="Active status")
    display_order: int = Field(0, description="Display order")
    notes: Optional[str] = Field(None, description="Internal notes")
    public_notes: Optional[str] = Field(None, description="Public notes")

    @validator('nationality_type')
    def validate_nationality_type(cls, v):
        valid_types = ['local', 'foreign', 'all']
        if v.lower() not in valid_types:
            raise ValueError(f'Nationality type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('max_age_override')
    def validate_age_range(cls, v, values):
        min_age = values.get('min_age_override')
        if v is not None and min_age is not None and v < min_age:
            raise ValueError('Maximum age must be greater than minimum age')
        return v


class RatePassengerPriceCreate(RatePassengerPriceBase):
    """Schema for creating a Rate Passenger Price"""
    pass


class RatePassengerPriceUpdate(BaseModel):
    """Schema for updating a Rate Passenger Price"""
    passenger_category: Optional[PassengerType] = Field(None, description="Passenger category")
    nationality_type: Optional[str] = Field(None, description="Nationality type")
    price: Optional[Decimal] = Field(None, ge=0, description="Absolute price")
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Discount amount")
    requires_documentation: Optional[bool] = Field(None, description="Requires documentation")
    documentation_types: Optional[List[str]] = Field(None, description="Required documentation types")
    special_conditions: Optional[Dict[str, Any]] = Field(None, description="Special conditions")
    min_age_override: Optional[int] = Field(None, ge=0, description="Minimum age override")
    max_age_override: Optional[int] = Field(None, ge=0, description="Maximum age override")
    min_passengers: Optional[int] = Field(None, ge=1, description="Minimum passengers")
    max_passengers: Optional[int] = Field(None, ge=1, description="Maximum passengers")
    requires_adult_supervision: Optional[bool] = Field(None, description="Requires adult supervision")
    is_active: Optional[bool] = Field(None, description="Active status")
    display_order: Optional[int] = Field(None, description="Display order")
    notes: Optional[str] = Field(None, description="Internal notes")
    public_notes: Optional[str] = Field(None, description="Public notes")


class RatePassengerPriceResponse(RatePassengerPriceBase):
    """Schema for Rate Passenger Price response"""
    id: int = Field(..., description="Rate passenger price ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PACKAGE RATE SCHEMAS
# ============================================

class PackageRateBase(BaseModel):
    """Base schema for Package Rate"""
    package_code: Optional[str] = Field(None, max_length=50, description="Package code")
    package_name: str = Field(..., min_length=1, max_length=255, description="Package name")
    description: Optional[str] = Field(None, description="Package description")
    included_services: List[int] = Field(..., min_items=1, description="Included service IDs")
    package_price: Decimal = Field(..., gt=0, description="Package price")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    valid_from: date = Field(..., description="Valid from date")
    valid_to: date = Field(..., description="Valid to date")
    min_passengers: int = Field(1, ge=1, description="Minimum passengers")
    max_passengers: Optional[int] = Field(None, ge=1, description="Maximum passengers")
    min_duration_days: int = Field(1, ge=1, description="Minimum duration days")
    advance_booking_days: int = Field(0, ge=0, description="Advance booking days")
    cancellation_policy_id: Optional[int] = Field(None, description="Cancellation policy ID")
    early_bird_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Early bird discount %")
    early_bird_days_before: Optional[int] = Field(None, ge=0, description="Early bird days before")
    group_discount_threshold: Optional[int] = Field(None, ge=1, description="Group discount threshold")
    group_discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Group discount %")
    is_active: bool = Field(True, description="Active status")
    is_featured: bool = Field(False, description="Featured package")
    priority: int = Field(0, description="Priority order")
    inclusions: Optional[List[str]] = Field(None, description="Package inclusions")
    exclusions: Optional[List[str]] = Field(None, description="Package exclusions")
    special_conditions: Optional[Dict[str, Any]] = Field(None, description="Special conditions")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('valid_to')
    def validate_date_range(cls, v, values):
        valid_from = values.get('valid_from')
        if valid_from and v < valid_from:
            raise ValueError('Valid to date must be after valid from date')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        return v.upper()


class PackageRateCreate(PackageRateBase):
    """Schema for creating a Package Rate"""
    pass


class PackageRateUpdate(BaseModel):
    """Schema for updating a Package Rate"""
    package_code: Optional[str] = Field(None, max_length=50, description="Package code")
    package_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Package name")
    description: Optional[str] = Field(None, description="Package description")
    included_services: Optional[List[int]] = Field(None, min_items=1, description="Included service IDs")
    package_price: Optional[Decimal] = Field(None, gt=0, description="Package price")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Currency code")
    valid_from: Optional[date] = Field(None, description="Valid from date")
    valid_to: Optional[date] = Field(None, description="Valid to date")
    min_passengers: Optional[int] = Field(None, ge=1, description="Minimum passengers")
    max_passengers: Optional[int] = Field(None, ge=1, description="Maximum passengers")
    min_duration_days: Optional[int] = Field(None, ge=1, description="Minimum duration days")
    advance_booking_days: Optional[int] = Field(None, ge=0, description="Advance booking days")
    cancellation_policy_id: Optional[int] = Field(None, description="Cancellation policy ID")
    is_active: Optional[bool] = Field(None, description="Active status")
    is_featured: Optional[bool] = Field(None, description="Featured package")
    priority: Optional[int] = Field(None, description="Priority order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PackageRateResponse(PackageRateBase):
    """Schema for Package Rate response"""
    id: int = Field(..., description="Package rate ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RATE LIST RESPONSES
# ============================================

class RateListResponse(BaseModel):
    """Schema for Rate list response"""
    rates: List[RateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class RateVariantListResponse(BaseModel):
    """Schema for Rate Variant list response"""
    variants: List[RateVariantResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class PackageRateListResponse(BaseModel):
    """Schema for Package Rate list response"""
    packages: List[PackageRateResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# PRICING CALCULATION SCHEMAS
# ============================================

class PriceCalculationRequest(BaseModel):
    """Schema for price calculation request"""
    service_id: int = Field(..., description="Service ID")
    service_date: date = Field(..., description="Service date")
    passengers: List[Dict[str, Any]] = Field(..., min_items=1, description="Passenger details")
    variant_id: Optional[int] = Field(None, description="Rate variant ID")
    apply_discounts: bool = Field(True, description="Apply discounts")


class PriceCalculationResponse(BaseModel):
    """Schema for price calculation response"""
    service_id: int
    service_date: date
    rate_id: int
    rate_name: str
    variant_id: Optional[int]
    variant_name: Optional[str]
    passenger_prices: List[Dict[str, Any]]
    subtotal: Decimal
    discounts: Decimal
    total_price: Decimal
    currency: str
    breakdown: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# RATE AVAILABILITY SCHEMAS
# ============================================

class RateAvailabilityRequest(BaseModel):
    """Schema for rate availability request"""
    service_id: int = Field(..., description="Service ID")
    check_date: date = Field(..., description="Check date")
    passengers: int = Field(1, ge=1, description="Number of passengers")


class RateAvailabilityResponse(BaseModel):
    """Schema for rate availability response"""
    service_id: int
    check_date: date
    available_rates: List[RateResponse]
    recommended_rate: Optional[RateResponse]
    capacity_available: bool
    minimum_price: Optional[Decimal]
    maximum_price: Optional[Decimal]

    model_config = ConfigDict(from_attributes=True)
