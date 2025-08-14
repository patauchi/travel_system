# Communication Service

A comprehensive microservice for managing all communication-related operations in the travel system, including inbox conversations, messaging, and real-time chat functionality.

## 📁 Project Structure

The service has been organized into modular components for better maintainability and scalability:

```
communication-service/
├── inbox/                  # Inbox module for external communications
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models for inbox entities
│   ├── schemas.py         # Pydantic schemas for API validation
│   └── endpoints.py       # FastAPI endpoints for inbox operations
│
├── chat/                   # Chat module for internal team communication
│   ├── __init__.py
│   ├── models.py          # SQLAlchemy models for chat entities
│   ├── schemas.py         # Pydantic schemas for chat API
│   └── endpoints.py       # FastAPI endpoints for chat operations
│
├── common/                 # Shared utilities and enums
│   ├── __init__.py
│   └── enums.py           # Common enums used across modules
│
├── main.py                # FastAPI application entry point
├── database.py            # Database connection and session management
├── schema_manager.py      # Multi-tenant schema management
├── shared_auth.py         # Shared authentication system
├── requirements.txt       # Python dependencies
└── Dockerfile            # Container configuration
```

## 🔐 Authentication & Security

This service implements JWT-based authentication with role-based access control:

### Authentication Features
- **JWT Token Validation**: All protected endpoints require valid JWT tokens
- **Multi-Tenant Access Control**: Users can only access their assigned tenant data
- **Role-Based Permissions**: Support for `super_admin`, `tenant_admin`, and `tenant_user` roles
- **Service-to-Service Auth**: Internal service communication via service tokens

### Protected Endpoints
All main endpoints require authentication:

- ✅ **Conversations**: Require `conversations.read` permission
- ✅ **Messages**: Require `messages.read` permission  
- ✅ **Chat Channels**: Require `channels.read` permission
- ✅ **Quick Replies**: Require admin role for management

### Authentication Testing Endpoints
- `GET /api/v1/auth/test` - Test basic authentication
- `GET /api/v1/tenants/{tenant_slug}/auth/test` - Test tenant access control

## 🎯 Modules Overview

### Inbox Module (`/inbox`)
Handles external communication channels and customer interactions:

**Entities:**
- **InboxConversation**: Manages conversations from various channels (WhatsApp, Email, Messenger, etc.)
- **InboxMessage**: Individual messages within conversations
- **InboxQuickReply**: Pre-defined templates for quick responses

**Features:**
- Multi-channel support (WhatsApp, Email, Messenger, Instagram, etc.)
- Conversation tracking and status management
- Message threading and history
- Quick reply templates
- Lead qualification
- Assignment to team members
- Priority management
- Spam detection

### Chat Module (`/chat`)
Manages internal team communication and collaboration:

**Entities:**
- **Channel**: Chat rooms for team discussions
- **ChannelMember**: Members and their roles in channels
- **ChatEntry**: Messages and system events in channels
- **Mention**: User mentions and notifications

**Features:**
- Public, private, and direct message channels
- Role-based permissions (admin, moderator, member)
- Message reactions and mentions
- Read receipts and unread counts
- Message editing and deletion
- File attachments
- Typing indicators

### Common Module (`/common`)
Shared utilities and enumerations used across the service:

- Channel types and communication platforms
- Message statuses and directions
- Priority levels
- Member roles and permissions
- Webhook events

## 🚀 API Endpoints

### Authentication Required

All endpoints require a valid JWT token in the Authorization header:
```bash
Authorization: Bearer <your-jwt-token>
```

### Inbox Endpoints

#### Conversations
- `POST /api/v1/communications/conversations?tenant_slug={slug}` - Create new conversation ⚡ **AUTH REQUIRED**
- `GET /api/v1/communications/conversations?tenant_slug={slug}` - List conversations ⚡ **AUTH REQUIRED**
- `GET /api/v1/communications/conversations/{id}?tenant_slug={slug}` - Get conversation details
- `PUT /api/v1/communications/conversations/{id}?tenant_slug={slug}` - Update conversation
- `POST /api/v1/communications/conversations/{id}/assign?tenant_slug={slug}` - Assign to user
- `POST /api/v1/communications/conversations/{id}/qualify?tenant_slug={slug}` - Qualify as lead
- `DELETE /api/v1/communications/conversations/{id}?tenant_slug={slug}` - Archive conversation

