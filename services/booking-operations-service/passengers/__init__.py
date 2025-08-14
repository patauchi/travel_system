"""
Passengers module for Booking Operations Service
Handles passenger data management and related operations
"""

from .models import Passenger
from .schemas import (
    PassengerResponse,
    PassengerCreate,
    PassengerUpdate,
    PassengerListResponse,
    PassengerSearch,
    PassengerSearchResponse,
    PassengerSummary,
    PassengerDocument,
    PassengerContact,
    PassengerPreferences
)
from .endpoints import router

__all__ = [
    # Models
    'Passenger',

    # Schemas
    'PassengerResponse',
    'PassengerCreate',
    'PassengerUpdate',
    'PassengerListResponse',
    'PassengerSearch',
    'PassengerSearchResponse',
    'PassengerSummary',
    'PassengerDocument',
    'PassengerContact',
    'PassengerPreferences',

    # Router
    'router'
]
