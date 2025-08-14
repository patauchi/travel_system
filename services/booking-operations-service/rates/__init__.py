"""
Rates module for Booking Operations Service
Handles rate and pricing management
"""

from .models import (
    Rate,
    RateVariant,
    RatePassengerPrice,
    RateTierPrice,
    PackageRate,
    PackageRatePassengerPrice
)
from .schemas import (
    RateResponse,
    RateCreate,
    RateUpdate,
    RateListResponse,
    RateVariantResponse,
    RateVariantCreate,
    RateVariantUpdate,
    RateVariantListResponse,
    RatePassengerPriceResponse,
    RatePassengerPriceCreate,
    RatePassengerPriceUpdate,
    PackageRateResponse,
    PackageRateCreate,
    PackageRateUpdate,
    PackageRateListResponse,
    PriceCalculationRequest,
    PriceCalculationResponse,
    RateAvailabilityRequest,
    RateAvailabilityResponse
)
from .endpoints import router

__all__ = [
    # Models
    'Rate',
    'RateVariant',
    'RatePassengerPrice',
    'RateTierPrice',
    'PackageRate',
    'PackageRatePassengerPrice',

    # Rate Schemas
    'RateResponse',
    'RateCreate',
    'RateUpdate',
    'RateListResponse',

    # Rate Variant Schemas
    'RateVariantResponse',
    'RateVariantCreate',
    'RateVariantUpdate',
    'RateVariantListResponse',

    # Rate Passenger Price Schemas
    'RatePassengerPriceResponse',
    'RatePassengerPriceCreate',
    'RatePassengerPriceUpdate',

    # Package Rate Schemas
    'PackageRateResponse',
    'PackageRateCreate',
    'PackageRateUpdate',
    'PackageRateListResponse',

    # Calculation Schemas
    'PriceCalculationRequest',
    'PriceCalculationResponse',
    'RateAvailabilityRequest',
    'RateAvailabilityResponse',

    # Router
    'router'
]
