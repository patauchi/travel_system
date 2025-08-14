"""
Accounts Module for CRM Service
Handles account management functionality
"""

from .models import Account
from .schemas import AccountCreate, AccountUpdate, AccountResponse
from .endpoints import router

__all__ = [
    'Account',
    'AccountCreate',
    'AccountUpdate',
    'AccountResponse',
    'router'
]
