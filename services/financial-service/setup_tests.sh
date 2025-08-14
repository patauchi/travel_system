#!/bin/bash
#
# Financial Service Test Setup Script
# Quick setup for running tests in the modular financial service
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
}

# Check if running from correct directory
check_directory() {
    if [[ ! -f "main.py" ]] || [[ ! -d "orders" ]] || [[ ! -d "tests" ]]; then
        print_error "Please run this script from the financial-service directory"
        print_error "Expected structure: financial-service/main.py, financial-service/orders/, etc."
        exit 1
    fi
    print_success "Running from correct directory: $(pwd)"
}

# Check Python version
check_python() {
    print_status "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [[ $MAJOR_VERSION -lt 3 ]] || [[ $MAJOR_VERSION -eq 3 && $MINOR_VERSION -lt 8 ]]; then
        print_error "Python 3.8+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python version: $PYTHON_VERSION"
}

# Check PostgreSQL
check_postgresql() {
    print_status "Checking PostgreSQL..."

    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL client (psql) not found"
        print_warning "Please install PostgreSQL client tools"
        return 1
    fi

    # Try to connect to PostgreSQL
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        print_success "PostgreSQL is running"
        return 0
    else
        print_warning "PostgreSQL is not running on localhost:5432"
        print_warning "Please start PostgreSQL service"
        return 1
    fi
}

# Create test database
create_test_database() {
    print_status "Setting up test database..."

    if ! check_postgresql; then
        print_warning "Skipping database setup due to PostgreSQL issues"
        return 1
    fi

    # Check if database exists
    if psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw financial_test_db; then
        print_warning "Test database 'financial_test_db' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Dropping existing test database..."
            dropdb -h localhost -U postgres financial_test_db 2>/dev/null || true
        else
            print_success "Using existing test database"
            return 0
        fi
    fi

    print_status "Creating test database 'financial_test_db'..."
    if createdb -h localhost -U postgres financial_test_db; then
        print_success "Test database created successfully"
    else
        print_error "Failed to create test database"
        print_error "Please ensure PostgreSQL is running and you have proper permissions"
        return 1
    fi
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."

    # Check if pip is available
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi

    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate

    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip

    # Install testing dependencies
    print_status "Installing testing dependencies..."
    pip install pytest pytest-cov pytest-timeout

    # Install FastAPI and related
    print_status "Installing FastAPI dependencies..."
    pip install fastapi uvicorn

    # Install database dependencies
    print_status "Installing database dependencies..."
    pip install sqlalchemy psycopg2-binary

    # Install validation dependencies
    print_status "Installing validation dependencies..."
    pip install pydantic

    # Install project requirements if they exist
    if [[ -f "requirements.txt" ]]; then
        print_status "Installing project requirements..."
        pip install -r requirements.txt
    fi

    print_success "Dependencies installed successfully"
}

# Setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."

    # Create .env file for testing
    cat > .env.test << EOF
# Test Environment Configuration
TESTING=true
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db
LOG_LEVEL=INFO
SECRET_KEY=test-secret-key-for-testing-only
API_PORT=8012
CORS_ORIGINS=*

# Authentication settings (for testing)
AUTH_SECRET_KEY=test-auth-secret
AUTH_ALGORITHM=HS256
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Test-specific settings
PYTEST_TIMEOUT=300
COVERAGE_THRESHOLD=80
EOF

    print_success "Environment file created: .env.test"
}

# Setup test directory structure
setup_test_structure() {
    print_status "Setting up test directory structure..."

    # Create test directories
    mkdir -p tests/{unit,integration,fixtures}
    mkdir -p logs
    mkdir -p htmlcov

    # Make run_tests.py executable
    if [[ -f "run_tests.py" ]]; then
        chmod +x run_tests.py
        print_success "Made run_tests.py executable"
    fi

    print_success "Test directory structure created"
}

