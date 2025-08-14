"""
Destinations module schemas
Contains Pydantic schemas for Destination data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class DestinationBase(BaseModel):
    """Base schema for Destination"""
    country_id: int = Field(..., description="Country ID")
    parent_destination_id: Optional[int] = Field(None, description="Parent destination ID")
    code: str = Field(..., min_length=1, max_length=20, description="Destination code")
    name: str = Field(..., min_length=1, max_length=200, description="Destination name")
    type: str = Field(..., max_length=50, description="Destination type (city, region, area, district, landmark)")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    altitude_meters: Optional[int] = Field(None, description="Altitude in meters")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    description: Optional[str] = Field(None, description="Destination description")
    highlights: Optional[List[str]] = Field(None, description="Destination highlights")
    best_time_to_visit: Optional[Dict[str, Any]] = Field(None, description="Best time to visit information")
    airport_codes: Optional[List[str]] = Field(None, description="Airport codes")
    nearest_airport_distance_km: Optional[Decimal] = Field(None, ge=0, description="Distance to nearest airport in km")
    requires_special_permit: bool = Field(False, description="Requires special permit")
    tourism_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Tourism rating (0-5)")
    safety_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Safety rating (0-5)")
    popularity_score: Optional[int] = Field(None, ge=1, le=100, description="Popularity score (1-100)")
    is_active: bool = Field(True, description="Destination active status")
    is_featured: bool = Field(False, description="Featured destination status")
    destination_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['city', 'region', 'area', 'district', 'landmark', 'country', 'state', 'province']
        if v.lower() not in valid_types:
            raise ValueError(f'Type must be one of: {", ".join(valid_types)}')
        return v.lower()

    @validator('airport_codes')
    def validate_airport_codes(cls, v):
        if v is not None:
            for code in v:
                if not isinstance(code, str) or len(code) != 3:
                    raise ValueError('Airport codes must be 3-letter strings')
        return v


class DestinationCreate(DestinationBase):
    """Schema for creating a new Destination"""
    pass


class DestinationUpdate(BaseModel):
    """Schema for updating a Destination"""
    country_id: Optional[int] = Field(None, description="Country ID")
    parent_destination_id: Optional[int] = Field(None, description="Parent destination ID")
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="Destination code")
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Destination name")
    type: Optional[str] = Field(None, max_length=50, description="Destination type")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    altitude_meters: Optional[int] = Field(None, description="Altitude in meters")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    description: Optional[str] = Field(None, description="Destination description")
    highlights: Optional[List[str]] = Field(None, description="Destination highlights")
    best_time_to_visit: Optional[Dict[str, Any]] = Field(None, description="Best time to visit information")
    airport_codes: Optional[List[str]] = Field(None, description="Airport codes")
    nearest_airport_distance_km: Optional[Decimal] = Field(None, ge=0, description="Distance to nearest airport in km")
    requires_special_permit: Optional[bool] = Field(None, description="Requires special permit")
    tourism_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Tourism rating (0-5)")
    safety_rating: Optional[Decimal] = Field(None, ge=0, le=5, description="Safety rating (0-5)")
    popularity_score: Optional[int] = Field(None, ge=1, le=100, description="Popularity score (1-100)")
    is_active: Optional[bool] = Field(None, description="Destination active status")
    is_featured: Optional[bool] = Field(None, description="Featured destination status")
    destination_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('type')
    def validate_type(cls, v):
        if v is not None:
            valid_types = ['city', 'region', 'area', 'district', 'landmark', 'country', 'state', 'province']
            if v.lower() not in valid_types:
                raise ValueError(f'Type must be one of: {", ".join(valid_types)}')
            return v.lower()
        return v

    @validator('airport_codes')
    def validate_airport_codes(cls, v):
        if v is not None:
            for code in v:
                if not isinstance(code, str) or len(code) != 3:
                    raise ValueError('Airport codes must be 3-letter strings')
        return v


class CountryBasic(BaseModel):
    """Basic country information for destination response"""
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class DestinationResponse(DestinationBase):
    """Schema for Destination response"""
    id: int = Field(..., description="Destination ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    country: Optional[CountryBasic] = Field(None, description="Country information")

    model_config = ConfigDict(from_attributes=True)


class DestinationListResponse(BaseModel):
    """Schema for Destination list response"""
    destinations: List[DestinationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)


class DestinationHierarchy(BaseModel):
    """Schema for hierarchical destination response"""
    id: int
    code: str
    name: str
    type: str
    children: List['DestinationHierarchy'] = []

    model_config = ConfigDict(from_attributes=True)


class DestinationSearch(BaseModel):
    """Schema for destination search results"""
    id: int
    code: str
    name: str
    type: str
    country_code: str
    country_name: str
    full_path: str  # e.g., "Peru > Cusco > Sacred Valley"

    model_config = ConfigDict(from_attributes=True)


class DestinationSearchResponse(BaseModel):
    """Schema for destination search response"""
    results: List[DestinationSearch]
    total: int

    model_config = ConfigDict(from_attributes=True)
