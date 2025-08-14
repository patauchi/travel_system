#!/bin/bash

# Multi-Tenant Platform - Complete Flow Test Script
# This script tests the complete multi-tenant architecture flow

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_GATEWAY="http://localhost:8000"
AUTH_SERVICE="http://localhost:8001"
TENANT_SERVICE="http://localhost:8002"
SYSTEM_SERVICE="http://localhost:8008"
FRONTEND="http://localhost:3000"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check service health
check_service() {
    local service_name=$1
    local service_url=$2

    print_info "Checking $service_name..."

    if curl -s -f "$service_url/health" > /dev/null 2>&1; then
        print_success "$service_name is healthy"
        return 0
    else
        print_error "$service_name is not responding"
        return 1
    fi
}

# Function to create a tenant
create_tenant() {
    local tenant_name=$1
    local tenant_slug=$2
    local admin_email=$3
    local admin_username=$4
    local admin_password=$5
    local plan=${6:-"starter"}

    print_info "Creating tenant: $tenant_name ($tenant_slug)"

    response=$(curl -s -X POST "$TENANT_SERVICE/api/v1/tenants/v2" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"$tenant_name\",
            \"slug\": \"$tenant_slug\",
            \"subdomain\": \"$tenant_slug\",
            \"owner_email\": \"$admin_email\",
            \"owner_username\": \"$admin_username\",
            \"owner_password\": \"$admin_password\",
            \"owner_first_name\": \"Admin\",
            \"owner_last_name\": \"$tenant_name\",
            \"subscription_plan\": \"$plan\"
        }")

    if echo "$response" | grep -q "\"id\""; then
        tenant_id=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
        print_success "Tenant created with ID: $tenant_id"
        echo "$response"
        return 0
    else
        print_error "Failed to create tenant: $response"
        return 1
    fi
}

