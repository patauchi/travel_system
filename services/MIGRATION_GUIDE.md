# Service Migration Guide

Complete guide for migrating monolithic services to the modular, authenticated architecture used by `communication-service`.

## 🎯 Migration Overview

This guide will help you transform existing monolithic services into scalable, maintainable, and secure microservices with proper authentication and modular structure.

### Current State vs Target State

**Before (Monolithic):**
```
service-name/
├── main.py          # Everything in one file
├── models.py        # All models mixed together
├── requirements.txt
└── Dockerfile
```

**After (Modular):**
```
service-name/
├── module1/            # Feature-based modules
│   ├── __init__.py
│   ├── models.py      # Module-specific models
│   ├── schemas.py     # Pydantic schemas
│   └── endpoints.py   # Module endpoints
├── module2/
├── common/            # Shared utilities
│   ├── __init__.py
│   └── enums.py      # Common enums
├── main.py           # Clean application entry
├── database.py       # DB session management
├── shared_auth.py    # Authentication system
├── requirements.txt
└── Dockerfile
```

## 📋 Migration Checklist

### Phase 1: Preparation ✅
- [ ] Backup current service code
- [ ] Identify logical modules/features
- [ ] List all current endpoints
- [ ] Document current database models
- [ ] Test current functionality

### Phase 2: Structure Setup ✅
- [ ] Create modular directory structure
- [ ] Copy shared authentication system
- [ ] Set up database management
- [ ] Create base files for each module

### Phase 3: Code Migration ✅
- [ ] Migrate models to appropriate modules
- [ ] Create Pydantic schemas
- [ ] Migrate endpoints with authentication
- [ ] Update main.py to use modules
- [ ] Test each module independently

### Phase 4: Authentication Integration ✅
- [ ] Add authentication to all protected endpoints
- [ ] Implement tenant access control
- [ ] Test authentication flows
- [ ] Verify security measures

### Phase 5: Testing & Validation ✅
- [ ] Run integration tests
- [ ] Verify all endpoints work
- [ ] Check performance
- [ ] Update documentation

## 🏗️ Step-by-Step Migration Process

### Step 1: Analyze Current Service

First, understand what you're working with:

```bash
# List all endpoints in your service
grep -r "@app\." services/YOUR-SERVICE/
grep -r "@router\." services/YOUR-SERVICE/

# List all models
grep -r "class.*Base" services/YOUR-SERVICE/models.py
```

**Example Analysis for CRM Service:**
```
Current endpoints:
- /leads (GET, POST, PUT, DELETE)
- /customers (GET, POST, PUT, DELETE) 
- /contacts (GET, POST, PUT)
- /opportunities (GET, POST, PUT)

Current models:
- Lead, Customer, Contact, Opportunity, SalesActivity
```

### Step 2: Design Module Structure

Group related functionality into logical modules:

**CRM Service Example:**
```
crm-service/
├── leads/              # Lead management
│   ├── models.py      # Lead, SalesActivity
│   ├── schemas.py     # LeadCreate, LeadResponse
│   └── endpoints.py   # Lead CRUD operations
├── customers/          # Customer management  
│   ├── models.py      # Customer, Contact
│   ├── schemas.py     # CustomerCreate, CustomerResponse
│   └── endpoints.py   # Customer CRUD operations
├── opportunities/      # Sales opportunities
│   ├── models.py      # Opportunity, OpportunityStage
│   ├── schemas.py     # OpportunityCreate, OpportunityResponse
│   └── endpoints.py   # Opportunity management
├── common/
│   └── enums.py       # LeadStatus, CustomerType, etc.
├── main.py
├── database.py
└── shared_auth.py
```

### Step 3: Copy Shared Authentication

Copy the authentication system from communication-service:

```bash
# Copy authentication system
cp services/communication-service/shared_auth.py services/YOUR-SERVICE/

# Copy database management pattern  
cp services/communication-service/database.py services/YOUR-SERVICE/database.py
```

### Step 4: Create Module Structure

For each module, create the directory and base files:

```bash
# Create module directories
mkdir -p services/YOUR-SERVICE/leads
mkdir -p services/YOUR-SERVICE/customers
mkdir -p services/YOUR-SERVICE/common

# Create __init__.py files
touch services/YOUR-SERVICE/leads/__init__.py
touch services/YOUR-SERVICE/customers/__init__.py
touch services/YOUR-SERVICE/common/__init__.py
```

### Step 5: Migrate Models

Move models to appropriate modules:

**Before (monolithic `models.py`):**
```python
# All models in one file
class Lead(Base):
    __tablename__ = "leads"
    # ... 

class Customer(Base):
    __tablename__ = "customers"
    # ...

class Opportunity(Base):
    __tablename__ = "opportunities"
    # ...
```

**After (modular):**

