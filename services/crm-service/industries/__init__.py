"""
Industries Module for CRM Service
Handles industry management functionality
"""

from .models import Industry
from .schemas import IndustryCreate, IndustryUpdate, IndustryResponse
from .endpoints import router

__all__ = [
    'Industry',
    'IndustryCreate',
    'IndustryUpdate',
    'IndustryResponse',
    'router'
]
