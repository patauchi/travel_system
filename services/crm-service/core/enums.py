"""
Core Enums for CRM Service
Centralized enums used across multiple modules
"""

import enum

# ============================================
# ACTOR & GENERAL ENUMS
# ============================================

class ActorType(str, enum.Enum):
    lead = "lead"
    contact = "contact"
    account_business = "account_business"
    account_person = "account_person"

class TravelFrequency(str, enum.Enum):
    occasional = "occasional"
    frequent = "frequent"
    business_regular = "business_regular"

class Rating(int, enum.Enum):
    one = 1
    two = 2
    three = 3
    four = 4
    five = 5

# ============================================
# LEAD ENUMS
# ============================================

class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    qualified = "qualified"
    converted = "converted"
    disqualified = "disqualified"

class InterestLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

# ============================================
# CONTACT ENUMS
# ============================================

class ContactStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    do_not_contact = "do_not_contact"

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"

class PreferredCommunication(str, enum.Enum):
    email = "email"
    phone = "phone"
    sms = "sms"
    whatsapp = "whatsapp"

# ============================================
# ACCOUNT ENUMS
# ============================================

class AccountType(str, enum.Enum):
    business = "business"
    person = "person"

class AccountStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    prospect = "prospect"
    customer = "customer"
    partner = "partner"

class PaymentMethod(str, enum.Enum):
    credit_card = "credit_card"
    bank_transfer = "bank_transfer"
    check = "check"
    cash = "cash"

class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

# ============================================
# OPPORTUNITY ENUMS
# ============================================

class OpportunityStage(str, enum.Enum):
    prospecting = "prospecting"
    qualification = "qualification"
    needs_analysis = "needs_analysis"
    value_proposition = "value_proposition"
    decision_making = "decision_making"
    perception_analysis = "perception_analysis"
    quotes = "quotes"
    negotiation = "negotiation"
    closed_won = "closed_won"
    closed_lost = "closed_lost"

class TravelType(str, enum.Enum):
    leisure = "leisure"
    business = "business"
    corporate = "corporate"
    honeymoon = "honeymoon"
    family = "family"
    adventure = "adventure"
    luxury = "luxury"
    cultural = "cultural"
    educational = "educational"
    medical = "medical"
    religious = "religious"
    backpacking = "backpacking"
    volunteer = "volunteer"
    sports = "sports"
    wellness = "wellness"
    personal = "personal"
    ecotourism = "ecotourism"
    other = "other"

class BudgetLevel(str, enum.Enum):
    economy = "economy"
    standard = "standard"
    premium = "premium"
    luxury = "luxury"

# ============================================
# QUOTE ENUMS
# ============================================

class QuoteStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"
    converted = "converted"

class Currency(str, enum.Enum):
    usd = "USD"
    eur = "EUR"
    gbp = "GBP"
    jpy = "JPY"
    pen = "PEN"
    cop = "COP"
    ars = "ARS"
    clp = "CLP"
    mxn = "MXN"
    bol = "BOL"

class QuoteLineType(str, enum.Enum):
    flight = "flight"
    hotel = "hotel"
    transfer = "transfer"
    tour = "tour"
    cruise = "cruise"
    insurance = "insurance"
    visa = "visa"
    other = "other"
    package = "package"
    activity = "activity"
    car_rental = "car_rental"
    train = "train"
    bus = "bus"
