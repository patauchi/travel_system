from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from jose import JWTError, jwt
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Tenant API Gateway",
    description="Central API Gateway for Multi-Tenant Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
SERVICE_TOKEN_EXPIRE_HOURS = 24

# Security scheme
security = HTTPBearer(auto_error=False)

# Service URLs
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
TENANT_SERVICE_URL = os.getenv("TENANT_SERVICE_URL", "http://tenant-service:8002")
BUSINESS_SERVICE_URL = os.getenv("BUSINESS_SERVICE_URL", "http://business-service:8003")

def create_service_token() -> str:
    """Create a token for service-to-service communication"""
    data = {
        "sub": "api-gateway",
        "type": "service",
        "service": "api-gateway",
        "role": "super_admin",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=SERVICE_TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def verify_user_token(token: str) -> Dict[str, Any]:
    """Verify and decode a user JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Extract current user from JWT token if present"""
    if not credentials:
        return None

    try:
        payload = verify_user_token(credentials.credentials)
        return {
            "token": credentials.credentials,
            "user_id": payload.get("sub"),
            "tenant_id": payload.get("tenant_id"),
            "role": payload.get("role"),
            "email": payload.get("email"),
            "username": payload.get("username")
        }
    except HTTPException:
        return None

# Health check for dependent services
async def check_service_health(service_url: str, service_name: str) -> Dict[str, Any]:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            if response.status_code == 200:
                return {"name": service_name, "status": "healthy", "url": service_url}
            else:
                return {"name": service_name, "status": "unhealthy", "url": service_url}
    except Exception as e:
        return {"name": service_name, "status": "error", "url": service_url, "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Multi-Tenant API Gateway",
        "version": "1.0.0",
        "description": "Central gateway for all microservices",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "auth": "/api/v1/auth",
            "tenants": "/api/v1/tenants",
            "business": "/api/v1/business"
        },
        "services": {
            "auth": AUTH_SERVICE_URL,
            "tenant": TENANT_SERVICE_URL,
            "business": BUSINESS_SERVICE_URL
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services_health = await asyncio.gather(
        check_service_health(AUTH_SERVICE_URL, "auth-service"),
        check_service_health(TENANT_SERVICE_URL, "tenant-service"),
        check_service_health(BUSINESS_SERVICE_URL, "business-service"),
        return_exceptions=True
    )

    all_healthy = all(
        service.get("status") == "healthy"
        for service in services_health
        if isinstance(service, dict)
    )

    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": services_health
    }

@app.get("/api/v1/services/status")
async def services_status():
    """Get status of all services"""
    import asyncio

    services_health = await asyncio.gather(
        check_service_health(AUTH_SERVICE_URL, "auth-service"),
        check_service_health(TENANT_SERVICE_URL, "tenant-service"),
        check_service_health(BUSINESS_SERVICE_URL, "business-service"),
        return_exceptions=True
    )

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": services_health
    }

# Auth Service Routes
@app.api_route("/api/v1/auth", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth_base(request: Request):
    """Proxy requests to auth service base"""
    return await proxy_request(request, AUTH_SERVICE_URL, "/api/v1/auth")

@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_auth(request: Request, path: str):
    """Proxy requests to auth service"""
    return await proxy_request(request, AUTH_SERVICE_URL, f"/api/v1/auth/{path}")

# Tenant Service Routes
@app.api_route("/api/v1/tenants", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_tenants_base(request: Request):
    """Proxy requests to tenant service base"""
    return await proxy_request(request, TENANT_SERVICE_URL, "/api/v1/tenants")

@app.api_route("/api/v1/tenants/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_tenants(request: Request, path: str):
    """Proxy requests to tenant service"""
    return await proxy_request(request, TENANT_SERVICE_URL, f"/api/v1/tenants/{path}")

# Business Service Routes
@app.api_route("/api/v1/business", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_business_base(request: Request):
    """Proxy requests to business service base"""
    return await proxy_request(request, BUSINESS_SERVICE_URL, "/api/v1/business")

@app.api_route("/api/v1/business/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_business(request: Request, path: str):
    """Proxy requests to business service"""
    return await proxy_request(request, BUSINESS_SERVICE_URL, f"/api/v1/business/{path}")

# Generic proxy function
async def proxy_request(
    request: Request,
    service_url: str,
    path: str,
    headers: Optional[Dict[str, str]] = None
):
    """Generic proxy function for forwarding requests to services"""
    # Build the full URL
    url = f"{service_url}{path}"

    # Get query parameters
    query_params = dict(request.query_params)

    # Use provided headers or get from request
    if headers is None:
        headers = dict(request.headers)

    # Remove host header as it will be set by httpx
    headers.pop("host", None)

    # Get body for POST/PUT requests
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    try:
        # Make the request to the microservice
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=url,
                params=query_params,
                headers=headers,
                content=body
            )

        # Return the response
        return JSONResponse(
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: Cannot connect to {service_url}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Service timeout: Request to {service_url} timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Catch-all route for undefined endpoints
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path: str):
    """Catch all undefined routes"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Route not found",
            "path": f"/{path}",
            "method": request.method,
            "available_endpoints": [
                "/api/v1/auth",
                "/api/v1/tenants",
                "/api/v1/business"
            ],
            "documentation": "/docs"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
