# System Service - Tenant User Management

## 📋 Overview

The System Service is a dedicated microservice responsible for managing **tenant-specific** users, roles, permissions, and settings. This service handles all user management operations within each tenant's isolated schema.

## 🏗️ Architecture

### Service Separation

```
┌─────────────────────────────────────────────────────────────┐
│                     Platform Level                          │
├─────────────────────────────────────────────────────────────┤
│  auth-service         │  tenant-service                     │
│  • System admins      │  • Tenant CRUD                      │
│  • Platform auth      │  • Subscription management           │
│  (shared.system_users)│  (shared.tenants)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tenant Level                           │
├─────────────────────────────────────────────────────────────┤
│                     system-service                          │
│  • Tenant users (tenant_*.users)                           │
│  • Roles & permissions (tenant_*.roles, permissions)       │
│  • Settings (tenant_*.settings)                            │
│  • Teams (tenant_*.teams)                                  │
│  • Audit logs (tenant_*.audit_logs)                        │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Structure

Each tenant has its own isolated schema with the following tables:

- `users` - Tenant-specific users
- `roles` - Customizable roles
- `permissions` - Granular permissions
- `role_permissions` - Role-permission mappings
- `user_permissions` - User-specific permission overrides
- `user_roles` - User-role assignments
- `teams` - Organizational units
- `team_members` - Team memberships
- `user_sessions` - Active sessions
- `settings` - Tenant configuration
- `audit_logs` - Activity tracking
- `password_reset_tokens` - Password recovery
- `email_verification_tokens` - Email verification
- `api_keys` - API access keys

## 🚀 Key Features

### 1. **Complete User Isolation**
- Each tenant has its own user table
- No cross-tenant data leakage possible
- Users can have same email/username across different tenants

### 2. **Flexible Role System**
- Default roles: admin, manager, user, viewer, guest
- Custom roles can be created per tenant
- Role priority system for conflict resolution

### 3. **Granular Permissions**
- Resource-based permissions (user, role, project, document, etc.)
- Action-based permissions (create, read, update, delete, etc.)
- Permission inheritance through roles
- Direct permission grants/denials to users

### 4. **Comprehensive Audit Logging**
- All actions are logged
- IP tracking
- Session tracking
- Change history with before/after values

### 5. **Advanced Security**
- Password policies per tenant
- Account lockout after failed attempts
- Two-factor authentication support
- API key management
- Session management with expiration

## 📁 Project Structure

```
system-service/
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── main.py                # FastAPI application
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── database.py            # Database connections
├── utils.py               # Utility functions
├── migrations/            # Database migrations
│   ├── 001_initial_tenant_structure.sql
│   └── manager.py         # Migration manager
└── tests/                 # Unit tests
```

## 🔧 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Service Configuration
ENVIRONMENT=development
SERVICE_PORT=8004
```

## 📡 API Endpoints

### Authentication
- `POST /api/v1/tenants/{tenant_slug}/auth/login` - Tenant user login
- `POST /api/v1/tenants/{tenant_slug}/auth/logout` - Logout
- `POST /api/v1/tenants/{tenant_slug}/auth/refresh` - Refresh token

### User Management
- `GET /api/v1/tenants/{tenant_slug}/users` - List users
- `POST /api/v1/tenants/{tenant_slug}/users` - Create user
- `GET /api/v1/tenants/{tenant_slug}/users/{id}` - Get user
- `PUT /api/v1/tenants/{tenant_slug}/users/{id}` - Update user
- `DELETE /api/v1/tenants/{tenant_slug}/users/{id}` - Delete user

### Role Management
- `GET /api/v1/tenants/{tenant_slug}/roles` - List roles
- `POST /api/v1/tenants/{tenant_slug}/roles` - Create role
- `GET /api/v1/tenants/{tenant_slug}/roles/{id}` - Get role
- `PUT /api/v1/tenants/{tenant_slug}/roles/{id}` - Update role
- `DELETE /api/v1/tenants/{tenant_slug}/roles/{id}` - Delete role

