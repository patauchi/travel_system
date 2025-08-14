# System Service - Tenant User Management

## 📋 Overview

The System Service is a dedicated microservice responsible for managing **tenant-specific** users, roles, permissions, and settings. This service handles all user management operations within each tenant's isolated schema using SQLAlchemy models for table creation and management.

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
│  • Extended models (notes, tasks, events, etc.)            │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema Structure

Each tenant has its own isolated schema with tables created from SQLAlchemy models:

#### Core System Tables (from `models.py`)
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

#### Extended Tables (from `models_extended.py`)
- `notes` - Notes system with polymorphic relationships
- `logacalls` - Call logging and tracking
- `tasks` - Task management with polymorphic relationships
- `attachments` - File attachment management
- `events` - Event and calendar system
- `carbon_footprints` - Carbon emission tracking
- `channel_configs` - Communication channel configuration
- `reviews` - Review system

#### Template Tables (from `init.sql`)
- `activity_log` - Basic activity logging (created from tenant_template)

## 🚀 Key Features

### 1. **Model-Based Table Creation**
- Tables are defined using SQLAlchemy models (Python)
- No SQL migration files needed
- Automatic schema generation from models
- Type-safe and maintainable

### 2. **Complete User Isolation**
- Each tenant has its own user table
- No cross-tenant data leakage possible
- Users can have same email/username across different tenants

### 3. **Flexible Role System**
- Default roles: admin, manager, user, viewer
- Custom roles can be created per tenant
- Role priority system for conflict resolution

### 4. **Extended Functionality**
- Notes management with priorities and assignments
- Task tracking with status and due dates
- Event scheduling and calendar
- File attachments with versioning
- Call logging system
- Carbon footprint tracking
- Multi-channel communication config

### 5. **Comprehensive Audit Logging**
- All actions are logged
- IP tracking
- Session tracking
- Change history with before/after values

## 📁 Project Structure

```
system-service/
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── main.py                # FastAPI application
├── models.py              # Core SQLAlchemy models
├── models_extended.py     # Extended feature models
├── schemas.py             # Pydantic schemas
├── database.py            # Database connections
├── schema_manager.py      # Schema and table management
├── utils.py               # Utility functions
└── tests/                 # Unit tests
```

## 🔧 Schema Management System

The service uses `SchemaManager` to handle all schema operations:

```python
from schema_manager import SchemaManager

manager = SchemaManager()

# Initialize a new tenant schema with all tables
result = manager.initialize_tenant_schema(tenant_id, schema_name)

# List tables in a schema
tables = manager.list_tables_in_schema(schema_name)

# Get schema information
info = manager.get_schema_info(schema_name)
```

### How It Works

1. **Tenant Creation**: When a new tenant is created, only `activity_log` is copied from `tenant_template`
2. **Schema Initialization**: The system-service creates all other tables using SQLAlchemy models
3. **Model-Based**: All tables are defined in Python, making them easy to maintain and version

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

### Schema Management
- `POST /api/v1/tenants/{tenant_id}/initialize` - Initialize tenant schema with all tables

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

### Settings Management
- `GET /api/v1/tenants/{tenant_slug}/settings` - List settings
- `PUT /api/v1/tenants/{tenant_slug}/settings/{id}` - Update setting

## 📊 Models Structure

### Core Models (`models.py`)
```python
- Role: System roles with priorities
- Permission: Granular permissions
- User: Tenant users with comprehensive profile
- Team: Organizational units
- UserSession: Active sessions
- Setting: Configuration options
- AuditLog: Activity tracking
- ApiKey: API access management
```

### Extended Models (`models_extended.py`)
```python
- Note: Notes with polymorphic relationships (notable_type, notable_id)
- LogCall: Call tracking (logacallable_type, logacallable_id)
- Task: Task management (taskable_type, taskable_id)
- Attachment: File management (attachable_type, attachable_id)
- Event: Calendar events (eventable_type, eventable_id)
- CarbonFootprint: Emission tracking
- ChannelConfig: Communication channels
- Review: Review system
```

## 🔄 Table Creation Flow

```mermaid
graph TD
    A[New Tenant Created] --> B[tenant_template.activity_log copied]
    B --> C[Schema created: tenant_tenantX]
    C --> D[System Service Initialize]
    D --> E[SchemaManager.initialize_tenant_schema]
    E --> F[Create tables from models.py]
    F --> G[Create tables from models_extended.py]
    G --> H[Run post-creation tasks]
    H --> I[Insert default data]
    I --> J[Tenant Ready]
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

# Test schema creation
python schema_manager.py create test_schema

# List tables in schema
python schema_manager.py list test_schema
```

## 🚦 Health Checks

- `GET /health` - Basic health check
- `GET /ready` - Readiness check (database, redis)

## 📈 Performance Considerations

1. **Connection Pooling**: Each tenant gets its own connection pool
2. **Caching**: Redis caching for frequently accessed data
3. **Indexes**: Automatically created from model definitions
4. **Soft Deletes**: Supported through `deleted_at` columns

## 🛠️ Development

### Local Setup
```bash
# Install dependencies
pip install -r requirements.txt

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

### Adding New Tables

1. Define the model in `models_extended.py`:
```python
class NewFeature(Base):
    __tablename__ = "new_features"
    
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    # ... more fields
```

2. Import the model in `schema_manager.py`
3. Restart the service
4. New tenants will automatically get the new table

## 📝 Important Notes

- Tables are created from SQLAlchemy models, NOT from SQL files
- The only SQL-created table is `activity_log` from `tenant_template`
- Each tenant's data is completely isolated
- All extended features support polymorphic relationships
- Soft deletes are implemented using `deleted_at` columns

## 🔮 Future Enhancements

- [ ] GraphQL API support
- [ ] Real-time updates via WebSockets
- [ ] Advanced audit log analytics
- [ ] Automated backup per tenant
- [ ] Data export/import tools
- [ ] Multi-language support
- [ ] Advanced search with Elasticsearch

---

**Version**: 2.0.0  
**Last Updated**: January 2025  
**Architecture**: Model-Based Schema Management  
**Maintainer**: Platform Team