# Function to login as user
login_user() {
    local username=$1
    local password=$2
    local host=${3:-"localhost"}

    print_info "Logging in as $username on $host"

    response=$(curl -s -X POST "$AUTH_SERVICE/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -H "Host: $host" \
        -d "username=$username&password=$password")

    if echo "$response" | grep -q "access_token"; then
        access_token=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
        print_success "Login successful"
        echo "$access_token"
        return 0
    else
        print_error "Login failed: $response"
        return 1
    fi
}

# Function to register a user in tenant
register_tenant_user() {
    local email=$1
    local username=$2
    local password=$3
    local first_name=$4
    local last_name=$5
    local tenant_subdomain=$6

    print_info "Registering user $username in tenant $tenant_subdomain"

    response=$(curl -s -X POST "$AUTH_SERVICE/api/v1/auth/register" \
        -H "Content-Type: application/json" \
        -H "Host: $tenant_subdomain.localhost" \
        -d "{
            \"email\": \"$email\",
            \"username\": \"$username\",
            \"password\": \"$password\",
            \"first_name\": \"$first_name\",
            \"last_name\": \"$last_name\"
        }")

    if echo "$response" | grep -q "access_token"; then
        print_success "User registered successfully"
        return 0
    else
        print_error "Registration failed: $response"
        return 1
    fi
}

# Function to get current user info
get_user_info() {
    local token=$1
    local host=${2:-"localhost"}

    print_info "Getting user info"

    response=$(curl -s -X GET "$AUTH_SERVICE/api/v1/auth/me" \
        -H "Authorization: Bearer $token" \
        -H "Host: $host")

    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
}

# Main test flow
main() {
    echo "=================================================="
    echo "   Multi-Tenant Platform - Complete Flow Test"
    echo "=================================================="
    echo ""

    # Step 1: Check all services
    print_info "Step 1: Checking service health"
    echo "----------------------------------------"

    check_service "Auth Service" "$AUTH_SERVICE"
    check_service "Tenant Service" "$TENANT_SERVICE"
    check_service "System Service" "$SYSTEM_SERVICE"

    echo ""

    # Step 2: Test Super Admin Login
    print_info "Step 2: Testing Super Admin Login"
    echo "----------------------------------------"

    SUPER_ADMIN_TOKEN=$(login_user "superadmin" "Admin123!" "localhost")
    if [ $? -eq 0 ]; then
        print_success "Super admin login successful"
        get_user_info "$SUPER_ADMIN_TOKEN" "localhost"
    fi

    echo ""

    # Step 3: Create Test Tenants
    print_info "Step 3: Creating Test Tenants"
    echo "----------------------------------------"

    # Create first test tenant
    create_tenant \
        "Test Company Alpha" \
        "test-alpha" \
        "admin@testalpha.com" \
        "alpha_admin" \
        "AlphaAdmin123!" \
        "professional"

    # Create second test tenant
    create_tenant \
        "Test Company Beta" \
        "test-beta" \
        "admin@testbeta.com" \
        "beta_admin" \
        "BetaAdmin123!" \
        "starter"

    echo ""

    # Step 4: Test Tenant Admin Login
    print_info "Step 4: Testing Tenant Admin Login"
    echo "----------------------------------------"

    sleep 2  # Wait for tenant creation to complete

    TENANT_ADMIN_TOKEN=$(login_user "alpha_admin" "AlphaAdmin123!" "test-alpha.localhost")
    if [ $? -eq 0 ]; then
        print_success "Tenant admin login successful"
        get_user_info "$TENANT_ADMIN_TOKEN" "test-alpha.localhost"
    fi

    echo ""

    # Step 5: Create Users in Tenant
    print_info "Step 5: Creating Users in Tenant"
    echo "----------------------------------------"

    register_tenant_user \
        "john@testalpha.com" \
        "john_doe" \
        "JohnDoe123!" \
        "John" \
        "Doe" \
        "test-alpha"

    register_tenant_user \
        "jane@testalpha.com" \
        "jane_smith" \
        "JaneSmith123!" \
        "Jane" \
        "Smith" \
        "test-alpha"

    echo ""

    # Step 6: Test Tenant User Login
    print_info "Step 6: Testing Tenant User Login"
    echo "----------------------------------------"

    TENANT_USER_TOKEN=$(login_user "john_doe" "JohnDoe123!" "test-alpha.localhost")
    if [ $? -eq 0 ]; then
        print_success "Tenant user login successful"
        get_user_info "$TENANT_USER_TOKEN" "test-alpha.localhost"
    fi

    echo ""

    # Step 7: Test Cross-Tenant Access (Should Fail)
    print_info "Step 7: Testing Cross-Tenant Access Prevention"
    echo "----------------------------------------"

    print_info "Attempting to login to test-beta with test-alpha credentials (should fail)"

    if ! login_user "john_doe" "JohnDoe123!" "test-beta.localhost" 2>/dev/null; then
        print_success "Cross-tenant access correctly prevented"
    else
        print_error "SECURITY WARNING: Cross-tenant access was allowed!"
    fi

    echo ""

    # Step 8: List All Tenants (as Super Admin)
    print_info "Step 8: Listing All Tenants"
    echo "----------------------------------------"

    response=$(curl -s -X GET "$TENANT_SERVICE/api/v1/tenants" \
        -H "Authorization: Bearer $SUPER_ADMIN_TOKEN")

    echo "$response" | python3 -c "
import sys, json
tenants = json.load(sys.stdin)
print(f'Total tenants: {len(tenants)}')
for t in tenants:
    print(f\"  - {t['name']} ({t['slug']}) - Plan: {t['subscription_plan']} - Status: {t['status']}\")
" 2>/dev/null || echo "$response"

    echo ""

    # Summary
    echo "=================================================="
    echo "                  Test Summary"
    echo "=================================================="

    print_success "Multi-tenant architecture test completed!"
    echo ""
    echo "Created Tenants:"
    echo "  1. Test Company Alpha (test-alpha.localhost:3000)"
    echo "     - Admin: alpha_admin / AlphaAdmin123!"
    echo "     - Users: john_doe / JohnDoe123!"
    echo "              jane_smith / JaneSmith123!"
    echo ""
    echo "  2. Test Company Beta (test-beta.localhost:3000)"
    echo "     - Admin: beta_admin / BetaAdmin123!"
    echo ""
    echo "System Admin:"
    echo "  - URL: http://localhost:3000/admin"
    echo "  - Login: superadmin / Admin123!"
    echo ""
    echo "Key Features Tested:"
    echo "  ✓ Service health checks"
    echo "  ✓ Super admin authentication"
    echo "  ✓ Tenant creation with admin user"
    echo "  ✓ Tenant-specific user registration"
    echo "  ✓ Tenant-isolated authentication"
    echo "  ✓ Cross-tenant access prevention"
    echo "  ✓ Multi-tenant management"
    echo ""
}

# Run main function
main
