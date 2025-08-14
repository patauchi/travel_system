#!/bin/bash

# Simple test script to verify shared authentication integration
# Tests basic authentication functionality step by step

echo "🧪 Testing Shared Authentication Integration"
echo "============================================"

# Configuration
COMM_SERVICE_URL="http://localhost:8003"
AUTH_SERVICE_URL="http://localhost:8001"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "📋 Testing basic endpoints..."

# Test 1: Health check (should work without auth)
echo -e "\n🔧 Test 1: Health Check (no auth required)"
if curl -s "$COMM_SERVICE_URL/health" > /dev/null; then
    print_success "Communication service is running"
else
    print_error "Communication service not accessible at $COMM_SERVICE_URL"
    echo "Start it with: cd services/communication-service && python main.py"
    exit 1
fi

# Test 2: Try protected endpoint without auth (should fail)
echo -e "\n🔧 Test 2: Protected endpoint without auth (should get 401)"
response=$(curl -s -w "%{http_code}" -o /dev/null "$COMM_SERVICE_URL/api/v1/auth/test")
if [ "$response" = "401" ]; then
    print_success "Correctly rejected unauthenticated request"
elif [ "$response" = "404" ]; then
    print_warning "Auth test endpoint not found (may not be implemented yet)"
else
    print_warning "Expected 401, got $response"
fi

# Test 3: Try to get a token
echo -e "\n🔧 Test 3: Getting authentication token from auth service"
if ! curl -s "$AUTH_SERVICE_URL/health" > /dev/null; then
    print_warning "Auth service not running at $AUTH_SERVICE_URL"
    echo "You can test manually with a token if you have one"
else
    print_success "Auth service is accessible"

    # Try to login
    login_response=$(curl -s -X POST "$AUTH_SERVICE_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "demo_admin", "password": "Demo123!"}')

    if echo "$login_response" | grep -q "access_token"; then
        token=$(echo "$login_response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        print_success "Successfully obtained token"

        # Test 4: Use token with protected endpoint
        echo -e "\n🔧 Test 4: Using token with protected endpoint"
        auth_response=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $token" \
            "$COMM_SERVICE_URL/api/v1/auth/test")

        if echo "$auth_response" | grep -q "200$"; then
            print_success "Authentication working correctly!"
        else
            print_warning "Auth endpoint may not be fully implemented"
        fi

        # Test 5: Tenant access
        echo -e "\n🔧 Test 5: Testing tenant access control"
        tenant_response=$(curl -s -w "%{http_code}" \
            -H "Authorization: Bearer $token" \
            "$COMM_SERVICE_URL/api/v1/tenants/demo/auth/test")

        if echo "$tenant_response" | grep -q "200$"; then
            print_success "Tenant access control working!"
        elif echo "$tenant_response" | grep -q "403$"; then
            print_warning "Access denied - check if user belongs to 'demo' tenant"
        else
            print_warning "Tenant endpoint may not be implemented yet"
        fi

    else
        print_warning "Could not get token (check auth service and credentials)"
    fi
fi

echo -e "\n============================================"
echo "🎯 Integration Status"
echo "============================================"

echo -e "\n📝 What this tested:"
echo "1. Communication service accessibility"
echo "2. Rejection of unauthenticated requests"
echo "3. Token-based authentication"
echo "4. Tenant access control"

echo -e "\n💡 To add auth to your endpoints:"
echo "1. Import: from auth import get_current_user"
echo "2. Add dependency: current_user = Depends(get_current_user)"
echo "3. Check tenant: check_tenant_slug_access(current_user, tenant_slug)"

echo -e "\n🔗 Quick examples:"
echo "# Basic auth:"
echo "@app.get('/protected')"
echo "async def endpoint(user = Depends(get_current_user)):"
echo "    return {'user': user['username']}"
echo ""
echo "# Tenant auth:"
echo "@app.get('/tenants/{tenant_slug}/data')"
echo "async def endpoint(tenant_slug: str, user = Depends(get_current_user)):"
echo "    if not check_tenant_slug_access(user, tenant_slug):"
echo "        raise HTTPException(403, 'Access denied')"
echo "    return {'data': 'success'}"

echo -e "\n✅ Test completed"
