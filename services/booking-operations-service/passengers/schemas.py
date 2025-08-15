"""
Passengers module schemas
Contains Pydantic schemas for Passenger data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

from common.enums import PassengerGender, DocumentType, LoyaltyTier


class PassengerBase(BaseModel):
    """Base schema for Passenger"""
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[PassengerGender] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, min_length=2, max_length=2, description="Nationality (ISO country code)")
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    document_number: Optional[str] = Field(None, max_length=50, description="Document number")
    document_expiry_date: Optional[date] = Field(None, description="Document expiry date")
    document_issuing_country: Optional[str] = Field(None, min_length=2, max_length=2, description="Document issuing country")
    emergency_contact_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=50, description="Emergency contact phone")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50, description="Emergency contact relationship")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="Accessibility needs")
    special_requests: Optional[str] = Field(None, description="Special requests")
    loyalty_tier: LoyaltyTier = Field(LoyaltyTier.bronze, description="Loyalty tier")
    preferred_language: Optional[str] = Field(None, min_length=2, max_length=2, description="Preferred language")
    marketing_consent: bool = Field(False, description="Marketing consent")
    medical_conditions: Optional[List[str]] = Field(None, description="Medical conditions")
    medications: Optional[List[str]] = Field(None, description="Medications")
    allergies: Optional[List[str]] = Field(None, description="Allergies")
    is_verified: bool = Field(False, description="Verification status")
    is_active: bool = Field(True, description="Active status")
    risk_level: str = Field("low", description="Risk level")
    passenger_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('nationality', 'document_issuing_country', 'preferred_language')
    def validate_country_codes(cls, v):
        if v is not None:
            return v.upper()
        return v

    @validator('risk_level')
    def validate_risk_level(cls, v):
        valid_levels = ['low', 'medium', 'high']
        if v.lower() not in valid_levels:
            raise ValueError(f'Risk level must be one of: {", ".join(valid_levels)}')
        return v.lower()

    @validator('document_expiry_date')
    def validate_document_expiry(cls, v, values):
        if v is not None and v <= date.today():
            raise ValueError('Document expiry date must be in the future')
        return v


class PassengerCreate(PassengerBase):
    """Schema for creating a new Passenger"""
    pass


class PassengerUpdate(BaseModel):
    """Schema for updating a Passenger"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[PassengerGender] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, min_length=2, max_length=2, description="Nationality")
    document_type: Optional[DocumentType] = Field(None, description="Document type")
    document_number: Optional[str] = Field(None, max_length=50, description="Document number")
    document_expiry_date: Optional[date] = Field(None, description="Document expiry date")
    document_issuing_country: Optional[str] = Field(None, min_length=2, max_length=2, description="Document issuing country")
    emergency_contact_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=50, description="Emergency contact phone")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50, description="Emergency contact relationship")
    dietary_restrictions: Optional[List[str]] = Field(None, description="Dietary restrictions")
    accessibility_needs: Optional[List[str]] = Field(None, description="Accessibility needs")
    special_requests: Optional[str] = Field(None, description="Special requests")
    loyalty_tier: Optional[LoyaltyTier] = Field(None, description="Loyalty tier")
    preferred_language: Optional[str] = Field(None, min_length=2, max_length=2, description="Preferred language")
    marketing_consent: Optional[bool] = Field(None, description="Marketing consent")
    medical_conditions: Optional[List[str]] = Field(None, description="Medical conditions")
    medications: Optional[List[str]] = Field(None, description="Medications")
    allergies: Optional[List[str]] = Field(None, description="Allergies")
    is_verified: Optional[bool] = Field(None, description="Verification status")
    is_active: Optional[bool] = Field(None, description="Active status")
    risk_level: Optional[str] = Field(None, description="Risk level")
    passenger_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('nationality', 'document_issuing_country', 'preferred_language')
    def validate_country_codes(cls, v):
        if v is not None:
            return v.upper()
        return v

    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v is not None:
            valid_levels = ['low', 'medium', 'high']
            if v.lower() not in valid_levels:
                raise ValueError(f'Risk level must be one of: {", ".join(valid_levels)}')
            return v.lower()
        return v

    @validator('document_expiry_date')
    def validate_document_expiry(cls, v, values):
        if v is not None and v <= date.today():
            raise ValueError('Document expiry date must be in the future')
        return v


class PassengerResponse(PassengerBase):
    """Schema for Passenger response"""
    id: int = Field(..., description="Passenger ID")
    previous_bookings_count: int = Field(..., description="Previous bookings count")
    total_spent: Decimal = Field(..., description="Total amount spent")
    last_booking_date: Optional[datetime] = Field(None, description="Last booking date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")

    # Computed fields
    full_name: Optional[str] = Field(None, description="Full name")
    age: Optional[int] = Field(None, description="Age in years")
    document_valid: Optional[bool] = Field(None, description="Document validity")
    has_special_needs: Optional[bool] = Field(None, description="Has special needs")

    model_config = ConfigDict(from_attributes=True)


class PassengerListResponse(BaseModel):
    """Schema for Passenger list response"""
    passengers: List[PassengerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class PassengerSearch(BaseModel):
    """Schema for passenger search results"""
    id: int
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    document_number: Optional[str]
    loyalty_tier: str

    model_config = ConfigDict(from_attributes=True)


class PassengerSearchResponse(BaseModel):
    """Schema for passenger search response"""
    results: List[PassengerSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)


class PassengerSummary(BaseModel):
    """Schema for passenger summary statistics"""
    total_passengers: int
    verified_passengers: int
    loyalty_distribution: Dict[str, int]
    age_distribution: Dict[str, int]
    risk_distribution: Dict[str, int]
    top_nationalities: List[Dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)


class PassengerDocument(BaseModel):
    """Schema for passenger document information"""
    document_type: Optional[DocumentType]
    document_number: Optional[str]
    document_expiry_date: Optional[date]
    document_issuing_country: Optional[str]
    is_valid: bool

    model_config = ConfigDict(from_attributes=True)


class PassengerContact(BaseModel):
    """Schema for passenger contact information"""
    email: Optional[str]
    phone: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PassengerPreferences(BaseModel):
    """Schema for passenger preferences"""
    dietary_restrictions: Optional[List[str]]
    accessibility_needs: Optional[List[str]]
    preferred_language: Optional[str]
    special_requests: Optional[str]
    marketing_consent: bool

    model_config = ConfigDict(from_attributes=True)
