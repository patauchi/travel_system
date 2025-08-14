"""
Financial Service Common Enums
Shared enumerations used across financial service modules
"""

import enum

# ============================================
# ORDER ENUMS
# ============================================

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

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

class OrderLineType(str, enum.Enum):
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
    FEE = "fee"
    TAX = "tax"
    DISCOUNT = "discount"

class DocumentType(str, enum.Enum):
    PASSPORT = "passport"
    ID_CARD = "id_card"
    DRIVER_LICENSE = "driver_license"
    VISA = "visa"
    VACCINATION = "vaccination"
    INSURANCE = "insurance"
    OTHER = "other"

# ============================================
# INVOICE ENUMS
# ============================================

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL_PAID = "partial_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    WIRE_TRANSFER = "wire_transfer"
    OTHER = "other"

class PaymentType(str, enum.Enum):
    DEPOSIT = "deposit"
    PARTIAL = "partial"
    FULL = "full"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"

class TransactionType(str, enum.Enum):
    PAYMENT = "payment"
    REFUND = "refund"
    CREDIT = "credit"
    DEBIT = "debit"
    ADJUSTMENT = "adjustment"

# ============================================
# EXPENSE ENUMS
# ============================================

class ExpenseStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    REIMBURSED = "reimbursed"
    CANCELLED = "cancelled"

class ExpenseType(str, enum.Enum):
    TRAVEL = "travel"
    ACCOMMODATION = "accommodation"
    MEALS = "meals"
    TRANSPORTATION = "transportation"
    SUPPLIES = "supplies"
    UTILITIES = "utilities"
    MARKETING = "marketing"
    OFFICE = "office"
    ENTERTAINMENT = "entertainment"
    PROFESSIONAL_FEES = "professional_fees"
    INSURANCE = "insurance"
    TAXES = "taxes"
    OTHER = "other"

# ============================================
# PETTY CASH ENUMS
# ============================================

class PettyCashTransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    EXPENSE = "expense"
    REIMBURSEMENT = "reimbursement"
    ADJUSTMENT = "adjustment"

class PettyCashStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    RECONCILED = "reconciled"

# ============================================
# ACCOUNTS RECEIVABLE/PAYABLE ENUMS
# ============================================

class AccountsReceivableStatus(str, enum.Enum):
    OPEN = "open"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    WRITTEN_OFF = "written_off"

class AccountsPayableStatus(str, enum.Enum):
    OPEN = "open"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"

class AgingBucket(str, enum.Enum):
    CURRENT = "current"
    DAYS_30 = "30"
    DAYS_60 = "60"
    DAYS_90 = "90"
    DAYS_120_PLUS = "120+"

class CollectionStatus(str, enum.Enum):
    NORMAL = "normal"
    WARNING = "warning"
    COLLECTION = "collection"
    LEGAL = "legal"

# ============================================
# VOUCHER ENUMS
# ============================================

class VoucherStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"

class VoucherType(str, enum.Enum):
    PAYMENT = "payment"
    RECEIPT = "receipt"
    JOURNAL = "journal"
    CONTRA = "contra"

class PayeeType(str, enum.Enum):
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    OTHER = "other"
