#!/bin/bash

# Quick Start Script for Multi-tenant Platform
# This script sets up and starts the entire platform

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# Clean up existing containers and volumes
cleanup() {
    print_step "Cleaning up existing containers and volumes..."

    if [ "$1" == "--clean" ] || [ "$1" == "-c" ]; then
        docker-compose down -v &> /dev/null || true
        print_success "Cleaned up existing containers and volumes"
    else
        docker-compose down &> /dev/null || true
        print_success "Stopped existing containers (volumes preserved)"
    fi
}

# Create necessary directories
create_directories() {
    print_step "Creating necessary directories..."

    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/rabbitmq

    print_success "Directories created"
}

# Create environment file if it doesn't exist
setup_environment() {
    print_step "Setting up environment..."

    if [ ! -f .env ]; then
        cat > .env << 'EOF'
# Database
POSTGRES_DB=multitenant_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/multitenant_db

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# RabbitMQ
RABBITMQ_DEFAULT_USER=admin
RABBITMQ_DEFAULT_PASS=admin123
RABBITMQ_URL=amqp://admin:admin123@rabbitmq:5672/

# JWT
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8001
TENANT_SERVICE_URL=http://tenant-service:8002
BUSINESS_SERVICE_URL=http://business-service:8003
SYSTEM_SERVICE_URL=http://system-service:8004
API_GATEWAY_URL=http://api-gateway:8000

# Environment
ENVIRONMENT=development
DEBUG=true

# Frontend
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000

# Celery
CELERY_BROKER_URL=amqp://admin:admin123@rabbitmq:5672/
CELERY_RESULT_BACKEND=redis://redis:6379/1
EOF
        print_success "Environment file created"
        print_warning "Please update the SECRET_KEY in .env for production use"
    else
        print_success "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_step "Building Docker images..."

    docker-compose build --parallel

    print_success "Docker images built"
}

# Start services
start_services() {
    print_step "Starting services..."

    # Start infrastructure services first
    docker-compose up -d postgres redis rabbitmq

    print_step "Waiting for infrastructure services to be ready..."
    sleep 10

    # Start application services
    docker-compose up -d

    print_success "All services started"
}

# Wait for services to be healthy
wait_for_health() {
    print_step "Waiting for services to be healthy..."

    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "unhealthy"; then
            echo -n "."
            sleep 2
            ((attempt++))
        else
            echo ""
            print_success "All services are healthy"
            return 0
        fi
    done

    echo ""
    print_warning "Some services may not be fully healthy"
}

# Initialize database
initialize_database() {
    print_step "Initializing database..."

    # Wait a bit for services to stabilize
    sleep 5

    # Run initialization script
    docker-compose exec -T auth-service python /app/scripts/init_admin.py 2>/dev/null || {
        print_warning "Database initialization skipped or already initialized"
    }

    print_success "Database initialization complete"
}

# Show service status
show_status() {
    print_step "Service Status:"
    echo ""
    docker-compose ps
    echo ""

    print_step "Service URLs:"
    echo "  Frontend:        http://localhost:3000"
    echo "  API Gateway:     http://localhost:8000"
    echo "  Auth Service:    http://localhost:8001"
    echo "  Tenant Service:  http://localhost:8002"
    echo "  Business Service: http://localhost:8003"
    echo "  System Service:  http://localhost:8004"
    echo "  RabbitMQ Admin:  http://localhost:15672 (admin/admin123)"
    echo "  Flower (Celery): http://localhost:5555"
    echo ""

    print_step "Default Credentials:"
    echo "  Super Admin: admin / Admin123!"
    echo "  Demo Admin:  demo_admin / Demo123!"
    echo "  Demo User:   demo_user / User123!"
    echo "  ACME Admin:  acme_admin / Acme123!"
    echo ""
}

# Show logs
show_logs() {
    if [ "$1" == "--logs" ] || [ "$1" == "-l" ]; then
        print_step "Showing logs (press Ctrl+C to exit)..."
        docker-compose logs -f
    fi
}

# Main execution
main() {
    echo ""
    echo "======================================"
    echo "  Multi-tenant Platform Quick Start"
    echo "======================================"
    echo ""

    # Parse arguments
    CLEAN_FLAG=""
    LOGS_FLAG=""

    for arg in "$@"; do
        case $arg in
            --clean|-c)
                CLEAN_FLAG="--clean"
                ;;
            --logs|-l)
                LOGS_FLAG="--logs"
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --clean, -c    Clean up volumes before starting (fresh start)"
                echo "  --logs, -l     Show logs after starting"
                echo "  --help, -h     Show this help message"
                echo ""
                exit 0
                ;;
        esac
    done

    # Execute steps
    check_prerequisites
    cleanup $CLEAN_FLAG
    create_directories
    setup_environment
    build_images
    start_services
    wait_for_health

    if [ "$CLEAN_FLAG" == "--clean" ]; then
        initialize_database
    fi

    show_status

    print_success "Platform is ready!"
    echo ""

    show_logs $LOGS_FLAG
}

# Run main function
main "$@"
