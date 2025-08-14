"""
Booking Operations Service Main Application
FastAPI application for Booking Operations Management
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
from endpoints_bookings import router as bookings_router

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
    description="Booking Operations Management Service for Multi-tenant Platform",
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

# Include routers
app.include_router(
    bookings_router,
    prefix="/api/v1",
    tags=["bookings"]
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
        "version": "1.0.0",
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
# IMPORT ROUTERS
# ============================================

# Import routers for different Booking Operations modules
from endpoints_suppliers import router as suppliers_router
from endpoints_services import router as services_router
from endpoints_bookings import router as bookings_router
from endpoints_passengers import router as passengers_router
from endpoints_rates import router as rates_router
from endpoints_operations import router as operations_router
from endpoints_availability import router as availability_router

# Include routers
app.include_router(suppliers_router, prefix="/api/v1", tags=["Suppliers"])
app.include_router(services_router, prefix="/api/v1", tags=["Services"])
app.include_router(bookings_router, prefix="/api/v1", tags=["Bookings"])
app.include_router(passengers_router, prefix="/api/v1", tags=["Passengers"])
app.include_router(rates_router, prefix="/api/v1", tags=["Rates"])
app.include_router(operations_router, prefix="/api/v1", tags=["Operations"])
app.include_router(availability_router, prefix="/api/v1", tags=["Availability"])


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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )
