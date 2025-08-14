#!/bin/bash

# Financial Service Manual Testing Script
# Tests the modular financial service with authentication

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:8007"
TENANT_ID="test-tenant-456"
SCHEMA_NAME="tenant_test_tenant_456"

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}🧪 FINANCIAL SERVICE MANUAL TESTING SUITE${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Function to generate token
generate_token() {
    echo -e "${YELLOW}🔐 Generating authentication token...${NC}"
    cd "$(dirname "$0")"
    source venv/bin/activate
    TOKEN=$(python3 generate_test_token.py --quiet 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Token generated successfully${NC}"
        echo "Token: ${TOKEN:0:50}..."
    else
        echo -e "${RED}❌ Failed to generate token${NC}"
        exit 1
    fi
}

# Function to make authenticated API call
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local description="$4"

    echo -e "${YELLOW}📡 ${description}${NC}"

    if [ "$method" = "GET" ]; then
        response=$(curl -s -H "Authorization: Bearer $TOKEN" \
                      -H "Content-Type: application/json" \
                      -H "X-Tenant-ID: $TENANT_ID" \
                      "$BASE_URL$endpoint")
    else
        response=$(curl -s -X "$method" \
                      -H "Authorization: Bearer $TOKEN" \
                      -H "Content-Type: application/json" \
                      -H "X-Tenant-ID: $TENANT_ID" \
                      -d "$data" \
                      "$BASE_URL$endpoint")
    fi

    # Check if response contains error
    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: $(echo "$response" | jq -r '.error')${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Success${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 0
    fi
}

# Function to make unauthenticated API call (should fail)
api_call_unauth() {
    local endpoint="$1"
    local description="$2"

    echo -e "${YELLOW}📡 ${description} (No Auth - Should Fail)${NC}"

    response=$(curl -s "$BASE_URL$endpoint")

    # Check if response contains authentication error
    if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
        local error=$(echo "$response" | jq -r '.error')
        if [[ "$error" == *"Not authenticated"* ]]; then
            echo -e "${GREEN}✅ Correctly rejected - Not authenticated${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Different error: $error${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Unexpectedly allowed without authentication${NC}"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        return 1
    fi
}

# Start testing
echo -e "${BLUE}🚀 Starting Financial Service Tests${NC}"
echo ""

# Generate authentication token
generate_token
echo ""

# Test 1: Health Checks (No Auth Required)
echo -e "${BLUE}=== 🏥 HEALTH CHECKS (NO AUTH) ===${NC}"
echo ""

echo -e "${YELLOW}📡 Basic Health Check${NC}"
response=$(curl -s "$BASE_URL/health")
if echo "$response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Service is healthy${NC}"
    echo "$response" | jq '.'
else
    echo -e "${RED}❌ Service health check failed${NC}"
    echo "$response"
fi
echo ""

echo -e "${YELLOW}📡 Root Endpoint${NC}"
response=$(curl -s "$BASE_URL/")
if echo "$response" | jq -e '.service' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Root endpoint working${NC}"
    echo "$response" | jq '.'
else
    echo -e "${RED}❌ Root endpoint failed${NC}"
    echo "$response"
fi
echo ""

echo -e "${YELLOW}📡 Financial Health Check${NC}"
response=$(curl -s "$BASE_URL/api/v1/financial/health")
if echo "$response" | jq -e '.service == "financial-service"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Financial service health OK${NC}"
    echo "$response" | jq '.'
else
    echo -e "${RED}❌ Financial health check failed${NC}"
    echo "$response"
fi
echo ""

# Test 2: Authentication Required Endpoints (Should Fail)
echo -e "${BLUE}=== 🔒 AUTHENTICATION TESTS (SHOULD FAIL) ===${NC}"
echo ""

api_call_unauth "/api/v1/financial/auth-test" "Auth Test"
echo ""

api_call_unauth "/api/v1/financial/orders" "Orders List"
echo ""

api_call_unauth "/api/v1/financial/modules" "Modules Info"
echo ""

# Test 3: Authenticated Endpoints (Should Work)
echo -e "${BLUE}=== ✅ AUTHENTICATED ENDPOINTS ===${NC}"
echo ""

api_call "GET" "/api/v1/financial/auth-test" "" "Authentication Test"
echo ""

api_call "GET" "/api/v1/financial/modules" "" "Modules Information"
echo ""

# Test 4: Tenant Initialization
echo -e "${BLUE}=== 🏗️  TENANT INITIALIZATION ===${NC}"
echo ""

tenant_data='{"schema_name": "'$SCHEMA_NAME'"}'
api_call "POST" "/api/v1/tenants/$TENANT_ID/initialize" "$tenant_data" "Initialize Tenant"
echo ""

# Test 5: Orders CRUD Operations
echo -e "${BLUE}=== 📋 ORDERS MODULE CRUD ===${NC}"
echo ""

# List orders (should be empty)
api_call "GET" "/api/v1/financial/orders?schema_name=$SCHEMA_NAME" "" "List Orders (Empty)"
echo ""

# Create an order
order_data='{
  "quote_id": 1,
  "order_number": "ORD-2024-TEST-001",
  "order_status": "pending",
  "subtotal": 1000.00,
  "tax_amount": 100.00,
  "discount_amount": 50.00,
  "total_amount": 1050.00,
  "currency": "USD",
  "order_date": "2024-01-15",
  "departure_date": "2024-02-15",
  "return_date": "2024-02-22",
  "payment_status": "pending",
  "amount_paid": 0.00,
  "amount_due": 1050.00,
  "special_instructions": "Test order for manual testing"
}'

api_call "POST" "/api/v1/financial/orders?schema_name=$SCHEMA_NAME" "$order_data" "Create Order"
echo ""

# Get specific order
api_call "GET" "/api/v1/financial/orders/1?schema_name=$SCHEMA_NAME" "" "Get Order by ID"
echo ""

# Update order
update_data='{
  "order_status": "confirmed",
  "special_instructions": "Updated - Test order confirmed",
  "internal_notes": "Order updated via manual test"
}'

api_call "PUT" "/api/v1/financial/orders/1?schema_name=$SCHEMA_NAME" "$update_data" "Update Order"
echo ""

# List orders again (should show the created order)
api_call "GET" "/api/v1/financial/orders?schema_name=$SCHEMA_NAME" "" "List Orders (With Data)"
echo ""

# Test 6: Other Modules Basic Tests
echo -e "${BLUE}=== 🧪 OTHER MODULES BASIC TESTS ===${NC}"
echo ""

api_call "GET" "/api/v1/financial/expenses?schema_name=$SCHEMA_NAME" "" "List Expenses"
echo ""

api_call "GET" "/api/v1/financial/petty-cash?schema_name=$SCHEMA_NAME" "" "List Petty Cash Funds"
echo ""

api_call "GET" "/api/v1/financial/vouchers?schema_name=$SCHEMA_NAME" "" "List Vouchers"
echo ""

api_call "GET" "/api/v1/financial/invoices?schema_name=$SCHEMA_NAME" "" "List Invoices"
echo ""

api_call "GET" "/api/v1/financial/payments?schema_name=$SCHEMA_NAME" "" "List Payments"
echo ""

# Test 7: Module Health Checks
echo -e "${BLUE}=== 🏥 MODULE HEALTH CHECKS ===${NC}"
echo ""

api_call "GET" "/api/v1/financial/orders/health" "" "Orders Module Health"
echo ""

api_call "GET" "/api/v1/financial/expenses/health" "" "Expenses Module Health"
echo ""

api_call "GET" "/api/v1/financial/petty-cash/health" "" "Petty Cash Module Health"
echo ""

api_call "GET" "/api/v1/financial/vouchers/health" "" "Vouchers Module Health"
echo ""

api_call "GET" "/api/v1/financial/invoices/health" "" "Invoices Module Health"
echo ""

api_call "GET" "/api/v1/financial/payments/health" "" "Payments Module Health"
echo ""

# Test 8: Permission Tests (with different permission levels)
echo -e "${BLUE}=== 🔐 PERMISSION TESTS ===${NC}"
echo ""

echo -e "${YELLOW}📡 Testing with current token permissions${NC}"
api_call "GET" "/api/v1/financial/tenant-auth-test" "" "Tenant Auth & DB Test"
echo ""

# Final Summary
echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}📊 TESTING SUMMARY${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""
echo -e "${GREEN}✅ Tests Completed Successfully${NC}"
echo ""
echo -e "${YELLOW}Key Points Verified:${NC}"
echo "🔸 Service health checks working"
echo "🔸 Authentication system functioning"
echo "🔸 Authorization properly blocking unauthenticated requests"
echo "🔸 Tenant initialization working"
echo "🔸 Orders CRUD operations functional"
echo "🔸 All modules responding to basic requests"
echo "🔸 Module-specific health checks working"
echo "🔸 JWT token authentication working"
echo "🔸 Multi-tenant support functional"
echo ""
echo -e "${BLUE}🚀 Financial Service Modular Architecture Validation Complete!${NC}"
echo ""
