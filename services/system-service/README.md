# System Service

## 📋 Overview

The System Service is a core microservice in the Travel System that manages user authentication, authorization, system settings, and administrative tools. It follows a modular architecture pattern with robust multi-tenant support and comprehensive security features.

## 🏗️ Architecture

### Modular Structure

```
system-service/
├── main.py                 # Main FastAPI application with global error handling
├── database.py            # Multi-tenant database configuration & session management
├── shared_auth.py         # JWT authentication & tenant access utilities
├── requirements.txt       # Python dependencies
│
├── common/               # Shared enums and utilities
│   ├── __init__.py
│   └── enums.py          # System-wide enums (UserRole, TaskStatus, etc.)
│
├── users/                # User management module
│   ├── __init__.py
│   ├── models.py         # User, Role, Permission, Team models
│   ├── schemas.py        # Pydantic validation schemas
│   └── endpoints.py      # User management API endpoints
│
├── settings/             # System configuration module
│   ├── __init__.py
│   ├── models.py         # Setting, AuditLog models
│   ├── schemas.py        # Configuration schemas
│   └── endpoints.py      # Settings & audit API endpoints
│
└── tools/                # Productivity tools module
    ├── __init__.py
    ├── models.py         # Note, Task, LogCall, Event, Attachment models
    ├── schemas.py        # Tool-specific validation schemas
    └── endpoints.py      # Productivity tools API endpoints
```

### Key Architectural Principles

- **Multi-Tenant Isolation**: Complete data separation using PostgreSQL schemas
- **Two-Phase Creation Pattern**: Consistent validation and insertion across all modules
- **Session Management**: Robust handling of database sessions with proper cleanup
- **Error Resilience**: Comprehensive error handling with detailed logging
- **Response Serialization**: Consistent API responses using `.to_dict()` methods

## 🚀 Features

### Users Module
- **User Management**: Complete CRUD operations with validation
- **Role-Based Access Control (RBAC)**: Hierarchical roles and permissions
- **Team Management**: Organize users into functional teams
- **Session Tracking**: Monitor active user sessions
- **API Key Management**: Generate and manage programmatic access keys
- **Password Security**: Secure reset tokens and email verification

### Settings Module
- **System Configuration**: Global and tenant-specific settings
- **Audit Logging**: Comprehensive tracking of all system changes
- **Category Management**: Organized settings by category
- **Export Capabilities**: Audit log export functionality
- **Feature Flags**: Dynamic feature enabling/disabling

### Tools Module
- **Notes Management**: Rich note-taking with assignee support
- **Task Management**: Priority-based task system with status tracking
- **Call Logging**: Customer interaction tracking with call types
- **Event Management**: Calendar events with scheduling
- **File Attachments**: Document management with multiple disk support
- **Review System**: Customer feedback and rating management
- **Carbon Footprint**: Environmental impact tracking
- **Channel Configuration**: Multi-channel communication setup

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 13+
- Redis (for caching and sessions)
- Docker & Docker Compose (recommended)

### Local Development Setup

1. **Clone and navigate:**
```bash
cd travel_system/services/system-service
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set environment variables:**
```bash
export DATABASE_URL="postgresql://postgres:postgres123@localhost:5432/multitenant_db"
export JWT_SECRET_KEY="your-secret-key-change-in-production"
export REDIS_URL="redis://localhost:6379"
export SQL_ECHO="false"
```

4. **Run the service:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8008 --reload
```

### Docker Setup

```bash
# From project root
docker-compose up -d system-service
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres123@localhost:5432/multitenant_db` | Yes |
| `JWT_SECRET_KEY` | JWT signing secret | `your-secret-key-change-in-production` | Yes |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | No |
| `SQL_ECHO` | Enable SQL query logging | `false` | No |
| `HOST` | Service bind host | `0.0.0.0` | No |
| `PORT` | Service port | `8008` | No |
| `ENVIRONMENT` | Runtime environment | `production` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Database Configuration

The service supports advanced multi-tenant database features:

- **Schema Isolation**: Each tenant gets a dedicated PostgreSQL schema
- **Connection Pooling**: Efficient connection management with SQLAlchemy
- **Transaction Safety**: Automatic rollback on errors
- **Migration Support**: Automated schema creation for new tenants

## 📡 API Endpoints

