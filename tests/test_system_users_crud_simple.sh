#!/bin/bash

# ============================================
# Simple CRUD Tests for System Service - Users Module
# Using existing demo tenant
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
SYSTEM_SERVICE_URL="http://localhost:8008"
TENANT_SLUG="test_20250813_180552"  # Using existing demo tenant

# Test data
TIMESTAMP=$(date +%s)
TEST_USERNAME="testuser_${TIMESTAMP}"
TEST_EMAIL="testuser_${TIMESTAMP}@example.com"
TEST_PASSWORD="TestPass123!"

# Variables to store IDs and tokens
ACCESS_TOKEN=""
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
    print_status "$CYAN" "════════════════════════════════════════════════════════════════"
    print_status "$CYAN" "$title"
    print_status "$CYAN" "════════════════════════════════════════════════════════════════"
    echo ""
}

# Helper function for simple curl execution
do_curl() {
    local method=$1
    local url=$2
    local data=$3
    local description=$4

    print_status "$BLUE" "▶ $description"

    if [ -z "$data" ]; then
        response=$(curl -s -X "$method" "$url" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json")
    else
        response=$(curl -s -X "$method" "$url" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    if echo "$response" | jq '.' >/dev/null 2>&1; then
        if echo "$response" | jq -e '.detail' >/dev/null 2>&1; then
            error_detail=$(echo "$response" | jq -r '.detail')
            print_status "$RED" "  ✗ Error: $error_detail"
        else
            print_status "$GREEN" "  ✓ Success"
        fi
        echo "$response" | jq '.' | head -20
    else
        print_status "$YELLOW" "  ⚠ Response: $response"
    fi
    echo ""

    echo "$response"
}

# ============================================
# MAIN TEST EXECUTION
# ============================================

clear
print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║         SYSTEM SERVICE USERS MODULE - CRUD TEST              ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
echo ""
print_status "$YELLOW" "Configuration:"
print_status "$BLUE" "  • Tenant: ${TENANT_SLUG}"
print_status "$BLUE" "  • Test User: ${TEST_USERNAME}"
print_status "$BLUE" "  • Test Email: ${TEST_EMAIL}"
echo ""

# ============================================
# STEP 1: AUTHENTICATE
# ============================================

print_section "STEP 1: AUTHENTICATE"

print_status "$YELLOW" "Authenticating as super admin..."
AUTH_RESPONSE=$(curl -s -X POST "${AUTH_SERVICE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=Admin123!")

if echo "$AUTH_RESPONSE" | jq -e '.access_token' >/dev/null 2>&1; then
    ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
    print_status "$GREEN" "✓ Authentication successful"
    print_status "$BLUE" "  Token: ${ACCESS_TOKEN:0:50}..."
else
    print_status "$RED" "✗ Authentication failed"
    echo "$AUTH_RESPONSE" | jq '.'
    exit 1
fi

# ============================================
# STEP 2: CREATE USER
# ============================================

print_section "STEP 2: CREATE USER"

USER_DATA='{
    "email": "'${TEST_EMAIL}'",
    "username": "'${TEST_USERNAME}'",
    "password": "'${TEST_PASSWORD}'",
    "first_name": "Test",
    "last_name": "User",
    "phone": "+1234567890",
    "title": "QA Engineer",
    "department": "Engineering",
    "timezone": "UTC",
    "language": "en",
    "currency": "USD"
}'

CREATE_RESPONSE=$(do_curl "POST" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users" \
    "$USER_DATA" \
    "Create new user")

if echo "$CREATE_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    USER_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ User created with ID: $USER_ID"
fi

# ============================================
# STEP 3: READ USERS
# ============================================

print_section "STEP 3: READ USERS"

# List all users
do_curl "GET" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users?limit=5" \
    "" \
    "List users"

# Get specific user
if [ ! -z "$USER_ID" ]; then
    do_curl "GET" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users/${USER_ID}" \
        "" \
        "Get user by ID"
fi

# ============================================
# STEP 4: UPDATE USER
# ============================================

print_section "STEP 4: UPDATE USER"

if [ ! -z "$USER_ID" ]; then
    UPDATE_DATA='{
        "first_name": "Updated",
        "last_name": "TestUser",
        "title": "Senior QA Engineer",
        "department": "Quality Assurance",
        "bio": "Updated bio for test user",
        "phone_secondary": "+9876543210"
    }'

    do_curl "PATCH" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users/${USER_ID}" \
        "$UPDATE_DATA" \
        "Update user information"
fi

# ============================================
# STEP 5: CREATE ROLE
# ============================================

print_section "STEP 5: CREATE ROLE"

ROLE_DATA='{
    "name": "test_role_'${TIMESTAMP}'",
    "display_name": "Test Role '${TIMESTAMP}'",
    "description": "Test role for CRUD operations",
    "is_active": true,
    "priority": 10
}'

