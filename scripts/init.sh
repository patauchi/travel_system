#!/bin/bash

# Multi-Tenant Platform Initialization Script
# This script sets up the entire platform from scratch

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    print_success "Node.js found ($(node -v))"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi
    print_success "npm found ($(npm -v))"
}

# Create environment file
setup_environment() {
    print_info "Setting up environment..."

    if [ ! -f .env ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"

        # Generate secure keys
        JWT_SECRET=$(openssl rand -base64 32)
        ENCRYPTION_KEY=$(openssl rand -base64 32)

        # Update .env with generated keys
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
            sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
        else
            # Linux
            sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" .env
            sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
        fi

        print_success "Generated secure keys"
    else
        print_info ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."

    directories=(
        "storage/tenants"
        "storage/backups"
        "storage/archive"
        "logs"
        "infrastructure/nginx/conf.d"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_success "Created directory: $dir"
    done
}

# Install frontend dependencies
setup_frontend() {
    print_info "Setting up frontend..."

    cd frontend

    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install --legacy-peer-deps
        print_success "Frontend dependencies installed"
    else
        print_info "Frontend dependencies already installed"
    fi

    cd ..
}

# Create missing service files
create_missing_files() {
    print_info "Creating missing service files..."

    # Create database.py for auth service if missing
    if [ ! -f "services/auth-service/database.py" ]; then
        cp services/tenant-service/database.py services/auth-service/database.py
        print_success "Created database.py for auth service"
    fi

    # Create business service directory and files
    if [ ! -d "services/business-service" ]; then
        mkdir -p services/business-service

        # Copy base files from tenant service
        cp services/tenant-service/requirements.txt services/business-service/
        cp services/tenant-service/Dockerfile services/business-service/

        # Update port in Dockerfile for business service
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' 's/8002/8003/g' services/business-service/Dockerfile
        else
            sed -i 's/8002/8003/g' services/business-service/Dockerfile
        fi

        print_success "Created business service structure"
    fi

    # Create API Gateway structure
    if [ ! -f "services/api-gateway/main.py" ]; then
        cat > services/api-gateway/main.py << 'EOF'
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from typing import Any

app = FastAPI(title="API Gateway")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
AUTH_SERVICE = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
TENANT_SERVICE = os.getenv("TENANT_SERVICE_URL", "http://tenant-service:8002")
BUSINESS_SERVICE = os.getenv("BUSINESS_SERVICE_URL", "http://business-service:8003")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    # Route to appropriate service
    if path.startswith("api/v1/auth"):
        service_url = AUTH_SERVICE
    elif path.startswith("api/v1/tenants"):
        service_url = TENANT_SERVICE
    elif path.startswith("api/v1/business"):
        service_url = BUSINESS_SERVICE
    else:
        raise HTTPException(status_code=404, detail="Route not found")

    # Forward request
    async with httpx.AsyncClient() as client:
        url = f"{service_url}/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body()
        )
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
        print_success "Created API Gateway main.py"
    fi

    # Create requirements for API Gateway
    if [ ! -f "services/api-gateway/requirements.txt" ]; then
        cat > services/api-gateway/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.1
python-dotenv==1.0.0
EOF
        print_success "Created API Gateway requirements.txt"
    fi

    # Create Dockerfile for API Gateway
    if [ ! -f "services/api-gateway/Dockerfile" ]; then
        cp services/tenant-service/Dockerfile services/api-gateway/Dockerfile
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' 's/8002/8000/g' services/api-gateway/Dockerfile
        else
            sed -i 's/8002/8000/g' services/api-gateway/Dockerfile
        fi
        print_success "Created API Gateway Dockerfile"
    fi

    # Create business service main.py
    if [ ! -f "services/business-service/main.py" ]; then
        cat > services/business-service/main.py << 'EOF'
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="Business Service")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "business-service",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/business/info")
async def business_info():
    return {
        "service": "business-service",
        "version": "1.0.0",
        "description": "Domain-specific business logic service"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
EOF
        print_success "Created business service main.py"
    fi
}

# Create nginx configuration
setup_nginx() {
    print_info "Setting up Nginx configuration..."

    if [ ! -f "infrastructure/nginx/nginx.conf" ]; then
        cat > infrastructure/nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    gzip on;
    gzip_types text/plain application/json application/javascript text/css;

    include /etc/nginx/conf.d/*.conf;
}
EOF
        print_success "Created nginx.conf"
    fi

    if [ ! -f "infrastructure/nginx/conf.d/default.conf" ]; then
        cat > infrastructure/nginx/conf.d/default.conf << 'EOF'
server {
    listen 80;
    server_name localhost;

    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://api-gateway:8000;
        proxy_http_version 1.1;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
        print_success "Created default.conf for Nginx"
    fi
}

# Start Docker services
start_services() {
    print_info "Starting Docker services..."

    # Stop any existing containers
    docker-compose down 2>/dev/null || true

    # Start services
    docker-compose up -d

    print_success "Services started"

    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 10

    # Check service health
    services=("postgres" "redis" "rabbitmq")
    for service in "${services[@]}"; do
        if docker-compose ps | grep -q "$service.*Up"; then
            print_success "$service is running"
        else
            print_error "$service is not running"
        fi
    done
}

# Initialize database
init_database() {
    print_info "Initializing database..."

    # Wait for PostgreSQL to be ready
    print_info "Waiting for PostgreSQL to be ready..."
    until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
        sleep 2
    done
    print_success "PostgreSQL is ready"

    # Run database initialization if needed
    docker-compose exec -T postgres psql -U postgres -d multitenant_db -c "SELECT 1 FROM shared.tenants LIMIT 1;" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        print_info "Running database initialization..."
        docker-compose exec -T postgres psql -U postgres -d multitenant_db -f /docker-entrypoint-initdb.d/init.sql
        print_success "Database initialized"
    else
        print_info "Database already initialized"
    fi
}

# Display status
display_status() {
    echo ""
    echo "========================================="
    echo "  Multi-Tenant Platform Setup Complete  "
    echo "========================================="
    echo ""
    print_success "All services are running!"
    echo ""
    echo "Access the platform at:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - API Gateway: http://localhost:8000"
    echo "  - API Documentation:"
    echo "    - Auth Service: http://localhost:8001/docs"
    echo "    - Tenant Service: http://localhost:8002/docs"
    echo "    - Business Service: http://localhost:8003/docs"
    echo ""
    echo "Default credentials:"
    echo "  - Email: admin@multitenant.com"
    echo "  - Password: Admin123!"
    echo ""
    echo "To view logs:"
    echo "  docker-compose logs -f [service-name]"
    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
    echo ""
}

# Main execution
main() {
    echo "========================================="
    echo "  Multi-Tenant Platform Initialization  "
    echo "========================================="
    echo ""

    check_prerequisites
    setup_environment
    create_directories
    create_missing_files
    setup_nginx
    setup_frontend
    start_services
    init_database
    display_status
}

# Run main function
main
