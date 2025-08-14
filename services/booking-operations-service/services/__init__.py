"""
Services module for Booking Operations Service
Handles service catalog and related operations
"""

from .models import Service, ServiceAvailability, ServiceDailyCapacity, ServiceParticipant
from .schemas import (
    ServiceResponse,
    ServiceCreate,
    ServiceUpdate,
    ServiceListResponse,
    ServiceAvailability as ServiceAvailabilitySchema,
    ServiceSearch,
    ServiceSearchResponse,
    ServiceDailyCapacityResponse,
    ServiceDailyCapacityCreate,
    ServiceDailyCapacityUpdate,
    ServiceParticipantResponse,
    ServiceParticipantCreate,
    ServiceParticipantUpdate
)
from .endpoints import router

__all__ = [
    # Models
    'Service',
    'ServiceAvailability',
    'ServiceDailyCapacity',
    'ServiceParticipant',

    # Service Schemas
    'ServiceResponse',
    'ServiceCreate',
    'ServiceUpdate',
    'ServiceListResponse',
    'ServiceAvailabilitySchema',
    'ServiceSearch',
    'ServiceSearchResponse',

    # Service Daily Capacity Schemas
    'ServiceDailyCapacityResponse',
    'ServiceDailyCapacityCreate',
    'ServiceDailyCapacityUpdate',

    # Service Participant Schemas
    'ServiceParticipantResponse',
    'ServiceParticipantCreate',
    'ServiceParticipantUpdate',

    # Router
    'router'
]
