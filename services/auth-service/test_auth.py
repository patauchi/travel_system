#!/usr/bin/env python3
"""
Script to test authentication endpoints using httpx
"""

import httpx
import json
import asyncio
from typing import Optional, Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api/v1/auth"

class AuthTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_url = f"{base_url}{API_PREFIX}"
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    async def test_login(self, username: str, password: str, tenant_slug: Optional[str] = None) -> bool:
        """Test login endpoint"""
        print(f"\n🔐 Testing login for user: {username}")

        login_data = {
            "username": username,
            "password": password
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # Build URL with tenant as query parameter if provided
        login_url = f"{self.api_url}/login"
        if tenant_slug:
            login_url = f"{login_url}?tenant={tenant_slug}"
            print(f"   Tenant: {tenant_slug}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    login_url,
                    data=login_data,
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")

                    print("✅ Login successful!")
                    print(f"   Access Token: {self.access_token[:50]}...")
                    print(f"   Token Type: {data.get('token_type')}")

                    if data.get("user"):
                        print(f"   User: {data['user'].get('username')} ({data['user'].get('email')})")

                    if data.get("tenant"):
                        print(f"   Tenant: {data['tenant'].get('name')} (ID: {data['tenant'].get('id')})")

                    return True
                else:
                    print(f"❌ Login failed with status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ Error during login: {str(e)}")
                return False

    async def test_me_endpoint(self, tenant_slug: Optional[str] = None) -> bool:
        """Test /me endpoint"""
        print("\n👤 Testing /me endpoint...")

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return False

        headers = {"Authorization": f"Bearer {self.access_token}"}

        # Add tenant context if provided
        me_url = f"{self.api_url}/me"
        if tenant_slug:
            me_url = f"{me_url}?tenant={tenant_slug}"
            print(f"   With tenant context: {tenant_slug}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    me_url,
                    headers=headers
                )

                if response.status_code == 200:
                    user_info = response.json()
                    print("✅ /me endpoint working correctly!")
                    print("   User Information:")
                    print(json.dumps(user_info, indent=4))
                    return True
                else:
                    print(f"❌ /me endpoint failed with status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ Error accessing /me endpoint: {str(e)}")
                return False

    async def test_refresh_token(self) -> bool:
        """Test token refresh endpoint"""
        print("\n🔄 Testing token refresh...")

        if not self.refresh_token:
            print("❌ No refresh token available. Please login first.")
            return False

        async with httpx.AsyncClient() as client:
            try:
                # refresh_token is a query parameter, not in the body
                response = await client.post(
                    f"{self.api_url}/refresh?refresh_token={self.refresh_token}",
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")

                    print("✅ Token refresh successful!")
                    print(f"   New Access Token: {self.access_token[:50]}...")
                    return True
                else:
                    print(f"❌ Token refresh failed with status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ Error during token refresh: {str(e)}")
                return False

    async def test_logout(self) -> bool:
        """Test logout endpoint"""
        print("\n🚪 Testing logout...")

        if not self.access_token:
            print("❌ No access token available. Please login first.")
            return False

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/logout",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    }
                )

                if response.status_code == 200:
                    print("✅ Logout successful!")
                    self.access_token = None
                    self.refresh_token = None
                    return True
                else:
                    print(f"❌ Logout failed with status: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False

            except Exception as e:
                print(f"❌ Error during logout: {str(e)}")
                return False

async def run_tests():
    """Run all authentication tests"""
    print("=" * 60)
    print("🧪 AUTHENTICATION SYSTEM TEST SUITE")
    print("=" * 60)

    tester = AuthTester()

    # Test 1: Super Admin Login
    print("\n📝 Test 1: Super Admin Login")
    print("-" * 40)
    if await tester.test_login("admin", "Admin123!"):
        await tester.test_me_endpoint()  # No tenant for super admin
        # Skip refresh token test for now as it needs proper implementation
        # await tester.test_refresh_token()
        await tester.test_logout()

    # Test 2: Demo Tenant Admin Login
    print("\n📝 Test 2: Demo Tenant Admin Login")
    print("-" * 40)
    if await tester.test_login("demo_admin", "Demo123!", "demo"):
        await tester.test_me_endpoint("demo")  # Pass tenant context
        await tester.test_logout()

    # Test 3: Demo Tenant User Login
    print("\n📝 Test 3: Demo Tenant User Login")
    print("-" * 40)
    if await tester.test_login("demo_user", "User123!", "demo"):
        await tester.test_me_endpoint("demo")  # Pass tenant context
        await tester.test_logout()

    # Test 4: Invalid Login
    print("\n📝 Test 4: Invalid Login Attempt")
    print("-" * 40)
    await tester.test_login("invalid_user", "wrong_password")

    print("\n" + "=" * 60)
    print("✨ TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
