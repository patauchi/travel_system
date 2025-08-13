"""
Communication Service - Main Application
Handles inbox conversations, messages, chats and communication features
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
import httpx
from datetime import datetime

from database import verify_connection, cleanup_engines
from schema_manager import SchemaManager
from endpoints import include_routers
from communication_endpoints import router as communication_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize schema manager
schema_manager = SchemaManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    # Startup
    logger.info("Starting Communication Service...")

    # Verify database connection
    if not verify_connection():
        logger.error("Failed to connect to database")
        raise Exception("Database connection failed")

    logger.info("Database connection established")

    yield

    # Shutdown
    logger.info("Shutting down Communication Service...")
    cleanup_engines()
    logger.info("Communication Service stopped")


# Create FastAPI application
app = FastAPI(
    title="Communication Service",
    description="Multi-tenant communication service for inbox, messages, and chat",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
include_routers(app)

# Include communication endpoints router
app.include_router(
    communication_router,
    prefix="/api/v1",
    tags=["communications"]
)


# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "communication-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    checks = {
        "database": verify_connection()
    }

    if all(checks.values()):
        return {
            "status": "ready",
            "checks": checks
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not ready",
                "checks": checks
            }
        )


# ============================================
# TENANT INITIALIZATION ENDPOINT
# ============================================

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant(tenant_id: str, request: Request):
    """
    Initialize communication tables for a new tenant
    This endpoint is called by tenant-service when creating a new tenant
    """
    try:
        # Get request body
        body = await request.json()
        schema_name = body.get("schema_name", f"tenant_{tenant_id}")

        logger.info(f"Initializing communication schema for tenant {tenant_id}")

        # Initialize schema with all communication tables
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] == "success":
            logger.info(f"Successfully initialized tenant {tenant_id} with {len(result['tables_created'])} tables")

            # Optional: Notify other services or perform additional setup
            # await notify_other_services(tenant_id, schema_name)

            return {
                "status": "success",
                "tenant_id": tenant_id,
                "schema_name": schema_name,
                "tables_created": result["tables_created"],
                "message": f"Communication service initialized with {len(result['tables_created'])} tables"
            }
        else:
            logger.error(f"Failed to initialize tenant {tenant_id}: {result.get('errors')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize tenant: {result.get('errors')}"
            )

    except Exception as e:
        logger.error(f"Error initializing tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing tenant: {str(e)}"
        )


@app.get("/api/v1/tenants/{tenant_id}/schema/info")
async def get_tenant_schema_info(tenant_id: str):
    """Get information about a tenant's schema"""
    schema_name = f"tenant_{tenant_id}"
    info = schema_manager.get_schema_info(schema_name)

    if not info["exists"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema for tenant {tenant_id} not found"
        )

    return info


# ============================================
# WEBHOOK ENDPOINTS
# ============================================

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request):
    """Webhook endpoint for WhatsApp messages"""
    try:
        body = await request.json()
        logger.info(f"Received WhatsApp webhook: {body}")

        # Process webhook based on your WhatsApp provider (Twilio, WhatsApp Business API, etc.)
        # This is a placeholder implementation

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )


@app.post("/webhooks/messenger")
async def messenger_webhook(request: Request):
    """Webhook endpoint for Facebook Messenger"""
    try:
        body = await request.json()
        logger.info(f"Received Messenger webhook: {body}")

        # Process webhook based on Facebook Messenger API
        # This is a placeholder implementation

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing Messenger webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )


@app.post("/webhooks/email")
async def email_webhook(request: Request):
    """Webhook endpoint for email notifications"""
    try:
        body = await request.json()
        logger.info(f"Received email webhook: {body}")

        # Process email webhook (SendGrid, AWS SES, etc.)
        # This is a placeholder implementation

        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing email webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================
# UTILITY FUNCTIONS
# ============================================

async def notify_other_services(tenant_id: str, schema_name: str):
    """
    Notify other services about tenant initialization
    """
    # This is optional - you can notify other services if needed
    services_to_notify = [
        # Add service URLs if needed
        # "http://booking-service:8005",
        # "http://financial-service:8006",
    ]

    async with httpx.AsyncClient() as client:
        for service_url in services_to_notify:
            try:
                response = await client.post(
                    f"{service_url}/api/v1/tenants/{tenant_id}/sync",
                    json={"schema_name": schema_name},
                    timeout=5.0
                )
                logger.info(f"Notified {service_url} about tenant {tenant_id}")
            except Exception as e:
                logger.warning(f"Failed to notify {service_url}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", "8010"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
