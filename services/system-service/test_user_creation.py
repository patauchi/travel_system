#!/usr/bin/env python3
"""
Test script to verify user creation endpoint works correctly with tenant database context
Tests the /api/v1/tenants/{tenant_slug}/users endpoint
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import verify_tenant_schema_exists, get_schema_name_from_slug
from dependencies import get_tenant_db_session
from models import User
from utils import get_password_hash, create_access_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TENANT_SLUG = "tenant100"
TEST_SCHEMA_NAME = "tenant_tenant100"
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8004")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)

# Test user data
TEST_ADMIN_USER = {
    "email": "admin@tenant100.com",
    "username": "admin100",
    "password": "Admin123!@#"
}

TEST_NEW_USER = {
    "email": "testuser@tenant100.com",
    "username": "testuser100",
    "password": "Test123!@#",
    "first_name": "Test",
    "last_name": "User",
    "department": "Engineering",
    "title": "Software Engineer"
}


def create_test_token(user_id: str, tenant_id: str) -> str:
    """Create a test JWT token for authentication"""
    token_data = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "permissions": ["users.create", "users.view", "users.update", "users.delete"],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return create_access_token(token_data)


def setup_test_admin_user():
    """Setup an admin user in the tenant for testing"""
    logger.info("Setting up test admin user...")

    try:
        # Get a database session for the tenant
        gen = get_tenant_db_session(TEST_TENANT_SLUG)
        db = next(gen)

        try:
            # Check if admin user already exists
            existing_user = db.query(User).filter(
                User.email == TEST_ADMIN_USER["email"]
            ).first()

            if existing_user:
                logger.info(f"Admin user already exists: {existing_user.username}")
                return str(existing_user.id), TEST_TENANT_SLUG

            # Create admin user
            admin_user = User(
                email=TEST_ADMIN_USER["email"],
                username=TEST_ADMIN_USER["username"],
                password_hash=get_password_hash(TEST_ADMIN_USER["password"]),
                first_name="Admin",
                last_name="User",
                full_name="Admin User",
                is_active=True,
                is_superuser=True
            )

            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            logger.info(f"Created admin user: {admin_user.username} (ID: {admin_user.id})")
            return str(admin_user.id), TEST_TENANT_SLUG

        finally:
            # Cleanup
            try:
                next(gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error setting up admin user: {str(e)}")
        raise


def test_user_creation_endpoint():
    """Test the user creation endpoint"""
    logger.info("=" * 60)
    logger.info("Testing User Creation Endpoint")
    logger.info("=" * 60)

    # Setup admin user and get token
    try:
        admin_id, tenant_id = setup_test_admin_user()
        token = create_test_token(admin_id, tenant_id)
        logger.info(f"Generated auth token for admin user {admin_id}")
    except Exception as e:
        logger.error(f"Failed to setup test environment: {str(e)}")
        return False

    # Prepare request
    url = f"{API_BASE_URL}/api/v1/tenants/{TEST_TENANT_SLUG}/users"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logger.info(f"POST {url}")
    logger.info(f"Request body: {json.dumps(TEST_NEW_USER, indent=2)}")

    # Make request
    try:
        response = requests.post(url, json=TEST_NEW_USER, headers=headers)

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")

        if response.status_code == 201 or response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response body: {json.dumps(response_data, indent=2)}")

            # Verify the user was created
            if verify_user_created(TEST_NEW_USER["email"]):
                logger.info("✅ User creation successful!")
                return True
            else:
                logger.error("❌ User creation endpoint returned success but user not found in database")
                return False

        else:
            logger.error(f"❌ User creation failed with status {response.status_code}")
            try:
                error_detail = response.json()
                logger.error(f"Error response: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error(f"Error response text: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error("❌ Failed to connect to the API. Is the service running?")
        logger.info("Start the service with: cd services/system-service && venv/bin/python main.py")
        return False
    except Exception as e:
        logger.error(f"❌ Request failed: {str(e)}")
        return False


def verify_user_created(email: str) -> bool:
    """Verify that a user was created in the tenant database"""
    try:
        gen = get_tenant_db_session(TEST_TENANT_SLUG)
        db = next(gen)

        try:
            user = db.query(User).filter(User.email == email).first()

            if user:
                logger.info(f"Found user in database: {user.username} (ID: {user.id})")
                logger.info(f"  Email: {user.email}")
                logger.info(f"  Name: {user.full_name}")
                logger.info(f"  Department: {user.department}")
                logger.info(f"  Title: {user.title}")
                return True
            else:
                logger.warning(f"User with email {email} not found in database")
                return False

        finally:
            # Cleanup
            try:
                next(gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error verifying user: {str(e)}")
        return False


def cleanup_test_user():
    """Remove the test user from the database"""
    try:
        gen = get_tenant_db_session(TEST_TENANT_SLUG)
        db = next(gen)

        try:
            # Find and delete test user
            test_user = db.query(User).filter(
                User.email == TEST_NEW_USER["email"]
            ).first()

            if test_user:
                db.delete(test_user)
                db.commit()
                logger.info(f"Cleaned up test user: {test_user.username}")

        finally:
            # Cleanup
            try:
                next(gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.warning(f"Error during cleanup: {str(e)}")


def test_user_list_endpoint():
    """Test the user list endpoint"""
    logger.info("=" * 60)
    logger.info("Testing User List Endpoint")
    logger.info("=" * 60)

    # Setup admin user and get token
    try:
        admin_id, tenant_id = setup_test_admin_user()
        token = create_test_token(admin_id, tenant_id)
    except Exception as e:
        logger.error(f"Failed to setup test environment: {str(e)}")
        return False

    # Prepare request
    url = f"{API_BASE_URL}/api/v1/tenants/{TEST_TENANT_SLUG}/users"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    logger.info(f"GET {url}")

    # Make request
    try:
        response = requests.get(url, headers=headers)

        logger.info(f"Response status: {response.status_code}")

        if response.status_code == 200:
            users = response.json()
            logger.info(f"Found {len(users)} users in tenant {TEST_TENANT_SLUG}")

            for user in users[:3]:  # Show first 3 users
                logger.info(f"  - {user.get('username')} ({user.get('email')})")

            logger.info("✅ User list endpoint working correctly!")
            return True
        else:
            logger.error(f"❌ User list failed with status {response.status_code}")
            try:
                error_detail = response.json()
                logger.error(f"Error response: {json.dumps(error_detail, indent=2)}")
            except:
                logger.error(f"Error response text: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error("❌ Failed to connect to the API. Is the service running?")
        return False
    except Exception as e:
        logger.error(f"❌ Request failed: {str(e)}")
        return False


def run_all_tests():
    """Run all endpoint tests"""
    logger.info("=" * 60)
    logger.info("USER ENDPOINT TESTS")
    logger.info(f"Testing with tenant: {TEST_TENANT_SLUG}")
    logger.info(f"API URL: {API_BASE_URL}")
    logger.info("=" * 60)

    # Verify schema exists
    if not verify_tenant_schema_exists(TEST_SCHEMA_NAME):
        logger.error(f"Schema {TEST_SCHEMA_NAME} does not exist!")
        return 1

    # Cleanup any existing test user
    cleanup_test_user()

    # Run tests
    tests = [
        ("User List Endpoint", test_user_list_endpoint),
        ("User Creation Endpoint", test_user_creation_endpoint),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            logger.info(f"\nRunning: {test_name}")
            result = test_func()
            results[test_name] = result

        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {str(e)}")
            results[test_name] = False

    # Cleanup
    cleanup_test_user()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! User endpoints are working correctly with tenant database.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Please check the logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
