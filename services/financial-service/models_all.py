"""
Financial Service Unified Models
This module imports and exports all models from all modules for schema management
"""

# Import Base from models_base
from models_base import Base

# Import all models from each module
from orders.models import Order, OrderLine, PassengerDocument
from expenses.models import Expense, ExpenseCategory
from pettycash.models import PettyCash, PettyCashTransaction
from voucher.models import Voucher
from invoices.models import Invoice, InvoiceLine, AccountsReceivable, AccountsPayable
from payments.models import Payment, PaymentGateway, PaymentAttempt

# Export all models for schema manager
__all__ = [
    # Base
    "Base",

    # Orders Module
    "Order",
    "OrderLine",
    "PassengerDocument",

    # Expenses Module
    "Expense",
    "ExpenseCategory",

    # Petty Cash Module
    "PettyCash",
    "PettyCashTransaction",

    # Voucher Module
    "Voucher",

    # Invoices Module
    "Invoice",
    "InvoiceLine",
    "AccountsReceivable",
    "AccountsPayable",

    # Payments Module
    "Payment",
    "PaymentGateway",
    "PaymentAttempt"
]

# Make all models available at module level
globals().update({name: globals()[name] for name in __all__})
