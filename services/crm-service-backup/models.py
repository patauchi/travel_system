"""
CRM Service Models
Main module that imports all CRM models
"""

# Import Base and all models from sub-modules
from models_core import (
    Base,
    # Enums
    ActorType,
    TravelFrequency,
    Rating,
    LeadStatus,
    InterestLevel,
    ContactStatus,
    Gender,
    PreferredCommunication,
    AccountType,
    AccountStatus,
    PaymentMethod,
    RiskLevel,
    # Core Models
    Actor,
    Industry
)

from models_leads_contacts import (
    Lead,
    Contact
)

from models_accounts_opportunities import (
    # Enums
    OpportunityStage,
    TravelType,
    BudgetLevel,
    # Models
    Account,
    Opportunity
)

from models_quotes import (
    # Enums
    QuoteStatus,
    Currency,
    QuoteLineType,
    # Models
    Quote,
    QuoteLine
)

# Export all models and enums
__all__ = [
    # Base
    'Base',

    # Core Enums
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

    # Opportunity Enums
    'OpportunityStage',
    'TravelType',
    'BudgetLevel',

    # Quote Enums
    'QuoteStatus',
    'Currency',
    'QuoteLineType',

    # Core Models
    'Actor',
    'Industry',

    # Lead and Contact Models
    'Lead',
    'Contact',

    # Account and Opportunity Models
    'Account',
    'Opportunity',

    # Quote Models
    'Quote',
    'QuoteLine'
]
