# System Service

## 📋 Overview

The System Service is a core microservice in the Travel System that manages user authentication, authorization, system settings, and administrative tools. It follows a modular architecture pattern for better maintainability and scalability.

## 🏗️ Architecture

### Modular Structure

```
system-service/
├── main.py                 # Main FastAPI application
├── database.py            # Async database configuration
├── dependencies.py        # Shared dependencies
├── shared_auth.py         # Authentication utilities
├── shared_models.py       # Base SQLAlchemy models
├── requirements.txt       # Python dependencies
│
├── common/               # Shared enums and utilities
│   ├── __init__.py
│   └── enums.py          # System-wide enums
│
├── users/                # User management module
│   ├── __init__.py
│   ├── models.py         # User, Role, Permission models
│   ├── schemas.py        # Pydantic schemas
│   └── endpoints.py      # User-related API endpoints
│
├── settings/             # System settings module
│   ├── __init__.py
│   ├── models.py         # Setting, AuditLog models
│   ├── schemas.py        # Pydantic schemas
│   └── endpoints.py      # Settings API endpoints
│
└── tools/                # Administrative tools module
    ├── __init__.py
    ├── models.py         # Note, Task, LogCall models
    ├── schemas.py        # Pydantic schemas
    └── endpoints.py      # Tools API endpoints
```

## 🚀 Features

### Users Module
- **User Management**: Create, read, update, delete users
- **Role-Based Access Control (RBAC)**: Manage roles and permissions
- **Team Management**: Organize users into teams
- **Session Management**: Track and manage user sessions
- **API Keys**: Generate and manage API keys for programmatic access
- **Password Management**: Reset tokens, email verification

### Settings Module
- **System Configuration**: Manage system-wide settings
- **Audit Logging**: Track all system changes and user actions
- **Tenant Settings**: Configure tenant-specific settings
- **Feature Flags**: Enable/disable features dynamically

### Tools Module
- **Notes**: Create and manage notes
- **Tasks**: Task management with priorities and statuses
- **Call Logs**: Track customer interactions
- **Attachments**: File management
- **Events**: Calendar and event management
- **Reviews**: Customer feedback management

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis (optional, for caching)

### Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/multitenant_db"
export SECRET_KEY="your-secret-key-change-in-production"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

3. **Run the service:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8008 --reload
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres123@localhost:5432/multitenant_db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-change-in-production` |
| `REDIS_HOST` | Redis host | `localhost` |
| `REDIS_PORT` | Redis port | `6379` |
| `SQL_ECHO` | Enable SQL query logging | `false` |
| `HOST` | Service host | `0.0.0.0` |
| `PORT` | Service port | `8008` |
| `ENVIRONMENT` | Environment (development/production) | `production` |

## 📡 API Endpoints

### Health Check
- `GET /` - Service information
- `GET /health` - Health check
- `GET /readiness` - Kubernetes readiness probe

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/test` - Test authentication
- `POST /api/v1/auth/initialize-tenant` - Initialize tenant schema
- `POST /api/v1/auth/verify-tenant` - Verify tenant schema

### Users Module
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users/roles` - List roles
- `POST /api/v1/users/roles` - Create role
- `GET /api/v1/users/permissions` - List permissions
- `GET /api/v1/users/teams` - List teams
- `POST /api/v1/users/teams` - Create team

### Settings Module
- `GET /api/v1/settings` - List settings
- `POST /api/v1/settings` - Create setting
- `GET /api/v1/settings/{key}` - Get setting by key
- `PUT /api/v1/settings/{key}` - Update setting
- `DELETE /api/v1/settings/{key}` - Delete setting
- `GET /api/v1/settings/audit-logs` - List audit logs
- `GET /api/v1/settings/audit-logs/export` - Export audit logs

### Tools Module
- `GET /api/v1/tools/notes` - List notes
- `POST /api/v1/tools/notes` - Create note
- `GET /api/v1/tools/tasks` - List tasks
- `POST /api/v1/tools/tasks` - Create task
- `PUT /api/v1/tools/tasks/{task_id}` - Update task
- `GET /api/v1/tools/calls` - List call logs
- `POST /api/v1/tools/calls` - Log call

## 🔐 Authentication

The service uses JWT-based authentication with support for:
- Access tokens (short-lived)
- Refresh tokens (long-lived)
- Multi-tenant isolation
- Role-based permissions
- API key authentication

### Token Structure
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "username": "username",
  "tenant_id": "tenant_123",
  "exp": 1234567890,
  "iat": 1234567890,
  "jti": "unique_token_id"
}
```

## 🏢 Multi-Tenancy

The service supports full multi-tenant isolation using PostgreSQL schemas:

1. **Schema Naming**: Each tenant has a dedicated schema named `tenant_{tenant_id}`
2. **Data Isolation**: Complete data isolation between tenants
3. **Dynamic Schema Creation**: Automatic schema creation for new tenants
4. **Tenant Context**: All requests include tenant context via headers

### Tenant Header
```
X-Tenant-ID: tenant_123
```

## 🧪 Testing

### Run Tests
```bash
pytest tests/ -v
```

### Test Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Integration Tests
```bash
python tests/test_integration.py
```

## 📊 Database Schema

### Core Tables

#### Users Module
- `users` - User accounts
- `roles` - User roles
- `permissions` - Granular permissions
- `role_permissions` - Role-permission mappings
- `user_roles` - User-role assignments
- `user_permissions` - Direct user permissions
- `teams` - Organizational teams
- `team_members` - Team membership
- `user_sessions` - Active sessions
- `password_reset_tokens` - Password reset tokens
- `email_verification_tokens` - Email verification
- `api_keys` - API keys for programmatic access

#### Settings Module
- `settings` - System and tenant settings
- `audit_logs` - Audit trail of all actions

#### Tools Module
- `notes` - User notes
- `tasks` - Task management
- `log_calls` - Call logging
- `attachments` - File attachments
- `events` - Calendar events
- `reviews` - Customer reviews

## 🔄 Migration Guide

To migrate from a monolithic structure to this modular pattern:

1. **Backup existing data**
2. **Create module directories**
3. **Move models to respective modules**
4. **Update imports in endpoints**
5. **Test each module independently**
6. **Update main application**

See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) for detailed instructions.

## 🚨 Error Handling

The service implements comprehensive error handling:

- **HTTP Exceptions**: Proper status codes and messages
- **Database Errors**: Transaction rollback and logging
- **Authentication Errors**: Clear security messages
- **Validation Errors**: Detailed field-level errors

## 📈 Performance

### Optimizations
- **Async Operations**: Full async/await support
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Indexed queries and eager loading
- **Caching**: Redis caching for frequently accessed data
- **Pagination**: Efficient data pagination

### Monitoring
- Health check endpoints
- Detailed logging
- Performance metrics
- Database connection monitoring

## 🐳 Docker Support

### Build Image
```bash
docker build -t system-service:latest .
```

### Run Container
```bash
docker run -d \
  -p 8008:8008 \
  -e DATABASE_URL="postgresql://postgres:password@db:5432/multitenant_db" \
  -e SECRET_KEY="your-secret-key" \
  --name system-service \
  system-service:latest
```

## 📝 License

This service is part of the Travel System platform.

## 🤝 Contributing

1. Follow the modular pattern
2. Write tests for new features
3. Update documentation
4. Submit pull requests

## 📞 Support

For issues or questions, please contact the development team.

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Status**: Production Ready