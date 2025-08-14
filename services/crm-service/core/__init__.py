"""
Core Module for CRM Service
Provides base models, enums, and shared functionality
"""

from .models import Actor
from .enums import (
    ActorType, TravelFrequency, Rating, LeadStatus, InterestLevel,
    ContactStatus, Gender, PreferredCommunication, AccountType,
    AccountStatus, PaymentMethod, RiskLevel, OpportunityStage,
    TravelType, BudgetLevel, QuoteStatus, Currency, QuoteLineType
)

__all__ = [
    # Base models
    'Actor',

    # Core enums
    'ActorType',
    'TravelFrequency',
    'Rating',
    'LeadStatus',
    'InterestLevel',
    'ContactStatus',
    'Gender',
    'PreferredCommunication',
    'AccountType',
    'AccountStatus',
    'PaymentMethod',
    'RiskLevel',
    'OpportunityStage',
    'TravelType',
    'BudgetLevel',
    'QuoteStatus',
    'Currency',
    'QuoteLineType'
]
