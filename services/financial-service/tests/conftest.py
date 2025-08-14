"""
Test Configuration and Fixtures for Financial Service
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

# Import the main app and dependencies
from main import app
from database import get_db, get_tenant_db, Base
from shared_auth import get_current_user, get_current_tenant

# Test database URL - use a separate test database
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/financial_test_db"

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def setup_test_database():
    """Setup test database and create all tables"""
    # Create all tables in the test database
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session(setup_test_database):
    """Create a test database session"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_current_user():
    """Mock current user for authentication"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "permissions": [
            "orders:read", "orders:create", "orders:update", "orders:delete",
            "expenses:read", "expenses:create", "expenses:update", "expenses:delete", "expenses:approve", "expenses:reimburse",
            "pettycash:read", "pettycash:create", "pettycash:update", "pettycash:delete", "pettycash:reconcile", "pettycash:replenish",
            "vouchers:read", "vouchers:create", "vouchers:update", "vouchers:delete", "vouchers:approve", "vouchers:pay",
            "invoices:read", "invoices:create", "invoices:update", "invoices:delete", "invoices:send", "invoices:payment",
            "payments:read", "payments:create", "payments:update", "payments:delete", "payments:process", "payments:refund",
            "financial:read", "financial:admin"
        ],
        "roles": ["financial_admin"]
    }

@pytest.fixture
def mock_current_tenant():
    """Mock current tenant for multi-tenancy"""
    return {
        "tenant_id": "test-tenant-456",
        "tenant_name": "Test Company",
        "schema_name": "test_schema"
    }

@pytest.fixture
def client(db_session, mock_current_user, mock_current_tenant):
    """Create test client with mocked dependencies"""

    def override_get_db():
        return db_session

    def override_get_tenant_db():
        return db_session

    async def override_get_current_user():
        return mock_current_user

    async def override_get_current_tenant():
        return mock_current_tenant

    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_tenant_db] = override_get_tenant_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_tenant] = override_get_current_tenant

    with TestClient(app) as test_client:
        yield test_client

    # Clear overrides after test
    app.dependency_overrides.clear()

@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "quote_id": 1,
        "order_number": "ORD-2024-001",
        "order_status": "pending",
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "discount_amount": 50.00,
        "total_amount": 1050.00,
        "currency": "USD",
        "order_date": "2024-01-15",
        "departure_date": "2024-02-15",
        "return_date": "2024-02-22",
        "payment_status": "pending",
        "amount_paid": 0.00,
        "amount_due": 1050.00,
        "special_instructions": "Test order for integration testing"
    }

@pytest.fixture
def sample_expense_category_data():
    """Sample expense category data for testing"""
    return {
        "name": "Travel Expenses",
        "code": "TRAVEL",
        "description": "Business travel related expenses",
        "budget_monthly": 5000.00,
        "budget_yearly": 60000.00,
        "account_code": "6100",
        "tax_deductible": True,
        "requires_receipt": True,
        "requires_approval": True,
        "is_active": True,
        "approval_limit": 1000.00,
        "auto_approve_under": 100.00
    }

@pytest.fixture
def sample_expense_data():
    """Sample expense data for testing"""
    return {
        "category_id": 1,
        "expense_number": "EXP-2024-001",
        "expense_date": "2024-01-15",
        "expense_type": "travel",
        "description": "Business trip to client meeting",
        "amount": 250.00,
        "tax_amount": 25.00,
        "total_amount": 275.00,
        "currency": "USD",
        "payment_method": "credit_card",
        "is_reimbursable": True,
        "has_receipt": True,
        "receipt_number": "REC-001",
        "vendor_name": "Hotel ABC",
        "notes": "Client meeting accommodation"
    }

@pytest.fixture
def sample_petty_cash_data():
    """Sample petty cash fund data for testing"""
    return {
        "fund_name": "Office Petty Cash",
        "fund_code": "OFC-PC-001",
        "description": "Main office petty cash fund",
        "custodian_id": "test-user-123",
        "location": "Main Office",
        "initial_amount": 500.00,
        "current_balance": 500.00,
        "minimum_balance": 50.00,
        "maximum_balance": 1000.00,
        "replenishment_amount": 500.00,
        "status": "open",
        "is_active": True,
        "reconciliation_frequency": "monthly",
        "requires_receipt": True,
        "max_transaction_amount": 100.00
    }

@pytest.fixture
def sample_voucher_data():
    """Sample voucher data for testing"""
    return {
        "voucher_number": "VOU-2024-001",
        "voucher_date": "2024-01-15",
        "voucher_type": "payment",
        "payee_name": "ABC Supplier Ltd",
        "payee_type": "supplier",
        "amount": 1500.00,
        "currency": "USD",
        "exchange_rate": 1.0,
        "amount_in_words": "One thousand five hundred dollars",
        "payment_method": "bank_transfer",
        "purpose": "Office supplies purchase",
        "cost_center": "ADMIN",
        "status": "draft",
        "accounting_period": "2024-01",
        "notes": "Monthly office supplies order"
    }

@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
        "order_id": 1,
        "account_id": 1,
        "contact_id": 1,
        "invoice_number": "INV-2024-001",
        "status": "draft",
        "invoice_date": "2024-01-15",
        "due_date": "2024-02-15",
        "subtotal": 1000.00,
        "tax_amount": 100.00,
        "discount_amount": 0.00,
        "total_amount": 1100.00,
        "paid_amount": 0.00,
        "balance_due": 1100.00,
        "currency": "USD",
        "notes": "Test invoice for integration testing",
        "terms_conditions": "Net 30 days",
        "billing_name": "Test Customer",
        "billing_address": "123 Test Street",
        "billing_city": "Test City",
        "billing_state": "Test State",
        "billing_postal_code": "12345",
        "billing_country": "USA"
    }

@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing"""
    return {
        "invoice_id": 1,
        "payment_number": "PAY-2024-001",
        "payment_date": "2024-01-15",
        "amount": 1100.00,
        "currency": "USD",
        "payment_method": "credit_card",
        "payment_type": "full",
        "transaction_type": "payment",
        "reference_number": "REF-001",
        "transaction_id": "TXN-12345",
        "gateway_transaction_id": "GTW-67890",
        "card_last4": "1234",
        "card_brand": "Visa",
        "card_type": "credit",
        "authorization_code": "AUTH123",
        "status": "completed",
        "notes": "Payment for test invoice"
    }