### Health & Status
```
GET  /                    # Service information
GET  /health             # Health check endpoint
GET  /readiness          # Kubernetes readiness probe
```

### Authentication
```
POST /api/v1/auth/login              # User authentication
POST /api/v1/auth/logout             # Session termination
GET  /api/v1/auth/me                 # Current user info
GET  /api/v1/auth/test               # Authentication test
POST /api/v1/auth/initialize-tenant  # Initialize tenant schema
POST /api/v1/auth/verify-tenant      # Verify tenant schema
```

### Users Module (Tenant-scoped)
```
# User Management
GET    /api/v1/tenants/{tenant_slug}/users/           # List users with pagination
POST   /api/v1/tenants/{tenant_slug}/users/           # Create new user
GET    /api/v1/tenants/{tenant_slug}/users/{user_id}  # Get user details
PUT    /api/v1/tenants/{tenant_slug}/users/{user_id}  # Update user
DELETE /api/v1/tenants/{tenant_slug}/users/{user_id}  # Delete user (soft delete)

# Role Management
GET    /api/v1/tenants/{tenant_slug}/roles/           # List roles
POST   /api/v1/tenants/{tenant_slug}/roles/           # Create role
GET    /api/v1/tenants/{tenant_slug}/roles/{role_id}  # Get role details

# Team Management
GET    /api/v1/tenants/{tenant_slug}/teams/           # List teams
POST   /api/v1/tenants/{tenant_slug}/teams/           # Create team
```

### Settings Module (Tenant-scoped)
```
GET    /api/v1/tenants/{tenant_slug}/settings/              # List settings
POST   /api/v1/tenants/{tenant_slug}/settings/              # Create setting
GET    /api/v1/tenants/{tenant_slug}/settings/{setting_id}  # Get setting
PUT    /api/v1/tenants/{tenant_slug}/settings/{setting_id}  # Update setting
DELETE /api/v1/tenants/{tenant_slug}/settings/{setting_id}  # Delete setting

# Audit Logs
GET    /api/v1/tenants/{tenant_slug}/audit-logs/            # List audit logs
GET    /api/v1/tenants/{tenant_slug}/audit-logs/export      # Export logs
```

### Tools Module (Tenant-scoped)
```
# Notes
GET    /api/v1/tenants/{tenant_slug}/tools/notes            # List notes
POST   /api/v1/tenants/{tenant_slug}/tools/notes            # Create note
GET    /api/v1/tenants/{tenant_slug}/tools/notes/{note_id}  # Get note
PUT    /api/v1/tenants/{tenant_slug}/tools/notes/{note_id}  # Update note
DELETE /api/v1/tenants/{tenant_slug}/tools/notes/{note_id}  # Delete note

# Tasks
GET    /api/v1/tenants/{tenant_slug}/tools/tasks            # List tasks
POST   /api/v1/tenants/{tenant_slug}/tools/tasks            # Create task
GET    /api/v1/tenants/{tenant_slug}/tools/tasks/{task_id}  # Get task
PUT    /api/v1/tenants/{tenant_slug}/tools/tasks/{task_id}  # Update task
DELETE /api/v1/tenants/{tenant_slug}/tools/tasks/{task_id}  # Delete task

# Log Calls
GET    /api/v1/tenants/{tenant_slug}/tools/logcalls         # List call logs
POST   /api/v1/tenants/{tenant_slug}/tools/logcalls         # Create call log
GET    /api/v1/tenants/{tenant_slug}/tools/logcalls/{id}    # Get call log

# Events
GET    /api/v1/tenants/{tenant_slug}/tools/events           # List events
POST   /api/v1/tenants/{tenant_slug}/tools/events           # Create event
GET    /api/v1/tenants/{tenant_slug}/tools/events/{id}      # Get event

# Bulk Operations
PUT    /api/v1/tenants/{tenant_slug}/tools/tasks/bulk-update  # Bulk update tasks
PUT    /api/v1/tenants/{tenant_slug}/tools/notes/bulk-update  # Bulk update notes
```

## 🔐 Authentication & Security

### JWT Authentication
The service implements secure JWT-based authentication with:

- **Access Tokens**: Short-lived tokens (30 minutes default)
- **Tenant Context**: Embedded tenant information in tokens
- **Role-Based Access**: Hierarchical permission system
- **Service Tokens**: Inter-service communication tokens

