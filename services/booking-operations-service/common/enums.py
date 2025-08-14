"""
Common enums for Booking Operations Service
Contains all shared enumerations used across different modules
"""

import enum

# ============================================
# SUPPLIER ENUMS
# ============================================

class SupplierType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    GOVERNMENT = "government"

class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLACKLIST = "blacklist"

# ============================================
# SERVICE ENUMS
# ============================================

class ServiceType(str, enum.Enum):
    ACCOMMODATION = "accommodation"
    TRANSFER = "transfer"
    TOUR = "tour"
    TRANSPORT = "transport"
    RESTAURANT = "restaurant"
    TICKET = "ticket"
    GUIDE = "guide"
    EQUIPMENT = "equipment"
    OTHER = "other"

class OperationModel(str, enum.Enum):
    NO_DEFINED = "no_defined"
    DIRECT = "direct"
    RESALE = "resale"
    WHITE_LABEL = "white_label"
    HYBRID = "hybrid"

class TransferType(str, enum.Enum):
    PRIVATE = "private"
    SHARED = "shared"
    SHUTTLE = "shuttle"
    EXECUTIVE = "executive"
    LUXURY = "luxury"

class VehicleType(str, enum.Enum):
    SEDAN = "sedan"
    SUV = "suv"
    VAN = "van"
    MINIBUS = "minibus"
    BUS = "bus"
    LIMOUSINE = "limousine"
    HELICOPTER = "helicopter"
    BOAT = "boat"
    OTHER = "other"

class TourType(str, enum.Enum):
    PRIVATE = "private"
    GROUP = "group"
    REGULAR = "regular"
    VIP = "vip"

class DurationType(str, enum.Enum):
    HOURS = "hours"
    HALF_DAY = "half_day"
    FULL_DAY = "full_day"
    MULTI_DAY = "multi_day"

# ============================================
# BOOKING ENUMS
# ============================================

class BookingOverallStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONFIRMED = "confirmed"
    PARTIALLY_CANCELLED = "partially_cancelled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class BookingLineStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    MODIFIED = "modified"
    CANCELLED = "cancelled"
    FAILED = "failed"
    EXPIRED = "expired"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ServiceOperationStatus(str, enum.Enum):
    PLANNED = "planned"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DELAYED = "delayed"
    INCIDENT = "incident"

class OperationalAlert(str, enum.Enum):
    NONE = "none"
    WEATHER = "weather"
    TRAFFIC = "traffic"
    SUPPLIER_ISSUE = "supplier_issue"
    PASSENGER_ISSUE = "passenger_issue"
    DOCUMENTATION = "documentation"
    PAYMENT = "payment"
    OTHER = "other"

# ============================================
# PASSENGER ENUMS
# ============================================

class PassengerGender(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVER_LICENSE = "driver_license"
    BIRTH_CERTIFICATE = "birth_certificate"
    OTHER = "other"

class LoyaltyTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"

# ============================================
# RATE ENUMS
# ============================================

class RateType(str, enum.Enum):
    STANDARD = "standard"
    SEASONAL = "seasonal"
    PROMOTIONAL = "promotional"
    SPECIAL = "special"
    CONTRACT = "contract"
    PACKAGE = "package"

class PricingModel(str, enum.Enum):
    PER_PERSON = "per_person"
    PER_GROUP = "per_group"
    PER_VEHICLE = "per_vehicle"
    PER_ROOM = "per_room"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_UNIT = "per_unit"
    TIERED = "tiered"
    DYNAMIC = "dynamic"

class SeasonType(str, enum.Enum):
    LOW = "low"
    SHOULDER = "shoulder"
    HIGH = "high"
    PEAK = "peak"

class CancellationPolicyType(str, enum.Enum):
    FLEXIBLE = "flexible"
    MODERATE = "moderate"
    STRICT = "strict"
    SUPER_STRICT = "super_strict"
    NON_REFUNDABLE = "non_refundable"
    CUSTOM = "custom"

class PassengerType(str, enum.Enum):
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"
    SENIOR = "senior"
    STUDENT = "student"
