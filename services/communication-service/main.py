"""
Communication Service Main Application
FastAPI application for handling all communication-related operations
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any
from datetime import datetime

# Import shared authentication (copied locally to avoid Docker path issues)
from shared_auth import get_current_user, require_super_admin, check_tenant_slug_access

# Import database and schema management
from database import get_tenant_db, verify_connection
from schema_manager import SchemaManager

# Import routers from modules
from inbox.endpoints import (
    conversations_router,
    messages_router,
    quick_replies_router
)
from chat.endpoints import (
    channels_router,
    chat_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Schema manager instance
schema_manager = SchemaManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    logger.info("Starting Communication Service...")

    # Verify database connection
    if not verify_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")

    logger.info("Communication Service started successfully")

    yield

    # Cleanup
    logger.info("Shutting down Communication Service...")
    from database import cleanup_engines
    cleanup_engines()

# Create FastAPI application
app = FastAPI(
    title="Communication Service",
    description="API for managing inbox conversations, messages, chat channels, and communication features",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# INCLUDE ROUTERS
# ============================================

# Inbox module routers
app.include_router(conversations_router)
app.include_router(messages_router)
app.include_router(quick_replies_router)

# Chat module routers
app.include_router(channels_router)
app.include_router(chat_router)

# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Communication Service",
        "version": "1.0.0",
        "status": "running",
        "modules": {
            "inbox": {
                "description": "Handles inbox conversations, messages, and quick replies",
                "endpoints": [
                    "/api/v1/tenants/{tenant_slug}/conversations",
                    "/api/v1/tenants/{tenant_slug}/messages",
                    "/api/v1/tenants/{tenant_slug}/quick-replies"
                ]
            },
            "chat": {
                "description": "Handles chat channels, members, and entries",
                "endpoints": [
                    "/api/v1/tenants/{tenant_slug}/channels",
                    "/api/v1/tenants/{tenant_slug}/chat"
                ]
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # You could add database connectivity check here
        return {
            "status": "healthy",
            "service": "Communication Service",
            "modules": {
                "inbox": "active",
                "chat": "active"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/v1/info")
async def service_info():
    """Get service information"""
    return {
        "service": "Communication Service",
        "version": "1.0.0",
        "description": "Manages all communication-related operations",
        "features": [
            "Multi-channel inbox (WhatsApp, Email, Messenger, etc.)",
            "Real-time chat channels",
            "Quick reply templates",
            "Message threading and conversations",
            "User mentions and reactions",
            "Channel member management",
            "Read receipts and delivery status",
            "Multi-tenant support"
        ],
        "api_documentation": "/docs",
        "modules": {
            "inbox": {
                "models": ["InboxConversation", "InboxMessage", "InboxQuickReply"],
                "features": [
                    "Multi-channel conversations",
                    "Message tracking",
                    "Quick replies",
                    "Lead qualification",
                    "Conversation assignment"
                ]
            },
            "chat": {
                "models": ["Channel", "ChannelMember", "ChatEntry", "Mention"],
                "features": [
                    "Public/Private channels",
                    "Direct messaging",
                    "User mentions",
                    "Message reactions",
                    "Read receipts",
                    "Channel roles and permissions"
                ]
            }
        }
    }

# ============================================
# TENANT INITIALIZATION ENDPOINT
# ============================================

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant(
    tenant_id: str,
    request: Dict[str, Any]
):
    """Initialize Communication Service tables for a new tenant"""
    try:
        schema_name = request.get("schema_name")
        if not schema_name:
            raise HTTPException(status_code=400, detail="schema_name is required")

        logger.info(f"Initializing Communication schema for tenant {tenant_id}")

        # Initialize the schema with Communication tables
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] == "success":
            logger.info(f"Successfully initialized Communication schema for tenant {tenant_id}")
            return {
                "tenant_id": tenant_id,
                "schema_name": schema_name,
                "service": "communication-service",
                "status": "success",
                "tables_created": result.get("tables_created", []),
                "errors": []
            }
        else:
            logger.error(f"Failed to initialize Communication schema for tenant {tenant_id}: {result.get('errors')}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize schema: {result.get('errors', ['Unknown error'])}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing tenant {tenant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.post("/api/v1/webhooks/incoming/{channel}")
async def receive_webhook(
    channel: str,
    payload: Dict[Any, Any]
):
    """
    Receive incoming webhooks from external services
    (WhatsApp, Messenger, Email providers, etc.)
    """
    logger.info(f"Received webhook from {channel}: {payload}")

    # Here you would process the incoming webhook based on the channel
    # and create appropriate inbox conversations/messages

    return {"status": "received", "channel": channel}

# ============================================
# AUTHENTICATION TEST ENDPOINTS
# ============================================

@app.get("/api/v1/auth/test")
async def auth_test(
    current_user: dict = Depends(get_current_user)
):
    """Test endpoint to verify authentication is working"""
    return {
        "message": "Authentication working!",
        "user": {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
            "tenant_slug": current_user.get("tenant_slug")
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/tenants/{tenant_slug}/auth/test")
async def tenant_auth_test(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Test endpoint to verify tenant access control"""
    # Check tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    return {
        "message": f"Tenant access working for {tenant_slug}!",
        "user": {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
            "user_tenant": current_user.get("tenant_slug"),
            "requested_tenant": tenant_slug
        },
        "access_granted": True
    }

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url)
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal error: {exc}")
    return {
        "error": "Internal Server Error",
        "message": "An internal error occurred"
    }

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn

    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8003))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
