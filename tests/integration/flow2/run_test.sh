#!/bin/bash

# Flow 2 Integration Test Runner
# This script runs the Flow 2 test directly using Python

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../../.." && pwd )"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   FLOW 2 - Integration Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Testing:"
echo "1. Login with existing super_admin"
echo "2. Create tenant via /api/v1/tenants/v2"
echo "3. Verify all tables exist (75-80)"
echo "4. Login to tenant and create new user"
echo "5. Create channel configurations for Inbox (Email, WhatsApp, Facebook)"
echo "6. Create Inbox Conversations"
echo "7. Create Inbox Messages"
echo "8. Verify messages belong to conversations"
echo ""

# Check if httpx is installed, if not install it
echo -e "${YELLOW}[INFO]${NC} Checking Python dependencies..."

# Create temporary virtual environment if needed
TEMP_VENV="$PROJECT_ROOT/.test_venv"

if [ ! -d "$TEMP_VENV" ]; then
    echo -e "${YELLOW}[INFO]${NC} Creating virtual environment..."
    python3 -m venv "$TEMP_VENV"
fi

# Activate virtual environment
source "$TEMP_VENV/bin/activate"

# Install required package
pip install httpx --quiet 2>/dev/null || {
    echo -e "${YELLOW}[INFO]${NC} Installing httpx..."
    pip install httpx
}

# Run the test
echo -e "${GREEN}[START]${NC} Running Flow 2 test..."
echo ""

# Execute the Python test file directly
python3 "$SCRIPT_DIR/test_flow2.py"

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ SUCCESS: Flow 2 test completed successfully!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ FAILED: Flow 2 test failed${NC}"
    exit 1
fi