### Token Structure
```json
{
  "sub": "user_uuid",
  "email": "user@example.com", 
  "username": "username",
  "tenant_id": "tenant_uuid",
  "tenant_slug": "tenant-slug",
  "role": "tenant_admin",
  "permissions": ["users.read", "users.write"],
  "exp": 1234567890,
  "iat": 1234567890,
  "type": "access"
}
```

### Security Features
- **Tenant Isolation**: Complete data separation between tenants
- **Permission Checks**: Granular permission validation
- **SQL Injection Protection**: Parameterized queries and ORM
- **CORS Support**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive Pydantic validation

## 🏢 Multi-Tenancy

### Schema Management
The service implements advanced multi-tenant architecture:

1. **Dynamic Schema Creation**: Automatic schema provisioning for new tenants
2. **Schema Naming**: Convention-based naming `tenant_{tenant_slug}`
3. **Connection Pooling**: Efficient per-tenant connection management
4. **Data Isolation**: Complete separation at the database level

### Tenant Context
All API requests require tenant context via URL path:
```
/api/v1/tenants/{tenant_slug}/...
```

### Tenant Validation
- Automatic tenant access validation
- Cross-tenant access prevention
- Tenant schema existence verification

## 🧪 Testing

### Security Tests
The service includes comprehensive security testing:

```bash
# Run all security tests
./tests/security/system-service/run_test.sh

# Test results: 55 tests, 100% pass rate
✅ Authentication & Authorization: 19 tests
✅ CRUD Operations: 27 tests  
✅ Cross-Tenant Access Prevention: 9 tests
```

### Test Coverage Areas
- **Authentication**: Login, logout, token validation
- **CRUD Operations**: All modules (Users, Settings, Tools)
- **Multi-Tenancy**: Cross-tenant access prevention
- **Input Validation**: Schema validation and error handling
- **Database Operations**: Transaction integrity

### Running Tests
```bash
# Security tests
./tests/security/system-service/run_test.sh

# Unit tests
pytest tests/ -v

# Integration tests  
python tests/test_integration.py

# Coverage report
pytest tests/ --cov=. --cov-report=html
```

## 📊 Database Schema

### Schema Design Principles
- **Tenant Isolation**: Each tenant has a dedicated schema
- **Consistent Patterns**: Standardized table structures across modules
- **Audit Trail**: Comprehensive change tracking
- **Soft Deletes**: Recoverable deletion using `deleted_at` columns
- **Indexing**: Optimized queries with strategic indexes

### Core Tables by Module

#### Users Module
```sql
users                    # User accounts with authentication
roles                    # System and tenant roles  
permissions              # Granular access permissions
role_permissions         # Role-permission relationships
user_roles              # User role assignments
teams                   # Organizational teams
team_members            # Team membership
user_sessions           # Active session tracking
password_reset_tokens   # Secure password reset
email_verification_tokens # Email verification workflow
api_keys                # Programmatic access keys
```

#### Settings Module  
```sql
settings                # System and tenant configuration
audit_logs             # Comprehensive audit trail
```

#### Tools Module
```sql
notes                  # User notes with assignments
tasks                  # Task management with priorities
log_calls             # Customer call logging
attachments           # File management system
events                # Calendar and scheduling
carbon_footprints     # Environmental tracking
channel_configs       # Communication channels
reviews               # Customer feedback system
```

### Key Database Features
- **UUID Primary Keys**: Globally unique identifiers
- **Timestamp Tracking**: `created_at`, `updated_at`, `deleted_at`
- **Foreign Key Constraints**: Referential integrity (where appropriate)
- **Index Optimization**: Performance-tuned queries
- **JSONB Support**: Flexible metadata storage

## 🔄 Recent Improvements

### 🐛 Bug Fixes (v2.1.0)
- **Fixed DetachedInstanceError**: Resolved SQLAlchemy session issues in model `__repr__` methods
- **Eliminated TaskService**: Removed inconsistent service layer, standardized to two-phase creation pattern
- **Fixed Response Serialization**: All endpoints now return properly serialized dictionaries
- **Corrected LogCall Schema**: Fixed field name mismatch between model and response schema
- **Fixed Enum Validation**: Corrected CallStatus enum values in test data

