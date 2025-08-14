"""
Quotes Module for CRM Service
Handles quote management functionality
"""

from .models import Quote, QuoteLine
from .schemas import QuoteCreate, QuoteUpdate, QuoteResponse, QuoteLineCreate, QuoteLineResponse
from .endpoints import router

__all__ = [
    'Quote',
    'QuoteLine',
    'QuoteCreate',
    'QuoteUpdate',
    'QuoteResponse',
    'QuoteLineCreate',
    'QuoteLineResponse',
    'router'
]
