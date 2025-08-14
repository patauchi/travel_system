"""
Industries Schemas for CRM Service
Pydantic models for industry request/response validation
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

# ============================================
# INDUSTRY SCHEMAS
# ============================================

class IndustryBase(BaseModel):
    """Base schema for Industry"""
    name: str = Field(..., max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_active: bool = True

    @validator('code')
    def validate_code_format(cls, v):
        if v and not v.isalnum():
            raise ValueError('Industry code must be alphanumeric')
        return v

    @validator('name')
    def validate_name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Industry name cannot be empty')
        return v.strip()

class IndustryCreate(IndustryBase):
    """Schema for creating an Industry"""
    parent_id: Optional[int] = None

    @validator('parent_id')
    def validate_parent_not_self(cls, v, values):
        # This validation would need to be done at the endpoint level
        # since we don't have access to the database here
        return v

class IndustryUpdate(BaseModel):
    """Schema for updating an Industry"""
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

    @validator('code')
    def validate_code_format(cls, v):
        if v and not v.isalnum():
            raise ValueError('Industry code must be alphanumeric')
        return v

    @validator('name')
    def validate_name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Industry name cannot be empty')
        return v.strip() if v else v

class IndustryResponse(IndustryBase):
    """Schema for Industry response"""
    id: int
    parent_id: Optional[int] = None
    parent_name: Optional[str] = None
    children_count: int = 0
    accounts_count: int = 0
    level: int = 0  # Hierarchy level (0 for root industries)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# FILTERING AND BULK OPERATIONS
# ============================================

class IndustryListFilter(BaseModel):
    """Schema for filtering industry list"""
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    has_children: Optional[bool] = None  # Filter by whether industry has sub-industries
    has_accounts: Optional[bool] = None  # Filter by whether industry has associated accounts
    level: Optional[int] = Field(None, ge=0, le=10)  # Filter by hierarchy level
    search: Optional[str] = None  # Search in name, code, description
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("name", pattern="^(name|code|created_at|updated_at|accounts_count|children_count)$")
    sort_order: str = Field("asc", pattern="^(asc|desc)$")

class IndustryBulkAction(BaseModel):
    """Schema for bulk actions on industries"""
    industry_ids: List[int]
    action: str = Field(..., pattern="^(activate|deactivate|delete|move_to_parent)$")

    # Action-specific fields
    new_parent_id: Optional[int] = None  # For move_to_parent action

class IndustryHierarchy(BaseModel):
    """Schema for industry hierarchy representation"""
    id: int
    name: str
    code: Optional[str] = None
    parent_id: Optional[int] = None
    children: List["IndustryHierarchy"] = []
    level: int = 0
    accounts_count: int = 0
    is_active: bool = True
    total_descendants: int = 0  # Total number of all descendant industries

    class Config:
        from_attributes = True

# Enable forward references for recursive model
IndustryHierarchy.model_rebuild()

class IndustryTree(BaseModel):
    """Schema for complete industry tree"""
    root_industries: List[IndustryHierarchy]
    total_industries: int
    max_depth: int
    active_industries: int
    inactive_industries: int

class IndustryStats(BaseModel):
    """Schema for industry statistics"""
    total_industries: int
    active_industries: int
    inactive_industries: int
    root_industries: int  # Industries without parent
    max_hierarchy_depth: int
    industries_with_accounts: int
    total_accounts: int
    top_industries_by_accounts: List[dict]

class IndustryMove(BaseModel):
    """Schema for moving an industry to a different parent"""
    new_parent_id: Optional[int] = None  # None means move to root level
    preserve_children: bool = True

    @validator('new_parent_id')
    def validate_parent_move(cls, v, values):
        # Additional validation would be done at endpoint level
        # to prevent circular references
        return v

class IndustryMerge(BaseModel):
    """Schema for merging two industries"""
    target_industry_id: int
    preserve_children: bool = True
    update_accounts: bool = True  # Whether to update associated accounts
    merge_description: bool = False  # Whether to combine descriptions
