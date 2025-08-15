#!/bin/bash

# System Service Security Test Runner
# This script runs security tests for the system service

echo "=========================================="
echo "System Service Security Tests"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"

echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if services are running
echo "Checking if services are running..."
echo ""

# Function to check if a service is running
check_service() {
    local service_name=$1
    local port=$2
    local url=$3

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
        echo -e "${GREEN}✓${NC} $service_name is running on port $port"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is not running on port $port"
        return 1
    fi
}

# Check required services
services_ok=true

if ! check_service "Auth Service" 8001 "http://localhost:8001/health"; then
    services_ok=false
fi

if ! check_service "Tenant Service" 8002 "http://localhost:8002/health"; then
    services_ok=false
fi

if ! check_service "System Service" 8008 "http://localhost:8008/health"; then
    services_ok=false
fi

echo ""

if [ "$services_ok" = false ]; then
    echo -e "${RED}Error: Required services are not running${NC}"
    echo ""
    echo "Please start the services first:"
    echo "  1. cd $PROJECT_ROOT"
    echo "  2. docker-compose up -d"
    echo ""
    exit 1
fi

echo -e "${GREEN}All required services are running${NC}"
echo ""

# Check required packages
echo "Checking Python dependencies..."
missing_packages=""

if ! python3 -c "import httpx" 2>/dev/null; then
    missing_packages="$missing_packages httpx"
fi

if [ ! -z "$missing_packages" ]; then
    echo -e "${YELLOW}Warning: Missing Python packages:$missing_packages${NC}"
    echo "Please install them manually:"
    echo "  pip3 install --user --break-system-packages httpx"
    echo ""
    echo "Attempting to continue anyway..."
    echo ""
else
    echo -e "${GREEN}Python dependencies OK${NC}"
    echo ""
fi

# Run the test
echo "=========================================="
echo "Running System Service Security Tests"
echo "=========================================="
echo ""

# Change to script directory to ensure proper imports
cd "$SCRIPT_DIR"

# Run the test with Python
python3 test_system.py

# Capture exit code
test_exit_code=$?

echo ""
echo "=========================================="
if [ $test_exit_code -eq 0 ]; then
    echo -e "${GREEN}System Service Security Tests Completed Successfully${NC}"
else
    echo -e "${RED}System Service Security Tests Failed${NC}"
fi
echo "=========================================="

exit $test_exit_code
