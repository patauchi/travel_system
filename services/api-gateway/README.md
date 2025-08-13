# API Gateway Service

Central API Gateway for the Multi-Tenant Travel Management Platform. This service acts as the single entry point for all client requests, routing them to the appropriate microservices.

## Overview

The API Gateway provides:
- Unified entry point for all microservices
- Request routing and proxying
- Service health monitoring
- Cross-Origin Resource Sharing (CORS) support
- Service discovery and load balancing preparation
- JWT token validation and forwarding

## Service URLs and Ports

| Service | Internal URL | Port | Base Path |
|---------|-------------|------|-----------|
| API Gateway | http://api-gateway:8000 | 8000 | / |
| Auth Service | http://auth-service:8001 | 8001 | /api/v1/auth |
| Tenant Service | http://tenant-service:8002 | 8002 | /api/v1/tenants |
| Booking Operations Service | http://booking-operations-service:8004 | 8004 | /api/v1/bookings |
| Communication Service | http://communication-service:8005 | 8005 | /api/v1/communications |
| CRM Service | http://crm-service:8006 | 8006 | /api/v1/crm |
| Financial Service | http://financial-service:8007 | 8007 | /api/v1/financial |
| System Service | http://system-service:8008 | 8008 | /api/v1/system |

## API Endpoints

### Gateway Management

#### Root Endpoint
- **GET** `/` - API Gateway information and available endpoints

#### Health Check
- **GET** `/health` - Gateway and all services health status

#### Services Status
- **GET** `/api/v1/services/status` - Detailed status of all microservices

### Authentication Service Routes
- **Base Path**: `/api/v1/auth`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all authentication-related requests to the Auth Service
- Examples:
  - `POST /api/v1/auth/login` - User login
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/refresh` - Token refresh
  - `GET /api/v1/auth/me` - Current user info

### Tenant Management Routes
- **Base Path**: `/api/v1/tenants`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all tenant-related requests to the Tenant Service
- Examples:
  - `GET /api/v1/tenants` - List tenants
  - `POST /api/v1/tenants` - Create tenant
  - `GET /api/v1/tenants/{id}` - Get tenant details
  - `PUT /api/v1/tenants/{id}` - Update tenant

### Booking Operations Routes
- **Base Path**: `/api/v1/bookings`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all booking-related requests to the Booking Operations Service
- Examples:
  - `GET /api/v1/bookings` - List bookings
  - `POST /api/v1/bookings` - Create booking
  - `GET /api/v1/bookings/{id}` - Get booking details
  - `PUT /api/v1/bookings/{id}/status` - Update booking status
  - `POST /api/v1/bookings/{id}/cancel` - Cancel booking

### Communication Service Routes
- **Base Path**: `/api/v1/communications`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all communication requests to the Communication Service
- Examples:
  - `POST /api/v1/communications/emails` - Send email
  - `POST /api/v1/communications/sms` - Send SMS
  - `GET /api/v1/communications/templates` - List templates
  - `POST /api/v1/communications/notifications` - Send notification

### CRM Service Routes
- **Base Path**: `/api/v1/crm`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all CRM-related requests to the CRM Service
- Examples:
  - `GET /api/v1/crm/customers` - List customers
  - `POST /api/v1/crm/customers` - Create customer
  - `GET /api/v1/crm/customers/{id}` - Get customer details
  - `POST /api/v1/crm/leads` - Create lead
  - `GET /api/v1/crm/analytics` - CRM analytics

### Financial Service Routes
- **Base Path**: `/api/v1/financial`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all financial requests to the Financial Service
- Examples:
  - `GET /api/v1/financial/transactions` - List transactions
  - `POST /api/v1/financial/payments` - Process payment
  - `GET /api/v1/financial/invoices` - List invoices
  - `POST /api/v1/financial/refunds` - Process refund
  - `GET /api/v1/financial/reports` - Financial reports

### System Service Routes
- **Base Path**: `/api/v1/system`
- **All Methods**: GET, POST, PUT, DELETE, PATCH
- Routes all system management requests to the System Service
- Examples:
  - `GET /api/v1/system/users` - List system users
  - `POST /api/v1/system/users` - Create user
  - `GET /api/v1/system/settings` - System settings
  - `PUT /api/v1/system/configuration` - Update configuration
  - `GET /api/v1/system/audit-logs` - Audit logs

## Environment Variables

```bash
# Service URLs
AUTH_SERVICE_URL=http://auth-service:8001
TENANT_SERVICE_URL=http://tenant-service:8002
BOOKING_SERVICE_URL=http://booking-operations-service:8004
COMMUNICATION_SERVICE_URL=http://communication-service:8005
CRM_SERVICE_URL=http://crm-service:8006
FINANCIAL_SERVICE_URL=http://financial-service:8007
SYSTEM_SERVICE_URL=http://system-service:8008

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Redis Cache
REDIS_URL=redis://redis:6379

# Environment
ENVIRONMENT=development
```

## Running the Service

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run with hot reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker
```bash
# Build and run all services
docker-compose up api-gateway

# Or run individually
docker build -t api-gateway .
docker run -p 8000:8000 api-gateway
```

## API Documentation

Once the service is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Request Flow

1. Client sends request to API Gateway
2. Gateway validates request headers and authentication (if required)
3. Gateway determines target service based on path
4. Request is proxied to appropriate microservice
5. Response is returned to client through gateway

## Error Handling

The gateway handles various error scenarios:
- **503 Service Unavailable**: When target service is down
- **504 Gateway Timeout**: When target service doesn't respond in time
- **404 Not Found**: When route doesn't exist
- **401 Unauthorized**: When authentication fails
- **500 Internal Server Error**: For unexpected errors

## Security Features

- JWT token validation
- Service-to-service authentication tokens
- CORS configuration
- Request/Response header filtering
- Rate limiting preparation

## Health Monitoring

The gateway monitors health of all connected services:

```bash
# Check gateway and all services health
curl http://localhost:8000/health

# Response example:
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": [
    {"name": "auth-service", "status": "healthy", "url": "http://auth-service:8001"},
    {"name": "tenant-service", "status": "healthy", "url": "http://tenant-service:8002"},
    {"name": "booking-operations-service", "status": "healthy", "url": "http://booking-operations-service:8004"},
    ...
  ]
}
```

## Development Guidelines

1. **Adding New Services**:
   - Add service URL to environment variables
   - Create proxy routes in main.py
   - Update health check monitoring
   - Document new endpoints in README

2. **Modifying Routes**:
   - Keep consistent URL patterns (/api/v1/{service})
   - Maintain backward compatibility
   - Update documentation

3. **Error Handling**:
   - Log all errors with appropriate context
   - Return meaningful error messages to clients
   - Handle service failures gracefully

## Testing

```bash
# Run tests
pytest tests/

# Test specific endpoint
curl -X GET http://localhost:8000/api/v1/tenants

# Test with authentication
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Service Connection Issues
- Verify service is running: `docker ps`
- Check service logs: `docker logs multitenant-api-gateway`
- Test service directly: `curl http://service-name:port/health`

### Authentication Issues
- Verify JWT token is valid
- Check token expiration
- Ensure secret keys match across services

### Performance Issues
- Monitor response times in logs
- Check service health endpoints
- Verify network connectivity between containers

## Support

For issues or questions, please refer to the main project documentation or create an issue in the repository.