#!/usr/bin/env python3
"""
Test script for Booking Operations Service
Tests authentication, CRUD operations, and tenant-specific endpoints
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8004"
AUTH_URL = "http://localhost:8001"

# Test data storage
test_data = {
    "token": None,
    "tenant_slug": "tenant1",
    "created_ids": {
        "country": None,
        "destination": None,
        "supplier": None,
        "service": None,
        "cancellation_policy": None,
        "booking": None,
        "passenger": None,
        "rate": None
    }
}


def print_test_header(test_name: str):
    """Print a formatted test header"""
    print("\n" + "="*60)
    print(f"TEST: {test_name}")
    print("="*60)


def print_result(success: bool, message: str, details: Any = None):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"Details: {json.dumps(details, indent=2)}")


def get_auth_token() -> Optional[str]:
    """Get authentication token from auth service"""
    print_test_header("Authentication")

    # Try to create a test user first
    print("Creating test user...")
    register_url = f"{AUTH_URL}/api/v1/auth/register"
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }

    try:
        # Try to register (might fail if user exists)
        requests.post(register_url, json=user_data)
    except:
        pass

    # Now try to login with form data
    login_url = f"{AUTH_URL}/api/v1/auth/login"
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }

    try:
        response = requests.post(
            login_url,
            data=login_data,  # Use form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print_result(True, "Authentication successful", {"token": token[:20] + "..."})
            return token
        else:
            print_result(False, f"Authentication failed: {response.status_code}", response.json())
            return None
    except Exception as e:
        print_result(False, f"Authentication error: {str(e)}")
        return None


def test_without_auth():
    """Test endpoints without authentication"""
    print_test_header("Tests WITHOUT Authentication")

    # Test health endpoint (should work without auth)
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_result(True, "Health check accessible without auth", response.json())
        else:
            print_result(False, f"Health check failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Health check error: {str(e)}")

    # Test protected endpoint (should fail without auth)
    print("\n2. Testing protected endpoint without auth...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/test")
        if response.status_code == 401:
            print_result(True, "Protected endpoint correctly requires auth")
        else:
            print_result(False, f"Protected endpoint should return 401, got {response.status_code}")
    except Exception as e:
        print_result(False, f"Protected endpoint error: {str(e)}")

    # Test service info endpoint
    print("\n3. Testing service info endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/service/info")
        if response.status_code == 200:
            print_result(True, "Service info accessible", response.json()["modules"])
        else:
            print_result(False, f"Service info failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Service info error: {str(e)}")


def test_with_auth(token: str):
    """Test endpoints with authentication"""
    print_test_header("Tests WITH Authentication")

    headers = {"Authorization": f"Bearer {token}"}

    # Test auth verification
    print("\n1. Testing auth verification...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/test", headers=headers)
        if response.status_code == 200:
            print_result(True, "Auth verification successful", response.json())
        else:
            print_result(False, f"Auth verification failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Auth verification error: {str(e)}")

    # Test tenant-specific auth
    print("\n2. Testing tenant-specific auth...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/{test_data['tenant_slug']}/auth/test",
            headers=headers
        )
        if response.status_code == 200:
            print_result(True, "Tenant auth successful", response.json())
        else:
            print_result(False, f"Tenant auth failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Tenant auth error: {str(e)}")


def test_crud_countries(token: str):
    """Test CRUD operations for countries"""
    print_test_header("CRUD Operations - Countries")

    headers = {"Authorization": f"Bearer {token}"}
    tenant_slug = test_data["tenant_slug"]

    # CREATE
    print("\n1. CREATE Country...")
    country_data = {
        "code": "PE",
        "code3": "PER",
        "name": "Peru",
        "continent": "South America",
        "is_active": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/countries",
            headers=headers,
            json=country_data
        )
        if response.status_code in [200, 201]:
            result = response.json()
            test_data["created_ids"]["country"] = result.get("id")
            print_result(True, "Country created successfully", result)
        else:
            print_result(False, f"Country creation failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Country creation error: {str(e)}")

    # READ (List)
    print("\n2. READ Countries (List)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/countries",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Listed {len(result.get('items', []))} countries")
        else:
            print_result(False, f"Country list failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Country list error: {str(e)}")

    # READ (Single)
    if test_data["created_ids"]["country"]:
        print("\n3. READ Single Country...")
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/tenants/{tenant_slug}/countries/{test_data['created_ids']['country']}",
                headers=headers
            )
            if response.status_code == 200:
                print_result(True, "Country retrieved successfully", response.json())
            else:
                print_result(False, f"Country retrieval failed: {response.status_code}")
        except Exception as e:
            print_result(False, f"Country retrieval error: {str(e)}")

    # UPDATE
    if test_data["created_ids"]["country"]:
        print("\n4. UPDATE Country...")
        update_data = {"name": "Republic of Peru"}
        try:
            response = requests.put(
                f"{BASE_URL}/api/v1/tenants/{tenant_slug}/countries/{test_data['created_ids']['country']}",
                headers=headers,
                json=update_data
            )
            if response.status_code == 200:
                print_result(True, "Country updated successfully", response.json())
            else:
                print_result(False, f"Country update failed: {response.status_code}")
        except Exception as e:
            print_result(False, f"Country update error: {str(e)}")


def test_crud_suppliers(token: str):
    """Test CRUD operations for suppliers"""
    print_test_header("CRUD Operations - Suppliers")

    headers = {"Authorization": f"Bearer {token}"}
    tenant_slug = test_data["tenant_slug"]

    # CREATE
    print("\n1. CREATE Supplier...")
    supplier_data = {
        "code": "SUP001",
        "name": "Test Travel Agency",
        "legal_name": "Test Travel Agency S.A.",
        "tax_id": "20123456789",
        "supplier_type": "agency",
        "status": "active",
        "contact_email": "contact@testagency.com",
        "contact_phone": "+51999888777",
        "website": "https://testagency.com",
        "is_active": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/suppliers",
            headers=headers,
            json=supplier_data
        )
        if response.status_code in [200, 201]:
            result = response.json()
            test_data["created_ids"]["supplier"] = result.get("id")
            print_result(True, "Supplier created successfully", result)
        else:
            print_result(False, f"Supplier creation failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Supplier creation error: {str(e)}")

    # READ (List)
    print("\n2. READ Suppliers (List)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/suppliers",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Listed {len(result.get('items', []))} suppliers")
        else:
            print_result(False, f"Supplier list failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Supplier list error: {str(e)}")


def test_crud_services(token: str):
    """Test CRUD operations for services"""
    print_test_header("CRUD Operations - Services")

    headers = {"Authorization": f"Bearer {token}"}
    tenant_slug = test_data["tenant_slug"]

    # First ensure we have a supplier
    if not test_data["created_ids"]["supplier"]:
        print("No supplier available, skipping service tests")
        return

    # CREATE
    print("\n1. CREATE Service...")
    service_data = {
        "supplier_id": test_data["created_ids"]["supplier"],
        "code": "SRV001",
        "name": "Machu Picchu Tour",
        "description": "Full day tour to Machu Picchu",
        "service_type": "tour",
        "operation_model": "scheduled",
        "base_price": 150.00,
        "currency": "USD",
        "duration_value": 12,
        "duration_unit": "hours",
        "max_capacity": 20,
        "min_capacity": 2,
        "is_active": True
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/services",
            headers=headers,
            json=service_data
        )
        if response.status_code in [200, 201]:
            result = response.json()
            test_data["created_ids"]["service"] = result.get("id")
            print_result(True, "Service created successfully", result)
        else:
            print_result(False, f"Service creation failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Service creation error: {str(e)}")

    # READ (List)
    print("\n2. READ Services (List)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/services",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Listed {len(result.get('items', []))} services")
        else:
            print_result(False, f"Service list failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Service list error: {str(e)}")


def test_crud_bookings(token: str):
    """Test CRUD operations for bookings"""
    print_test_header("CRUD Operations - Bookings")

    headers = {"Authorization": f"Bearer {token}"}
    tenant_slug = test_data["tenant_slug"]

    # CREATE
    print("\n1. CREATE Booking...")
    booking_data = {
        "order_id": 1001,
        "booking_reference": "BK2024001",
        "external_reference": "EXT001",
        "booking_date": datetime.now().isoformat(),
        "service_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "overall_status": "pending",
        "total_amount": 300.00,
        "currency": "USD",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "notes": "Test booking"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/bookings",
            headers=headers,
            json=booking_data
        )
        if response.status_code in [200, 201]:
            result = response.json()
            test_data["created_ids"]["booking"] = result.get("id")
            print_result(True, "Booking created successfully", result)
        else:
            print_result(False, f"Booking creation failed: {response.status_code}", response.json())
    except Exception as e:
        print_result(False, f"Booking creation error: {str(e)}")

    # READ (List)
    print("\n2. READ Bookings (List)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/tenants/{tenant_slug}/bookings",
            headers=headers
        )
        if response.status_code == 200:
            result = response.json()
            print_result(True, f"Listed {len(result.get('items', []))} bookings")
        else:
            print_result(False, f"Booking list failed: {response.status_code}")
    except Exception as e:
        print_result(False, f"Booking list error: {str(e)}")

    # UPDATE Status
    if test_data["created_ids"]["booking"]:
        print("\n3. UPDATE Booking Status...")
        update_data = {"overall_status": "confirmed"}
        try:
            response = requests.patch(
                f"{BASE_URL}/api/v1/tenants/{tenant_slug}/bookings/{test_data['created_ids']['booking']}/status",
                headers=headers,
                json=update_data
            )
            if response.status_code == 200:
                print_result(True, "Booking status updated successfully")
            else:
                print_result(False, f"Booking status update failed: {response.status_code}")
        except Exception as e:
            print_result(False, f"Booking status update error: {str(e)}")


def test_cleanup(token: str):
    """Clean up test data"""
    print_test_header("Cleanup")

    headers = {"Authorization": f"Bearer {token}"}
    tenant_slug = test_data["tenant_slug"]

    # Delete in reverse order of dependencies
    cleanup_order = [
        ("booking", "bookings"),
        ("service", "services"),
        ("supplier", "suppliers"),
        ("country", "countries")
    ]

    for key, endpoint in cleanup_order:
        if test_data["created_ids"][key]:
            print(f"\nDeleting {key}...")
            try:
                response = requests.delete(
                    f"{BASE_URL}/api/v1/tenants/{tenant_slug}/{endpoint}/{test_data['created_ids'][key]}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    print_result(True, f"{key.capitalize()} deleted successfully")
                else:
                    print_result(False, f"{key.capitalize()} deletion failed: {response.status_code}")
            except Exception as e:
                print_result(False, f"{key.capitalize()} deletion error: {str(e)}")


def main():
    """Main test execution"""
    print("\n" + "="*60)
    print("BOOKING OPERATIONS SERVICE TEST SUITE")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    print(f"Auth URL: {AUTH_URL}")
    print(f"Testing at: {datetime.now().isoformat()}")

    # Test without authentication
    test_without_auth()

    # Get authentication token
    token = get_auth_token()
    if not token:
        print("\n❌ Cannot continue without authentication token")
        return 1

    test_data["token"] = token

    # Test with authentication
    test_with_auth(token)

    # Test CRUD operations
    test_crud_countries(token)
    test_crud_suppliers(token)
    test_crud_services(token)
    test_crud_bookings(token)

    # Cleanup
    test_cleanup(token)

    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
