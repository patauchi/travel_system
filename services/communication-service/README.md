# Communication Service

## 📋 Overview

The Communication Service is a multi-tenant microservice that handles all communication-related features including inbox conversations, messages, internal chat, and quick replies. It supports multiple communication channels like WhatsApp, Messenger, Instagram, Email, and more.

## 🏗️ Architecture

This service follows the same architecture pattern as the system-service:
- **SQLAlchemy Models** for database table definitions (NO SQL files)
- **FastAPI** for REST API endpoints
- **Pydantic** for request/response validation
- **Multi-tenant** isolation using PostgreSQL schemas

## 📊 Database Tables

The service manages the following tables per tenant:

### Inbox System
- `inbox_conversations` - Main conversations from various channels
- `inbox_messages` - Individual messages within conversations
- `inbox_quick_replies` - Pre-defined reply templates

### Chat System
- `channels` - Internal chat channels
- `channel_members` - Members of chat channels
- `chat_entries` - Messages in chat channels
- `mentions` - User mentions in chat

## 🚀 Features

### Inbox Management
- Multi-channel support (WhatsApp, Messenger, Email, etc.)
- Conversation tracking and status management
- Message threading
- Quick reply templates
- Lead qualification
- Assignment and routing

### Chat System
- Create public/private channels
- Real-time messaging
- User mentions
- Message reactions
- File attachments
- Edit/delete messages

### Analytics
- Conversation statistics
- Response time tracking
- Message volume metrics
- User activity monitoring

## 📁 Project Structure

```
communication-service/
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── main.py                # FastAPI application
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── database.py            # Database connections
├── schema_manager.py      # Schema management
├── endpoints.py           # API endpoints
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Service Configuration
SERVICE_PORT=8010

# Optional
SQL_ECHO=false  # Enable SQL query logging
```

## 📡 API Endpoints

### Conversations
- `POST /api/v1/tenants/{tenant_slug}/conversations` - Create conversation
- `GET /api/v1/tenants/{tenant_slug}/conversations` - List conversations
- `GET /api/v1/tenants/{tenant_slug}/conversations/{id}` - Get conversation
- `PUT /api/v1/tenants/{tenant_slug}/conversations/{id}` - Update conversation
- `POST /api/v1/tenants/{tenant_slug}/conversations/{id}/assign` - Assign conversation
- `POST /api/v1/tenants/{tenant_slug}/conversations/{id}/qualify` - Qualify as lead
- `DELETE /api/v1/tenants/{tenant_slug}/conversations/{id}` - Archive conversation
- `GET /api/v1/tenants/{tenant_slug}/conversations/stats` - Get statistics

### Messages
- `POST /api/v1/tenants/{tenant_slug}/messages` - Create message
- `GET /api/v1/tenants/{tenant_slug}/messages/conversation/{id}` - List messages
- `PUT /api/v1/tenants/{tenant_slug}/messages/{id}/status` - Update status

### Quick Replies
- `POST /api/v1/tenants/{tenant_slug}/quick-replies` - Create quick reply
- `GET /api/v1/tenants/{tenant_slug}/quick-replies` - List quick replies
- `PUT /api/v1/tenants/{tenant_slug}/quick-replies/{id}` - Update quick reply
- `POST /api/v1/tenants/{tenant_slug}/quick-replies/{id}/use` - Track usage
- `DELETE /api/v1/tenants/{tenant_slug}/quick-replies/{id}` - Delete quick reply

### Webhooks
- `POST /webhooks/whatsapp` - WhatsApp webhook
- `POST /webhooks/messenger` - Messenger webhook
- `POST /webhooks/email` - Email webhook

### System
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `POST /api/v1/tenants/{tenant_id}/initialize` - Initialize tenant schema

## 🚀 Getting Started

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py

# Or with uvicorn
uvicorn main:app --reload --port 8010
```

### Docker

```bash
# Build image
docker build -t communication-service .

