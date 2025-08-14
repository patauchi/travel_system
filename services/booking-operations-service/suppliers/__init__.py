"""
Suppliers module for Booking Operations Service
Handles supplier management and operations
"""

from .models import Supplier
from .schemas import (
    # Core Supplier Schemas
    SupplierResponse,
    SupplierCreate,
    SupplierUpdate,
    SupplierListResponse,

    # Search and Filter Schemas
    SupplierSearch,
    SupplierSearchResponse,
    SupplierFilter,

    # Statistics and Performance Schemas
    SupplierStatistics,
    SupplierPerformance,

    # Management Schemas
    SupplierStatusUpdate,
    SupplierRatingUpdate,
    SupplierContact,
    SupplierContractInfo,
    SupplierOnboarding,

    # Integration Schemas
    SupplierIntegration,

    # Component Schemas
    ContactInfo,
    Address,
    BankingInfo,
    Certifications
)
from .endpoints import router

__all__ = [
    # Models
    'Supplier',

    # Core Supplier Schemas
    'SupplierResponse',
    'SupplierCreate',
    'SupplierUpdate',
    'SupplierListResponse',

    # Search and Filter Schemas
    'SupplierSearch',
    'SupplierSearchResponse',
    'SupplierFilter',

    # Statistics and Performance Schemas
    'SupplierStatistics',
    'SupplierPerformance',

    # Management Schemas
    'SupplierStatusUpdate',
    'SupplierRatingUpdate',
    'SupplierContact',
    'SupplierContractInfo',
    'SupplierOnboarding',

    # Integration Schemas
    'SupplierIntegration',

    # Component Schemas
    'ContactInfo',
    'Address',
    'BankingInfo',
    'Certifications',

    # Router
    'router'
]
