"""
Common enums for Booking Operations Service
Contains all shared enumerations used across different modules
"""

import enum

# ============================================
# SUPPLIER ENUMS
# ============================================

class SupplierType(str, enum.Enum):
    individual = "individual"
    company = "company"
    government = "government"

class SupplierStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    blacklist = "blacklist"

# ============================================
# SERVICE ENUMS
# ============================================

class ServiceType(str, enum.Enum):
    accommodation = "accommodation"
    transfer = "transfer"
    tour = "tour"
    transport = "transport"
    restaurant = "restaurant"
    ticket = "ticket"
    guide = "guide"
    equipment = "equipment"
    other = "other"

class OperationModel(str, enum.Enum):
    no_defined = "no_defined"
    direct = "direct"
    resale = "resale"
    white_label = "white_label"
    hybrid = "hybrid"

class TransferType(str, enum.Enum):
    private = "private"
    shared = "shared"
    shuttle = "shuttle"
    executive = "executive"
    luxury = "luxury"

class VehicleType(str, enum.Enum):
    sedan = "sedan"
    suv = "suv"
    van = "van"
    minibus = "minibus"
    bus = "bus"
    limousine = "limousine"
    helicopter = "helicopter"
    boat = "boat"
    other = "other"

class TourType(str, enum.Enum):
    private = "private"
    group = "group"
    regular = "regular"
    vip = "vip"

class DurationType(str, enum.Enum):
    hours = "hours"
    half_day = "half_day"
    full_day = "full_day"
    multi_day = "multi_day"

# ============================================
# BOOKING ENUMS
# ============================================

class BookingOverallStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    confirmed = "confirmed"
    partially_cancelled = "partially_cancelled"
    cancelled = "cancelled"
    completed = "completed"
    archived = "archived"

class BookingLineStatus(str, enum.Enum):
    pending = "pending"
    confirming = "confirming"
    confirmed = "confirmed"
    waitlisted = "waitlisted"
    modified = "modified"
    cancelled = "cancelled"
    failed = "failed"
    expired = "expired"
    completed = "completed"
    no_show = "no_show"

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class ServiceOperationStatus(str, enum.Enum):
    planned = "planned"
    ready = "ready"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    delayed = "delayed"
    incident = "incident"

class OperationalAlert(str, enum.Enum):
    none = "none"
    weather = "weather"
    traffic = "traffic"
    supplier_issue = "supplier_issue"
    passenger_issue = "passenger_issue"
    documentation = "documentation"
    payment = "payment"
    other = "other"

# ============================================
# PASSENGER ENUMS
# ============================================

class PassengerGender(str, enum.Enum):
    male = "M"
    female = "F"
    other = "O"

class DocumentType(str, enum.Enum):
    passport = "passport"
    national_id = "national_id"
    driver_license = "driver_license"
    birth_certificate = "birth_certificate"
    other = "other"

class LoyaltyTier(str, enum.Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"

# ============================================
# RATE ENUMS
# ============================================

class RateType(str, enum.Enum):
    standard = "standard"
    seasonal = "seasonal"
    promotional = "promotional"
    special = "special"
    contract = "contract"
    package = "package"

class PricingModel(str, enum.Enum):
    per_person = "per_person"
    per_group = "per_group"
    per_vehicle = "per_vehicle"
    per_room = "per_room"
    per_hour = "per_hour"
    per_day = "per_day"
    per_unit = "per_unit"
    tiered = "tiered"
    dynamic = "dynamic"

class SeasonType(str, enum.Enum):
    low = "low"
    shoulder = "shoulder"
    high = "high"
    peak = "peak"

class CancellationPolicyType(str, enum.Enum):
    flexible = "flexible"
    moderate = "moderate"
    strict = "strict"
    super_strict = "super_strict"
    non_refundable = "non_refundable"
    custom = "custom"

class PassengerType(str, enum.Enum):
    adult = "adult"
    child = "child"
    infant = "infant"
    senior = "senior"
    student = "student"
