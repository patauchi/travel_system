"""
CRM Service Main Application
FastAPI application for Customer Relationship Management
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, status, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from database import get_db, get_tenant_db, cleanup_engines, get_schema_from_tenant_id
from schema_manager import SchemaManager
from sqlalchemy.orm import Session

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
    logger.info("Starting CRM Service...")

    # Startup
    try:
        # Test database connection
        from sqlalchemy import create_engine, text
        engine = create_engine(os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@postgres:5432/multitenant_db"
        ))
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down CRM Service...")
    cleanup_engines()
    logger.info("CRM Service stopped")


# Create FastAPI app
app = FastAPI(
    title="CRM Service",
    description="Customer Relationship Management Service for Multi-tenant Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "crm-service",
        "version": "1.0.0"
    }


# ============================================
# TENANT INITIALIZATION
# ============================================

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initialize CRM schema for a new tenant

    Args:
        tenant_id: UUID of the tenant
        request: FastAPI request object
        db: Database session

    Returns:
        Initialization result
    """
    try:
        # Get request body if any
        body = {}
        try:
            body = await request.json()
        except:
            pass

        # Get schema name from request or database
        schema_name = body.get("schema_name")
        if not schema_name:
            schema_name = get_schema_from_tenant_id(tenant_id, db)

        if not schema_name:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found or inactive"
            )

        # Initialize schema with CRM tables
        logger.info(f"Initializing CRM schema for tenant {tenant_id}")
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] == "success":
            logger.info(f"Successfully initialized CRM schema for tenant {tenant_id}")
            return result
        else:
            logger.error(f"Failed to initialize tenant {tenant_id}: {result['errors']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize tenant: {', '.join(result['errors'])}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing tenant {tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing tenant: {str(e)}"
        )


# ============================================
# IMPORT ROUTERS
# ============================================

# Import routers for different CRM modules
from endpoints_leads import router as leads_router
from endpoints_contacts import router as contacts_router
from endpoints_accounts import router as accounts_router
from endpoints_opportunities import router as opportunities_router
from endpoints_quotes import router as quotes_router

# Include routers
app.include_router(leads_router, prefix="/api/v1", tags=["Leads"])
app.include_router(contacts_router, prefix="/api/v1", tags=["Contacts"])
app.include_router(accounts_router, prefix="/api/v1", tags=["Accounts"])
app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"])
app.include_router(quotes_router, prefix="/api/v1", tags=["Quotes"])


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
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8011))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