#### Messages
- `POST /api/v1/communications/messages?tenant_slug={slug}` - Send message
- `GET /api/v1/communications/messages/conversation/{id}?tenant_slug={slug}` - List messages
- `PUT /api/v1/communications/messages/{id}/status?tenant_slug={slug}` - Update status

#### Quick Replies
- `POST /api/v1/communications/quick-replies?tenant_slug={slug}` - Create template
- `GET /api/v1/communications/quick-replies?tenant_slug={slug}` - List templates
- `PUT /api/v1/communications/quick-replies/{id}?tenant_slug={slug}` - Update template
- `POST /api/v1/communications/quick-replies/{id}/use?tenant_slug={slug}` - Use template

### Chat Endpoints

#### Channels
- `POST /api/v1/communications/channels?tenant_slug={slug}` - Create channel
- `GET /api/v1/communications/channels?tenant_slug={slug}` - List channels
- `GET /api/v1/communications/channels/{id}?tenant_slug={slug}` - Get channel details
- `PUT /api/v1/communications/channels/{id}?tenant_slug={slug}` - Update channel
- `DELETE /api/v1/communications/channels/{id}?tenant_slug={slug}` - Delete channel

#### Channel Members
- `POST /api/v1/communications/channels/{id}/members?tenant_slug={slug}` - Add member
- `GET /api/v1/communications/channels/{id}/members?tenant_slug={slug}` - List members
- `PUT /api/v1/communications/channels/{id}/members/{user_id}?tenant_slug={slug}` - Update member
- `DELETE /api/v1/communications/channels/{id}/members/{user_id}?tenant_slug={slug}` - Remove member

#### Chat Messages
- `POST /api/v1/communications/chat/channels/{id}/messages?tenant_slug={slug}` - Send message
- `GET /api/v1/communications/chat/channels/{id}/messages?tenant_slug={slug}` - List messages
- `PUT /api/v1/communications/chat/messages/{id}?tenant_slug={slug}` - Edit message
- `POST /api/v1/communications/chat/messages/{id}/reactions?tenant_slug={slug}` - Add reaction

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/multitenant_db

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Service Configuration
HOST=0.0.0.0
PORT=8005
RELOAD=true

