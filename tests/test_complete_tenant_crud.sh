#!/bin/bash

# ============================================
# Complete Tenant Creation and CRUD Test
# Tests tenant creation with all service schemas and tables
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
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="multitenant_db"
DB_USER="postgres"
DB_PASSWORD="postgres123"

# Test data
TIMESTAMP=$(date +%s)
RANDOM_SUFFIX=$(date +%N | cut -c1-6)  # Use nanoseconds for uniqueness
TEST_TENANT_SLUG="crud${TIMESTAMP}${RANDOM_SUFFIX}"
TEST_TENANT_NAME="CRUD Test ${TIMESTAMP}"
TENANT_ADMIN_EMAIL="admin@${TEST_TENANT_SLUG}.com"
TENANT_ADMIN_USERNAME="admin_${TEST_TENANT_SLUG}"
TENANT_ADMIN_PASSWORD="Admin${TIMESTAMP}!"

TEST_USERNAME="testuser_${TIMESTAMP}"
TEST_EMAIL="testuser_${TIMESTAMP}@example.com"
TEST_PASSWORD="TestPass123!"

# Variables to store IDs and tokens
SUPER_ADMIN_TOKEN=""
TENANT_ID=""
TENANT_SCHEMA=""
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

# Helper function to execute database queries
db_query() {
    local query=$1
    docker exec multitenant-postgres psql -U "$DB_USER" -d "$DB_NAME" -t -c "$query" 2>/dev/null
}

# Helper function to check if schema exists
check_schema() {
    local schema=$1
    result=$(db_query "SELECT schema_name FROM information_schema.schemata WHERE schema_name = '$schema';")
    if [ ! -z "$result" ]; then
        return 0
    else
        return 1
    fi
}

# Helper function to list tables in schema
list_schema_tables() {
    local schema=$1
    db_query "SELECT tablename FROM pg_tables WHERE schemaname = '$schema' ORDER BY tablename;" | grep -v '^$'
}

# Helper function to count tables in schema
count_schema_tables() {
    local schema=$1
    db_query "SELECT COUNT(*) FROM pg_tables WHERE schemaname = '$schema';" | tr -d ' '
}

# ============================================
# MAIN TEST EXECUTION
# ============================================

clear
print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║        COMPLETE TENANT CREATION AND CRUD TEST                ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
echo ""
print_status "$YELLOW" "Test Configuration:"
print_status "$BLUE" "  • New Tenant: ${TEST_TENANT_SLUG}"
print_status "$BLUE" "  • Admin User: ${TENANT_ADMIN_USERNAME}"
print_status "$BLUE" "  • Test User: ${TEST_USERNAME}"
print_status "$BLUE" "  • Timestamp: ${TIMESTAMP}"
echo ""

# ============================================
# STEP 1: VERIFY DATABASE CONNECTION
# ============================================

print_section "STEP 1: VERIFY DATABASE CONNECTION"

print_status "$YELLOW" "Testing database connection..."
if db_query "SELECT 1;" > /dev/null; then
    print_status "$GREEN" "✓ Database connection successful"
else
    print_status "$RED" "✗ Cannot connect to database"
    exit 1
fi

# List existing schemas
print_status "$YELLOW" "Existing tenant schemas:"
db_query "SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%' ORDER BY schema_name;" | while read schema; do
    if [ ! -z "$schema" ]; then
        table_count=$(count_schema_tables "$schema")
        print_status "$BLUE" "  • $schema (${table_count} tables)"
    fi
done

# ============================================
# STEP 2: AUTHENTICATE AS SUPER ADMIN
# ============================================

print_section "STEP 2: AUTHENTICATE AS SUPER ADMIN"

print_status "$YELLOW" "Authenticating as super admin..."
AUTH_RESPONSE=$(curl -s -X POST "${AUTH_SERVICE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=Admin123!")

if echo "$AUTH_RESPONSE" | jq -e '.access_token' >/dev/null 2>&1; then
    SUPER_ADMIN_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.access_token')
    print_status "$GREEN" "✓ Authentication successful"
    print_status "$BLUE" "  Token: ${SUPER_ADMIN_TOKEN:0:50}..."
else
    print_status "$RED" "✗ Authentication failed"
    echo "$AUTH_RESPONSE" | jq '.'
    exit 1
fi

# ============================================
# STEP 3: CREATE NEW TENANT
# ============================================

print_section "STEP 3: CREATE NEW TENANT"

