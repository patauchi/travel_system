"""
Suppliers module schemas
Contains Pydantic schemas for Supplier data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from common.enums import SupplierType, SupplierStatus


# ============================================
# CONTACT INFO SCHEMAS
# ============================================

class ContactInfo(BaseModel):
    """Schema for supplier contact information"""
    phones: Optional[List[str]] = Field(None, description="Phone numbers")
    emails: Optional[List[EmailStr]] = Field(None, description="Email addresses")
    websites: Optional[List[str]] = Field(None, description="Website URLs")
    social_media: Optional[Dict[str, str]] = Field(None, description="Social media accounts")

    @validator('phones')
    def validate_phones(cls, v):
        if v is not None:
            for phone in v:
                if not isinstance(phone, str) or len(phone.strip()) == 0:
                    raise ValueError('Phone numbers must be non-empty strings')
        return v

    @validator('websites')
    def validate_websites(cls, v):
        if v is not None:
            for website in v:
                if not isinstance(website, str) or not (website.startswith('http://') or website.startswith('https://')):
                    raise ValueError('Websites must be valid URLs starting with http:// or https://')
        return v


class Address(BaseModel):
    """Schema for supplier address"""
    street: Optional[str] = Field(None, max_length=500, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    country: Optional[str] = Field(None, min_length=2, max_length=3, description="Country code")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal code")
    coordinates: Optional[Dict[str, float]] = Field(None, description="GPS coordinates")

    @validator('country')
    def validate_country(cls, v):
        if v is not None:
            return v.upper()
        return v

    @validator('coordinates')
    def validate_coordinates(cls, v):
        if v is not None:
            if 'latitude' in v and 'longitude' in v:
                lat = v['latitude']
                lng = v['longitude']
                if not (-90 <= lat <= 90):
                    raise ValueError('Latitude must be between -90 and 90')
                if not (-180 <= lng <= 180):
                    raise ValueError('Longitude must be between -180 and 180')
        return v


class BankingInfo(BaseModel):
    """Schema for supplier banking information"""
    accounts: Optional[List[Dict[str, str]]] = Field(None, description="Bank accounts")
    swift: Optional[str] = Field(None, max_length=11, description="SWIFT code")
    payment_methods: Optional[List[str]] = Field(None, description="Accepted payment methods")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    currency_preferences: Optional[List[str]] = Field(None, description="Preferred currencies")

    @validator('swift')
    def validate_swift(cls, v):
        if v is not None and len(v.strip()) > 0:
            v = v.strip().upper()
            if not (8 <= len(v) <= 11):
                raise ValueError('SWIFT code must be 8-11 characters long')
        return v

    @validator('payment_methods')
    def validate_payment_methods(cls, v):
        if v is not None:
            valid_methods = ['bank_transfer', 'credit_card', 'cash', 'check', 'paypal', 'cryptocurrency']
            for method in v:
                if method.lower() not in valid_methods:
                    raise ValueError(f'Payment method must be one of: {", ".join(valid_methods)}')
        return v


class Certifications(BaseModel):
    """Schema for supplier certifications"""
    licenses: Optional[List[Dict[str, Any]]] = Field(None, description="Business licenses")
    insurance: Optional[List[Dict[str, Any]]] = Field(None, description="Insurance policies")
    quality_seals: Optional[List[str]] = Field(None, description="Quality certifications")
    accreditations: Optional[List[str]] = Field(None, description="Industry accreditations")
    certifications_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional certification data")


# ============================================
# SUPPLIER SCHEMAS
# ============================================

class SupplierBase(BaseModel):
    """Base schema for Supplier"""
    code: str = Field(..., min_length=1, max_length=20, description="Supplier code")
    name: str = Field(..., min_length=1, max_length=255, description="Supplier name")
    legal_name: Optional[str] = Field(None, max_length=255, description="Legal business name")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    type: SupplierType = Field(SupplierType.company, description="Supplier type")
    contact_info: Optional[ContactInfo] = Field(None, description="Contact information")
    address: Optional[Address] = Field(None, description="Business address")
    banking_info: Optional[BankingInfo] = Field(None, description="Banking information")
    certifications: Optional[Certifications] = Field(None, description="Certifications and compliance")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed service types")
    allowed_destinations: Optional[List[int]] = Field(None, description="Allowed destination IDs")
    status: SupplierStatus = Field(SupplierStatus.active, description="Supplier status")
    ratings: Optional[Decimal] = Field(None, ge=0, le=5, description="Supplier rating (0-5)")
    supplier_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('code')
    def validate_code(cls, v):
        # Code should be alphanumeric and may contain hyphens/underscores
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Supplier code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()

    @validator('allowed_services')
    def validate_allowed_services(cls, v):
        if v is not None:
            valid_services = [
                'accommodation', 'transfer', 'tour', 'transport', 'restaurant',
                'ticket', 'guide', 'equipment', 'other'
            ]
            for service in v:
                if service.lower() not in valid_services:
                    raise ValueError(f'Service type must be one of: {", ".join(valid_services)}')
        return v

    @validator('allowed_destinations')
    def validate_allowed_destinations(cls, v):
        if v is not None:
            for dest_id in v:
                if not isinstance(dest_id, int) or dest_id <= 0:
                    raise ValueError('Destination IDs must be positive integers')
        return v


class SupplierCreate(SupplierBase):
    """Schema for creating a new Supplier"""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a Supplier"""
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Supplier code")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Supplier name")
    legal_name: Optional[str] = Field(None, max_length=255, description="Legal business name")
    tax_id: Optional[str] = Field(None, max_length=50, description="Tax identification number")
    type: Optional[SupplierType] = Field(None, description="Supplier type")
    contact_info: Optional[ContactInfo] = Field(None, description="Contact information")
    address: Optional[Address] = Field(None, description="Business address")
    banking_info: Optional[BankingInfo] = Field(None, description="Banking information")
    certifications: Optional[Certifications] = Field(None, description="Certifications and compliance")
    allowed_services: Optional[List[str]] = Field(None, description="Allowed service types")
    allowed_destinations: Optional[List[int]] = Field(None, description="Allowed destination IDs")
    status: Optional[SupplierStatus] = Field(None, description="Supplier status")
    ratings: Optional[Decimal] = Field(None, ge=0, le=5, description="Supplier rating (0-5)")
    supplier_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('code')
    def validate_code(cls, v):
        if v is not None:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Supplier code must be alphanumeric (hyphens and underscores allowed)')
            return v.upper()
        return v

    @validator('allowed_services')
    def validate_allowed_services(cls, v):
        if v is not None:
            valid_services = [
                'accommodation', 'transfer', 'tour', 'transport', 'restaurant',
                'ticket', 'guide', 'equipment', 'other'
            ]
            for service in v:
                if service.lower() not in valid_services:
                    raise ValueError(f'Service type must be one of: {", ".join(valid_services)}')
        return v

    @validator('allowed_destinations')
    def validate_allowed_destinations(cls, v):
        if v is not None:
            for dest_id in v:
                if not isinstance(dest_id, int) or dest_id <= 0:
                    raise ValueError('Destination IDs must be positive integers')
        return v


