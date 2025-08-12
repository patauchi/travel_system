# Multi-Tenant SaaS Platform

A production-ready multi-tenant SaaS platform built with microservices architecture, featuring complete tenant isolation, JWT authentication, and scalable infrastructure.

## 🚀 Features

- **Multi-Tenant Architecture**: Complete data isolation between tenants with separate PostgreSQL schemas
- **Microservices Design**: Modular services for authentication, tenant management, business logic, and system operations
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-Based Access Control**: Hierarchical roles (super_admin, tenant_admin, tenant_user)
- **API Gateway**: Centralized routing and request handling
- **Async Task Processing**: Celery workers for background jobs
- **Real-time Monitoring**: RabbitMQ and Flower for task monitoring
- **Container Orchestration**: Docker and Docker Compose for easy deployment
- **React Frontend**: Modern responsive UI with Material-UI

## 📁 Project Structure

```
multitenant-platform/
├── docs/                      # Documentation
│   ├── DATABASE_STRUCTURE.md  # Database schema documentation
│   ├── TENANT_ACCESS_SYSTEM.md # Tenant access system design
│   └── USER_MODEL_REDESIGN.md  # User model architecture
├── frontend/                  # React frontend application
│   ├── public/               # Static assets
│   └── src/                  # React source code
├── infrastructure/           # Infrastructure configuration
│   ├── nginx/               # Nginx configuration
│   ├── postgres/            # PostgreSQL initialization scripts
│   └── redis/               # Redis configuration
├── services/                 # Microservices
│   ├── api-gateway/         # API Gateway service
│   ├── auth-service/        # Authentication service
│   ├── business-service/    # Business logic service
│   ├── system-service/      # System management service
│   └── tenant-service/      # Tenant management service
├── scripts/                  # Utility scripts
│   ├── init_admin.py        # Initialize admin user
│   ├── quick_start.sh       # Quick start script
│   ├── init.sh             # Initial setup script
│   └── test_multitenant_flow.sh # Test multi-tenant flow
├── tests/                    # Test suites
│   └── test_auth.py         # Authentication tests
├── storage/                  # File storage
│   ├── archive/             # Archived files
│   ├── backups/             # Database backups
│   └── tenants/             # Tenant-specific storage
├── logs/                     # Application logs
├── docker-compose.yml        # Docker Compose configuration
├── Makefile                  # Common commands
└── README.md                # This file
```

## 🛠️ Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Primary database with multi-schema support
- **Redis**: Session storage and caching
- **RabbitMQ**: Message broker for async tasks
- **Celery**: Distributed task queue
- **SQLAlchemy**: ORM and database toolkit
- **Alembic**: Database migration tool

### Frontend
- **React**: UI framework
- **Material-UI**: Component library
- **React Router**: Client-side routing
- **Axios**: HTTP client

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy and static file serving

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Make (optional, for using Makefile commands)
- 8GB+ RAM recommended

### Using Make (Recommended)

```bash
# Show all available commands
make help

# Quick start with clean database
make reset

# Start all services
make up

# View logs
make logs

# Run tests
make test
```

### Using Scripts

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Quick start with all services
./scripts/quick_start.sh --clean

# Follow logs
./scripts/quick_start.sh --logs
```

### Manual Setup

```bash
# Build and start all services
docker-compose build
docker-compose up -d

# Initialize database
docker-compose exec auth-service python scripts/init_admin.py

# Check service health
docker-compose ps
```

## 📝 Default Credentials

### Super Admin
- Username: `admin`
- Password: `Admin123!`

### Demo Tenant
- Admin: `demo_admin` / `Demo123!`
- User: `demo_user` / `User123!`

### ACME Tenant
- Admin: `acme_admin` / `Acme123!`
- User: `acme_user` / `Acme123!`

### RabbitMQ Management
- URL: http://localhost:15672
- Username: `admin`
- Password: `admin123`

## 🔗 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| API Gateway | http://localhost:8000 | Central API endpoint |
| Auth Service | http://localhost:8001 | Authentication API |
| Tenant Service | http://localhost:8002 | Tenant management API |
| Business Service | http://localhost:8003 | Business logic API |
| System Service | http://localhost:8004 | System management API |
| RabbitMQ Admin | http://localhost:15672 | Message broker UI |
| Flower | http://localhost:5555 | Celery monitoring |

## 📚 API Documentation

Each service provides interactive API documentation:

- Auth Service: http://localhost:8001/docs
- Tenant Service: http://localhost:8002/docs
- Business Service: http://localhost:8003/docs
- System Service: http://localhost:8004/docs
- API Gateway: http://localhost:8000/docs

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Run Specific Tests
```bash
# Authentication tests
make test-auth

# Integration tests
make test-integration

# Unit tests
make test-unit
```

### Manual Testing
```bash
# Test authentication flow
python tests/test_auth.py

# Test multi-tenant flow
./scripts/test_multitenant_flow.sh
```

## 🔧 Development

### Accessing Service Shells
```bash
# Auth service shell
make shell-auth

# Database shell
make db-shell

# Redis CLI
make shell-redis
```

### Database Management
```bash
# Backup database
make db-backup

# Restore from backup
make db-restore FILE=backups/backup_20240101_120000.sql.gz

# Run migrations
make migrate
```

### Code Quality
```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check
```

## 🏗️ Architecture

### Multi-Tenancy Model
- **Shared Database, Separate Schemas**: Each tenant has an isolated PostgreSQL schema
- **Tenant Detection**: Via subdomain, header, or query parameter
- **Data Isolation**: Complete separation of tenant data
- **Resource Limits**: Configurable per-tenant limits

### Service Communication
- **Synchronous**: REST APIs via HTTP
- **Asynchronous**: Message queues via RabbitMQ
- **Caching**: Redis for session and data caching

### Security
- **JWT Tokens**: Short-lived access tokens with refresh mechanism
- **Password Hashing**: Bcrypt with configurable rounds
- **Rate Limiting**: API endpoint protection
- **CORS**: Configurable cross-origin policies

## 📈 Monitoring

### Service Health
```bash
# Check all services
make health

# View resource usage
make stats
```

### Logs
```bash
# All services
make logs

# Specific service
make logs-auth
make logs-tenant
```

### Task Monitoring
- Flower UI: http://localhost:5555
- RabbitMQ Management: http://localhost:15672

## 🚀 Deployment

### Production Considerations
1. Update `SECRET_KEY` in environment variables
2. Configure proper database credentials
3. Set up SSL/TLS certificates
4. Configure backup strategies
5. Implement monitoring and alerting
6. Set resource limits for containers
7. Configure log aggregation

### Environment Variables
Create a `.env` file with production values:

```env
ENVIRONMENT=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://redis:6379/0
# ... other configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📝 License

Proprietary - All rights reserved

## 📞 Support

For issues and questions, please create an issue in the repository.

---

Built with ❤️ using FastAPI, React, and Docker