print_status "$YELLOW" "Creating new tenant: ${TEST_TENANT_SLUG}"
print_status "$BLUE" "  • Slug: ${TEST_TENANT_SLUG}"
print_status "$BLUE" "  • Admin: ${TENANT_ADMIN_USERNAME}"

CREATE_TENANT_RESPONSE=$(curl -s -X POST "${TENANT_SERVICE_URL}/api/v1/tenants" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
    -d "{
        \"slug\": \"${TEST_TENANT_SLUG}\",
        \"name\": \"${TEST_TENANT_NAME}\",
        \"email\": \"${TENANT_ADMIN_EMAIL}\",
        \"owner_email\": \"${TENANT_ADMIN_EMAIL}\",
        \"owner_username\": \"${TENANT_ADMIN_USERNAME}\",
        \"owner_password\": \"${TENANT_ADMIN_PASSWORD}\",
        \"settings\": {
            \"max_users\": 100,
            \"max_storage_gb\": 10,
            \"features\": [\"users\", \"roles\", \"teams\", \"crm\", \"bookings\", \"communications\", \"financial\"]
        }
    }")

if echo "$CREATE_TENANT_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    TENANT_ID=$(echo "$CREATE_TENANT_RESPONSE" | jq -r '.id')
    TENANT_SCHEMA="tenant_${TEST_TENANT_SLUG}"
    print_status "$GREEN" "✓ Tenant created successfully"
    print_status "$BLUE" "  • Tenant ID: ${TENANT_ID}"
    print_status "$BLUE" "  • Schema: ${TENANT_SCHEMA}"
    echo "$CREATE_TENANT_RESPONSE" | jq '{id, slug, name, status, subscription_plan}'
else
    print_status "$RED" "✗ Failed to create tenant"
    echo "$CREATE_TENANT_RESPONSE" | jq '.'
    exit 1
fi

# ============================================
# STEP 4: WAIT FOR SCHEMA CREATION
# ============================================

print_section "STEP 4: VERIFY SCHEMA CREATION"

print_status "$YELLOW" "Waiting for schema creation to complete..."
sleep 5

# Check if schema was created
if check_schema "$TENANT_SCHEMA"; then
    print_status "$GREEN" "✓ Schema ${TENANT_SCHEMA} created successfully"
else
    print_status "$RED" "✗ Schema ${TENANT_SCHEMA} was not created"
    exit 1
fi

# ============================================
# STEP 5: VERIFY ALL TABLES CREATED
# ============================================

print_section "STEP 5: VERIFY ALL SERVICE TABLES"

print_status "$YELLOW" "Checking tables in schema ${TENANT_SCHEMA}..."

# Expected tables for each service
declare -A SERVICE_TABLES
SERVICE_TABLES["System Service"]="users roles permissions teams user_roles user_teams role_permissions team_members user_sessions audit_logs api_keys"
SERVICE_TABLES["CRM Service"]="leads contacts companies opportunities activities notes tasks calls emails attachments tags lead_tags contact_tags company_tags"
SERVICE_TABLES["Booking Service"]="bookings booking_items passengers payments booking_status_history booking_documents"
SERVICE_TABLES["Communication Service"]="channels conversations messages message_attachments notifications email_templates sms_templates"
SERVICE_TABLES["Financial Service"]="accounts transactions invoices invoice_items payments receipts currencies exchange_rates"

# Get actual tables
ACTUAL_TABLES=$(list_schema_tables "$TENANT_SCHEMA")
TOTAL_TABLES=$(count_schema_tables "$TENANT_SCHEMA")

print_status "$BLUE" "Total tables created: ${TOTAL_TABLES}"
echo ""

# Display tables grouped by service (approximate)
print_status "$CYAN" "Tables created in ${TENANT_SCHEMA}:"
echo "$ACTUAL_TABLES" | while read table; do
    if [ ! -z "$table" ]; then
        print_status "$BLUE" "  • $table"
    fi
done

# Check for critical tables
CRITICAL_TABLES="users roles permissions teams"
MISSING_TABLES=""

for table in $CRITICAL_TABLES; do
    if ! echo "$ACTUAL_TABLES" | grep -q "^${table}$"; then
        MISSING_TABLES="${MISSING_TABLES} ${table}"
    fi
done

if [ -z "$MISSING_TABLES" ]; then
    print_status "$GREEN" "✓ All critical tables are present"