CREATE_ROLE_RESPONSE=$(do_curl "POST" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/roles" \
    "$ROLE_DATA" \
    "Create new role")

if echo "$CREATE_ROLE_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    ROLE_ID=$(echo "$CREATE_ROLE_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Role created with ID: $ROLE_ID"
fi

# ============================================
# STEP 6: READ ROLES
# ============================================

print_section "STEP 6: READ ROLES"

do_curl "GET" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/roles" \
    "" \
    "List all roles"

if [ ! -z "$ROLE_ID" ]; then
    do_curl "GET" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/roles/${ROLE_ID}" \
        "" \
        "Get role by ID"
fi

# ============================================
# STEP 7: CREATE TEAM
# ============================================

print_section "STEP 7: CREATE TEAM"

TEAM_DATA='{
    "name": "test_team_'${TIMESTAMP}'",
    "display_name": "Test Team '${TIMESTAMP}'",
    "description": "Test team for CRUD operations",
    "code": "TT'${TIMESTAMP:0:4}'",
    "is_active": true
}'

CREATE_TEAM_RESPONSE=$(do_curl "POST" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/teams" \
    "$TEAM_DATA" \
    "Create new team")

if echo "$CREATE_TEAM_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    TEAM_ID=$(echo "$CREATE_TEAM_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Team created with ID: $TEAM_ID"
fi

# ============================================
# STEP 8: READ TEAMS
# ============================================

print_section "STEP 8: READ TEAMS"

do_curl "GET" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/teams" \
    "" \
    "List all teams"

if [ ! -z "$TEAM_ID" ]; then
    do_curl "GET" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/teams/${TEAM_ID}" \
        "" \
        "Get team by ID"
fi

# ============================================
# STEP 9: PERMISSIONS
# ============================================

print_section "STEP 9: PERMISSIONS"

do_curl "GET" \
    "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/permissions" \
    "" \
    "List all permissions"

# ============================================
# STEP 10: USER LOGIN TEST
# ============================================

print_section "STEP 10: USER LOGIN TEST"

if [ ! -z "$TEST_USERNAME" ]; then
    print_status "$YELLOW" "Testing login with created user..."
    LOGIN_RESPONSE=$(curl -s -X POST "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users/login" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "'${TEST_USERNAME}'",
            "password": "'${TEST_PASSWORD}'",
            "remember_me": false
        }')

    if echo "$LOGIN_RESPONSE" | jq -e '.access_token' >/dev/null 2>&1; then
        print_status "$GREEN" "✓ User login successful"
        echo "$LOGIN_RESPONSE" | jq '{access_token: .access_token[:50] + "...", user: .user.username}'
    else
        print_status "$YELLOW" "⚠ User login failed (this might be expected)"
        echo "$LOGIN_RESPONSE" | jq '.' | head -10
    fi
fi

# ============================================
# STEP 11: ERROR HANDLING TESTS
# ============================================

print_section "STEP 11: ERROR HANDLING TESTS"

# Test invalid email
print_status "$YELLOW" "Testing invalid email (expect error)..."
INVALID_USER_DATA='{
    "email": "invalid-email",
    "username": "test",
    "password": "weak"
}'

ERROR_RESPONSE=$(curl -s -X POST "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$INVALID_USER_DATA")

if echo "$ERROR_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    print_status "$GREEN" "✓ Expected error for invalid data"
    echo "$ERROR_RESPONSE" | jq '.detail' | head -10
else
    print_status "$YELLOW" "⚠ Unexpected response"
fi

# Test non-existent user
print_status "$YELLOW" "Testing non-existent user (expect error)..."
ERROR_RESPONSE=$(curl -s -X GET "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users/00000000-0000-0000-0000-000000000000" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ERROR_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
    print_status "$GREEN" "✓ Expected error for non-existent user"
    echo "$ERROR_RESPONSE" | jq '.detail'
else
    print_status "$YELLOW" "⚠ Unexpected response"
fi

# ============================================
# STEP 12: CLEANUP
# ============================================

print_section "STEP 12: CLEANUP"

# Delete team
if [ ! -z "$TEAM_ID" ]; then
    do_curl "DELETE" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/teams/${TEAM_ID}" \
        "" \
        "Delete team"
fi

# Delete role
if [ ! -z "$ROLE_ID" ]; then
    do_curl "DELETE" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/roles/${ROLE_ID}" \
        "" \
        "Delete role"
fi

# Delete user
if [ ! -z "$USER_ID" ]; then
    do_curl "DELETE" \
        "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TENANT_SLUG}/users/${USER_ID}" \
        "" \
        "Delete user"
fi

# ============================================
# SUMMARY
# ============================================

print_section "TEST SUMMARY"

print_status "$GREEN" "Test Execution Completed!"
echo ""
print_status "$BLUE" "Test Details:"
print_status "$CYAN" "  • Tenant Used: ${TENANT_SLUG}"
print_status "$CYAN" "  • Test User: ${TEST_USERNAME}"
print_status "$CYAN" "  • Test Email: ${TEST_EMAIL}"
print_status "$CYAN" "  • User ID: ${USER_ID:-Not created}"
print_status "$CYAN" "  • Role ID: ${ROLE_ID:-Not created}"
print_status "$CYAN" "  • Team ID: ${TEAM_ID:-Not created}"
echo ""

print_status "$YELLOW" "Notes:"
print_status "$YELLOW" "  • Check the output above for any unexpected errors"
print_status "$YELLOW" "  • All test resources should have been cleaned up"
echo ""

print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║                    TEST COMPLETED                            ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