# Run a quick test to verify setup
verify_setup() {
    print_status "Verifying test setup..."

    # Activate virtual environment
    source venv/bin/activate

    # Set test environment
    export TESTING=true
    export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db

    # Run a simple test
    print_status "Running health check tests..."
    if python -m pytest tests/test_integration.py::TestHealthChecks::test_main_health_check -v; then
        print_success "Health check test passed"
    else
        print_warning "Health check test failed - this might be expected if service is not running"
    fi

    # Test import of main modules
    print_status "Testing module imports..."
    python -c "
import sys
sys.path.append('.')

try:
    from orders import router as orders_router
    from expenses import router as expenses_router
    from pettycash import router as pettycash_router
    from voucher import router as voucher_router
    from invoices import router as invoices_router
    from payments import router as payments_router
    print('✅ All module imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

    if [[ $? -eq 0 ]]; then
        print_success "Module imports verified"
    else
        print_error "Module import verification failed"
        return 1
    fi
}

# Generate test execution commands
generate_commands() {
    print_status "Generating test execution commands..."

    cat > run_quick_tests.sh << 'EOF'
#!/bin/bash
# Quick test execution script
source venv/bin/activate
export TESTING=true
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db

echo "Running quick tests..."
python run_tests.py --quick
EOF

    cat > run_full_tests.sh << 'EOF'
#!/bin/bash
# Full test execution script
source venv/bin/activate
export TESTING=true
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db

echo "Running full test suite..."
python run_tests.py
EOF

    cat > run_coverage.sh << 'EOF'
#!/bin/bash
# Coverage test execution script
source venv/bin/activate
export TESTING=true
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_test_db

echo "Running tests with coverage..."
python run_tests.py --coverage
echo "Coverage report generated in htmlcov/index.html"
EOF

    chmod +x run_quick_tests.sh run_full_tests.sh run_coverage.sh

    print_success "Test execution scripts created:"
    echo "  - ./run_quick_tests.sh    (health checks + unit tests)"
    echo "  - ./run_full_tests.sh     (all tests)"
    echo "  - ./run_coverage.sh       (tests with coverage report)"
}

# Print usage instructions
print_usage() {
    print_banner "SETUP COMPLETE"

    echo "🎉 Test environment setup completed successfully!"
    echo
    echo "📋 What was configured:"
    echo "  ✅ Python environment and dependencies"
    echo "  ✅ PostgreSQL test database"
    echo "  ✅ Environment variables"
    echo "  ✅ Test directory structure"
    echo "  ✅ Test execution scripts"
    echo
    echo "🚀 How to run tests:"
    echo
    echo "  Quick tests (recommended for development):"
    echo "    ./run_quick_tests.sh"
    echo
    echo "  Full test suite:"
    echo "    ./run_full_tests.sh"
    echo
    echo "  Coverage report:"
    echo "    ./run_coverage.sh"
    echo
    echo "  Individual module tests:"
    echo "    source venv/bin/activate"
    echo "    python run_tests.py --module orders"
    echo "    python run_tests.py --module expenses"
    echo
    echo "  Direct pytest usage:"
    echo "    source venv/bin/activate"
    echo "    pytest tests/test_integration.py -v"
    echo
    echo "📊 Coverage reports will be available at:"
    echo "    htmlcov/index.html"
    echo
    echo "📖 For more information, see:"
    echo "    tests/README.md"
}

# Main execution
main() {
    print_banner "FINANCIAL SERVICE TEST SETUP"

    print_status "Starting test environment setup..."

    # Run setup steps
    check_directory
    check_python
    create_test_database
    install_dependencies
    setup_environment
    setup_test_structure
    verify_setup
    generate_commands

    print_usage
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Financial Service Test Setup Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --skip-db      Skip database setup"
        echo "  --skip-deps    Skip dependency installation"
        echo
        echo "This script will:"
        echo "  - Check Python and PostgreSQL"
        echo "  - Create test database"
        echo "  - Install Python dependencies"
        echo "  - Setup environment variables"
        echo "  - Verify test setup"
        echo "  - Generate test execution scripts"
        exit 0
        ;;
    --skip-db)
        SKIP_DB=true
        ;;
    --skip-deps)
        SKIP_DEPS=true
        ;;
esac

# Run main function
main "$@"
