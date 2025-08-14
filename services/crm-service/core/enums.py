"""
Core Enums for CRM Service
Centralized enums used across multiple modules
"""

import enum

# ============================================
# ACTOR & GENERAL ENUMS
# ============================================

class ActorType(str, enum.Enum):
    LEAD = "lead"
    CONTACT = "contact"
    ACCOUNT_BUSINESS = "account_business"
    ACCOUNT_PERSON = "account_person"

class TravelFrequency(str, enum.Enum):
    OCCASIONAL = "occasional"
    FREQUENT = "frequent"
    BUSINESS_REGULAR = "business_regular"

class Rating(int, enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

# ============================================
# LEAD ENUMS
# ============================================

class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    DISQUALIFIED = "disqualified"

class InterestLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# ============================================
# CONTACT ENUMS
# ============================================

class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DO_NOT_CONTACT = "do_not_contact"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class PreferredCommunication(str, enum.Enum):
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"

# ============================================
# ACCOUNT ENUMS
# ============================================

class AccountType(str, enum.Enum):
    BUSINESS = "business"
    PERSON = "person"

class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"

class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# ============================================
# OPPORTUNITY ENUMS
# ============================================

class OpportunityStage(str, enum.Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    DECISION_MAKING = "decision_making"
    PERCEPTION_ANALYSIS = "perception_analysis"
    QUOTES = "quotes"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class TravelType(str, enum.Enum):
    LEISURE = "leisure"
    BUSINESS = "business"
    CORPORATE = "corporate"
    HONEYMOON = "honeymoon"
    FAMILY = "family"
    ADVENTURE = "adventure"
    LUXURY = "luxury"
    CULTURAL = "cultural"
    EDUCATIONAL = "educational"
    MEDICAL = "medical"
    RELIGIOUS = "religious"
    BACKPACKING = "backpacking"
    VOLUNTEER = "volunteer"
    SPORTS = "sports"
    WELLNESS = "wellness"
    PERSONAL = "personal"
    ECOTOURISM = "ecotourism"
    OTHER = "other"

class BudgetLevel(str, enum.Enum):
    ECONOMY = "economy"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"

# ============================================
# QUOTE ENUMS
# ============================================

class QuoteStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CONVERTED = "converted"

class Currency(str, enum.Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    PEN = "PEN"
    COP = "COP"
    ARS = "ARS"
    CLP = "CLP"
    MXN = "MXN"
    BOL = "BOL"

class QuoteLineType(str, enum.Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    TRANSFER = "transfer"
    TOUR = "tour"
    CRUISE = "cruise"
    INSURANCE = "insurance"
    VISA = "visa"
    OTHER = "other"
    PACKAGE = "package"
    ACTIVITY = "activity"
    CAR_RENTAL = "car_rental"
    TRAIN = "train"
    BUS = "bus"