`leads/models.py`:
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    # ... other fields
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

`customers/models.py`:
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # ... customer fields
```

### Step 6: Create Pydantic Schemas

Create validation schemas for each module:

`leads/schemas.py`:
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted" 
    QUALIFIED = "qualified"
    CONVERTED = "converted"

class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = None
    source: Optional[str] = None
    status: LeadStatus = LeadStatus.NEW

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None

class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### Step 7: Migrate Endpoints with Authentication

Transform endpoints to use the modular pattern:

`leads/endpoints.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import shared authentication
from shared_auth import get_current_user, check_tenant_slug_access

from database import get_tenant_session
from .models import Lead
from .schemas import LeadCreate, LeadUpdate, LeadResponse

# Create router
leads_router = APIRouter(prefix="/api/v1/leads", tags=["Leads"])

@leads_router.post("/", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: LeadCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new lead"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        lead = Lead(**lead_data.dict())
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

@leads_router.get("/", response_model=List[LeadResponse])
async def list_leads(
    tenant_slug: str = Query(..., description="Tenant identifier"),
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List leads with filters"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        query = db.query(Lead)
        
        if status:
            query = query.filter(Lead.status == status)
            
        leads = query.offset(skip).limit(limit).all()
        return leads
```

### Step 8: Update Main Application

Update `main.py` to use the modular structure:

```python
"""
Service Name - Modular Architecture
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from typing import Dict, Any
from datetime import datetime

# Import shared authentication
from shared_auth import get_current_user, require_super_admin

# Import database management
from database import verify_connection
from schema_manager import SchemaManager

# Import module routers
from leads.endpoints import leads_router
from customers.endpoints import customers_router
from opportunities.endpoints import opportunities_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Service...")
    if not verify_connection():
        raise Exception("Database connection failed")
    logger.info("Service started successfully")
    yield
    logger.info("Shutting down Service...")

# Create FastAPI application
app = FastAPI(
    title="Your Service Name",
    description="Modular microservice with authentication",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include module routers
app.include_router(leads_router)
app.include_router(customers_router)
app.include_router(opportunities_router)

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Your Service Name",
        "modules": {
            "leads": "active",
            "customers": "active",
            "opportunities": "active"
        }
    }

# Authentication test endpoints
@app.get("/api/v1/auth/test")
async def auth_test(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Authentication working!",
        "user": {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
            "tenant_slug": current_user.get("tenant_slug")
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8006, reload=True)
```

## 🔄 Service-Specific Migration Examples

### CRM Service Migration

**Current Issues:**
- All models in one file (leads, customers, contacts, opportunities)
- No authentication on endpoints
- Mixed responsibilities

**Migration Plan:**
```
crm-service/
├── leads/              # Lead management and qualification
├── customers/          # Customer profiles and history
├── sales/             # Sales pipeline and opportunities
├── contacts/          # Contact management
├── common/            # Shared CRM enums and utilities
```

### Financial Service Migration

**Current Issues:**
- Payment, invoice, commission logic mixed
- No proper tenant isolation
- Missing authentication

**Migration Plan:**
```
financial-service/
├── payments/          # Payment processing
├── invoicing/         # Invoice management
├── commissions/       # Commission calculations
├── reporting/         # Financial reporting
├── common/           # Financial enums and utilities
```

### Booking Operations Service Migration

**Current Issues:**
- Booking, itinerary, package logic in one place
- Complex interdependencies

**Migration Plan:**
```
booking-service/
├── bookings/          # Booking management
├── itineraries/       # Travel itinerary planning
├── packages/          # Package definitions
├── operations/        # Operational tasks
├── common/           # Booking enums and utilities
```

## 🔐 Authentication Integration Steps

### Step 1: Copy Authentication System

```bash
# Copy from communication-service
cp services/communication-service/shared_auth.py services/YOUR-SERVICE/
```

### Step 2: Add Authentication to Endpoints

**Pattern to follow:**
```python
from shared_auth import get_current_user, check_tenant_slug_access

@router.post("/resource")
async def create_resource(
    data: ResourceCreate,
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # 1. Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # 2. Get database session
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        # 3. Your business logic
        resource = Resource(**data.dict())
        db.add(resource)
        db.commit()
        return resource
```

### Step 3: Add Test Endpoints

Add these to every migrated service for testing:

```python
@app.get("/api/v1/auth/test")
async def auth_test(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Authentication working!",
        "user": current_user,
        "service": "YOUR-SERVICE-NAME"
    }

@app.get("/api/v1/tenants/{tenant_slug}/auth/test")
async def tenant_auth_test(
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "message": f"Tenant access working for {tenant_slug}!",
        "user_tenant": current_user.get("tenant_slug"),
        "requested_tenant": tenant_slug
    }
```

## 🎯 Module Design Principles

### 1. Single Responsibility
Each module should handle one business domain:
- ✅ `leads/` - Only lead management
- ✅ `customers/` - Only customer data
- ❌ `mixed/` - Don't mix leads and customers

### 2. Clear Dependencies
```python
# ✅ Good - Clear imports
from shared_auth import get_current_user
from database import get_tenant_session
from .models import Lead
from .schemas import LeadCreate

# ❌ Bad - Importing from other modules
from customers.models import Customer  # Wrong!
```

### 3. Consistent Structure
Every module should have:
- `models.py` - Database models
- `schemas.py` - Pydantic validation
- `endpoints.py` - API routes
- `__init__.py` - Module exports

### 4. Authentication Pattern
Every protected endpoint should:
```python
async def endpoint(
    tenant_slug: str = Query(...),                    # 1. Tenant parameter
    current_user: Dict[str, Any] = Depends(get_current_user)  # 2. Auth dependency
):
    if not check_tenant_slug_access(current_user, tenant_slug):  # 3. Tenant validation
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_tenant_session(f"tenant_{tenant_slug}") as db:     # 4. DB session
        # Your logic here
```

## 🧪 Testing Migration

### Test Authentication
```bash
# Create test token
TOKEN=$(docker-compose exec -T YOUR-SERVICE python3 -c "
from shared_auth import create_access_token
token = create_access_token({
    'sub': 'test_user',
    'tenant_slug': 'demo', 
    'role': 'tenant_admin'
})
print(token)
")

# Test without auth (should fail)
curl http://localhost:PORT/api/v1/auth/test

# Test with auth (should work)
curl -H "Authorization: Bearer $TOKEN" http://localhost:PORT/api/v1/auth/test
```

### Test Endpoints
```bash
# Test protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:PORT/api/v1/leads/?tenant_slug=demo"
```

## 🚨 Common Migration Issues

### Issue 1: Import Errors
**Problem:** `ModuleNotFoundError: No module named 'shared_auth'`

**Solution:** Check file path and ensure shared_auth.py is in service directory

### Issue 2: Database Session Errors
**Problem:** `'dict' object is not callable`

**Solution:** Use manual session creation after authentication:
```python
with get_tenant_session(f"tenant_{tenant_slug}") as db:
    # Your queries here
```

### Issue 3: Token Validation Fails
**Problem:** `Could not validate credentials`

**Solution:** Ensure JWT_SECRET_KEY is consistent across all services

### Issue 4: Tenant Access Denied
**Problem:** `Access denied to tenant: demo`

**Solution:** Check that user's `tenant_slug` matches the requested tenant

## 📋 Migration Priority Order

Recommended order to migrate services:

1. **CRM Service** - Most business logic, good for testing patterns
2. **Financial Service** - Critical for security testing
3. **Booking Service** - Complex relationships, good for advanced patterns
4. **System Service** - Already partially modular

## 🎯 Success Criteria

A successful migration includes:

✅ **Modular Structure**: Clear separation of concerns
✅ **Authentication**: All endpoints properly protected
✅ **Tenant Isolation**: Multi-tenant access control working
✅ **Documentation**: Updated README and API docs
✅ **Testing**: Auth and functionality tests passing
✅ **Performance**: No degradation in response times

## 📚 Reference Implementation

Use `communication-service` as your reference:

- **Authentication**: `shared_auth.py`
- **Module Structure**: `inbox/` and `chat/` modules
- **Database Handling**: `database.py` with tenant sessions
- **Endpoint Pattern**: See `inbox/endpoints.py`

## 🔄 Rollback Plan

If migration fails:

1. **Git Reset**: `git checkout HEAD~1` to previous working version
2. **Docker Rollback**: `docker-compose build SERVICE && docker-compose up -d SERVICE`
3. **Test Recovery**: Verify all endpoints work again

## 🤝 Migration Support

### Before Starting
- Review this guide completely
- Understand the communication-service structure
- Test authentication system manually
- Plan your module breakdown

### During Migration
- Migrate one module at a time
- Test after each module migration
- Keep authentication simple
- Don't over-engineer

### After Migration
- Update service documentation
- Add comprehensive tests
- Monitor performance
- Share learnings with team

---

## 🏆 Expected Benefits After Migration

1. **Maintainability**: Code is easier to understand and modify
2. **Scalability**: New features can be added as separate modules
3. **Security**: Proper authentication and tenant isolation
4. **Team Collaboration**: Multiple developers can work on different modules
5. **Testing**: Each module can be tested independently
6. **Performance**: Better organization leads to better performance

---

**Next Steps**: Choose your first service to migrate and follow this guide step by step. Start with the simplest service to validate the pattern before tackling complex ones.

**Remember**: Keep it simple, follow the communication-service pattern, and test frequently!