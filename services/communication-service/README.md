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
├── requirements.txt       # Python dependencies
└── Dockerfile            # Container configuration
```

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

### Inbox Endpoints

#### Conversations
- `POST /api/v1/communications/conversations` - Create new conversation
- `GET /api/v1/communications/conversations` - List conversations
- `GET /api/v1/communications/conversations/{id}` - Get conversation details
- `PUT /api/v1/communications/conversations/{id}` - Update conversation
- `POST /api/v1/communications/conversations/{id}/assign` - Assign to user
- `POST /api/v1/communications/conversations/{id}/qualify` - Qualify as lead
- `DELETE /api/v1/communications/conversations/{id}` - Archive conversation

#### Messages
- `POST /api/v1/communications/messages` - Send message
- `GET /api/v1/communications/messages/conversation/{id}` - List messages
- `PUT /api/v1/communications/messages/{id}/status` - Update status

#### Quick Replies
- `POST /api/v1/communications/quick-replies` - Create template
- `GET /api/v1/communications/quick-replies` - List templates
- `PUT /api/v1/communications/quick-replies/{id}` - Update template
- `POST /api/v1/communications/quick-replies/{id}/use` - Use template

### Chat Endpoints

#### Channels
- `POST /api/v1/communications/channels` - Create channel
- `GET /api/v1/communications/channels` - List channels
- `GET /api/v1/communications/channels/{id}` - Get channel details
- `PUT /api/v1/communications/channels/{id}` - Update channel
- `DELETE /api/v1/communications/channels/{id}` - Delete channel

#### Channel Members
- `POST /api/v1/communications/channels/{id}/members` - Add member
- `GET /api/v1/communications/channels/{id}/members` - List members
- `PUT /api/v1/communications/channels/{id}/members/{user_id}` - Update member
- `DELETE /api/v1/communications/channels/{id}/members/{user_id}` - Remove member

#### Chat Messages
- `POST /api/v1/communications/chat/channels/{id}/messages` - Send message
- `GET /api/v1/communications/chat/channels/{id}/messages` - List messages
- `PUT /api/v1/communications/chat/messages/{id}` - Edit message
- `POST /api/v1/communications/chat/messages/{id}/reactions` - Add reaction

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/travel_system

# Service Configuration
HOST=0.0.0.0
PORT=8003
RELOAD=true

# External Services (Optional)
WHATSAPP_API_KEY=your_whatsapp_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SENDGRID_API_KEY=your_sendgrid_key
```

## 🏗️ Installation & Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export DATABASE_URL=postgresql://user:password@localhost:5432/travel_system
```

3. Run the service:
```bash
python main.py
```

### Docker Deployment

1. Build the image:
```bash
docker build -t communication-service .
```

2. Run the container:
```bash
docker run -p 8003:8003 \
  -e DATABASE_URL=postgresql://user:password@db:5432/travel_system \
  communication-service
```

## 📊 Database Schema

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

## 🔐 Multi-Tenant Support

The service supports multi-tenancy through PostgreSQL schemas:
- Each tenant has its own schema (e.g., `tenant_abc123`)
- Tables are created dynamically for new tenants
- Complete data isolation between tenants
- Tenant identification via URL slug

## 🔄 Integration Points

### Webhooks
The service can receive webhooks from:
- WhatsApp Business API
- Facebook Messenger
- Email providers (SendGrid, AWS SES)
- SMS providers (Twilio)

### Internal Services
Integrates with:
- User Service (for user authentication and profiles)
- Notification Service (for push notifications)
- File Service (for attachment handling)

## 📝 Development Guidelines

### Adding New Features

1. Determine the appropriate module (inbox or chat)
2. Update models in `models.py`
3. Create/update Pydantic schemas in `schemas.py`
4. Add endpoints in `endpoints.py`
5. Update the main router includes if needed

### Code Organization

- **Models**: SQLAlchemy ORM models define database structure
- **Schemas**: Pydantic models for request/response validation
- **Endpoints**: FastAPI routes handle HTTP requests
- **Common**: Shared enums and utilities

## 🧪 Testing

Run tests with pytest:
```bash
pytest tests/
```

## 📚 API Documentation

When the service is running, access:
- Swagger UI: `http://localhost:8003/docs`
- ReDoc: `http://localhost:8003/redoc`

## 🤝 Contributing

1. Follow the modular structure
2. Add appropriate indexes for new database fields
3. Include Pydantic validation for all endpoints
4. Update this README for significant changes

## 📄 License

[Your License Here]