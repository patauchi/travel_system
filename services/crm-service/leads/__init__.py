"""
Leads Module for CRM Service
Handles lead management functionality
"""

from .models import Lead
from .schemas import LeadCreate, LeadUpdate, LeadResponse
from .endpoints import router

__all__ = [
    'Lead',
    'LeadCreate',
    'LeadUpdate',
    'LeadResponse',
    'router'
]
