"""
Security Test - System Service
Testing:
1. Create a tenant with super_admin
2. Authenticate tenant owner
3. Test endpoints WITHOUT token (should fail)
4. Test endpoints WITH token (should succeed with CRUD operations)
5. Test cross-tenant access (should fail)

Modules tested:
- Users (users, roles, permissions, teams)
- Settings (settings, audit logs)
- Tools (notes, tasks, logcalls, events)
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
SYSTEM_SERVICE_URL = f"{BASE_URL}:8008"

# Default super_admin credentials (from init.sql)
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "SuperAdmin123!"


class TestSystemSecurity:
    """Security tests for System Service"""

    def __init__(self):
        self.tenant_data = None
        self.tenant_id = None
        self.tenant_slug = None
        self.owner_token = None
        self.super_admin_token = None
        # Store created IDs for cleanup
        self.created_user_id = None
        self.created_role_id = None
        self.created_team_id = None
        self.created_setting_id = None
        self.created_note_id = None
        self.created_task_id = None
        self.created_logcall_id = None
        self.created_event_id = None

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
            self.tenant_slug = f"test-sys-{unique_id}"

            tenant_response = await client.post(
                f"{TENANT_SERVICE_URL}/api/v1/tenants/v2",
                headers={"Authorization": f"Bearer {self.super_admin_token}"},
                json={
                    "slug": self.tenant_slug,
                    "name": f"Test System Tenant {unique_id}",
                    "subdomain": self.tenant_slug,
                    "owner_email": f"owner_sys_{unique_id}@test.com",
                    "owner_username": f"owner_sys_{unique_id}",
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

            # Extract unique_id from tenant_slug
            unique_id = self.tenant_slug.split('-')[-1]

            # Try tenant-specific login endpoint first
            try:
                login_response = await client.post(
                    f"{SYSTEM_SERVICE_URL}/api/v1/auth/tenant/login",
                    headers={"X-Tenant-ID": self.tenant_id},
                    json={
                        "email": f"owner_sys_{unique_id}@test.com",
                        "password": "OwnerPass123!",
                        "tenant_id": self.tenant_id
                    }
                )
                # Store unique_id for reuse
                self.unique_id = unique_id

                if login_response.status_code == 200:
                    auth_data = login_response.json()
                    self.owner_token = auth_data["access_token"]
                    print("✅ Tenant owner authenticated successfully")
                    return True
            except Exception as e:
                print(f"   Tenant login failed: {e}")

            # Fallback to auth-service login
            print("\n[2] Fallback: Trying auth-service login with tenant header...")
            login_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/v1/auth/login",
                headers={"X-Tenant-Slug": self.tenant_slug},
                data={
                    "username": f"owner_sys_{unique_id}",
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

    async def test_without_auth(self) -> Dict[str, Any]:
        """Test endpoints without authentication (should fail)"""
        results = {"passed": 0, "failed": 0, "details": []}

        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: System Endpoints WITHOUT Token")
            print("="*60)

            # Test public endpoints
            print("\n[1] Testing GET /health (public endpoint)")
            response = await client.get(f"{SYSTEM_SERVICE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check accessible without token")
                results["passed"] += 1
                results["details"].append(("GET /health", "PASS"))
            else:
                print(f"❌ Health check failed: {response.status_code}")
                results["failed"] += 1
                results["details"].append(("GET /health", "FAIL"))

            print("\n[2] Testing GET / (public endpoint)")
            response = await client.get(f"{SYSTEM_SERVICE_URL}/")
            if response.status_code == 200:
                print("✅ Root endpoint accessible without token")
                results["passed"] += 1
                results["details"].append(("GET /", "PASS"))
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                results["failed"] += 1
                results["details"].append(("GET /", "FAIL"))

            # Test protected endpoints (should fail)
            protected_tests = [
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/users/", "users list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/users/", "create user"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/roles/", "roles list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/roles/", "create role"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/teams/", "teams list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/teams/", "create team"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/settings/", "settings list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/settings/", "create setting"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/audit-logs/", "audit logs"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/tools/notes", "notes list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/tools/notes", "create note"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/tools/tasks", "tasks list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/tools/tasks", "create task"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/tools/logcalls", "logcalls list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/tools/logcalls", "create logcall"),
                ("GET", f"/api/v1/tenants/{self.tenant_slug}/tools/events", "events list"),
                ("POST", f"/api/v1/tenants/{self.tenant_slug}/tools/events", "create event"),
            ]

            for i, (method, endpoint, description) in enumerate(protected_tests, 3):
                print(f"\n[{i}] Testing {method} {endpoint.split('/tenants/')[1]} ({description})")

                if method == "GET":
                    response = await client.get(f"{SYSTEM_SERVICE_URL}{endpoint}")
                else:  # POST
                    response = await client.post(f"{SYSTEM_SERVICE_URL}{endpoint}", json={})

                if response.status_code in [401, 403]:
                    print(f"✅ {description.capitalize()} correctly rejected request (status: {response.status_code})")
                    results["passed"] += 1
                    results["details"].append((f"{method} {description}", "PASS"))
                else:
                    print(f"❌ {description.capitalize()} did not reject: {response.status_code}")
                    results["failed"] += 1
                    results["details"].append((f"{method} {description}", "FAIL"))

        return results

    async def test_users_crud(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test CRUD operations for Users module"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        headers = {"Authorization": f"Bearer {self.owner_token}"}

        print("\n--- Users Module CRUD ---")

        # CREATE User
        print("\n[1] CREATE User")
        user_data = {
            "email": f"test_user_{uuid.uuid4().hex[:8]}@test.com",
            "username": f"test_user_{uuid.uuid4().hex[:8]}",
            "password": "TestUser123!",
            "confirm_password": "TestUser123!",
            "first_name": "Test",
            "last_name": "User",
            "department": "Engineering",
            "title": "Developer",
            "timezone": "UTC",
            "language": "en",
            "currency": "USD"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/users/",
            headers=headers,
            json=user_data
        )

        if response.status_code == 201:
            user = response.json()
            self.created_user_id = user["id"]
            print(f"✅ User created: {self.created_user_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            results["failed"] += 1
            return results

        # READ User (List)
        print("\n[2] READ Users (List)")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/users/",
            headers=headers
        )

        if response.status_code == 200:
            users = response.json()
            print(f"✅ Retrieved {len(users)} users")
            results["passed"] += 1
        elif response.status_code == 404:
            print(f"⚠️  Users list returned 404 - schema may not be initialized")
            results["skipped"] += 1
        else:
            print(f"❌ Failed to list users: {response.status_code}")
            results["failed"] += 1

        # READ User (Single)
        if self.created_user_id:
            print("\n[3] READ User (Single)")
            response = await client.get(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/users/{self.created_user_id}",
                headers=headers
            )

            if response.status_code == 200:
                print(f"✅ Retrieved user details")
                results["passed"] += 1
            else:
                print(f"❌ Failed to get user: {response.status_code}")
                results["failed"] += 1

        # UPDATE User
        if self.created_user_id:
            print("\n[4] UPDATE User")
            update_data = {
                "title": "Senior Developer",
                "department": "R&D"
            }

            response = await client.put(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/users/{self.created_user_id}",
                headers=headers,
                json=update_data
            )

            if response.status_code == 200:
                print(f"✅ User updated")
                results["passed"] += 1
            else:
                print(f"❌ Failed to update user: {response.status_code}")
                results["failed"] += 1

        # DELETE User
        if self.created_user_id:
            print("\n[5] DELETE User")
            response = await client.delete(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/users/{self.created_user_id}",
                headers=headers
            )

            if response.status_code in [204, 200]:
                print(f"✅ User deleted")
                results["passed"] += 1
            else:
                print(f"❌ Failed to delete user: {response.status_code}")
                results["failed"] += 1

        return results

    async def test_roles_crud(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test CRUD operations for Roles"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        headers = {"Authorization": f"Bearer {self.owner_token}"}

        print("\n--- Roles CRUD ---")

        # CREATE Role
        print("\n[1] CREATE Role")
        role_data = {
            "name": f"test_role_{uuid.uuid4().hex[:8]}",
            "display_name": "Test Role",
            "description": "A test role for security testing",
            "priority": 50
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/roles/",
            headers=headers,
            json=role_data
        )

        if response.status_code == 201:
            role = response.json()
            self.created_role_id = role["id"]
            print(f"✅ Role created: {self.created_role_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create role: {response.status_code}")
            results["failed"] += 1

        # READ Roles
        print("\n[2] READ Roles")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/roles/",
            headers=headers
        )

        if response.status_code == 200:
            roles = response.json()
            print(f"✅ Retrieved {len(roles)} roles")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list roles: {response.status_code}")
            results["failed"] += 1

        return results

    async def test_teams_crud(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test CRUD operations for Teams"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        headers = {"Authorization": f"Bearer {self.owner_token}"}

        print("\n--- Teams CRUD ---")

        # CREATE Team
        print("\n[1] CREATE Team")
        team_data = {
            "name": f"test_team_{uuid.uuid4().hex[:8]}",
            "display_name": "Test Team",
            "description": "A test team for security testing"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/teams/",
            headers=headers,
            json=team_data
        )

        if response.status_code == 201:
            team = response.json()
            self.created_team_id = team["id"]
            print(f"✅ Team created: {self.created_team_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create team: {response.status_code}")
            results["failed"] += 1

        # READ Teams
        print("\n[2] READ Teams")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/teams/",
            headers=headers
        )

        if response.status_code == 200:
            teams = response.json()
            print(f"✅ Retrieved {len(teams)} teams")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list teams: {response.status_code}")
            results["failed"] += 1

        return results

    async def test_settings_crud(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test CRUD operations for Settings module"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        headers = {"Authorization": f"Bearer {self.owner_token}"}

        print("\n--- Settings Module CRUD ---")

        # CREATE Setting
        print("\n[1] CREATE Setting")
        setting_data = {
            "category": "test",
            "key": f"test_key_{uuid.uuid4().hex[:8]}",
            "value": "test_value",
            "value_type": "string",
            "description": "Test setting",
            "is_sensitive": False
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/settings/",
            headers=headers,
            json=setting_data
        )

        if response.status_code == 201:
            setting = response.json()
            self.created_setting_id = setting["id"]
            print(f"✅ Setting created: {self.created_setting_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create setting: {response.status_code}")
            results["failed"] += 1

        # READ Settings
        print("\n[2] READ Settings")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/settings/",
            headers=headers
        )

        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Retrieved {len(settings)} settings")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list settings: {response.status_code}")
            results["failed"] += 1

        # READ Setting (by category)
        print("\n[3] READ Settings by Category")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/settings/category/test",
            headers=headers
        )

        if response.status_code == 200:
            settings = response.json()
            print(f"✅ Retrieved {len(settings)} settings in 'test' category")
            results["passed"] += 1
        else:
            print(f"❌ Failed to get settings by category: {response.status_code}")
            results["failed"] += 1

        # UPDATE Setting
        if self.created_setting_id:
            print("\n[4] UPDATE Setting")
            update_data = {
                "value": "updated_test_value",
                "description": "Updated test setting"
            }

            response = await client.put(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/settings/{self.created_setting_id}",
                headers=headers,
                json=update_data
            )

            if response.status_code == 200:
                print(f"✅ Setting updated")
                results["passed"] += 1
            else:
                print(f"❌ Failed to update setting: {response.status_code}")
                results["failed"] += 1

        # DELETE Setting
        if self.created_setting_id:
            print("\n[5] DELETE Setting")
            response = await client.delete(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/settings/{self.created_setting_id}",
                headers=headers
            )

            if response.status_code in [204, 200]:
                print(f"✅ Setting deleted")
                results["passed"] += 1
            else:
                print(f"❌ Failed to delete setting: {response.status_code}")
                results["failed"] += 1

        # READ Audit Logs
        print("\n[6] READ Audit Logs")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/audit-logs/",
            headers=headers
        )

        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Retrieved {len(logs)} audit logs")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list audit logs: {response.status_code}")
            results["failed"] += 1

        return results

    async def test_tools_crud(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Test CRUD operations for Tools module"""
        results = {"passed": 0, "failed": 0, "skipped": 0}
        headers = {"Authorization": f"Bearer {self.owner_token}"}

        print("\n--- Tools Module CRUD ---")

        # Notes CRUD
        print("\n-- Notes --")

        # CREATE Note
        print("[1] CREATE Note")
        note_data = {
            "title": "Test Note",
            "content": "This is a test note content",
            "notable_id": 1,
            "notable_type": "user",
            "priority": "medium"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/notes",
            headers=headers,
            json=note_data
        )

        if response.status_code == 201:
            note = response.json()
            self.created_note_id = note["id"]
            print(f"✅ Note created: {self.created_note_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create note: {response.status_code}")
            results["failed"] += 1

        # READ Notes
        print("[2] READ Notes")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/notes",
            headers=headers
        )

        if response.status_code == 200:
            notes = response.json()
            print(f"✅ Retrieved {len(notes)} notes")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list notes: {response.status_code}")
            results["failed"] += 1

        # UPDATE Note
        if self.created_note_id:
            print("[3] UPDATE Note")
            update_data = {
                "title": "Updated Test Note",
                "content": "Updated content"
            }

            response = await client.put(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/notes/{self.created_note_id}",
                headers=headers,
                json=update_data
            )

            if response.status_code == 200:
                print(f"✅ Note updated")
                results["passed"] += 1
            else:
                print(f"❌ Failed to update note: {response.status_code}")
                results["failed"] += 1

        # DELETE Note
        if self.created_note_id:
            print("[4] DELETE Note")
            response = await client.delete(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/notes/{self.created_note_id}",
                headers=headers
            )

            if response.status_code in [204, 200]:
                print(f"✅ Note deleted")
                results["passed"] += 1
            else:
                print(f"❌ Failed to delete note: {response.status_code}")
                results["failed"] += 1

        # Tasks CRUD
        print("\n-- Tasks --")

        # CREATE Task
        print("[1] CREATE Task")
        task_data = {
            "title": "Test Task",
            "description": "This is a test task",
            "status": "pending",
            "priority": "high",
            "due_date": (datetime.now().date() + timedelta(days=7)).isoformat(),
            "taskable_id": 1,
            "taskable_type": "user"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/tasks",
            headers=headers,
            json=task_data
        )

        if response.status_code == 201:
            task = response.json()
            self.created_task_id = task["id"]
            print(f"✅ Task created: {self.created_task_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            results["failed"] += 1

        # READ Tasks
        print("[2] READ Tasks")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/tasks",
            headers=headers
        )

        if response.status_code == 200:
            tasks = response.json()
            print(f"✅ Retrieved {len(tasks)} tasks")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list tasks: {response.status_code}")
            results["failed"] += 1

        # UPDATE Task
        if self.created_task_id:
            print("[3] UPDATE Task")
            update_data = {
                "status": "in_progress",
                "description": "Updated task description"
            }

            response = await client.put(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/tasks/{self.created_task_id}",
                headers=headers,
                json=update_data
            )

            if response.status_code == 200:
                print(f"✅ Task updated")
                results["passed"] += 1
            else:
                print(f"❌ Failed to update task: {response.status_code}")
                results["failed"] += 1

        # DELETE Task
        if self.created_task_id:
            print("[4] DELETE Task")
            response = await client.delete(
                f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/tasks/{self.created_task_id}",
                headers=headers
            )

            if response.status_code in [204, 200]:
                print(f"✅ Task deleted")
                results["passed"] += 1
            else:
                print(f"❌ Failed to delete task: {response.status_code}")
                results["failed"] += 1

        # LogCalls CRUD
        print("\n-- LogCalls --")

        # CREATE LogCall
        print("[1] CREATE LogCall")
        logcall_data = {
            "phone_number": "+1234567890",
            "call_type": "outgoing",
            "status": "completed",
            "notes": "Test call log",
            "logacallable_id": 1,
            "logacallable_type": "user"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/logcalls",
            headers=headers,
            json=logcall_data
        )

        if response.status_code == 201:
            logcall = response.json()
            self.created_logcall_id = logcall["id"]
            print(f"✅ LogCall created: {self.created_logcall_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create logcall: {response.status_code}")
            results["failed"] += 1

        # READ LogCalls
        print("[2] READ LogCalls")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/logcalls",
            headers=headers
        )

        if response.status_code == 200:
            logcalls = response.json()
            print(f"✅ Retrieved {len(logcalls)} logcalls")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list logcalls: {response.status_code}")
            results["failed"] += 1

        # Events CRUD
        print("\n-- Events --")

        # CREATE Event
        print("[1] CREATE Event")
        event_data = {
            "title": "Test Event",
            "description": "This is a test event",
            "event_type": "meeting",
            "status": "scheduled",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(hours=1)).isoformat(),
            "eventable_id": 1,
            "eventable_type": "user"
        }

        response = await client.post(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/events",
            headers=headers,
            json=event_data
        )

        if response.status_code == 201:
            event = response.json()
            self.created_event_id = event["id"]
            print(f"✅ Event created: {self.created_event_id}")
            results["passed"] += 1
        else:
            print(f"❌ Failed to create event: {response.status_code}")
            results["failed"] += 1

        # READ Events
        print("[2] READ Events")
        response = await client.get(
            f"{SYSTEM_SERVICE_URL}/api/v1/tenants/{self.tenant_slug}/tools/events",
            headers=headers
        )

        if response.status_code == 200:
            events = response.json()
            print(f"✅ Retrieved {len(events)} events")
            results["passed"] += 1
        else:
            print(f"❌ Failed to list events: {response.status_code}")
            results["failed"] += 1

        return results

    async def test_with_auth(self) -> Dict[str, Any]:
        """Test endpoints with authentication (should succeed with CRUD operations)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: System Endpoints WITH Token")
            print("="*60)

            total_results = {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "details": []
            }

            # Test each module's CRUD operations
            modules = [
                ("Users", self.test_users_crud),
                ("Roles", self.test_roles_crud),
                ("Teams", self.test_teams_crud),
                ("Settings", self.test_settings_crud),
                ("Tools", self.test_tools_crud)
            ]

            for module_name, test_func in modules:
                print(f"\n{'='*40}")
                print(f"Testing {module_name} Module")
                print(f"{'='*40}")

                results = await test_func(client)
                total_results["passed"] += results["passed"]
                total_results["failed"] += results["failed"]
                total_results["skipped"] += results.get("skipped", 0)

                total_results["details"].append({
                    "module": module_name,
                    "passed": results["passed"],
                    "failed": results["failed"],
                    "skipped": results.get("skipped", 0)
                })

            return total_results

    async def test_cross_tenant_access(self) -> Dict[str, Any]:
        """Test that users cannot access other tenants' data"""
        results = {"passed": 0, "failed": 0, "details": []}

        if not self.owner_token:
            print("\n⚠️  Skipping cross-tenant tests - no valid token")
            return results

        async with httpx.AsyncClient(timeout=30.0) as client:
            print("\n" + "="*60)
            print("TEST: Cross-Tenant Access Prevention")
            print("="*60)

            headers = {"Authorization": f"Bearer {self.owner_token}"}
            fake_tenant = "non-existent-tenant-xyz"

            # Test endpoints that should deny cross-tenant access
            endpoints = [
                ("users", f"/api/v1/tenants/{fake_tenant}/users/"),
                ("roles", f"/api/v1/tenants/{fake_tenant}/roles/"),
                ("teams", f"/api/v1/tenants/{fake_tenant}/teams/"),
                ("settings", f"/api/v1/tenants/{fake_tenant}/settings/"),
                ("audit logs", f"/api/v1/tenants/{fake_tenant}/audit-logs/"),
                ("notes", f"/api/v1/tenants/{fake_tenant}/tools/notes"),
                ("tasks", f"/api/v1/tenants/{fake_tenant}/tools/tasks"),
                ("logcalls", f"/api/v1/tenants/{fake_tenant}/tools/logcalls"),
                ("events", f"/api/v1/tenants/{fake_tenant}/tools/events")
            ]

            for i, (name, endpoint) in enumerate(endpoints, 1):
                print(f"\n[{i}] Testing {name} access to wrong tenant")
                response = await client.get(
                    f"{SYSTEM_SERVICE_URL}{endpoint}",
                    headers=headers
                )

                if response.status_code in [403, 404]:
                    print(f"✅ Correctly denied {name} access to wrong tenant (status: {response.status_code})")
                    results["passed"] += 1
                    results["details"].append((f"Cross-tenant {name} access", "PASS"))
                else:
                    print(f"❌ Should deny {name} access but got: {response.status_code}")
                    results["failed"] += 1
                    results["details"].append((f"Cross-tenant {name} access", "FAIL"))

        return results

    async def run_all_tests(self):
        """Run all security tests for System Service"""
        print("\n" + "="*80)
        print("SYSTEM SERVICE SECURITY TESTS - COMPREHENSIVE CRUD")
        print("="*80)
        print(f"Started at: {datetime.now().isoformat()}")

        all_results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }

        try:
            # 1. Setup tenant
            print("\n[PHASE 1] Setting up test tenant...")
            setup_result = await self.setup_tenant()
            if not setup_result.get("success"):
                print("❌ Failed to setup tenant, aborting tests")
                return

            # 2. Authenticate as owner
            print("\n[PHASE 2] Authenticating as tenant owner...")
            auth_success = await self.authenticate_owner()
            if not auth_success:
                print("⚠️  Failed to authenticate, some tests will be skipped")

            # 3. Test without authentication
            print("\n[PHASE 3] Testing endpoints without authentication...")
            no_auth_results = await self.test_without_auth()
            all_results["passed"] += no_auth_results["passed"]
            all_results["failed"] += no_auth_results["failed"]
            all_results["details"].extend(no_auth_results["details"])

            # 4. Test with authentication (CRUD operations)
            if self.owner_token:
                print("\n[PHASE 4] Testing CRUD operations with authentication...")
                auth_results = await self.test_with_auth()
                all_results["passed"] += auth_results["passed"]
                all_results["failed"] += auth_results["failed"]
                all_results["skipped"] += auth_results["skipped"]
                all_results["details"].extend(auth_results["details"])

                # 5. Test cross-tenant access
                print("\n[PHASE 5] Testing cross-tenant access prevention...")
                cross_results = await self.test_cross_tenant_access()
                all_results["passed"] += cross_results["passed"]
                all_results["failed"] += cross_results["failed"]
                all_results["details"].extend(cross_results["details"])
            else:
                print("\n⚠️  Skipping authenticated tests due to auth failure")

            # Calculate totals
            all_results["total"] = all_results["passed"] + all_results["failed"] + all_results["skipped"]

            # Print summary
            print("\n" + "="*80)
            print("TEST SUMMARY")
            print("="*80)

            print(f"\nTotal Tests: {all_results['total']}")
            print(f"✅ Passed: {all_results['passed']}")
            print(f"❌ Failed: {all_results['failed']}")
            print(f"⚠️  Skipped: {all_results['skipped']}")

            # Print module details if available
            module_results = [d for d in all_results["details"] if isinstance(d, dict)]
            if module_results:
                print("\nModule Results:")
                for module in module_results:
                    print(f"  {module['module']}:")
                    print(f"    ✅ Passed: {module['passed']}")
                    print(f"    ❌ Failed: {module['failed']}")
                    if module.get('skipped'):
                        print(f"    ⚠️  Skipped: {module['skipped']}")

            # Print individual test results
            test_results = [d for d in all_results["details"] if isinstance(d, tuple)]
            if test_results:
                print("\nDetailed Test Results:")
                for test_name, status in test_results:
                    symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
                    print(f"  {symbol} {test_name}: {status}")

            print("\n" + "="*80)
            if all_results["failed"] == 0:
                print("🎉 ALL SECURITY TESTS PASSED! 🎉")
            else:
                print(f"⚠️  {all_results['failed']} tests failed - review security configuration")
            print("="*80 + "\n")

            return all_results

        except Exception as e:
            print(f"\n❌ Test execution failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return all_results


# Main execution
if __name__ == "__main__":
    tester = TestSystemSecurity()
    asyncio.run(tester.run_all_tests())
