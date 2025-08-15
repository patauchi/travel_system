"""
Communication Service Security Tests
Comprehensive testing of all CRUD operations and security features
Based on the same pattern as test_system.py
"""

import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid
import json

# Test configuration
BASE_URL = "http://localhost"
AUTH_SERVICE_URL = f"{BASE_URL}:8001"
TENANT_SERVICE_URL = f"{BASE_URL}:8002"
COMMUNICATION_SERVICE_URL = f"{BASE_URL}:8005"
SYSTEM_SERVICE_URL = f"{BASE_URL}:8008"

# Default super_admin credentials (from init.sql)
SUPER_ADMIN_USERNAME = "superadmin"
SUPER_ADMIN_PASSWORD = "SuperAdmin123!"


class TestCommunicationSecurity:
    """Security tests for Communication Service"""

    def __init__(self):
        self.tenant_data = None
        self.tenant_id = None
        self.tenant_slug = None
        self.owner_token = None
        self.super_admin_token = None
        self.unique_id = None

        # Store created IDs for cleanup
        self.created_conversation_id = None
        self.created_message_id = None
        self.created_quick_reply_id = None
        self.created_channel_id = None
        self.created_channel_member_id = None
        self.created_chat_entry_id = None
        self.created_mention_id = None

    async def setup_tenant(self) -> Dict[str, Any]:
        """Create a new tenant for testing"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("SETUP: Creating Test Tenant")
            print("="*60)

            # Login as super_admin
            print("\n[1] Logging in as super_admin...")
            login_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/auth/login",
                data={
                    "username": SUPER_ADMIN_USERNAME,
                    "password": SUPER_ADMIN_PASSWORD
                }
            )

            if login_response.status_code != 200:
                print(f"❌ Failed to login as super_admin: {login_response.status_code}")
                return {"success": False}

            auth_data = login_response.json()
            self.super_admin_token = auth_data["access_token"]
            print("✅ Super admin logged in successfully")

            # Create tenant
            print("\n[2] Creating test tenant...")
            unique_id = str(uuid.uuid4())[:8]
            self.tenant_slug = f"test-comm-{unique_id}"
            self.unique_id = unique_id

            tenant_response = await client.post(
                f"{TENANT_SERVICE_URL}/api/v1/tenants/v2",
                headers={"Authorization": f"Bearer {self.super_admin_token}"},
                json={
                    "slug": self.tenant_slug,
                    "name": f"Test Communication Tenant {unique_id}",
                    "subdomain": self.tenant_slug,
                    "owner_email": f"owner_comm_{unique_id}@test.com",
                    "owner_username": f"owner_comm_{unique_id}",
                    "owner_password": "OwnerPass123!",
                    "owner_first_name": "Test",
                    "owner_last_name": "Owner",
                    "subscription_plan": "professional",
                    "max_users": 50,
                    "settings": {
                        "timezone": "UTC",
                        "language": "en",
                        "currency": "USD"
                    }
                }
            )

            if tenant_response.status_code not in [200, 201]:
                print(f"❌ Failed to create tenant: {tenant_response.status_code}")
                print(f"   Response: {tenant_response.text}")
                return {"success": False}

            result = tenant_response.json()
            if "tenant" in result:
                self.tenant_data = result["tenant"]
                self.tenant_id = self.tenant_data["id"]
            else:
                # Fallback for different response formats
                self.tenant_data = result
                self.tenant_id = result.get("id")
            print(f"✅ Tenant created: {self.tenant_slug}")

            return {"success": True}

    async def authenticate_owner(self) -> bool:
        """Authenticate as tenant owner"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("AUTHENTICATION: Tenant Owner Login")
            print("="*60)

            print(f"\n[1] Attempting tenant-specific login for {self.tenant_slug}...")

            # Try communication-service specific login endpoint first
            try:
                login_response = await client.post(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/auth/tenant/login",
                    headers={"X-Tenant-ID": self.tenant_id},
                    json={
                        "email": f"owner_comm_{self.unique_id}@test.com",
                        "password": "OwnerPass123!",
                        "tenant_id": self.tenant_id
                    }
                )

                if login_response.status_code == 200:
                    auth_data = login_response.json()
                    self.owner_token = auth_data["access_token"]
                    print("✅ Tenant owner authenticated successfully")
                    return True
            except Exception as e:
                print(f"   Communication service login failed: {e}")

            # Fallback to auth-service login
            print("\n[2] Fallback: Trying auth-service login with tenant header...")
            login_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/auth/login",
                headers={"X-Tenant-Slug": self.tenant_slug},
                data={
                    "username": f"owner_comm_{self.unique_id}",
                    "password": "OwnerPass123!"
                }
            )

            if login_response.status_code == 200:
                auth_data = login_response.json()
                self.owner_token = auth_data["access_token"]
                print("✅ Tenant owner authenticated successfully via auth-service")
                return True

            print(f"❌ Failed to authenticate owner: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False

    async def test_endpoints_without_token(self) -> List[tuple]:
        """Test that protected endpoints reject requests without authentication"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: Communication Endpoints WITHOUT Token")
            print("="*60)

            test_results = []

            # Test public endpoints (should work without auth)
            public_tests = [
                ("GET", "/", "Root endpoint"),
                ("GET", "/health", "Health check"),
                ("GET", "/api/v1/info", "Service info")
            ]

            test_num = 1
            for method, endpoint, description in public_tests:
                print(f"\n[{test_num}] Testing {method} {endpoint} ({description})")
                response = await client.request(method, f"{COMMUNICATION_SERVICE_URL}{endpoint}")

                if response.status_code == 200:
                    print(f"✅ {description} accessible without token")
                    test_results.append((f"{method} {endpoint}", "PASS"))
                else:
                    print(f"❌ {description} failed: {response.status_code}")
                    test_results.append((f"{method} {endpoint}", "FAIL"))
                test_num += 1

            # Test protected endpoints (should fail without auth)
            protected_tests = [
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/conversations/", "conversations list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/conversations/", "create conversation"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/messages/", "messages list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/messages/", "create message"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/quick-replies/", "quick replies list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/quick-replies/", "create quick reply"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/channels/", "channels list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/channels/", "create channel"),
                ("GET", "/api/v1/auth/test", "auth test endpoint")
            ]

            for method, endpoint, description in protected_tests:
                print(f"\n[{test_num}] Testing {method} {endpoint} ({description})")

                headers = {"Content-Type": "application/json"}
                data = {"test": "data"} if method == "POST" else None

                response = await client.request(
                    method,
                    f"{COMMUNICATION_SERVICE_URL}{endpoint}",
                    headers=headers,
                    json=data
                )

                if response.status_code == 401:
                    print(f"✅ {description.title()} correctly rejected request (status: 401)")
                    test_results.append((f"{method} {description}", "PASS"))
                else:
                    print(f"❌ {description.title()} should reject unauthenticated request: {response.status_code}")
                    test_results.append((f"{method} {description}", "FAIL"))
                test_num += 1

            return test_results

    async def test_authenticated_endpoints(self) -> List[tuple]:
        """Test all CRUD operations with authentication"""
        if not self.owner_token:
            print("\n⚠️  Skipping authenticated tests - no valid token available")
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: Communication Endpoints WITH Token")
            print("="*60)

            test_results = []
            headers = {
                "Authorization": f"Bearer {self.owner_token}",
                "Content-Type": "application/json"
            }

            # ========================================
            # Authentication Tests
            # ========================================
            print("\n========================================")
            print("Testing Authentication")
            print("========================================")

            # Test auth endpoint
            print("\n[1] Testing authentication endpoint")
            response = await client.get(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/auth/test",
                headers=headers
            )

            if response.status_code == 200:
                print("✅ Authentication verified successfully")
                test_results.append(("GET /auth/test", "PASS"))
            else:
                print(f"❌ Authentication test failed: {response.status_code}")
                test_results.append(("GET /auth/test", "FAIL"))

            # ========================================
            # Inbox Module Tests
            # ========================================
            print("\n========================================")
            print("Testing Inbox Module")
            print("========================================")

            # --- Conversations CRUD ---
            print("\n--- Conversations Module CRUD ---")

            # CREATE Conversation
            print("\n[1] CREATE Conversation")
            conversation_data = {
                "external_id": f"conv_{self.unique_id}_001",
                "channel": "whatsapp",
                "contact_name": "John Doe",
                "contact_identifier": "+1234567890",
                "first_message": "Hello, this is a test conversation",
                "status": "open",
                "priority": "normal",
                "contact_metadata": {"source": "test"},
                "platform_metadata": {"test": True}
            }

            response = await client.post(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/conversations/",
                headers=headers,
                json=conversation_data
            )

            if response.status_code == 201:
                conversation = response.json()
                self.created_conversation_id = conversation["id"]
                print(f"✅ Conversation created: {self.created_conversation_id}")
                test_results.append(("CREATE Conversation", "PASS"))
            else:
                print(f"❌ Failed to create conversation: {response.status_code}")
                test_results.append(("CREATE Conversation", "FAIL"))

            # READ Conversations (List)
            print("\n[2] READ Conversations (List)")
            response = await client.get(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/conversations/",
                headers=headers
            )

            if response.status_code == 200:
                conversations = response.json()
                print(f"✅ Retrieved {len(conversations)} conversations")
                test_results.append(("READ Conversations", "PASS"))
            else:
                print(f"❌ Failed to list conversations: {response.status_code}")
                test_results.append(("READ Conversations", "FAIL"))

            # READ Conversation (Single)
            if self.created_conversation_id:
                print("\n[3] READ Conversation (Single)")
                response = await client.get(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/conversations/{self.created_conversation_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    print("✅ Retrieved conversation details")
                    test_results.append(("READ Conversation details", "PASS"))
                else:
                    print(f"❌ Failed to get conversation: {response.status_code}")
                    test_results.append(("READ Conversation details", "FAIL"))

            # UPDATE Conversation
            if self.created_conversation_id:
                print("\n[4] UPDATE Conversation")
                update_data = {
                    "contact_name": "John Doe Updated",
                    "status": "open"
                }

                response = await client.put(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/conversations/{self.created_conversation_id}",
                    headers=headers,
                    json=update_data
                )

                if response.status_code == 200:
                    print("✅ Conversation updated")
                    test_results.append(("UPDATE Conversation", "PASS"))
                else:
                    print(f"❌ Failed to update conversation: {response.status_code}")
                    test_results.append(("UPDATE Conversation", "FAIL"))

            # --- Messages CRUD ---
            print("\n--- Messages Module CRUD ---")

            # CREATE Message
            if self.created_conversation_id:
                print("\n[1] CREATE Message")
                message_data = {
                    "conversation_id": self.created_conversation_id,
                    "content": "Hello, this is a test message",
                    "type": "text",
                    "direction": "in"
                }

                response = await client.post(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/messages/",
                    headers=headers,
                    json=message_data
                )

                if response.status_code == 201:
                    message = response.json()
                    self.created_message_id = message["id"]
                    print(f"✅ Message created: {self.created_message_id}")
                    test_results.append(("CREATE Message", "PASS"))
                else:
                    print(f"❌ Failed to create message: {response.status_code}")
                    test_results.append(("CREATE Message", "FAIL"))

            # READ Messages
            print("\n[2] READ Messages")
            response = await client.get(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/messages/",
                headers=headers
            )

            if response.status_code == 200:
                messages = response.json()
                print(f"✅ Retrieved {len(messages)} messages")
                test_results.append(("READ Messages", "PASS"))
            else:
                print(f"❌ Failed to list messages: {response.status_code}")
                test_results.append(("READ Messages", "FAIL"))

            # --- Quick Replies CRUD ---
            print("\n--- Quick Replies Module CRUD ---")

            # CREATE Quick Reply
            print("\n[1] CREATE Quick Reply")
            quick_reply_data = {
                "title": "Welcome Message",
                "content": "Welcome to our service! How can we help you today?",
                "category": "greetings",
                "language": "en",
                "shortcuts": ["hello", "hi", "welcome"]
            }

            response = await client.post(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/quick-replies/",
                headers=headers,
                json=quick_reply_data
            )

            if response.status_code == 201:
                quick_reply = response.json()
                self.created_quick_reply_id = quick_reply["id"]
                print(f"✅ Quick Reply created: {self.created_quick_reply_id}")
                test_results.append(("CREATE Quick Reply", "PASS"))
            else:
                print(f"❌ Failed to create quick reply: {response.status_code}")
                test_results.append(("CREATE Quick Reply", "FAIL"))

            # READ Quick Replies
            print("\n[2] READ Quick Replies")
            response = await client.get(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/quick-replies/",
                headers=headers
            )

            if response.status_code == 200:
                quick_replies = response.json()
                print(f"✅ Retrieved {len(quick_replies)} quick replies")
                test_results.append(("READ Quick Replies", "PASS"))
            else:
                print(f"❌ Failed to list quick replies: {response.status_code}")
                test_results.append(("READ Quick Replies", "FAIL"))

            # UPDATE Quick Reply
            if self.created_quick_reply_id:
                print("\n[3] UPDATE Quick Reply")
                update_data = {
                    "content": "Updated welcome message!"
                }

                response = await client.put(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/quick-replies/{self.created_quick_reply_id}",
                    headers=headers,
                    json=update_data
                )

                if response.status_code == 200:
                    print("✅ Quick Reply updated")
                    test_results.append(("UPDATE Quick Reply", "PASS"))
                else:
                    print(f"❌ Failed to update quick reply: {response.status_code}")
                    test_results.append(("UPDATE Quick Reply", "FAIL"))

            # DELETE Quick Reply
            if self.created_quick_reply_id:
                print("\n[4] DELETE Quick Reply")
                response = await client.delete(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/quick-replies/{self.created_quick_reply_id}",
                    headers=headers
                )

                if response.status_code in [204, 200]:
                    print("✅ Quick Reply deleted")
                    test_results.append(("DELETE Quick Reply", "PASS"))
                else:
                    print(f"❌ Failed to delete quick reply: {response.status_code}")
                    test_results.append(("DELETE Quick Reply", "FAIL"))

            # ========================================
            # Chat Module Tests
            # ========================================
            print("\n========================================")
            print("Testing Chat Module")
            print("========================================")

            # --- Channels CRUD ---
            print("\n--- Channels Module CRUD ---")

            # CREATE Channel
            print("\n[1] CREATE Channel")
            channel_data = {
                "name": "General Chat",
                "slug": f"general-{self.unique_id}",
                "description": "General discussion channel",
                "channel_type": "public",
                "metadata": {"test": True}
            }

            response = await client.post(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/channels/",
                headers=headers,
                json=channel_data
            )

            if response.status_code == 201:
                channel = response.json()
                self.created_channel_id = channel["id"]
                print(f"✅ Channel created: {self.created_channel_id}")
                test_results.append(("CREATE Channel", "PASS"))
            else:
                print(f"❌ Failed to create channel: {response.status_code}")
                test_results.append(("CREATE Channel", "FAIL"))

            # READ Channels
            print("\n[2] READ Channels")
            response = await client.get(
                f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/channels/",
                headers=headers
            )

            if response.status_code == 200:
                channels = response.json()
                print(f"✅ Retrieved {len(channels)} channels")
                test_results.append(("READ Channels", "PASS"))
            else:
                print(f"❌ Failed to list channels: {response.status_code}")
                test_results.append(("READ Channels", "FAIL"))

            # READ Channel (Single)
            if self.created_channel_id:
                print("\n[3] READ Channel (Single)")
                response = await client.get(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/channels/{self.created_channel_id}",
                    headers=headers
                )

                if response.status_code == 200:
                    print("✅ Retrieved channel details")
                    test_results.append(("READ Channel details", "PASS"))
                else:
                    print(f"❌ Failed to get channel: {response.status_code}")
                    test_results.append(("READ Channel details", "FAIL"))

            # UPDATE Channel
            if self.created_channel_id:
                print("\n[4] UPDATE Channel")
                update_data = {
                    "description": "Updated general discussion channel"
                }

                response = await client.put(
                    f"{COMMUNICATION_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/channels/{self.created_channel_id}",
                    headers=headers,
                    json=update_data
                )

                if response.status_code == 200:
                    print("✅ Channel updated")
                    test_results.append(("UPDATE Channel", "PASS"))
                else:
                    print(f"❌ Failed to update channel: {response.status_code}")
                    test_results.append(("UPDATE Channel", "FAIL"))

            return test_results

    async def test_cross_tenant_access(self) -> List[tuple]:
        """Test that users cannot access other tenants' data"""
        if not self.owner_token:
            print("\n⚠️  Skipping cross-tenant tests - no valid token available")
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: Cross-Tenant Access Prevention")
            print("="*60)

            test_results = []
            headers = {
                "Authorization": f"Bearer {self.owner_token}",
                "Content-Type": "application/json"
            }

            # Test accessing different tenant's data
            wrong_tenant = "non-existent-tenant-xyz"

            cross_tenant_tests = [
                ("conversations access", f"/api/v1/tenants/{wrong_tenant}/conversations/"),
                ("messages access", f"/api/v1/tenants/{wrong_tenant}/messages/"),
                ("quick replies access", f"/api/v1/tenants/{wrong_tenant}/quick-replies/"),
                ("channels access", f"/api/v1/tenants/{wrong_tenant}/channels/"),
                ("auth test access", f"/api/v1/tenants/{wrong_tenant}/auth/test")
            ]

            test_num = 1
            for description, endpoint in cross_tenant_tests:
                print(f"\n[{test_num}] Testing {description} to wrong tenant")

                response = await client.get(
                    f"{COMMUNICATION_SERVICE_URL}{endpoint}",
                    headers=headers
                )

                if response.status_code == 403:
                    print(f"✅ Correctly denied {description} to wrong tenant (status: 403)")
                    test_results.append((f"Cross-tenant {description}", "PASS"))
                else:
                    print(f"❌ Should deny {description} to wrong tenant: {response.status_code}")
                    test_results.append((f"Cross-tenant {description}", "FAIL"))
                test_num += 1

            return test_results

    async def run_all_tests(self):
        """Run all security tests for Communication Service"""
        print("\n" + "="*80)
        print("COMMUNICATION SERVICE SECURITY TESTS - COMPREHENSIVE CRUD")
        print("="*80)
        print(f"Started at: {datetime.now().isoformat()}")

        all_results = []

        try:
            # Setup
            print("\n[PHASE 1] Setting up test tenant...")
            setup_result = await self.setup_tenant()
            if not setup_result.get("success"):
                print("❌ Setup failed, aborting tests")
                return

            print("\n[PHASE 2] Authenticating as tenant owner...")
            auth_success = await self.authenticate_owner()
            if not auth_success:
                print("❌ Authentication failed, aborting authenticated tests")

            # Test endpoints without auth
            print("\n[PHASE 3] Testing endpoints without authentication...")
            results1 = await self.test_endpoints_without_token()
            all_results.extend(results1)

            # Test authenticated endpoints
            if auth_success:
                print("\n[PHASE 4] Testing CRUD operations with authentication...")
                results2 = await self.test_authenticated_endpoints()
                all_results.extend(results2)

                # Test cross-tenant access
                print("\n[PHASE 5] Testing cross-tenant access prevention...")
                results3 = await self.test_cross_tenant_access()
                all_results.extend(results3)

            # Summary
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)

            passed = sum(1 for _, status in all_results if status == "PASS")
            failed = sum(1 for _, status in all_results if status == "FAIL")
            skipped = sum(1 for _, status in all_results if status == "SKIP")
            total = len(all_results)

            print(f"\nTotal Tests: {total}")
            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"⚠️  Skipped: {skipped}")

            # Group results by module
            module_results = {}
            for test_name, status in all_results:
                if "Conversation" in test_name:
                    module = "Conversations"
                elif "Message" in test_name:
                    module = "Messages"
                elif "Quick Reply" in test_name:
                    module = "Quick Replies"
                elif "Channel" in test_name:
                    module = "Channels"
                elif "Cross-tenant" in test_name:
                    module = "Cross-tenant"
                elif any(x in test_name for x in ["GET /", "GET /health", "GET /api/v1/info"]):
                    module = "Public Endpoints"
                elif "auth" in test_name.lower():
                    module = "Authentication"
                else:
                    module = "Other"

                if module not in module_results:
                    module_results[module] = {"passed": 0, "failed": 0}

                if status == "PASS":
                    module_results[module]["passed"] += 1
                elif status == "FAIL":
                    module_results[module]["failed"] += 1

            if module_results:
                print(f"\nModule Results:")
                for module, results in module_results.items():
                    print(f"  {module}:")
                    print(f"    ✅ Passed: {results['passed']}")
                    print(f"    ❌ Failed: {results['failed']}")

            print("\nDetailed Test Results:")
            for test_name, status in all_results:
                symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                print(f"  {symbol} {test_name}: {status}")

            print("\n" + "="*80)
            if failed == 0:
                print("🎉 ALL SECURITY TESTS PASSED! 🎉")
            else:
                print(f"⚠️  {failed} tests failed - review security configuration")
            print("="*80)

            return all_results

        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return all_results


# Main execution
if __name__ == "__main__":
    tester = TestCommunicationSecurity()
    asyncio.run(tester.run_all_tests())