# External Services (Optional)
WHATSAPP_API_KEY=your_whatsapp_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENDGRID_API_KEY=your_sendgrid_key
```

## 🔐 Authentication Integration

### Shared Authentication System

The service uses a shared authentication system located in `shared_auth.py` that provides:

- **JWT Token Validation**: Secure token verification across all endpoints
- **Role-Based Access Control**: Support for different user roles
- **Multi-Tenant Isolation**: Automatic tenant access validation
- **Service-to-Service Auth**: Internal service communication

### Authentication Functions

```python
from shared_auth import (
    get_current_user,           # Require any authenticated user
    require_super_admin,        # Require super admin role
    require_tenant_admin,       # Require tenant admin role
    check_tenant_slug_access,   # Validate tenant access
    check_permission           # Check specific permissions
)
```

### Example Protected Endpoint

```python
@router.post("/conversations")
async def create_conversation(
    conversation_data: ConversationCreate,
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Your business logic here
    return {"status": "success"}
```

## 🏗️ Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis (for caching)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/multitenant_db
export JWT_SECRET_KEY=your-secret-key-change-in-production
```

3. Run the service:
```bash
python main.py
```

### Docker Deployment

The service runs on **port 8005** in the Docker environment:

```bash
# Build and run via docker-compose
docker-compose build communication-service
docker-compose up -d communication-service

# Access the service
curl http://localhost:8005/health
```

## 📊 Database Schema

### Multi-Tenant Architecture
Each tenant has its own PostgreSQL schema:
- Schema naming: `tenant_{tenant_slug}` (e.g., `tenant_demo`)
- Complete data isolation between tenants
- Dynamic schema creation for new tenants

### Inbox Tables
- `inbox_conversations` - Main conversation records
- `inbox_messages` - Individual messages
- `inbox_quick_replies` - Reply templates

### Chat Tables
- `channels` - Chat channel definitions
- `channel_members` - Channel membership
- `chat_entries` - Chat messages and events
- `mentions` - User mentions

All tables include appropriate indexes for optimal query performance.

## 🧪 Testing Authentication

### Test Basic Authentication
```bash
# Should fail (401)
curl http://localhost:8005/api/v1/auth/test

# Should succeed
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8005/api/v1/auth/test
```

### Test Tenant Access Control
```bash
# Should succeed for correct tenant
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8005/api/v1/tenants/demo/auth/test

# Should fail (403) for wrong tenant
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8005/api/v1/tenants/other/auth/test
```

### Test Protected Endpoints
```bash
# List conversations (requires auth + tenant access)
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8005/api/v1/communications/conversations/?tenant_slug=demo"
```

## 🔄 Integration Points

### Webhooks
The service can receive webhooks from:
- WhatsApp Business API
- Facebook Messenger
- Email providers (SendGrid, AWS SES)
- SMS providers (Twilio)

### Internal Services
Integrates with:
- **Auth Service**: JWT token validation
- **User Service**: User profiles and permissions
- **Notification Service**: Push notifications
- **File Service**: Attachment handling

## 📝 Development Guidelines

### Adding New Features

1. **Choose Module**: Determine if feature belongs in `inbox` or `chat`
2. **Update Models**: Add/modify SQLAlchemy models in `models.py`
3. **Create Schemas**: Add Pydantic validation in `schemas.py`
4. **Add Endpoints**: Implement FastAPI routes in `endpoints.py`
5. **Add Authentication**: Use `Depends(get_current_user)` for protected endpoints
6. **Tenant Validation**: Add `check_tenant_slug_access()` for tenant-specific data

### Code Organization Best Practices

- **Models**: One file per module, clear relationships
- **Schemas**: Separate Create/Update/Response schemas
- **Endpoints**: Group related functionality, use descriptive names
- **Authentication**: Always validate tenant access for tenant-specific data
- **Error Handling**: Use appropriate HTTP status codes

### Authentication Integration Pattern

```python
# 1. Import authentication
from shared_auth import get_current_user, check_tenant_slug_access

# 2. Add to endpoint
async def my_endpoint(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 3. Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 4. Get database session manually (after validation)
    from database import get_tenant_session
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        # Your database operations here
        pass
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
# Test authentication
curl http://localhost:8005/api/v1/auth/test

# Test tenant access
curl http://localhost:8005/api/v1/tenants/demo/auth/test
```

## 📚 API Documentation

When the service is running, access:
- **Swagger UI**: `http://localhost:8005/docs`
- **ReDoc**: `http://localhost:8005/redoc`
- **Health Check**: `http://localhost:8005/health`

## 🏆 Modular Architecture Benefits

This service serves as a **reference implementation** for other microservices:

### ✅ Advantages of This Structure

1. **Separation of Concerns**: Each module has clear responsibilities
2. **Scalability**: Easy to add new modules without affecting existing ones
3. **Maintainability**: Code is organized and easy to find
4. **Testability**: Each module can be tested independently
5. **Reusability**: Common utilities shared across modules
6. **Team Collaboration**: Multiple developers can work on different modules

### 🎯 Recommended for Migration

Other services should adopt this modular structure:

```
service-name/
├── module1/           # Feature-based modules
│   ├── models.py     # Database models
│   ├── schemas.py    # API schemas
│   └── endpoints.py  # API endpoints
├── module2/
├── common/           # Shared utilities
├── main.py          # Application entry
├── database.py      # DB management
└── shared_auth.py   # Authentication
```

## 🤝 Contributing

1. Follow the modular structure pattern
2. Add authentication to all new endpoints
3. Include proper tenant access validation
4. Add appropriate database indexes
5. Update documentation for significant changes

## 📄 Next Steps

This service demonstrates the **gold standard** for microservice architecture in our travel system. Use this as a template for:

1. **Migrating existing monolithic services** to modular structure
2. **Implementing authentication** in other services
3. **Maintaining consistent** code organization across the platform

See `MIGRATION_GUIDE.md` for detailed instructions on how to migrate other services to this pattern.

---

**Status**: ✅ Production Ready with Authentication
**Architecture**: 🏗️ Modular, Scalable, Maintainable
**Security**: 🔐 JWT + Multi-Tenant Access Control