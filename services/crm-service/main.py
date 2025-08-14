"""
CRM Service Main Application - Modular Architecture
FastAPI application for Customer Relationship Management with modular structure
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
from shared_auth import get_current_user_from_token, check_tenant_access
from sqlalchemy.orm import Session

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modular routers
try:
    from leads.endpoints import router as leads_router
    from contacts.endpoints import router as contacts_router
    from accounts.endpoints import router as accounts_router
    from opportunities.endpoints import router as opportunities_router
    from quotes.endpoints import router as quotes_router
    from industries.endpoints import router as industries_router
    logger.info("All module routers imported successfully")
except ImportError as e:
    logger.error(f"Error importing module routers: {str(e)}")
    # Create placeholder routers if imports fail
    from fastapi import APIRouter
    leads_router = APIRouter()
    contacts_router = APIRouter()
    accounts_router = APIRouter()
    opportunities_router = APIRouter()
    quotes_router = APIRouter()
    industries_router = APIRouter()
    logger.warning("Using placeholder routers due to import errors")

# Initialize schema manager
schema_manager = SchemaManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle
    """
    logger.info("Starting CRM Service (Modular Architecture)...")

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

        # Initialize all module schemas
        logger.info("Initializing module schemas...")
        # This would normally initialize all module tables

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
    title="CRM Service - Modular",
    description="Customer Relationship Management Service with Modular Architecture",
    version="2.0.0",
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

# Include modular routers
try:
    app.include_router(leads_router, prefix="/api/v1", tags=["Leads"])
    app.include_router(contacts_router, prefix="/api/v1", tags=["Contacts"])
    app.include_router(accounts_router, prefix="/api/v1", tags=["Accounts"])
    app.include_router(opportunities_router, prefix="/api/v1", tags=["Opportunities"])
    app.include_router(quotes_router, prefix="/api/v1", tags=["Quotes"])
    app.include_router(industries_router, prefix="/api/v1", tags=["Industries"])
    logger.info("All module routers included successfully")
except Exception as e:
    logger.error(f"Error including module routers: {str(e)}")
    logger.warning("Some modules may not be available")


# ============================================
# HEALTH CHECK & ROOT
# ============================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "crm-service",
        "version": "2.0.0",
        "architecture": "modular",
        "status": "healthy",
        "modules": [
            "core", "leads", "contacts", "accounts",
            "opportunities", "quotes", "industries"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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

        return {
            "status": "healthy",
            "service": "crm-service",
            "version": "2.0.0",
            "architecture": "modular",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "crm-service",
            "version": "2.0.0",
            "architecture": "modular",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================
# AUTHENTICATION TEST ENDPOINTS
# ============================================

@app.get("/api/v1/auth/test")
async def auth_test(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """Test authentication"""
    return {
        "message": "Authentication successful",
        "user_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/tenants/{tenant_id}/auth/test")
async def tenant_auth_test(
    tenant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """Test tenant-specific authentication"""
    # Check tenant access
    if not check_tenant_access(current_user, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for this tenant"
        )

    return {
        "message": "Tenant authentication successful",
        "tenant_id": tenant_id,
        "user_id": current_user.get("sub"),
        "has_access": True,
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# TENANT INITIALIZATION
# ============================================

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant(
    tenant_id: str,
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Initialize CRM schema for a new tenant

    Args:
        tenant_id: UUID of the tenant
        request: FastAPI request object
        current_user: Authenticated user
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
            return {
                **result,
                "architecture": "modular",
                "modules_initialized": [
                    "core", "leads", "contacts", "accounts",
                    "opportunities", "quotes", "industries"
                ]
            }
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
# MODULE STATUS ENDPOINT
# ============================================

@app.get("/api/v1/modules/status")
async def get_modules_status():
    """Get status of all CRM modules"""
    modules_status = {
        "core": {
            "name": "Core Module",
            "description": "Base models and shared functionality",
            "status": "active",
            "models": ["Actor"]
        },
        "leads": {
            "name": "Leads Module",
            "description": "Lead management functionality",
            "status": "active",
            "models": ["Lead"]
        },
        "contacts": {
            "name": "Contacts Module",
            "description": "Contact management functionality",
            "status": "active",
            "models": ["Contact"]
        },
        "accounts": {
            "name": "Accounts Module",
            "description": "Account management functionality",
            "status": "active",
            "models": ["Account"]
        },
        "opportunities": {
            "name": "Opportunities Module",
            "description": "Opportunity management functionality",
            "status": "active",
            "models": ["Opportunity"]
        },
        "quotes": {
            "name": "Quotes Module",
            "description": "Quote management functionality",
            "status": "active",
            "models": ["Quote", "QuoteLine"]
        },
        "industries": {
            "name": "Industries Module",
            "description": "Industry categorization functionality",
            "status": "active",
            "models": ["Industry"]
        }
    }

    return {
        "total_modules": len(modules_status),
        "architecture": "modular",
        "modules": modules_status,
        "modules_loaded": {
            "leads": hasattr(leads_router, 'routes') and len(leads_router.routes) > 0,
            "contacts": hasattr(contacts_router, 'routes') and len(contacts_router.routes) > 0,
            "accounts": hasattr(accounts_router, 'routes') and len(accounts_router.routes) > 0,
            "opportunities": hasattr(opportunities_router, 'routes') and len(opportunities_router.routes) > 0,
            "quotes": hasattr(quotes_router, 'routes') and len(quotes_router.routes) > 0,
            "industries": hasattr(industries_router, 'routes') and len(industries_router.routes) > 0
        },
        "timestamp": datetime.utcnow().isoformat()
    }

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
            "architecture": "modular",
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
            "architecture": "modular",
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