else
    print_status "$YELLOW" "⚠ Missing critical tables:${MISSING_TABLES}"
fi

# ============================================
# STEP 6: TEST SYSTEM SERVICE CRUD
# ============================================

print_section "STEP 6: TEST USER CRUD IN NEW TENANT"

# 6.1 Create User
print_status "$YELLOW" "Creating user in new tenant..."
CREATE_USER_RESPONSE=$(curl -s -X POST "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
    -d "{
        \"email\": \"${TEST_EMAIL}\",
        \"username\": \"${TEST_USERNAME}\",
        \"password\": \"${TEST_PASSWORD}\",
        \"first_name\": \"Test\",
        \"last_name\": \"User\",
        \"phone\": \"+1234567890\",
        \"title\": \"Test Engineer\",
        \"department\": \"Engineering\"
    }")

if echo "$CREATE_USER_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    USER_ID=$(echo "$CREATE_USER_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ User created with ID: ${USER_ID}"
else
    print_status "$YELLOW" "⚠ Could not create user"
    echo "$CREATE_USER_RESPONSE" | jq '.' | head -10
fi

# 6.2 List Users
print_status "$YELLOW" "Listing users in tenant..."
LIST_USERS_RESPONSE=$(curl -s -X GET "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/users" \
    -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}")

if echo "$LIST_USERS_RESPONSE" | jq -e '.[0]' >/dev/null 2>&1; then
    user_count=$(echo "$LIST_USERS_RESPONSE" | jq '. | length')
    print_status "$GREEN" "✓ Found ${user_count} users in tenant"
    echo "$LIST_USERS_RESPONSE" | jq '.[] | {id, username, email}' | head -20
else
    print_status "$YELLOW" "⚠ No users found or error listing users"
fi

# 6.3 Create Role
print_status "$YELLOW" "Creating role in new tenant..."
CREATE_ROLE_RESPONSE=$(curl -s -X POST "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/roles" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
    -d "{
        \"name\": \"test_role_${TIMESTAMP}\",
        \"display_name\": \"Test Role\",
        \"description\": \"Test role for CRUD operations\",
        \"is_active\": true
    }")

if echo "$CREATE_ROLE_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    ROLE_ID=$(echo "$CREATE_ROLE_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Role created with ID: ${ROLE_ID}"
else
    print_status "$YELLOW" "⚠ Could not create role"
    echo "$CREATE_ROLE_RESPONSE" | jq '.' | head -10
fi

# 6.4 Create Team
print_status "$YELLOW" "Creating team in new tenant..."
CREATE_TEAM_RESPONSE=$(curl -s -X POST "${SYSTEM_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}/teams" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}" \
    -d "{
        \"name\": \"test_team_${TIMESTAMP}\",
        \"display_name\": \"Test Team\",
        \"description\": \"Test team for CRUD operations\",
        \"is_active\": true
    }")

if echo "$CREATE_TEAM_RESPONSE" | jq -e '.id' >/dev/null 2>&1; then
    TEAM_ID=$(echo "$CREATE_TEAM_RESPONSE" | jq -r '.id')
    print_status "$GREEN" "✓ Team created with ID: ${TEAM_ID}"
else
    print_status "$YELLOW" "⚠ Could not create team"
    echo "$CREATE_TEAM_RESPONSE" | jq '.' | head -10
fi

# ============================================
# STEP 7: VERIFY DATA IN DATABASE
# ============================================

print_section "STEP 7: VERIFY DATA IN DATABASE"

# Check users table
print_status "$YELLOW" "Checking users in database..."
USER_COUNT=$(db_query "SELECT COUNT(*) FROM ${TENANT_SCHEMA}.users;" | tr -d ' ')
print_status "$BLUE" "  • Users in database: ${USER_COUNT}"

# Check roles table
ROLE_COUNT=$(db_query "SELECT COUNT(*) FROM ${TENANT_SCHEMA}.roles;" | tr -d ' ')
print_status "$BLUE" "  • Roles in database: ${ROLE_COUNT}"

# Check teams table
TEAM_COUNT=$(db_query "SELECT COUNT(*) FROM ${TENANT_SCHEMA}.teams;" | tr -d ' ')
print_status "$BLUE" "  • Teams in database: ${TEAM_COUNT}"

