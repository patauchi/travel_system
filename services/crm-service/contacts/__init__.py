"""
Contacts Module for CRM Service
Handles contact management functionality
"""

from .models import Contact
from .schemas import ContactCreate, ContactUpdate, ContactResponse
from .endpoints import router

__all__ = [
    'Contact',
    'ContactCreate',
    'ContactUpdate',
    'ContactResponse',
    'router'
]
