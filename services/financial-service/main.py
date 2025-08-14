"""
Financial Service Main Application
FastAPI application for Financial Management with Modular Architecture
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
from shared_auth import get_current_user, get_current_tenant, require_permission
from sqlalchemy.orm import Session

# Import all modular routers
from orders import router as orders_router
from expenses import router as expenses_router
from pettycash import router as pettycash_router
from voucher import router as voucher_router
from invoices import router as invoices_router
from payments import router as payments_router

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
    logger.info("Starting Financial Service with Modular Architecture...")

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

        # Log module initialization
        logger.info("Initialized modules:")
        logger.info("- Orders Module")
        logger.info("- Expenses Module")
        logger.info("- Petty Cash Module")
        logger.info("- Voucher Module")
        logger.info("- Invoices Module")
        logger.info("- Payments Module")

    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Financial Service...")
    cleanup_engines()
    logger.info("Financial Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Financial Service - Modular Architecture",
    description="Comprehensive Financial Management Service with Modular Architecture for Multi-tenant Platform",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
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
# MODULE ROUTERS INTEGRATION
# ============================================

# Orders Module
app.include_router(
    orders_router,
    prefix="/api/v1/financial",
    tags=["Orders Management"],
    dependencies=[]
)

# Expenses Module
app.include_router(
    expenses_router,
    prefix="/api/v1/financial",
    tags=["Expenses Management"],
    dependencies=[]
)

# Petty Cash Module
app.include_router(
    pettycash_router,
    prefix="/api/v1/financial",
    tags=["Petty Cash Management"],
    dependencies=[]
)

# Voucher Module
app.include_router(
    voucher_router,
    prefix="/api/v1/financial",
    tags=["Voucher Management"],
    dependencies=[]
)

# Invoices Module
app.include_router(
    invoices_router,
    prefix="/api/v1/financial",
    tags=["Invoices & AR/AP Management"],
    dependencies=[]
)

# Payments Module
app.include_router(
    payments_router,
    prefix="/api/v1/financial",
    tags=["Payments & Gateway Management"],
    dependencies=[]
)

# ============================================
# HEALTH CHECK ENDPOINTS
# ============================================

@app.get("/health")
async def health_check():
    """Main service health check endpoint"""
    return {
        "status": "healthy",
        "service": "financial-service",
        "version": "2.0.0",
        "architecture": "modular",
        "modules": [
            "orders",
            "expenses",
            "pettycash",
            "voucher",
            "invoices",
            "payments"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/financial/health")
async def financial_health_check():
    """Financial service comprehensive health check"""
    try:
        # Test database connectivity
        from sqlalchemy import create_engine, text
        engine = create_engine(os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@postgres:5432/multitenant_db"
        ))
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()

        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "financial-service",
        "version": "2.0.0",
        "database": db_status,
        "modules": {
            "orders": "healthy",
            "expenses": "healthy",
            "pettycash": "healthy",
            "voucher": "healthy",
            "invoices": "healthy",
            "payments": "healthy"
        },
        "features": {
            "multi_tenant": True,
            "authentication": True,
            "authorization": True,
            "audit_trail": True,
            "soft_deletes": True
        },
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
    Initialize Financial schema for a new tenant with all modules

    Args:
        tenant_id: UUID of the tenant
        request: FastAPI request object
        db: Database session

    Returns:
        Initialization result with module status
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

        # Initialize schema with all Financial module tables
        logger.info(f"Initializing Financial schema for tenant {tenant_id} with all modules")
        result = schema_manager.initialize_tenant_schema(tenant_id, schema_name)

        if result["status"] == "success":
            logger.info(f"Successfully initialized Financial schema for tenant {tenant_id}")

            # Enhanced response with module information
            return {
                "status": "success",
                "tenant_id": tenant_id,
                "schema_name": schema_name,
                "initialized_modules": [
                    "orders",
                    "expenses",
                    "pettycash",
                    "voucher",
                    "invoices",
                    "payments"
                ],
                "tables_created": result.get("tables_created", []),
                "timestamp": datetime.utcnow().isoformat()
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
# AUTHENTICATION TEST ENDPOINTS
# ============================================

@app.get("/api/v1/financial/auth-test")
async def auth_test(
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant)
):
    """Test authentication functionality"""
    return {
        "message": "Authentication successful",
        "user_id": current_user.get("user_id"),
        "tenant_id": current_tenant.get("tenant_id"),
        "permissions": current_user.get("permissions", []),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/financial/tenant-auth-test")
async def tenant_auth_test(
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant),
    db: Session = Depends(get_tenant_db)
):
    """Test tenant-specific authentication and database access"""
    # Test basic permission
    await require_permission(current_user, "financial:read")

    try:
        # Test database connection for this tenant
        result = db.execute("SELECT 1 as test").fetchone()
        db_test = "success" if result else "failed"
    except Exception as e:
        db_test = f"failed: {str(e)}"

    return {
        "message": "Tenant authentication and database access test",
        "user_id": current_user.get("user_id"),
        "tenant_id": current_tenant.get("tenant_id"),
        "database_test": db_test,
        "permissions": current_user.get("permissions", []),
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# MODULE INFORMATION ENDPOINT
# ============================================

@app.get("/api/v1/financial/modules")
async def get_modules_info(
    current_user=Depends(get_current_user),
    current_tenant=Depends(get_current_tenant)
):
    """Get information about all financial modules"""
    await require_permission(current_user, "financial:read")

    return {
        "service": "financial-service",
        "version": "2.0.0",
        "architecture": "modular",
        "modules": {
            "orders": {
                "description": "Order and order line management",
                "models": ["Order", "OrderLine", "PassengerDocument"],
                "endpoints": [
                    "POST /orders", "GET /orders", "GET /orders/{id}",
                    "PUT /orders/{id}", "DELETE /orders/{id}"
                ]
            },
            "expenses": {
                "description": "Expense management with approval workflows",
                "models": ["Expense", "ExpenseCategory"],
                "endpoints": [
                    "POST /expenses", "GET /expenses", "POST /expenses/{id}/approve",
                    "POST /expenses/{id}/reimburse", "GET /expenses/summary"
                ]
            },
            "pettycash": {
                "description": "Petty cash fund management and reconciliation",
                "models": ["PettyCash", "PettyCashTransaction"],
                "endpoints": [
                    "POST /petty-cash", "GET /petty-cash", "POST /petty-cash/{id}/reconcile",
                    "POST /petty-cash/{id}/replenish", "GET /petty-cash/summary"
                ]
            },
            "voucher": {
                "description": "Payment voucher management and approval",
                "models": ["Voucher"],
                "endpoints": [
                    "POST /vouchers", "GET /vouchers", "POST /vouchers/{id}/approve",
                    "POST /vouchers/{id}/pay", "POST /vouchers/bulk-approve"
                ]
            },
            "invoices": {
                "description": "Invoice, accounts receivable and payable management",
                "models": ["Invoice", "InvoiceLine", "AccountsReceivable", "AccountsPayable"],
                "endpoints": [
                    "POST /invoices", "GET /invoices", "POST /invoices/{id}/send",
                    "POST /accounts-receivable", "POST /accounts-payable"
                ]
            },
            "payments": {
                "description": "Payment processing, gateways and transaction management",
                "models": ["Payment", "PaymentGateway", "PaymentAttempt"],
                "endpoints": [
                    "POST /payments", "POST /payments/process", "POST /payments/{id}/refund",
                    "POST /payment-gateways", "GET /payments/summary"
                ]
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with enhanced error information"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "service": "financial-service",
            "version": "2.0.0",
            "path": str(request.url),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with detailed logging"""
    logger.error(f"Unhandled exception in {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "service": "financial-service",
            "version": "2.0.0",
            "path": str(request.url),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Financial Service",
        "version": "2.0.0",
        "architecture": "Modular",
        "description": "Comprehensive Financial Management Service with Modular Architecture",
        "modules": ["orders", "expenses", "pettycash", "voucher", "invoices", "payments"],
        "documentation": "/docs",
        "health_check": "/health",
        "api_base": "/api/v1/financial",
        "features": [
            "Multi-tenant support",
            "Role-based authentication",
            "Audit trails",
            "Soft deletes",
            "Comprehensive reporting",
            "Workflow automation"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8012))
    logger.info(f"Starting Financial Service on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
