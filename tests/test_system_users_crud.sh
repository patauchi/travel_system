#!/bin/bash

# ============================================
# COMPREHENSIVE CRUD Tests for System Service - Users Module
# With Tenant Creation and Schema Verification
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
AUTH_SERVICE_URL="http://localhost:8001"
TENANT_SERVICE_URL="http://localhost:8002"
SYSTEM_SERVICE_URL="http://localhost:8008"

# Test data
TIMESTAMP=$(date +%s)
TEST_TENANT_SLUG="testenant${TIMESTAMP}"
TEST_TENANT_NAME="Test Tenant ${TIMESTAMP}"
TEST_USERNAME="testuser_${TIMESTAMP}"
TEST_EMAIL="testuser_${TIMESTAMP}@example.com"
TEST_PASSWORD="TestPass123!"

# Variables to store IDs and tokens
SUPER_ADMIN_TOKEN=""
TENANT_ID=""
TENANT_ADMIN_TOKEN=""
USER_ID=""
ROLE_ID=""
TEAM_ID=""

# Helper function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Helper function to print section headers
print_section() {
    local title=$1
    echo ""
    print_status "$CYAN" "╔══════════════════════════════════════════════════════════════╗"
    printf "${CYAN}║${NC} %-60s ${CYAN}║${NC}\n" "$title"
    print_status "$CYAN" "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

# Helper function to execute curl and display result
execute_curl() {
    local description=$1
    local curl_command=$2
    local expect_success=${3:-true}

    print_status "$BLUE" "▶ $description"
    echo "  Command: $curl_command" | sed 's/Bearer [^ ]*/Bearer ***/g'

    # Execute and capture response
    response=$(eval "$curl_command" 2>/dev/null)
    exit_code=$?

    # Check if we got a response
    if [ -z "$response" ]; then
        print_status "$RED" "  ✗ No response received"
        echo ""
        return 1
    fi

    # Try to parse as JSON
    if echo "$response" | jq '.' >/dev/null 2>&1; then
        # It's valid JSON
        if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
            # There's an error detail
            error_detail=$(echo "$response" | jq -r '.detail')
            if [ "$expect_success" = true ]; then
                print_status "$RED" "  ✗ Error: $error_detail"
                echo "$response" | jq '.' 2>&1 | head -20
                echo ""
                return 1
            else
                print_status "$GREEN" "  ✓ Expected error: $error_detail"
                echo ""
                return 0
            fi
        else
            # Success response
            if [ "$expect_success" = true ]; then
                print_status "$GREEN" "  ✓ Success"
                echo "$response" | jq '.' 2>&1 | head -20
            else
                print_status "$YELLOW" "  ⚠ Unexpected success"
                echo "$response" | jq '.' 2>&1 | head -20
            fi
        fi
    else
        # Not JSON, show raw response
        print_status "$YELLOW" "  ⚠ Non-JSON response:"
        echo "$response" | head -20
    fi

    # Return only the JSON response for variable assignment
    echo ""
}

# Helper function to execute curl and get only JSON response
execute_curl_json() {
    local description=$1
    local curl_command=$2
    local expect_success=${3:-true}

    print_status "$BLUE" "▶ $description"
    echo "  Command: $curl_command" | sed 's/Bearer [^ ]*/Bearer ***/g'

    # Execute and capture response
    response=$(eval "$curl_command" 2>/dev/null)
    exit_code=$?

    # Check if we got a response
    if [ -z "$response" ]; then
        print_status "$RED" "  ✗ No response received"
        return 1
    fi

    # Try to parse as JSON
    if echo "$response" | jq '.' >/dev/null 2>&1; then
        # It's valid JSON
        if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
            # There's an error detail
            error_detail=$(echo "$response" | jq -r '.detail')
            if [ "$expect_success" = true ]; then
                print_status "$RED" "  ✗ Error: $error_detail"
                echo "$response" | jq '.' 2>&1 | head -20
                return 1
            else
                print_status "$GREEN" "  ✓ Expected error: $error_detail"
            fi
        else
            # Success response
            if [ "$expect_success" = true ]; then
                print_status "$GREEN" "  ✓ Success"
                echo "$response" | jq '.' 2>&1 | head -20
            else
                print_status "$YELLOW" "  ⚠ Unexpected success"
                echo "$response" | jq '.' 2>&1 | head -20
            fi
        fi
    else
        # Not JSON, show raw response
        print_status "$YELLOW" "  ⚠ Non-JSON response:"
        echo "$response" | head -20
    fi

    # Return only the raw JSON
    echo "$response"
}

# Helper function to wait for service
wait_for_service() {
    local service_name=$1
    local service_url=$2
    local max_attempts=30
    local attempt=0

    print_status "$YELLOW" "Waiting for $service_name to be ready..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s "${service_url}/health" >/dev/null 2>&1; then
            print_status "$GREEN" "✓ $service_name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    print_status "$RED" "✗ $service_name failed to respond after $max_attempts attempts"
    return 1
}

# ============================================
# MAIN TEST EXECUTION
# ============================================

clear
print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║          COMPREHENSIVE SYSTEM SERVICE CRUD TEST              ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
echo ""
print_status "$YELLOW" "Test Configuration:"
print_status "$BLUE" "  • Tenant: ${TEST_TENANT_SLUG}"
print_status "$BLUE" "  • User: ${TEST_USERNAME}"
print_status "$BLUE" "  • Timestamp: ${TIMESTAMP}"
echo ""

# ============================================
# STEP 1: VERIFY SERVICES ARE RUNNING
# ============================================

print_section "STEP 1: VERIFY SERVICES"

wait_for_service "Auth Service" "$AUTH_SERVICE_URL"
wait_for_service "Tenant Service" "$TENANT_SERVICE_URL"
wait_for_service "System Service" "$SYSTEM_SERVICE_URL"

# ============================================
# STEP 2: AUTHENTICATE AS SUPER ADMIN
# ============================================

print_section "STEP 2: AUTHENTICATE AS SUPER ADMIN"

ADMIN_AUTH_RESPONSE=$(execute_curl_json "Login as super admin" \
    "curl -s -X POST '${AUTH_SERVICE_URL}/api/v1/auth/login' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=admin&password=Admin123!'")

if echo "$ADMIN_AUTH_RESPONSE" | grep -q "access_token"; then
    SUPER_ADMIN_TOKEN=$(echo "$ADMIN_AUTH_RESPONSE" | jq -r '.access_token')
    print_status "$GREEN" "✓ Super admin authentication successful"
else
    print_status "$RED" "✗ Failed to authenticate as super admin"
    exit 1
fi

# ============================================
# STEP 3: CREATE TEST TENANT
# ============================================

print_section "STEP 3: CREATE TEST TENANT"

CREATE_TENANT_RESPONSE=$(execute_curl_json "Create test tenant" \
    "curl -s -X POST '${TENANT_SERVICE_URL}/api/v1/tenants' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${SUPER_ADMIN_TOKEN}' \
    -d '{
        \"slug\": \"${TEST_TENANT_SLUG}\",
        \"name\": \"${TEST_TENANT_NAME}\",
        \"email\": \"admin@${TEST_TENANT_SLUG}.com\",
        \"owner_email\": \"admin@${TEST_TENANT_SLUG}.com\",
        \"owner_username\": \"admin_${TEST_TENANT_SLUG}\",
        \"owner_password\": \"Admin${TIMESTAMP}!\",
        \"settings\": {
            \"max_users\": 100,
            \"max_storage_gb\": 10,
            \"features\": [\"users\", \"roles\", \"teams\"]
        }
    }'")

if echo "$CREATE_TENANT_RESPONSE" | grep -q "\"id\""; then
    TENANT_ID=$(echo "$CREATE_TENANT_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Tenant created successfully with ID: $TENANT_ID"
else
    print_status "$RED" "✗ Failed to create tenant"
    exit 1
fi

# ============================================
# STEP 4: WAIT FOR SCHEMA CREATION
# ============================================

print_section "STEP 4: VERIFY SCHEMA CREATION"

print_status "$YELLOW" "Waiting for schema creation to complete..."
sleep 5

# Check if tenant is active
CHECK_TENANT_RESPONSE=$(execute_curl "Verify tenant status" \
    "curl -s -X GET '${TENANT_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}' \
    -H 'Authorization: Bearer ${SUPER_ADMIN_TOKEN}'")

if echo "$CHECK_TENANT_RESPONSE" | jq -e '.is_active == true' >/dev/null 2>&1; then
    print_status "$GREEN" "✓ Tenant is active"
else
    print_status "$RED" "✗ Tenant is not active"
    echo "$CHECK_TENANT_RESPONSE" | jq '.'
fi

# ============================================
# STEP 5: CREATE TENANT ADMIN USER
# ============================================

print_section "STEP 5: CREATE TENANT ADMIN"

TENANT_ADMIN_USERNAME="admin_${TEST_TENANT_SLUG}"
TENANT_ADMIN_PASSWORD="Admin${TIMESTAMP}!"

# Skip creating admin user since it's created with the tenant
print_status "$YELLOW" "Tenant admin user was created with the tenant"
TENANT_ADMIN_ID=""

# Admin user is created automatically with the tenant

# ============================================
# STEP 6: LOGIN AS TENANT ADMIN
# ============================================

print_section "STEP 6: AUTHENTICATE AS TENANT ADMIN"

# First try to login with the tenant context
TENANT_LOGIN_RESPONSE=$(execute_curl_json "Login as tenant admin" \
    "curl -s -X POST '${AUTH_SERVICE_URL}/api/v1/auth/login' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -H 'X-Tenant-Slug: ${TEST_TENANT_SLUG}' \
    -d 'username=${TENANT_ADMIN_USERNAME}&password=${TENANT_ADMIN_PASSWORD}'")

if echo "$TENANT_LOGIN_RESPONSE" | grep -q "access_token"; then
    TENANT_ADMIN_TOKEN=$(echo "$TENANT_LOGIN_RESPONSE" | jq -r '.access_token')
    print_status "$GREEN" "✓ Tenant admin authentication successful"
else
    print_status "$YELLOW" "⚠ Using super admin token for tenant operations"
    TENANT_ADMIN_TOKEN=$SUPER_ADMIN_TOKEN
fi

# ============================================
# STEP 7: USER CRUD OPERATIONS
# ============================================

print_section "STEP 7: USER CRUD OPERATIONS"

# 7.1 CREATE USER
print_status "$MAGENTA" "\n7.1 CREATE Operations"

CREATE_USER_RESPONSE=$(execute_curl_json "Create a new user" \
    "curl -s -X POST '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
    -d '{
        \"email\": \"${TEST_EMAIL}\",
        \"username\": \"${TEST_USERNAME}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\",
        \"phone\": \"+1234567890\",
        \"title\": \"Test Engineer\",
        \"department\": \"Engineering\",
        \"timezone\": \"UTC\",
        \"language\": \"en\",
        \"currency\": \"USD\"
    }'")

if echo "$CREATE_USER_RESPONSE" | grep -q "\"id\""; then
    USER_ID=$(echo "$CREATE_USER_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ User created with ID: $USER_ID"
fi

# 7.2 READ USER
print_status "$MAGENTA" "\n7.2 READ Operations"

# List all users
execute_curl "List all users in tenant" \
    "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users?limit=10' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"

# Get specific user
if [ ! -z "$USER_ID" ]; then
    execute_curl "Get user by ID" \
        "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users/${USER_ID}' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"
fi

# 7.3 UPDATE USER
print_status "$MAGENTA" "\n7.3 UPDATE Operations"

if [ ! -z "$USER_ID" ]; then
    UPDATE_USER_RESPONSE=$(execute_curl "Update user information" \
        "curl -s -X PATCH '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users/${USER_ID}' \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
        -d '{
            \"first_name\": \"Updated\",
            \"last_name\": \"User\",
            \"title\": \"Senior Test Engineer\",
            \"department\": \"Quality Assurance\",
            \"bio\": \"This is an updated bio for the test user\",
            \"phone_secondary\": \"+9876543210\"
        }'")
fi

# 7.4 DELETE USER
print_status "$MAGENTA" "\n7.4 DELETE Operations"

if [ ! -z "$USER_ID" ]; then
    execute_curl "Delete user" \
        "curl -s -X DELETE '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users/${USER_ID}' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"
fi

# ============================================
# STEP 8: ROLE CRUD OPERATIONS
# ============================================

print_section "STEP 8: ROLE CRUD OPERATIONS"

# 8.1 CREATE ROLE
CREATE_ROLE_RESPONSE=$(execute_curl_json "Create a new role" \
    "curl -s -X POST '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/roles' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
    -d '{
        \"name\": \"test_role_${TIMESTAMP}\",
        \"display_name\": \"Test Role ${TIMESTAMP}\",
        \"description\": \"A test role for CRUD operations\",
        \"is_active\": true,
        \"priority\": 10
    }'")

if echo "$CREATE_ROLE_RESPONSE" | grep -q "\"id\""; then
    ROLE_ID=$(echo "$CREATE_ROLE_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Role created with ID: $ROLE_ID"
fi

# 8.2 READ ROLES
execute_curl "List all roles" \
    "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/roles' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"

# 8.3 UPDATE ROLE
if [ ! -z "$ROLE_ID" ]; then
    execute_curl "Update role" \
        "curl -s -X PATCH '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/roles/${ROLE_ID}' \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
        -d '{
            \"display_name\": \"Updated Test Role\",
            \"description\": \"This role has been updated\"
        }'"
fi

# 8.4 DELETE ROLE
if [ ! -z "$ROLE_ID" ]; then
    execute_curl "Delete role" \
        "curl -s -X DELETE '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/roles/${ROLE_ID}' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"
fi

# ============================================
# STEP 9: TEAM CRUD OPERATIONS
# ============================================

print_section "STEP 9: TEAM CRUD OPERATIONS"

# 9.1 CREATE TEAM
CREATE_TEAM_RESPONSE=$(execute_curl_json "Create a new team" \
    "curl -s -X POST '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/teams' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
    -d '{
        \"name\": \"test_team_${TIMESTAMP}\",
        \"display_name\": \"Test Team ${TIMESTAMP}\",
        \"description\": \"A test team for CRUD operations\",
        \"code\": \"TT${TIMESTAMP:0:4}\",
        \"is_active\": true
    }'")

if echo "$CREATE_TEAM_RESPONSE" | grep -q "\"id\""; then
    TEAM_ID=$(echo "$CREATE_TEAM_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Team created with ID: $TEAM_ID"
fi

# 9.2 READ TEAMS
execute_curl "List all teams" \
    "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/teams' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"

# 9.3 UPDATE TEAM
if [ ! -z "$TEAM_ID" ]; then
    execute_curl "Update team" \
        "curl -s -X PATCH '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/teams/${TEAM_ID}' \
        -H 'Content-Type: application/json' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
        -d '{
            \"display_name\": \"Updated Test Team\",
            \"description\": \"This team has been updated\"
        }'"
fi

# 9.4 DELETE TEAM
if [ ! -z "$TEAM_ID" ]; then
    execute_curl "Delete team" \
        "curl -s -X DELETE '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/teams/${TEAM_ID}' \
        -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'"
fi

# ============================================
# STEP 10: ERROR HANDLING TESTS
# ============================================

print_section "STEP 10: ERROR HANDLING TESTS"

# Test invalid email format
execute_curl "Create user with invalid email (expect error)" \
    "curl -s -X POST '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
    -d '{
        \"email\": \"invalid-email\",
        \"username\": \"test\",
        \"password\": \"weak\"
    }'" false

# Test weak password
execute_curl "Create user with weak password (expect error)" \
    "curl -s -X POST '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}' \
    -d '{
        \"email\": \"test@example.com\",
        \"username\": \"testuser\",
        \"password\": \"weak\"
    }'" false

# Test accessing non-existent resource
execute_curl "Get non-existent user (expect error)" \
    "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users/00000000-0000-0000-0000-000000000000' \
    -H 'Authorization: Bearer ${TENANT_ADMIN_TOKEN}'" false

# Test unauthorized access
execute_curl "Access without token (expect error)" \
    "curl -s -X GET '${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users'" false

# ============================================
# STEP 11: CLEANUP
# ============================================

print_section "STEP 11: CLEANUP"

# Delete the test tenant
if [ ! -z "$TENANT_ID" ]; then
    DELETE_TENANT_RESPONSE=$(execute_curl_json "Delete test tenant" \
        "curl -s -X DELETE '${TENANT_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}' \
        -H 'Authorization: Bearer ${SUPER_ADMIN_TOKEN}'")

    if echo "$DELETE_TENANT_RESPONSE" | grep -q "error"; then
        print_status "$YELLOW" "⚠ Could not delete tenant (may require manual cleanup)"
    else
        print_status "$GREEN" "✓ Test tenant deleted successfully"
    fi
fi

# ============================================
# TEST SUMMARY
# ============================================

print_section "TEST SUMMARY"

print_status "$GREEN" "Test Execution Completed!"
echo ""
print_status "$BLUE" "Test Details:"
print_status "$CYAN" "  • Tenant Slug: ${TEST_TENANT_SLUG}"
print_status "$CYAN" "  • Tenant ID: ${TENANT_ID}"
print_status "$CYAN" "  • Test User: ${TEST_USERNAME}"
print_status "$CYAN" "  • Test Duration: $(($(date +%s) - TIMESTAMP)) seconds"
echo ""

print_status "$YELLOW" "Notes:"
print_status "$YELLOW" "  • Check the output above for any unexpected errors"
print_status "$YELLOW" "  • Verify that all CRUD operations completed successfully"
print_status "$YELLOW" "  • The test tenant should have been deleted in cleanup"
echo ""

print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║                    TEST COMPLETED                            ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
