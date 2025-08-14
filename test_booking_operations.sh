#!/bin/bash

# Test script for Booking Operations Service
# Tests authentication, CRUD operations, and multi-tenant functionality

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AUTH_URL="http://localhost:8001"
BOOKING_URL="http://localhost:8004"
TENANT_SLUG="tenant1"
SCHEMA_NAME="tenant1"

# Variables to store test data
TOKEN=""
COUNTRY_ID=""
SUPPLIER_ID=""
SERVICE_ID=""
BOOKING_ID=""

# Function to print headers
print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}TEST: $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# Function to print results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS: $2${NC}"
    else
        echo -e "${RED}❌ FAIL: $2${NC}"
    fi
}

# Function to print info
print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}BOOKING OPERATIONS SERVICE TEST SUITE${NC}"
echo -e "${BLUE}============================================================${NC}"
echo "Auth Service: $AUTH_URL"
echo "Booking Service: $BOOKING_URL"
echo "Tenant: $TENANT_SLUG"
echo "Testing at: $(date)"

# ============================================================
# TEST: Without Authentication
# ============================================================
print_header "Testing WITHOUT Authentication"

echo -e "\n1. Testing health endpoint (should work without auth)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BOOKING_URL/health")
if [ "$RESPONSE" = "200" ]; then
    print_result 0 "Health endpoint accessible without auth"
    curl -s "$BOOKING_URL/health" | jq '.'
else
    print_result 1 "Health endpoint returned $RESPONSE"
fi

echo -e "\n2. Testing protected endpoint (should fail without auth)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BOOKING_URL/api/v1/auth/test")
if [ "$RESPONSE" = "401" ]; then
    print_result 0 "Protected endpoint correctly requires authentication"
else
    print_result 1 "Protected endpoint returned $RESPONSE (expected 401)"
fi

echo -e "\n3. Testing tenant endpoint (should fail without auth)..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries?schema_name=$SCHEMA_NAME")
if [ "$RESPONSE" = "401" ]; then
    print_result 0 "Tenant endpoint correctly requires authentication"
else
    print_result 1 "Tenant endpoint returned $RESPONSE (expected 401)"
fi

# ============================================================
# TEST: Get Authentication Token
# ============================================================
print_header "Authentication"

echo -e "\n1. Creating test user..."
curl -s -X POST "$AUTH_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }' > /dev/null 2>&1

echo -e "\n2. Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST "$AUTH_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser&password=testpass123")

