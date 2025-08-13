"""
Booking Operations Service Models
Main module that imports all Booking Operations Service models
"""

# Import Base
from models_base import Base

# Import Supplier and Service models
from models_suppliers import (
    # Enums
    SupplierType,
    SupplierStatus,
    ServiceType,
    OperationModel,
    TransferType,
    VehicleType,
    TourType,
    DurationType,
    # Models
    Supplier,
    Service,
    TransferService,
    TourService,
    TransportService,
    RestaurantService,
    TicketService,
    GuideService,
    EquipmentService,
    TourComponent,
    ServiceAvailability
)

# Import Booking and Passenger models
from models_bookings import (
    # Enums
    BookingOverallStatus,
    BookingLineStatus,
    RiskLevel,
    PassengerGender,
    DocumentType,
    LoyaltyTier,
    ServiceOperationStatus,
    OperationalAlert,
    # Models
    Country,
    Destination,
    Passenger,
    Booking,
    BookingLine,
    BookingPassenger,
    ServiceOperation
)

# Import Rate and Cancellation Policy models
from models_rates import (
    # Enums
    RateType,
    PricingModel,
    SeasonType,
    CancellationPolicyType,
    PassengerType,
    # Models
    CancellationPolicy,
    Rate,
    RateVariant,
    RatePassengerPrice,
    RateTierPrice,
    PackageRate,
    PackageRatePassengerPrice,
    ServiceDailyCapacity,
    ServiceParticipant
)

# Export all models and enums
__all__ = [
    # Base
    'Base',

    # Supplier/Service Enums
    'SupplierType',
    'SupplierStatus',
    'ServiceType',
    'OperationModel',
    'TransferType',
    'VehicleType',
    'TourType',
    'DurationType',

    # Booking Enums
    'BookingOverallStatus',
    'BookingLineStatus',
    'RiskLevel',
    'PassengerGender',
    'DocumentType',
    'LoyaltyTier',
    'ServiceOperationStatus',
    'OperationalAlert',

    # Rate Enums
    'RateType',
    'PricingModel',
    'SeasonType',
    'CancellationPolicyType',
    'PassengerType',

    # Supplier/Service Models
    'Supplier',
    'Service',
    'TransferService',
    'TourService',
    'TransportService',
    'RestaurantService',
    'TicketService',
    'GuideService',
    'EquipmentService',
    'TourComponent',
    'ServiceAvailability',

    # Booking Models
    'Country',
    'Destination',
    'Passenger',
    'Booking',
    'BookingLine',
    'BookingPassenger',
    'ServiceOperation',

    # Rate Models
    'CancellationPolicy',
    'Rate',
    'RateVariant',
    'RatePassengerPrice',
    'RateTierPrice',
    'PackageRate',
    'PackageRatePassengerPrice',
    'ServiceDailyCapacity',
    'ServiceParticipant'
]
