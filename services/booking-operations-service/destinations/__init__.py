"""
Destinations module for Booking Operations Service
Handles destination data and related operations
"""

from .models import Destination
from .schemas import DestinationResponse, DestinationCreate, DestinationUpdate
from .endpoints import router

__all__ = [
    'Destination',
    'DestinationResponse',
    'DestinationCreate',
    'DestinationUpdate',
    'router'
]