@pytest.fixture
def sample_payment_gateway_data():
    """Sample payment gateway data for testing"""
    return {
        "gateway_name": "Test Stripe Gateway",
        "gateway_code": "stripe_test",
        "gateway_type": "stripe",
        "is_active": True,
        "is_test_mode": True,
        "priority": 1,
        "api_endpoint": "https://api.stripe.com/v1",
        "merchant_id": "acct_test123",
        "supports_credit_cards": True,
        "supports_debit_cards": True,
        "supports_bank_transfer": False,
        "supports_digital_wallets": True,
        "supports_recurring": True,
        "supports_refunds": True,
        "supports_partial_refunds": True,
        "transaction_fee_percent": 2.9,
        "transaction_fee_fixed": 0.30,
        "refund_fee_percent": 0.0,
        "refund_fee_fixed": 0.0,
        "min_transaction_amount": 1.00,
        "max_transaction_amount": 10000.00,
        "supported_currencies": ["USD", "EUR", "GBP"],
        "default_currency": "USD",
        "authorization_time_minutes": 5,
        "settlement_time_days": 2,
        "refund_time_days": 5,
        "configuration_notes": "Test gateway configuration"
    }

# Mock authentication patches
@pytest.fixture
def mock_auth_patches():
    """Mock authentication functions for testing"""
    with patch('shared_auth.verify_token') as mock_verify_token, \
         patch('shared_auth.get_user_permissions') as mock_get_permissions, \
         patch('shared_auth.get_tenant_info') as mock_get_tenant:

        mock_verify_token.return_value = {
            "user_id": "test-user-123",
            "email": "test@example.com"
        }

        mock_get_permissions.return_value = [
            "orders:read", "orders:create", "orders:update", "orders:delete",
            "expenses:read", "expenses:create", "expenses:update", "expenses:delete", "expenses:approve",
            "pettycash:read", "pettycash:create", "pettycash:update", "pettycash:delete",
            "vouchers:read", "vouchers:create", "vouchers:update", "vouchers:delete",
            "invoices:read", "invoices:create", "invoices:update", "invoices:delete",
            "payments:read", "payments:create", "payments:update", "payments:delete",
            "financial:read", "financial:admin"
        ]

        mock_get_tenant.return_value = {
            "tenant_id": "test-tenant-456",
            "tenant_name": "Test Company",
            "schema_name": "test_schema"
        }

        yield {
            "verify_token": mock_verify_token,
            "get_permissions": mock_get_permissions,
            "get_tenant": mock_get_tenant
        }

@pytest.fixture
def headers():
    """Standard headers for API requests"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
        "X-Tenant-ID": "test-tenant-456"
    }

# Utility functions for tests
def assert_response_success(response, expected_status=200):
    """Assert that response is successful"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"

def assert_response_error(response, expected_status=400):
    """Assert that response is an error"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"

def get_response_data(response):
    """Get response data and assert success"""
    assert_response_success(response)
    return response.json()
