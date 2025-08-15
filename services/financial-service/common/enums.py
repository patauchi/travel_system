"""
Financial Service Common Enums
Shared enumerations used across financial service modules
"""

import enum

# ============================================
# ORDER ENUMS
# ============================================

class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"
    refunded = "refunded"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"
    refunded = "refunded"

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

class OrderLineType(str, enum.Enum):
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
    fee = "fee"
    tax = "tax"
    discount = "discount"

class DocumentType(str, enum.Enum):
    passport = "passport"
    id_card = "id_card"
    driver_license = "driver_license"
    visa = "visa"
    vaccination = "vaccination"
    insurance = "insurance"
    other = "other"

# ============================================
# INVOICE ENUMS
# ============================================

class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    partial_paid = "partial_paid"
    paid = "paid"
    overdue = "overdue"
    cancelled = "cancelled"

class PaymentMethod(str, enum.Enum):
    cash = "cash"
    credit_card = "credit_card"
    debit_card = "debit_card"
    bank_transfer = "bank_transfer"
    check = "check"
    paypal = "paypal"
    stripe = "stripe"
    wire_transfer = "wire_transfer"
    other = "other"

class PaymentType(str, enum.Enum):
    deposit = "deposit"
    partial = "partial"
    full = "full"
    refund = "refund"
    adjustment = "adjustment"

class TransactionType(str, enum.Enum):
    payment = "payment"
    refund = "refund"
    credit = "credit"
    debit = "debit"
    adjustment = "adjustment"

# ============================================
# EXPENSE ENUMS
# ============================================

class ExpenseStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    paid = "paid"
    reimbursed = "reimbursed"
    cancelled = "cancelled"

class ExpenseType(str, enum.Enum):
    travel = "travel"
    accommodation = "accommodation"
    meals = "meals"
    transportation = "transportation"
    supplies = "supplies"
    utilities = "utilities"
    marketing = "marketing"
    office = "office"
    entertainment = "entertainment"
    professional_fees = "professional_fees"
    insurance = "insurance"
    taxes = "taxes"
    other = "other"

# ============================================
# PETTY CASH ENUMS
# ============================================

class PettyCashTransactionType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    expense = "expense"
    reimbursement = "reimbursement"
    adjustment = "adjustment"

class PettyCashStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    reconciled = "reconciled"

# ============================================
# ACCOUNTS RECEIVABLE/PAYABLE ENUMS
# ============================================

class AccountsReceivableStatus(str, enum.Enum):
    open = "open"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    written_off = "written_off"

class AccountsPayableStatus(str, enum.Enum):
    open = "open"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"
    disputed = "disputed"

class AgingBucket(str, enum.Enum):
    current = "current"
    days_30 = "30"
    days_60 = "60"
    days_90 = "90"
    days_120_plus = "120+"

class CollectionStatus(str, enum.Enum):
    normal = "normal"
    warning = "warning"
    collection = "collection"
    legal = "legal"

# ============================================
# VOUCHER ENUMS
# ============================================

class VoucherStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    paid = "paid"
    cancelled = "cancelled"

class VoucherType(str, enum.Enum):
    payment = "payment"
    receipt = "receipt"
    journal = "journal"
    contra = "contra"

class PayeeType(str, enum.Enum):
    employee = "employee"
    supplier = "supplier"
    customer = "customer"
    other = "other"
