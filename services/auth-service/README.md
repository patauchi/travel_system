# Authentication Service

Multi-tenant authentication service built with FastAPI, PostgreSQL, and Redis.

## Features

- **Multi-tenant Architecture**: Supports both shared and isolated user models
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Role-Based Access Control**: Support for super_admin, tenant_admin, and tenant_user roles
- **Redis Session Management**: Fast session storage and token blacklisting
- **Password Security**: Bcrypt hashing with configurable strength
- **Tenant Isolation**: Complete data isolation between tenants

## API Endpoints

### Public Endpoints

#### POST `/api/v1/auth/register`
Register a new user (super admin or tenant user).

#### POST `/api/v1/auth/login`
Authenticate user and receive JWT tokens.
- Supports multi-tenant login via query parameter: `?tenant=<tenant_slug>`
- Returns access and refresh tokens

#### POST `/api/v1/auth/refresh`
Refresh access token using refresh token.

### Protected Endpoints

#### GET `/api/v1/auth/me`
Get current user information.
- Requires valid JWT token
- For tenant users, include tenant context: `?tenant=<tenant_slug>`

#### POST `/api/v1/auth/logout`
Logout and invalidate current session.

#### POST `/api/v1/auth/change-password`
Change user password.

#### POST `/api/v1/auth/reset-password-request`
Request password reset token.

#### POST `/api/v1/auth/reset-password`
Reset password using token.

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/dbname

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service
ENVIRONMENT=development
SERVICE_NAME=auth-service
```

## Project Structure

```
auth-service/
├── main.py                 # FastAPI application and endpoints
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── database.py            # Database connection and session
├── utils.py               # Authentication utilities
├── tenant_context.py      # Multi-tenant context management
├── exceptions.py          # Custom exceptions
├── requirements.txt       # Python dependencies
└── Dockerfile            # Container configuration
```

## Multi-Tenancy

The service supports three ways to specify tenant context:

1. **Subdomain**: `tenant1.example.com`
2. **Header**: `X-Tenant-Slug: tenant1`
3. **Query Parameter**: `?tenant=tenant1`

## Database Schema

### Shared Schema (`shared.`)
- `users` - System administrators
- `tenants` - Tenant organizations
- `tenant_users` - Tenant-user associations
- `api_keys` - API key management
- `audit_logs` - System audit logs

### Tenant Schema (`tenant_<slug>.`)
- `users` - Tenant-specific users
- `roles` - Tenant-specific roles
- `user_roles` - User-role associations

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://...
export REDIS_URL=redis://...
export SECRET_KEY=...

# Run the service
uvicorn main:app --reload --port 8001
```

### Running Tests

```bash
# Run unit tests
pytest tests/

# Run integration tests
python tests/test_auth.py
```

## Docker

### Build Image

```bash
docker build -t auth-service .
```

### Run Container

```bash
docker run -p 8001:8001 \
  -e DATABASE_URL=... \
  -e REDIS_URL=... \
  -e SECRET_KEY=... \
  auth-service
```

## Security Considerations

- Passwords are hashed using bcrypt with salt
- JWT tokens include expiration and type claims
- Failed login attempts are tracked and accounts can be locked
- Token blacklisting on logout
- SQL injection prevention via parameterized queries
- CORS configuration for production environments

## Performance Optimizations

- Redis caching for sessions and frequently accessed data
- Connection pooling for database
- Async/await for non-blocking I/O
- Indexed database columns for faster queries

## Monitoring

The service exposes health check endpoints:
- `/health` - Basic health check
- `/health/ready` - Readiness probe (checks DB and Redis)
- `/health/live` - Liveness probe

## License

Proprietary - All rights reserved