# Run container
docker run -p 8010:8010 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  communication-service
```

### Docker Compose

Add to your `docker-compose.yml`:

```yaml
communication-service:
  build:
    context: ./services/communication-service
    dockerfile: Dockerfile
  container_name: multitenant-communication-service
  ports:
    - "8010:8010"
  environment:
    - DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/multitenant_db
    - SERVICE_PORT=8010
  depends_on:
    - postgres
    - redis
  networks:
    - multitenant-network
  volumes:
    - ./services/communication-service:/app
```

## 🔄 Integration with Tenant Service

The communication service is automatically initialized when a new tenant is created. The tenant-service calls the `/api/v1/tenants/{tenant_id}/initialize` endpoint to create all necessary tables.

### Manual Initialization

```bash
# Initialize for a specific tenant
curl -X POST http://localhost:8010/api/v1/tenants/tenant123/initialize \
  -H "Content-Type: application/json" \
  -d '{"schema_name": "tenant_tenant123"}'
```

## 📊 Database Schema Details

### Channel Types Supported
- `whatsapp` - WhatsApp Business
- `messenger` - Facebook Messenger
- `instagram` - Instagram Direct
- `email` - Email
- `web` - Web chat widget
- `twilio_whatsapp` - Twilio WhatsApp
- `twilio_call` - Twilio Voice
- `personal_whatsapp` - Personal WhatsApp
- `gmail` - Gmail
- `zendesk` - Zendesk

### Conversation Status
- `new` - New unread conversation
- `open` - Opened/being handled
- `replied` - Agent has replied
- `qualified` - Qualified as lead
- `archived` - Archived/closed

### Message Types
- `text` - Text message
- `image` - Image attachment
- `document` - Document attachment
- `audio` - Audio message
- `video` - Video attachment
- `location` - Location share

## 🧪 Testing

### Test Schema Creation

```python
python schema_manager.py create test_tenant
```

### Test API Endpoints

```bash
# Create a conversation
curl -X POST http://localhost:8010/api/v1/tenants/test/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "whatsapp",
    "contact_identifier": "+1234567890",
    "contact_name": "John Doe",
    "first_message": "Hello, I need help"
  }'

# List conversations
curl http://localhost:8010/api/v1/tenants/test/conversations

# Get statistics
curl http://localhost:8010/api/v1/tenants/test/conversations/stats
```

## 📈 Performance Considerations

1. **Indexes**: All foreign keys and frequently queried fields are indexed
2. **Pagination**: All list endpoints support pagination
3. **Connection Pooling**: Separate connection pools per tenant
4. **Async Operations**: All endpoints are async for better performance

## 🔍 Monitoring

- Health endpoint: `GET /health`
- Readiness endpoint: `GET /ready`
- Metrics can be added using Prometheus client
- Structured logging with correlation IDs

## 🚨 Error Handling

The service implements comprehensive error handling:
- HTTP exceptions with proper status codes
- Detailed error messages in development
- Generic messages in production
- All errors are logged with context

## 🔮 Future Enhancements

- [ ] WebSocket support for real-time messaging
- [ ] Message encryption
- [ ] AI-powered auto-replies
- [ ] Sentiment analysis
- [ ] Message translation
- [ ] Voice message transcription
- [ ] Advanced routing rules
- [ ] SLA tracking
- [ ] Conversation templates
- [ ] Bulk operations

## 📝 Notes

- All tables support soft deletes where applicable
- Timestamps are in UTC
- JSONB fields are used for flexible metadata
- Polymorphic relationships are avoided in favor of explicit foreign keys
- Each tenant's data is completely isolated

## 🆘 Troubleshooting

### Common Issues

1. **Schema not found**: Ensure tenant is initialized
2. **Connection refused**: Check DATABASE_URL
3. **Migration errors**: Verify models.py syntax
4. **Performance issues**: Check indexes and query optimization

### Debug Mode

Enable SQL logging:
```bash
export SQL_ECHO=true
```

## 📚 Related Services

- `tenant-service` - Creates tenants and triggers initialization
- `system-service` - Manages users and permissions
- `auth-service` - Handles authentication

---

**Version**: 1.0.0  
**Last Updated**: January 2025  
**Maintainer**: Platform Team