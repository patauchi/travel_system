"""
Settings Module Schemas
Pydantic schemas for settings-related API endpoints
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import json


# ============================================
# Setting Schemas
# ============================================

class SettingBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    key: str = Field(..., min_length=1, max_length=100)
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    value_type: Optional[str] = Field(None, max_length=50)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_public: bool = Field(default=False)
    is_encrypted: bool = Field(default=False)
    validation_rules: Optional[Dict[str, Any]] = None
    allowed_values: Optional[List[Any]] = None
    default_value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = None
    meta_data: Optional[Dict[str, Any]] = {}

    @validator('category', 'key')
    def validate_category_key(cls, v):
        # Remove spaces and convert to lowercase for consistency
        return v.lower().replace(' ', '_')

    @validator('value_type', pre=True, always=True)
    def set_value_type(cls, v, values):
        if v is None and 'value' in values:
            value = values['value']
            if isinstance(value, str):
                return 'string'
            elif isinstance(value, bool):
                return 'boolean'
            elif isinstance(value, int):
                return 'integer'
            elif isinstance(value, float):
                return 'number'
            elif isinstance(value, (dict, list)):
                return 'json'
        return v


class SettingCreate(SettingBase):
    is_system: bool = Field(default=False)


class SettingUpdate(BaseModel):
    value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = None
    value_type: Optional[str] = Field(None, max_length=50)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_public: Optional[bool] = None
    is_encrypted: Optional[bool] = None
    validation_rules: Optional[Dict[str, Any]] = None
    allowed_values: Optional[List[Any]] = None
    default_value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]] = None
    meta_data: Optional[Dict[str, Any]] = None

    @validator('value_type', pre=True, always=True)
    def set_value_type(cls, v, values):
        if v is None and 'value' in values and values['value'] is not None:
            value = values['value']
            if isinstance(value, str):
                return 'string'
            elif isinstance(value, bool):
                return 'boolean'
            elif isinstance(value, int):
                return 'integer'
            elif isinstance(value, float):
                return 'number'
            elif isinstance(value, (dict, list)):
                return 'json'
        return v


class SettingResponse(BaseModel):
    id: UUID
    category: str
    key: str
    value: Union[str, int, float, bool, Dict[str, Any], List[Any]]
    value_type: Optional[str]
    display_name: Optional[str]
    description: Optional[str]
    is_public: bool
    is_encrypted: bool
    is_system: bool
    validation_rules: Optional[Dict[str, Any]]
    allowed_values: Optional[List[Any]]
    default_value: Optional[Union[str, int, float, bool, Dict[str, Any], List[Any]]]
    meta_data: Optional[Dict[str, Any]]
    updated_at: datetime
    updated_by: Optional[UUID]

    class Config:
        orm_mode = True
        from_attributes = True


class SettingBulkUpdate(BaseModel):
    settings: List[Dict[str, Any]] = Field(..., min_items=1)

    @validator('settings')
    def validate_settings(cls, v):
        for setting in v:
            if 'category' not in setting or 'key' not in setting or 'value' not in setting:
                raise ValueError('Each setting must have category, key, and value')
        return v


# ============================================
# Audit Log Schemas
# ============================================

class AuditLogBase(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[str] = Field(None, max_length=255)
    resource_name: Optional[str] = Field(None, max_length=255)
    changes: Optional[Dict[str, Any]] = None
    result: Optional[str] = Field(None, max_length=50)
    error_message: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = {}


class AuditLogCreate(AuditLogBase):
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[UUID] = None
    request_id: Optional[str] = None
    duration_ms: Optional[int] = Field(None, ge=0)


class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    changes: Optional[Dict[str, Any]]
    result: Optional[str]
    error_message: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    session_id: Optional[UUID]
    request_id: Optional[str]
    duration_ms: Optional[int]
    meta_data: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# ============================================
# Filter and Query Schemas
# ============================================

class SettingFilter(BaseModel):
    category: Optional[str] = None
    key: Optional[str] = None
    value_type: Optional[str] = None
    is_public: Optional[bool] = None
    is_system: Optional[bool] = None
    search: Optional[str] = None  # Search in display_name, description, category, key


class AuditLogFilter(BaseModel):
    user_id: Optional[UUID] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None  # Search in action, resource_name, error_message


# ============================================
# Configuration Management Schemas
# ============================================

class ConfigurationExport(BaseModel):
    """Schema for exporting configuration settings"""
    version: str = Field(default="1.0")
    exported_at: datetime
    tenant_id: str
    categories: List[str]
    settings: List[SettingResponse]


class ConfigurationImport(BaseModel):
    """Schema for importing configuration settings"""
    settings: List[SettingCreate] = Field(..., min_items=1)
    overwrite_existing: bool = Field(default=False)
    skip_validation: bool = Field(default=False)


class ConfigurationImportResult(BaseModel):
    """Result of configuration import operation"""
    total_settings: int
    imported_settings: int
    skipped_settings: int
    failed_settings: int
    errors: List[Dict[str, str]] = []


# ============================================
# System Configuration Schemas
# ============================================

class SystemHealthResponse(BaseModel):
    """System health check response"""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]
    version: str
    uptime_seconds: int


class SystemInfoResponse(BaseModel):
    """System information response"""
    service_name: str
    version: str
    environment: str
    tenant_id: str
    database_status: str
    cache_status: str
    settings_count: int
    users_count: int
    roles_count: int
    last_backup: Optional[datetime]
