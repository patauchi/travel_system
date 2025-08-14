"""
Booking Operations Service Main Application
FastAPI application for Booking Operations Management - Modular Architecture
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

# Import shared authentication
from shared_auth import get_current_user, check_tenant_slug_access

# Import modular routers
from countries.endpoints import router as countries_router
from destinations.endpoints import router as destinations_router
from suppliers.endpoints import router as suppliers_router
from services.endpoints import router as services_router
from specialized_services.endpoints import router as specialized_services_router
from cancellation_policies.endpoints import router as cancellation_policies_router
from bookings.endpoints import router as bookings_router
from service_operations.endpoints import router as service_operations_router
from rates.endpoints import router as rates_router
from passengers.endpoints import router as passengers_router

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
    logger.info("Starting Booking Operations Service...")

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
    logger.info("Shutting down Booking Operations Service...")
    cleanup_engines()
    logger.info("Booking Operations Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Booking Operations Service",
    description="Booking Operations Management Service for Multi-tenant Platform - Modular Architecture",
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

# ============================================
# INCLUDE MODULAR ROUTERS
# ============================================

# Geographic and Reference Data
app.include_router(
    countries_router,
    prefix="/api/v1",
    tags=["Countries"]
)

app.include_router(
    destinations_router,
    prefix="/api/v1",
    tags=["Destinations"]
)

# Supplier Management
app.include_router(
    suppliers_router,
    prefix="/api/v1",
    tags=["Suppliers"]
)

# Service Management
app.include_router(
    services_router,
    prefix="/api/v1",
    tags=["Services"]
)

app.include_router(
    specialized_services_router,
    prefix="/api/v1",
    tags=["Specialized Services"]
)

# Policies and Rates
app.include_router(
    cancellation_policies_router,
    prefix="/api/v1",
    tags=["Cancellation Policies"]
)

app.include_router(
    rates_router,
    prefix="/api/v1",
    tags=["Rates"]
)

# Booking Management
app.include_router(
    bookings_router,
    prefix="/api/v1",
    tags=["Bookings"]
)

app.include_router(
    service_operations_router,
    prefix="/api/v1",
    tags=["Service Operations"]
)

# Passenger Management
app.include_router(
    passengers_router,
    prefix="/api/v1",
    tags=["Passengers"]
)



# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "booking-operations-service",
        "version": "2.0.0",
        "architecture": "modular",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": [
            "countries",
            "destinations",
            "suppliers",
            "services",
            "specialized_services",
            "cancellation_policies",
            "bookings",
            "service_operations",
            "rates",
            "passengers"
        ]
    }


# ============================================
# AUTHENTICATION TEST ENDPOINTS
# ============================================

@app.get("/api/v1/auth/test")
async def auth_test(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Test authentication endpoint

    Returns:
        User information if authentication is successful
    """
    return {
        "message": "Authentication successful",
        "user": current_user,
        "service": "booking-operations-service",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/tenants/{tenant_slug}/auth/test")
async def tenant_auth_test(
    tenant_slug: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Test tenant-specific authentication

    Args:
        tenant_slug: Tenant identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        Tenant access confirmation
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    return {
        "message": f"Tenant access successful for {tenant_slug}",
        "user": current_user,
        "tenant_slug": tenant_slug,
        "service": "booking-operations-service",
        "timestamp": datetime.utcnow().isoformat()
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
    Initialize Booking Operations schema for a new tenant

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

        # Initialize schema with Booking Operations tables
        logger.info(f"Initializing Booking Operations schema for tenant {tenant_id}")
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] == "success":
            logger.info(f"Successfully initialized Booking Operations schema for tenant {tenant_id}")
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
# SERVICE INFORMATION ENDPOINTS
# ============================================

@app.get("/api/v1/service/info")
async def service_info():
    """
    Get service information and module status

    Returns:
        Service metadata and module information
    """
    return {
        "service_name": "booking-operations-service",
        "version": "2.0.0",
        "architecture": "modular",
        "description": "Booking Operations Management Service for Multi-tenant Platform",
        "modules": {
            "countries": {
                "description": "Country reference data management",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "destinations": {
                "description": "Travel destination management",
                "endpoints": ["list", "get", "create", "update", "delete", "search"]
            },
            "suppliers": {
                "description": "Supplier management and operations",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "services": {
                "description": "Service catalog management",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "specialized_services": {
                "description": "Specialized service types (tours, transfers, etc.)",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "cancellation_policies": {
                "description": "Cancellation policy management",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "bookings": {
                "description": "Booking management and operations",
                "endpoints": ["list", "get", "create", "update", "cancel", "confirm"]
            },
            "service_operations": {
                "description": "Service operation tracking",
                "endpoints": ["list", "get", "create", "update", "status"]
            },
            "rates": {
                "description": "Rate and pricing management",
                "endpoints": ["list", "get", "create", "update", "delete"]
            },
            "passengers": {
                "description": "Passenger data management",
                "endpoints": ["list", "get", "create", "update", "delete"]
            }
        },
        "features": [
            "Multi-tenant architecture",
            "Authentication and authorization",
            "Modular design pattern",
            "Comprehensive booking management",
            "Rate and pricing management",
            "Service operation tracking",
            "International tour support"
        ],
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
            "service": "booking-operations-service",
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
            "service": "booking-operations-service",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )
