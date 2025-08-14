"""
Specialized Services module for Booking Operations Service
Handles specialized service types (tours, transfers, equipment, etc.)
"""

from .models import (
    TransferService,
    TourService,
    TourComponent,
    TransportService,
    RestaurantService,
    TicketService,
    GuideService,
    EquipmentService
)
from .schemas import (
    # Transfer Service
    TransferServiceBase,
    TransferServiceUpdate,

    # Tour Service
    TourServiceBase,
    TourServiceUpdate,
    TourComponentBase,

    # Transport Service
    TransportServiceBase,
    TransportServiceUpdate,

    # Restaurant Service
    RestaurantServiceBase,
    RestaurantServiceUpdate,

    # Ticket Service
    TicketServiceBase,
    TicketServiceUpdate,

    # Guide Service
    GuideServiceBase,
    GuideServiceUpdate,

    # Equipment Service
    EquipmentServiceBase,
    EquipmentServiceUpdate
)
from .endpoints import router

__all__ = [
    # Models
    'TransferService',
    'TourService',
    'TourComponent',
    'TransportService',
    'RestaurantService',
    'TicketService',
    'GuideService',
    'EquipmentService',

    # Transfer Service Schemas
    'TransferServiceBase',
    'TransferServiceUpdate',

    # Tour Service Schemas
    'TourServiceBase',
    'TourServiceUpdate',
    'TourComponentBase',

    # Transport Service Schemas
    'TransportServiceBase',
    'TransportServiceUpdate',

    # Restaurant Service Schemas
    'RestaurantServiceBase',
    'RestaurantServiceUpdate',

    # Ticket Service Schemas
    'TicketServiceBase',
    'TicketServiceUpdate',

    # Guide Service Schemas
    'GuideServiceBase',
    'GuideServiceUpdate',

    # Equipment Service Schemas
    'EquipmentServiceBase',
    'EquipmentServiceUpdate',

    # Router
    'router'
]