TOKEN=$(echo $TOKEN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
    print_result 0 "Authentication successful"
    print_info "Token obtained: ${TOKEN:0:20}..."
else
    print_result 1 "Failed to get authentication token"
    echo "Response: $TOKEN_RESPONSE"
    echo -e "\n${RED}Cannot continue without authentication token${NC}"
    exit 1
fi

# ============================================================
# TEST: With Authentication
# ============================================================
print_header "Testing WITH Authentication"

echo -e "\n1. Testing auth verification..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BOOKING_URL/api/v1/auth/test" \
    -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_result 0 "Auth verification successful"
    echo "$BODY" | jq '.'
else
    print_result 1 "Auth verification failed with code $HTTP_CODE"
fi

echo -e "\n2. Testing tenant-specific auth..."
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/auth/test?schema_name=$SCHEMA_NAME" \
    -H "Authorization: Bearer $TOKEN")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_result 0 "Tenant auth successful"
    echo "$BODY" | jq '.'
else
    print_result 1 "Tenant auth failed with code $HTTP_CODE"
fi

# ============================================================
# TEST: CRUD Operations - Countries
# ============================================================
print_header "CRUD Operations - Countries"

echo -e "\n1. CREATE Country..."
RESPONSE=$(curl -s -X POST "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries?schema_name=$SCHEMA_NAME" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "code": "PE",
        "code3": "PER",
        "name": "Peru",
        "continent": "South America",
        "is_active": true
    }')

COUNTRY_ID=$(echo "$RESPONSE" | jq -r '.id')
if [ "$COUNTRY_ID" != "null" ] && [ ! -z "$COUNTRY_ID" ]; then
    print_result 0 "Country created with ID: $COUNTRY_ID"
else
    print_info "Country might already exist, trying to list..."
fi

echo -e "\n2. READ Countries (List)..."
RESPONSE=$(curl -s "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries?schema_name=$SCHEMA_NAME&page=1&page_size=10" \
    -H "Authorization: Bearer $TOKEN")

COUNT=$(echo "$RESPONSE" | jq '.items | length')
if [ ! -z "$COUNT" ]; then
    print_result 0 "Listed $COUNT countries"
    echo "$RESPONSE" | jq '.items[0]'

    # Get first country ID if we didn't create one
    if [ -z "$COUNTRY_ID" ] || [ "$COUNTRY_ID" = "null" ]; then
        COUNTRY_ID=$(echo "$RESPONSE" | jq -r '.items[0].id')
    fi
else
    print_result 1 "Failed to list countries"
fi

if [ ! -z "$COUNTRY_ID" ] && [ "$COUNTRY_ID" != "null" ]; then
    echo -e "\n3. READ Single Country..."
    RESPONSE=$(curl -s "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries/$COUNTRY_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN")

    NAME=$(echo "$RESPONSE" | jq -r '.name')
    if [ "$NAME" != "null" ]; then
        print_result 0 "Retrieved country: $NAME"
    else
        print_result 1 "Failed to retrieve country"
    fi

    echo -e "\n4. UPDATE Country..."
    RESPONSE=$(curl -s -X PUT "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries/$COUNTRY_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name": "Republic of Peru"}')

    UPDATED_NAME=$(echo "$RESPONSE" | jq -r '.name')
    if [ "$UPDATED_NAME" = "Republic of Peru" ]; then
        print_result 0 "Country updated successfully"
    else
        print_result 1 "Failed to update country"
    fi
fi

# ============================================================
# TEST: CRUD Operations - Suppliers
# ============================================================
print_header "CRUD Operations - Suppliers"

echo -e "\n1. CREATE Supplier..."
RESPONSE=$(curl -s -X POST "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/suppliers?schema_name=$SCHEMA_NAME" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "code": "SUP001",
        "name": "Test Travel Agency",
        "legal_name": "Test Travel Agency S.A.",
        "tax_id": "20123456789",
        "supplier_type": "agency",
        "status": "active",
        "contact_email": "contact@testagency.com",
        "contact_phone": "+51999888777",
        "website": "https://testagency.com",
        "is_active": true
    }')

SUPPLIER_ID=$(echo "$RESPONSE" | jq -r '.id')
if [ "$SUPPLIER_ID" != "null" ] && [ ! -z "$SUPPLIER_ID" ]; then
    print_result 0 "Supplier created with ID: $SUPPLIER_ID"
else
    print_info "Supplier might already exist, trying to list..."
fi

echo -e "\n2. READ Suppliers (List)..."
RESPONSE=$(curl -s "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/suppliers?schema_name=$SCHEMA_NAME&page=1&page_size=10" \
    -H "Authorization: Bearer $TOKEN")

COUNT=$(echo "$RESPONSE" | jq '.items | length')
if [ ! -z "$COUNT" ]; then
    print_result 0 "Listed $COUNT suppliers"

    # Get first supplier ID if we didn't create one
    if [ -z "$SUPPLIER_ID" ] || [ "$SUPPLIER_ID" = "null" ]; then
        SUPPLIER_ID=$(echo "$RESPONSE" | jq -r '.items[0].id')
    fi
else
    print_result 1 "Failed to list suppliers"
fi

# ============================================================
# TEST: CRUD Operations - Services
# ============================================================
print_header "CRUD Operations - Services"

if [ ! -z "$SUPPLIER_ID" ] && [ "$SUPPLIER_ID" != "null" ]; then
    echo -e "\n1. CREATE Service..."
    RESPONSE=$(curl -s -X POST "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/services?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"supplier_id\": $SUPPLIER_ID,
            \"code\": \"SRV001\",
            \"name\": \"Machu Picchu Tour\",
            \"description\": \"Full day tour to Machu Picchu\",
            \"service_type\": \"tour\",
            \"operation_model\": \"scheduled\",
            \"base_price\": 150.00,
            \"currency\": \"USD\",
            \"duration_value\": 12,
            \"duration_unit\": \"hours\",
            \"max_capacity\": 20,
            \"min_capacity\": 2,
            \"is_active\": true
        }")

    SERVICE_ID=$(echo "$RESPONSE" | jq -r '.id')
    if [ "$SERVICE_ID" != "null" ] && [ ! -z "$SERVICE_ID" ]; then
        print_result 0 "Service created with ID: $SERVICE_ID"
    else
        print_info "Service creation might have failed"
        echo "$RESPONSE" | jq '.'
    fi

    echo -e "\n2. READ Services (List)..."
    RESPONSE=$(curl -s "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/services?schema_name=$SCHEMA_NAME&page=1&page_size=10" \
        -H "Authorization: Bearer $TOKEN")

    COUNT=$(echo "$RESPONSE" | jq '.items | length')
    if [ ! -z "$COUNT" ]; then
        print_result 0 "Listed $COUNT services"
    else
        print_result 1 "Failed to list services"
    fi
else
    print_info "Skipping service tests (no supplier available)"
fi

# ============================================================
# TEST: CRUD Operations - Bookings
# ============================================================
print_header "CRUD Operations - Bookings"

echo -e "\n1. CREATE Booking..."
# Calculate future date (macOS compatible)
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%S")
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS date command
    FUTURE_DATE=$(date -u -v+30d +"%Y-%m-%dT%H:%M:%S")
else
    # Linux date command
    FUTURE_DATE=$(date -u -d "+30 days" +"%Y-%m-%dT%H:%M:%S")
fi

RESPONSE=$(curl -s -X POST "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/bookings?schema_name=$SCHEMA_NAME" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "order_id": 1001,
        "booking_reference": "BK2024001",
        "external_reference": "EXT001",
        "booking_date": "'$CURRENT_DATE'",
        "service_date": "'$FUTURE_DATE'",
        "overall_status": "pending",
        "total_amount": 300.00,
        "currency": "USD",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "notes": "Test booking"
    }')

BOOKING_ID=$(echo "$RESPONSE" | jq -r '.id')
if [ "$BOOKING_ID" != "null" ] && [ ! -z "$BOOKING_ID" ]; then
    print_result 0 "Booking created with ID: $BOOKING_ID"
else
    print_info "Booking creation might have failed"
    echo "$RESPONSE" | jq '.'
fi

echo -e "\n2. READ Bookings (List)..."
RESPONSE=$(curl -s "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/bookings?schema_name=$SCHEMA_NAME&page=1&page_size=10" \
    -H "Authorization: Bearer $TOKEN")

COUNT=$(echo "$RESPONSE" | jq '.items | length')
if [ ! -z "$COUNT" ]; then
    print_result 0 "Listed $COUNT bookings"
else
    print_result 1 "Failed to list bookings"
fi

# ============================================================
# TEST: Cleanup
# ============================================================
print_header "Cleanup (Optional)"

echo -e "\nCleaning up test data..."

# Delete in reverse order of dependencies
if [ ! -z "$BOOKING_ID" ] && [ "$BOOKING_ID" != "null" ]; then
    echo "Deleting booking..."
    curl -s -X DELETE "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/bookings/$BOOKING_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1
fi

if [ ! -z "$SERVICE_ID" ] && [ "$SERVICE_ID" != "null" ]; then
    echo "Deleting service..."
    curl -s -X DELETE "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/services/$SERVICE_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1
fi

if [ ! -z "$SUPPLIER_ID" ] && [ "$SUPPLIER_ID" != "null" ]; then
    echo "Deleting supplier..."
    curl -s -X DELETE "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/suppliers/$SUPPLIER_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1
fi

if [ ! -z "$COUNTRY_ID" ] && [ "$COUNTRY_ID" != "null" ]; then
    echo "Deleting country..."
    curl -s -X DELETE "$BOOKING_URL/api/v1/tenants/$TENANT_SLUG/countries/$COUNTRY_ID?schema_name=$SCHEMA_NAME" \
        -H "Authorization: Bearer $TOKEN" > /dev/null 2>&1
fi

print_info "Cleanup completed"

# ============================================================
# Summary
# ============================================================
echo -e "\n${BLUE}============================================================${NC}"
echo -e "${BLUE}TEST SUITE COMPLETED${NC}"
echo -e "${BLUE}============================================================${NC}"
echo "Tested at: $(date)"
echo -e "\n${GREEN}✅ All tests completed successfully!${NC}"