### Permission Management
- `GET /api/v1/tenants/{tenant_slug}/permissions` - List permissions
- `POST /api/v1/tenants/{tenant_slug}/permissions` - Create permission
- `POST /api/v1/tenants/{tenant_slug}/roles/{id}/permissions` - Assign permissions to role
- `POST /api/v1/tenants/{tenant_slug}/users/{id}/permissions` - Grant/deny user permissions

### Settings Management
- `GET /api/v1/tenants/{tenant_slug}/settings` - List settings
- `PUT /api/v1/tenants/{tenant_slug}/settings/{id}` - Update setting

### Team Management
- `GET /api/v1/tenants/{tenant_slug}/teams` - List teams
- `POST /api/v1/tenants/{tenant_slug}/teams` - Create team
- `POST /api/v1/tenants/{tenant_slug}/teams/{id}/members` - Add team member

### Tenant Schema Management
- `POST /api/v1/tenants/{tenant_id}/initialize` - Initialize tenant schema

## 🔄 Migration System

The service includes a migration system that:
1. Creates tenant schemas on demand
2. Applies migrations to keep schemas updated
3. Seeds default data (roles, permissions, settings)

### Running Migrations

```python
# Automatically run when initializing a tenant
POST /api/v1/tenants/{tenant_id}/initialize
{
  "schema_name": "tenant_company1"
}
```

## 🔐 Security Model

### Token Types
```json
{
  "type": "tenant",
  "tenant_slug": "company1",
  "user_id": "uuid",
  "roles": ["manager"],
  "permissions": ["users.read", "projects.write"]
}
```

### Permission Check Flow
1. Check if user has direct permission grant
2. Check if user has permission through roles
3. Check for explicit permission denial
4. Apply default policy (deny by default)

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## 🚦 Health Checks

- `GET /health` - Basic health check
- `GET /ready` - Readiness check (database, redis)

## 📊 Default Roles and Permissions

### Roles Created on Tenant Initialization

| Role | Priority | Description |
|------|----------|-------------|
| admin | 100 | Full access to all resources |
| manager | 80 | Manage users and most resources |
| user | 50 | Standard user access |
| viewer | 30 | Read-only access |
| guest | 10 | Limited temporary access |

### Default Permissions

| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| users.create | user | create | Create new users |
| users.read | user | read | View user information |
| users.update | user | update | Update user information |
| users.delete | user | delete | Delete users |
| roles.* | role | * | Role management |
| settings.* | setting | * | Settings management |
| ... | ... | ... | ... |

## 🔄 Integration with Other Services

### Communication Flow
```
Frontend → API Gateway → System Service → Tenant DB
                     ↓
              Auth Service (verify token)
```

### Service Dependencies
- **PostgreSQL**: Main database
- **Redis**: Session storage, caching
- **RabbitMQ**: Async task processing

## 📈 Performance Considerations

1. **Connection Pooling**: Each tenant gets its own connection pool
2. **Caching**: Redis caching for frequently accessed data
3. **Indexes**: Optimized indexes on all foreign keys and search fields
4. **Soft Deletes**: Users are soft-deleted to maintain referential integrity

## 🛠️ Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python migrations/manager.py upgrade

# Start service
uvicorn main:app --reload --port 8004
```

### Docker Setup
```bash
# Build image
docker build -t system-service .

# Run container
docker run -p 8004:8004 system-service
```

## 📝 Notes

- This service manages ONLY tenant-level users
- Platform administrators are managed by auth-service
- Each tenant's data is completely isolated
- Migrations are versioned and applied per tenant
- All operations are audited

## 🔮 Future Enhancements

- [ ] Bulk user import/export
- [ ] Advanced permission templates
- [ ] LDAP/AD integration per tenant
- [ ] OAuth provider per tenant
- [ ] User impersonation for support
- [ ] Advanced audit log analytics
- [ ] Automated user provisioning workflows

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Maintainer**: Platform Team