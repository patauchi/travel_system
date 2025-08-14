#!/usr/bin/env python3
"""
Financial Service Startup Test
Quick test script to verify the service can start without errors
"""

import sys
import os
import traceback
from datetime import datetime

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    symbol = symbols.get(status, "•")
    print(f"[{timestamp}] {symbol} {message}")

def test_imports():
    """Test that all modules can be imported without errors"""
    print_status("Testing module imports...")

    try:
        # Test basic FastAPI imports
        import fastapi
        import uvicorn
        import sqlalchemy
        import pydantic
        print_status("Core dependencies imported successfully")

        # Test database imports
        from database import get_db, get_tenant_db
        print_status("Database modules imported successfully")

        # Test auth imports
        from shared_auth import get_current_user, get_current_tenant
        print_status("Authentication modules imported successfully")

        # Test common imports
        from common.enums import OrderStatus, ExpenseStatus, PaymentMethod
        print_status("Common enums imported successfully")

        # Test all module imports
        from orders import router as orders_router
        print_status("Orders module imported successfully")

        from expenses import router as expenses_router
        print_status("Expenses module imported successfully")

        from pettycash import router as pettycash_router
        print_status("Petty Cash module imported successfully")

        from voucher import router as voucher_router
        print_status("Voucher module imported successfully")

        from invoices import router as invoices_router
        print_status("Invoices module imported successfully")

        from payments import router as payments_router
        print_status("Payments module imported successfully")

        # Test models import
        from models_all import Base, Order, Expense, Payment
        print_status("Unified models imported successfully")

        return True

    except ImportError as e:
        print_status(f"Import error: {str(e)}", "ERROR")
        traceback.print_exc()
        return False
    except Exception as e:
        print_status(f"Unexpected error during imports: {str(e)}", "ERROR")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test that the FastAPI app can be created"""
    print_status("Testing FastAPI app creation...")

    try:
        # Import main app
        from main import app
        print_status("FastAPI app created successfully")

        # Check that routers are included
        routes = [route.path for route in app.routes]
        expected_prefixes = [
            "/api/v1/financial/orders",
            "/api/v1/financial/expenses",
            "/api/v1/financial/payments"
        ]

        for prefix in expected_prefixes:
            if any(route.startswith(prefix) for route in routes):
                print_status(f"Router registered: {prefix}")
            else:
                print_status(f"Router missing: {prefix}", "WARNING")

        print_status(f"Total routes registered: {len(routes)}")
        return True

    except Exception as e:
        print_status(f"App creation error: {str(e)}", "ERROR")
        traceback.print_exc()
        return False

def test_environment():
    """Test environment setup"""
    print_status("Testing environment configuration...")

    try:
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        print_status(f"Python version: {python_version}")

        if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 8):
            print_status("Python 3.8+ required", "WARNING")

        # Check environment variables
        env_vars = [
            "DATABASE_URL",
            "CORS_ORIGINS"
        ]

        for var in env_vars:
            value = os.getenv(var)
            if value:
                print_status(f"{var}: {'*' * min(len(value), 20)}")
            else:
                print_status(f"{var}: Not set", "WARNING")

        return True

    except Exception as e:
        print_status(f"Environment test error: {str(e)}", "ERROR")
        return False

def test_database_models():
    """Test that database models are properly defined"""
    print_status("Testing database models...")

    try:
        from models_all import Base
        from sqlalchemy import create_engine

        # Create in-memory SQLite database for testing
        engine = create_engine("sqlite:///:memory:")

        # Try to create all tables
        Base.metadata.create_all(engine)
        print_status("All database tables created successfully")

        # Check that all expected tables exist
        inspector = engine.inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = [
            'orders', 'order_lines', 'passenger_documents',
            'expenses', 'expense_categories',
            'petty_cashes', 'petty_cash_transactions',
            'vouchers',
            'invoices', 'invoice_lines', 'accounts_receivables', 'accounts_payables',
            'payments', 'payment_gateways', 'payment_attempts'
        ]

        for table in expected_tables:
            if table in tables:
                print_status(f"Table exists: {table}")
            else:
                print_status(f"Table missing: {table}", "WARNING")

        print_status(f"Total tables created: {len(tables)}")
        return True

    except Exception as e:
        print_status(f"Database models test error: {str(e)}", "ERROR")
        traceback.print_exc()
        return False

def test_startup_health():
    """Test service startup without actually starting server"""
    print_status("Testing service startup sequence...")

    try:
        from main import app

        # Test that health endpoint exists
        routes = [route.path for route in app.routes]
        health_routes = [route for route in routes if 'health' in route]

        if health_routes:
            print_status(f"Health endpoints found: {len(health_routes)}")
            for route in health_routes:
                print_status(f"  - {route}")
        else:
            print_status("No health endpoints found", "WARNING")

        # Test that all module routers are included
        module_count = 0
        for route in app.routes:
            if hasattr(route, 'tags') and route.tags:
                for tag in route.tags:
                    if 'Management' in tag:
                        module_count += 1
                        break

        print_status(f"Module routers detected: {module_count}")

        return True

    except Exception as e:
        print_status(f"Startup health test error: {str(e)}", "ERROR")
        traceback.print_exc()
        return False

def main():
    """Run all startup tests"""
    print("=" * 60)
    print("🚀 FINANCIAL SERVICE STARTUP TEST")
    print("=" * 60)
    print_status("Starting comprehensive startup tests...")

    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    tests = [
        ("Environment Check", test_environment),
        ("Module Imports", test_imports),
        ("Database Models", test_database_models),
        ("App Creation", test_app_creation),
        ("Startup Health", test_startup_health)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_status(f"Test {test_name} failed with exception: {str(e)}", "ERROR")
            results[test_name] = False

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✅" if result else "❌"
        print(f"{symbol} {status:<6} {test_name}")

    print(f"\nResult: {passed}/{total} tests passed")

    if passed == total:
        print_status("🎉 All tests passed! Service should start successfully.", "SUCCESS")
        return 0
    else:
        print_status(f"💥 {total - passed} test(s) failed. Service may have startup issues.", "ERROR")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("\n⚠️ Test interrupted by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"\n💥 Unexpected error: {str(e)}", "ERROR")
        traceback.print_exc()
        sys.exit(1)