# Show sample data
print_status "$YELLOW" "Sample users from database:"
db_query "SELECT id, username, email FROM ${TENANT_SCHEMA}.users LIMIT 3;" | while read line; do
    if [ ! -z "$line" ]; then
        print_status "$BLUE" "  $line"
    fi
done

# ============================================
# STEP 8: TEST TENANT LOGIN
# ============================================

print_section "STEP 8: TEST TENANT ADMIN LOGIN"

print_status "$YELLOW" "Testing login with tenant admin credentials..."
TENANT_LOGIN_RESPONSE=$(curl -s -X POST "${AUTH_SERVICE_URL}/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "X-Tenant-Slug: ${TEST_TENANT_SLUG}" \
    -d "username=${TENANT_ADMIN_USERNAME}&password=${TENANT_ADMIN_PASSWORD}")

if echo "$TENANT_LOGIN_RESPONSE" | jq -e '.access_token' >/dev/null 2>&1; then
    print_status "$GREEN" "✓ Tenant admin login successful"
    echo "$TENANT_LOGIN_RESPONSE" | jq '{user: .user.username, tenant: .tenant, role: .user.role}'
else
    print_status "$YELLOW" "⚠ Tenant admin login failed"
    echo "$TENANT_LOGIN_RESPONSE" | jq '.' | head -10
fi

# ============================================
# STEP 9: CLEANUP (OPTIONAL)
# ============================================

print_section "STEP 9: CLEANUP"

print_status "$YELLOW" "Do you want to delete the test tenant? (y/n)"
read -r DELETE_CHOICE

if [ "$DELETE_CHOICE" = "y" ] || [ "$DELETE_CHOICE" = "Y" ]; then
    print_status "$YELLOW" "Deleting test tenant..."

    DELETE_RESPONSE=$(curl -s -X DELETE "${TENANT_SERVICE_URL}/api/v1/tenants/${TEST_TENANT_SLUG}" \
        -H "Authorization: Bearer ${SUPER_ADMIN_TOKEN}")

    if [ -z "$DELETE_RESPONSE" ] || echo "$DELETE_RESPONSE" | jq -e '.detail' >/dev/null 2>&1; then
        print_status "$YELLOW" "⚠ Tenant deletion response:"
        echo "$DELETE_RESPONSE" | jq '.' 2>/dev/null || echo "Empty response (might be successful)"
    fi

    # Verify schema deletion
    sleep 2
    if check_schema "$TENANT_SCHEMA"; then
        print_status "$YELLOW" "⚠ Schema still exists, may need manual cleanup"
    else
        print_status "$GREEN" "✓ Schema deleted successfully"
    fi
else
    print_status "$BLUE" "Keeping test tenant for further inspection"
    print_status "$BLUE" "  • Tenant: ${TEST_TENANT_SLUG}"
    print_status "$BLUE" "  • Schema: ${TENANT_SCHEMA}"
    print_status "$BLUE" "  • Admin: ${TENANT_ADMIN_USERNAME} / ${TENANT_ADMIN_PASSWORD}"
fi

# ============================================
# TEST SUMMARY
# ============================================

print_section "TEST SUMMARY"

print_status "$GREEN" "Test Execution Completed!"
echo ""
print_status "$BLUE" "Test Results:"
print_status "$CYAN" "  • Tenant Created: ${TEST_TENANT_SLUG}"
print_status "$CYAN" "  • Schema: ${TENANT_SCHEMA}"
print_status "$CYAN" "  • Total Tables: ${TOTAL_TABLES}"
print_status "$CYAN" "  • Users Created: ${USER_COUNT:-0}"
print_status "$CYAN" "  • Roles Created: ${ROLE_COUNT:-0}"
print_status "$CYAN" "  • Teams Created: ${TEAM_COUNT:-0}"
echo ""

if [ ! -z "$MISSING_TABLES" ]; then
    print_status "$YELLOW" "Issues Found:"
    print_status "$YELLOW" "  • Missing tables:${MISSING_TABLES}"
fi

print_status "$YELLOW" "Recommendations:"
print_status "$YELLOW" "  • Check service logs if tables are missing"
print_status "$YELLOW" "  • Verify all services are running correctly"
print_status "$YELLOW" "  • Review schema creation process for each service"
echo ""

print_status "$MAGENTA" "╔══════════════════════════════════════════════════════════════╗"
print_status "$MAGENTA" "║                    TEST COMPLETED                            ║"
print_status "$MAGENTA" "╚══════════════════════════════════════════════════════════════╝"
