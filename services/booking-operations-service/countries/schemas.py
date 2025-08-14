"""
Countries module schemas
Contains Pydantic schemas for Country data validation and serialization
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CountryBase(BaseModel):
    """Base schema for Country"""
    code: str = Field(..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    code3: str = Field(..., min_length=3, max_length=3, description="ISO 3166-1 alpha-3 country code")
    name: str = Field(..., min_length=1, max_length=100, description="Country name")
    official_name: Optional[str] = Field(None, max_length=200, description="Official country name")
    native_name: Optional[str] = Field(None, max_length=100, description="Native country name")
    continent: Optional[str] = Field(None, max_length=50, description="Continent")
    region: Optional[str] = Field(None, max_length=100, description="Region")
    subregion: Optional[str] = Field(None, max_length=100, description="Subregion")
    capital: Optional[str] = Field(None, max_length=100, description="Capital city")
    currency_code: Optional[str] = Field(None, max_length=3, description="Currency code")
    phone_code: Optional[str] = Field(None, max_length=10, description="Phone country code")
    timezone_codes: Optional[List[str]] = Field(None, description="Array of timezone codes")
    languages: Optional[List[str]] = Field(None, description="Array of language codes")
    is_active: bool = Field(True, description="Country active status")


class CountryCreate(CountryBase):
    """Schema for creating a new Country"""
    pass


class CountryUpdate(BaseModel):
    """Schema for updating a Country"""
    code: Optional[str] = Field(None, min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code")
    code3: Optional[str] = Field(None, min_length=3, max_length=3, description="ISO 3166-1 alpha-3 country code")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Country name")
    official_name: Optional[str] = Field(None, max_length=200, description="Official country name")
    native_name: Optional[str] = Field(None, max_length=100, description="Native country name")
    continent: Optional[str] = Field(None, max_length=50, description="Continent")
    region: Optional[str] = Field(None, max_length=100, description="Region")
    subregion: Optional[str] = Field(None, max_length=100, description="Subregion")
    capital: Optional[str] = Field(None, max_length=100, description="Capital city")
    currency_code: Optional[str] = Field(None, max_length=3, description="Currency code")
    phone_code: Optional[str] = Field(None, max_length=10, description="Phone country code")
    timezone_codes: Optional[List[str]] = Field(None, description="Array of timezone codes")
    languages: Optional[List[str]] = Field(None, description="Array of language codes")
    is_active: Optional[bool] = Field(None, description="Country active status")


class CountryResponse(CountryBase):
    """Schema for Country response"""
    id: int = Field(..., description="Country ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CountryListResponse(BaseModel):
    """Schema for Country list response"""
    items: List[CountryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