### 🏗️ Architectural Improvements
- **Consistent Patterns**: All modules now follow identical endpoint patterns
- **Robust Session Management**: Improved database session handling with proper cleanup
- **Enhanced Error Handling**: Comprehensive error catching with detailed logging
- **Tenant Safety**: All operations use `safe_tenant_session` context manager
- **Response Standardization**: Uniform API response format across all endpoints

### 🧪 Testing Enhancements  
- **100% Test Pass Rate**: All 55 security tests now pass
- **Comprehensive Coverage**: Tests cover all CRUD operations across all modules
- **Security Validation**: Cross-tenant access prevention verified
- **Error Scenarios**: Proper error handling validation

## 📈 Performance & Monitoring

### Performance Optimizations
- **Async/Await**: Full asynchronous operation support
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Indexed queries and selective loading
- **Response Caching**: Strategic caching of frequently accessed data
- **Pagination**: Efficient large dataset handling

### Monitoring & Observability
- **Health Endpoints**: Kubernetes-compatible health checks
- **Detailed Logging**: Structured logging with correlation IDs
- **Performance Metrics**: Response time and throughput tracking
- **Error Tracking**: Comprehensive error logging and alerting
- **Database Monitoring**: Connection pool and query performance

### Scalability Features
- **Horizontal Scaling**: Stateless design for multiple instances
- **Database Scaling**: Read replica support
- **Caching Layer**: Redis integration for performance
- **Load Balancing**: Compatible with standard load balancers

## 🐳 Docker & Deployment

### Container Configuration
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8008
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8008"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  system-service:
    build: .
    ports:
      - "8008:8008"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/multitenant_db
      - JWT_SECRET_KEY=your-secret-key
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8008/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes Deployment
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: CPU and memory constraints
- **ConfigMaps**: Environment-specific configuration
- **Secrets**: Secure credential management
- **Service Mesh**: Istio compatibility

## 🚨 Error Handling

### Error Categories
- **Authentication Errors** (401): Invalid or expired tokens
- **Authorization Errors** (403): Insufficient permissions
- **Validation Errors** (422): Invalid input data
- **Not Found Errors** (404): Resource not found
- **Conflict Errors** (409): Duplicate resources
- **Server Errors** (500): Internal system errors

### Error Response Format
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-15T10:30:00Z",
  "request_id": "uuid",
  "field_errors": {
    "field_name": ["validation error message"]
  }
}
```

### Logging Strategy
- **Structured Logging**: JSON format for log aggregation
- **Correlation IDs**: Request tracking across services
- **Error Context**: Full error context and stack traces
- **Security Events**: Authentication and authorization logging

## 📝 API Documentation

### Interactive Documentation
- **Swagger UI**: Available at `/docs`
- **ReDoc**: Available at `/redoc`
- **OpenAPI Spec**: Available at `/openapi.json`

### Request/Response Examples
All endpoints include comprehensive examples in the interactive documentation, including:
- Request payload examples
- Response format examples  
- Error response examples
- Authentication requirements

## 🤝 Development Guidelines

### Code Standards
- **Python Style**: Follow PEP 8 with Black formatter
- **Type Hints**: Use type annotations throughout
- **Docstrings**: Document all functions and classes
- **Error Handling**: Implement comprehensive error handling
- **Testing**: Write tests for all new features

### Module Development Pattern
1. **Models**: Define SQLAlchemy models with proper relationships
2. **Schemas**: Create Pydantic schemas for validation
3. **Endpoints**: Implement endpoints using two-phase creation pattern
4. **Tests**: Write comprehensive tests including security tests
5. **Documentation**: Update API documentation

### Git Workflow
1. Create feature branch from `main`
2. Implement changes following coding standards
3. Run all tests locally
4. Update documentation
5. Submit pull request with detailed description

## 📞 Support & Troubleshooting

### Common Issues
- **Database Connection**: Check `DATABASE_URL` format and connectivity
- **JWT Errors**: Verify `JWT_SECRET_KEY` configuration
- **Tenant Access**: Ensure proper tenant slug in URL path
- **Permission Errors**: Verify user roles and permissions

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
export SQL_ECHO=true
```

### Health Checks
Monitor service health:
```bash
curl http://localhost:8008/health
curl http://localhost:8008/readiness
```

---

**Version**: 2.1.0  
**Last Updated**: January 15, 2025  
**Status**: Production Ready  
**Security Tests**: ✅ 55/55 Passing (100%)