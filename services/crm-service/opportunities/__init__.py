"""
Opportunities Module for CRM Service
Handles opportunity management functionality
"""

from .models import Opportunity
from .schemas import OpportunityCreate, OpportunityUpdate, OpportunityResponse
from .endpoints import router

__all__ = [
    'Opportunity',
    'OpportunityCreate',
    'OpportunityUpdate',
    'OpportunityResponse',
    'router'
]