class SupplierResponse(SupplierBase):
    """Schema for Supplier response"""
    id: int = Field(..., description="Supplier ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    # Computed fields
    total_services: Optional[int] = Field(None, description="Total number of services")
    active_services: Optional[int] = Field(None, description="Number of active services")
    last_booking_date: Optional[datetime] = Field(None, description="Last booking date")
    performance_score: Optional[Decimal] = Field(None, description="Performance score")

    model_config = ConfigDict(from_attributes=True)


class SupplierListResponse(BaseModel):
    """Schema for Supplier list response"""
    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SUPPLIER SEARCH AND FILTER SCHEMAS
# ============================================

class SupplierSearch(BaseModel):
    """Schema for supplier search results"""
    id: int
    code: str
    name: str
    type: str
    status: str
    ratings: Optional[Decimal]
    city: Optional[str]
    country: Optional[str]
    allowed_services: Optional[List[str]]

    model_config = ConfigDict(from_attributes=True)


class SupplierSearchResponse(BaseModel):
    """Schema for supplier search response"""
    results: List[SupplierSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)


class SupplierFilter(BaseModel):
    """Schema for supplier filtering"""
    types: Optional[List[SupplierType]] = Field(None, description="Filter by supplier types")
    statuses: Optional[List[SupplierStatus]] = Field(None, description="Filter by statuses")
    service_types: Optional[List[str]] = Field(None, description="Filter by service types")
    destinations: Optional[List[int]] = Field(None, description="Filter by destination IDs")
    countries: Optional[List[str]] = Field(None, description="Filter by countries")
    cities: Optional[List[str]] = Field(None, description="Filter by cities")
    min_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Minimum rating")
    max_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Maximum rating")
    has_certifications: Optional[bool] = Field(None, description="Has certifications")
    has_insurance: Optional[bool] = Field(None, description="Has insurance")

    @validator('max_rating')
    def validate_rating_range(cls, v, values):
        min_rating = values.get('min_rating')
        if v is not None and min_rating is not None and v < min_rating:
            raise ValueError('Maximum rating must be greater than or equal to minimum rating')
        return v


# ============================================
# SUPPLIER STATISTICS SCHEMAS
# ============================================

class SupplierStatistics(BaseModel):
    """Schema for supplier statistics"""
    total_suppliers: int
    suppliers_by_type: Dict[str, int]
    suppliers_by_status: Dict[str, int]
    suppliers_by_country: Dict[str, int]
    average_rating: Optional[Decimal]
    suppliers_with_certifications: int
    top_rated_suppliers: List[SupplierSearch]

    model_config = ConfigDict(from_attributes=True)


class SupplierPerformance(BaseModel):
    """Schema for supplier performance metrics"""
    supplier_id: int
    supplier_name: str
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    confirmation_rate: Decimal
    average_response_time_hours: Optional[Decimal]
    customer_satisfaction: Optional[Decimal]
    on_time_delivery_rate: Optional[Decimal]
    last_30_days_bookings: int
    performance_trend: str  # improving, stable, declining

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SUPPLIER MANAGEMENT SCHEMAS
# ============================================

class SupplierStatusUpdate(BaseModel):
    """Schema for updating supplier status"""
    supplier_id: int = Field(..., description="Supplier ID")
    new_status: SupplierStatus = Field(..., description="New status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    notes: Optional[str] = Field(None, description="Additional notes")


class SupplierRatingUpdate(BaseModel):
    """Schema for updating supplier rating"""
    supplier_id: int = Field(..., description="Supplier ID")
    new_rating: Decimal = Field(..., ge=0, le=5, description="New rating (0-5)")
    review_comments: Optional[str] = Field(None, description="Review comments")
    reviewer_id: Optional[int] = Field(None, description="Reviewer user ID")
    review_date: Optional[datetime] = Field(None, description="Review date")


class SupplierContact(BaseModel):
    """Schema for supplier contact summary"""
    supplier_id: int
    supplier_name: str
    primary_email: Optional[str]
    primary_phone: Optional[str]
    contact_person: Optional[str]
    preferred_contact_method: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class SupplierContractInfo(BaseModel):
    """Schema for supplier contract information"""
    contract_number: Optional[str] = Field(None, description="Contract number")
    contract_start_date: Optional[datetime] = Field(None, description="Contract start date")
    contract_end_date: Optional[datetime] = Field(None, description="Contract end date")
    contract_type: Optional[str] = Field(None, description="Contract type")
    commission_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Commission rate %")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    contract_status: Optional[str] = Field(None, description="Contract status")
    renewal_notice_days: Optional[int] = Field(None, ge=0, description="Renewal notice period in days")

    @validator('contract_end_date')
    def validate_contract_dates(cls, v, values):
        start_date = values.get('contract_start_date')
        if v is not None and start_date is not None and v < start_date:
            raise ValueError('Contract end date must be after start date')
        return v


class SupplierOnboarding(BaseModel):
    """Schema for supplier onboarding process"""
    supplier_id: int = Field(..., description="Supplier ID")
    onboarding_status: str = Field(..., description="Onboarding status")
    completed_steps: List[str] = Field(..., description="Completed onboarding steps")
    pending_steps: List[str] = Field(..., description="Pending onboarding steps")
    onboarding_progress: Decimal = Field(..., ge=0, le=100, description="Onboarding progress %")
    assigned_manager: Optional[int] = Field(None, description="Assigned manager user ID")
    estimated_completion_date: Optional[datetime] = Field(None, description="Estimated completion date")
    notes: Optional[str] = Field(None, description="Onboarding notes")

    @validator('onboarding_status')
    def validate_onboarding_status(cls, v):
        valid_statuses = ['not_started', 'in_progress', 'completed', 'on_hold', 'cancelled']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Onboarding status must be one of: {", ".join(valid_statuses)}')
        return v.lower()


# ============================================
# SUPPLIER INTEGRATION SCHEMAS
# ============================================

class SupplierIntegration(BaseModel):
    """Schema for supplier system integration"""
    supplier_id: int = Field(..., description="Supplier ID")
    integration_type: str = Field(..., description="Integration type")
    api_endpoint: Optional[str] = Field(None, description="API endpoint URL")
    api_key: Optional[str] = Field(None, description="API key (masked)")
    integration_status: str = Field(..., description="Integration status")
    last_sync_date: Optional[datetime] = Field(None, description="Last synchronization date")
    sync_frequency: Optional[str] = Field(None, description="Synchronization frequency")
    supported_operations: List[str] = Field(..., description="Supported operations")
    connection_test_passed: bool = Field(False, description="Connection test status")

    @validator('integration_type')
    def validate_integration_type(cls, v):
        valid_types = ['api', 'xml', 'email', 'ftp', 'manual', 'webhook']
        if v.lower() not in valid_types:
            raise ValueError(f'Integration type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('integration_status')
    def validate_integration_status(cls, v):
        valid_statuses = ['active', 'inactive', 'testing', 'error', 'maintenance']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Integration status must be one of: {", ".join(valid_statuses)}')
        return v.lower()
