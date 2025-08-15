# Modular Pattern Guide for Travel System Microservices

Complete practical guide with concrete examples for migrating monolithic services to the proven modular architecture.

## 🎯 Why Migrate to Modular Architecture?

### Current Problems with Monolithic Services
- **All models in one file**: Hard to find and maintain specific entities
- **Mixed responsibilities**: Business logic scattered across large files
- **No authentication**: Security vulnerabilities and inconsistent access control
- **Difficult scaling**: Can't work on different features simultaneously
- **Testing challenges**: Hard to test individual components

### Benefits of Modular Architecture
- **Clear separation**: Each module has specific responsibility
- **Easy maintenance**: Find and modify code quickly
- **Team collaboration**: Multiple developers can work simultaneously
- **Scalable growth**: Add new features without affecting existing ones
- **Better testing**: Test modules independently
- **Consistent authentication**: Unified security across all endpoints

## 🏗️ The Reference Pattern: Communication Service

The `communication-service` demonstrates the gold standard:

```
communication-service/
├── inbox/                    # External communications module
│   ├── models.py            # InboxConversation, InboxMessage, InboxQuickReply
│   ├── schemas.py           # ConversationCreate, MessageCreate, etc.
│   └── endpoints.py         # Conversation and message APIs
├── chat/                     # Internal team communication module
│   ├── models.py            # Channel, ChannelMember, ChatEntry, Mention
│   ├── schemas.py           # ChannelCreate, ChatEntryCreate, etc.
│   └── endpoints.py         # Chat and channel management APIs
├── common/                   # Shared utilities
│   └── enums.py             # ChannelType, MessageStatus, etc.
├── main.py                   # Clean application entry point
├── database.py               # Multi-tenant session management
├── schema_manager.py         # Tenant schema initialization
├── shared_auth.py            # JWT authentication system
└── requirements.txt
```

## 🔄 Step-by-Step Migration Process

### Phase 1: Analysis and Planning

#### 1.1 Analyze Current Service
```bash
# List all current endpoints
grep -r "@app\." services/YOUR-SERVICE/ | grep "def "

# List all models  
grep -r "class.*Base" services/YOUR-SERVICE/models.py

# Count lines of code
wc -l services/YOUR-SERVICE/main.py services/YOUR-SERVICE/models.py
```

#### 1.2 Identify Logical Modules
Group related functionality:

**CRM Service Example:**
- Models: `Lead`, `Customer`, `Contact`, `Opportunity`, `SalesActivity`
- Logical grouping:
  - `leads/` → Lead, SalesActivity
  - `customers/` → Customer, Contact  
  - `sales/` → Opportunity, SalesStage

**Financial Service Example:**
- Models: `Payment`, `Invoice`, `Commission`, `Transaction`, `Report`
- Logical grouping:
  - `payments/` → Payment, Transaction
  - `invoicing/` → Invoice, InvoiceLine
  - `reporting/` → Report, Analytics

### Phase 2: Prepare Migration Environment

#### 2.1 Backup Current Service
```bash
# Create backup branch
cd services/YOUR-SERVICE
git checkout -b backup-before-migration
git add . && git commit -m "Backup before modular migration"
git checkout main
```

#### 2.2 Copy Reference Files
```bash
# Copy authentication system
cp services/communication-service/shared_auth.py services/YOUR-SERVICE/

# Copy database management (if needed)
cp services/communication-service/database.py services/YOUR-SERVICE/database_reference.py
```

### Phase 3: Create Modular Structure

#### 3.1 Create Directory Structure
```bash
# Example for CRM service
mkdir -p services/crm-service/leads
mkdir -p services/crm-service/customers  
mkdir -p services/crm-service/sales
mkdir -p services/crm-service/common

# Create __init__.py files
touch services/crm-service/leads/__init__.py
touch services/crm-service/customers/__init__.py
touch services/crm-service/sales/__init__.py
touch services/crm-service/common/__init__.py
```

#### 3.2 Create Base Module Files

**Template for `module/models.py`:**
```python
"""
Module Name Models
SQLAlchemy models for [module purpose]
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class YourModel(Base):
    __tablename__ = "your_table"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    # Add your specific fields
    
    # Standard audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<YourModel(id={self.id}, name={self.name})>"
```

**Template for `module/schemas.py`:**
```python
"""
Module Name Schemas
Pydantic models for API validation and serialization
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class YourStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

# Request schemas
class YourModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: YourStatus = YourStatus.ACTIVE

class YourModelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[YourStatus] = None

# Response schemas
class YourModelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: YourStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Template for `module/endpoints.py`:**
```python
"""
Module Name Endpoints
API endpoints for [module purpose]
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

# Import shared authentication
from shared_auth import get_current_user, check_tenant_slug_access

from database import get_tenant_session
from .models import YourModel
from .schemas import YourModelCreate, YourModelUpdate, YourModelResponse

# Create router
router = APIRouter(prefix="/api/v1/your-module", tags=["Your Module"])

@router.post("/", response_model=YourModelResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_data: YourModelCreate,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new item"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        item = YourModel(**item_data.dict())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

@router.get("/", response_model=List[YourModelResponse])
async def list_items(
    tenant_slug: str = Query(..., description="Tenant identifier"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List items with pagination"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        items = db.query(YourModel).offset(skip).limit(limit).all()
        return items

@router.get("/{item_id}", response_model=YourModelResponse)
async def get_item(
    item_id: str,
    tenant_slug: str = Query(..., description="Tenant identifier"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get item by ID"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to tenant: {tenant_slug}"
        )

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        item = db.query(YourModel).filter(YourModel.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return item
```

## 🎯 Concrete Migration Examples

### Example 1: Migrating CRM Service

#### Current State (Monolithic)
```python
# models.py - Everything mixed together
class Lead(Base):
    __tablename__ = "leads"
    # 50 lines of lead fields

class Customer(Base):
    __tablename__ = "customers" 
    # 60 lines of customer fields

class Opportunity(Base):
    __tablename__ = "opportunities"
    # 40 lines of opportunity fields

# main.py - All endpoints in one file
@app.get("/leads")
def get_leads():
    # No authentication
    return db.query(Lead).all()

@app.post("/customers")  
def create_customer():
    # No tenant validation
    # Mixed with other logic
```

#### After Migration (Modular)
```
crm-service/
├── leads/
│   ├── models.py      # Only Lead and related models
│   ├── schemas.py     # LeadCreate, LeadUpdate, LeadResponse
│   └── endpoints.py   # Lead CRUD with authentication
├── customers/
│   ├── models.py      # Only Customer and related models
│   ├── schemas.py     # CustomerCreate, CustomerUpdate, CustomerResponse
│   └── endpoints.py   # Customer CRUD with authentication
├── sales/
│   ├── models.py      # Opportunity, SalesStage
│   ├── schemas.py     # OpportunityCreate, etc.
│   └── endpoints.py   # Sales pipeline management
├── shared_auth.py     # Authentication system
└── main.py           # Clean router includes
```

**Migration Steps for CRM:**

1. **Create leads module:**
```bash
mkdir -p services/crm-service/leads
```

2. **Move Lead model:**
```python
# leads/models.py
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    source = Column(String(100))
    status = Column(String(50), default="new")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

3. **Create schemas:**
```python
# leads/schemas.py
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
    notes: Optional[str] = None

class LeadResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    source: Optional[str]
    status: LeadStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

4. **Create endpoints with authentication:**
```python
# leads/endpoints.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any

from shared_auth import get_current_user, check_tenant_slug_access
from database import get_tenant_session
from .models import Lead
from .schemas import LeadCreate, LeadResponse

router = APIRouter(prefix="/api/v1/leads", tags=["Leads"])

@router.post("/", response_model=LeadResponse)
async def create_lead(
    lead_data: LeadCreate,
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        lead = Lead(**lead_data.dict())
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        leads = db.query(Lead).all()
        return leads
```

5. **Update main.py:**
```python
# main.py
from fastapi import FastAPI
from leads.endpoints import router as leads_router

app = FastAPI(title="CRM Service", version="2.0.0")
app.include_router(leads_router)

@app.get("/health") 
async def health():
    return {"status": "healthy", "modules": {"leads": "active"}}
```

### Example 2: Migrating Financial Service

#### Before (Monolithic)
```python
# Everything in models.py
class Payment(Base): pass
class Invoice(Base): pass  
class Commission(Base): pass
class Report(Base): pass

# Everything in main.py
@app.get("/payments")
@app.get("/invoices")
@app.get("/commissions")
@app.get("/reports")
```

#### After (Modular)
```
financial-service/
├── payments/          # Payment processing
│   ├── models.py     # Payment, Transaction, PaymentMethod
│   ├── schemas.py    # PaymentCreate, PaymentResponse
│   └── endpoints.py  # Payment processing APIs
├── invoicing/         # Invoice management
│   ├── models.py     # Invoice, InvoiceLine, InvoiceTemplate
│   ├── schemas.py    # InvoiceCreate, InvoiceResponse
│   └── endpoints.py  # Invoice CRUD and generation
├── reporting/         # Financial reporting
│   ├── models.py     # Report, ReportTemplate
│   ├── schemas.py    # ReportCreate, ReportResponse
│   └── endpoints.py  # Report generation and viewing
└── commissions/       # Commission management
    ├── models.py     # Commission, CommissionRule
    ├── schemas.py    # CommissionCreate, CommissionResponse
    └── endpoints.py  # Commission calculation
```

## 🔐 Authentication Integration Patterns

### Pattern 1: Basic Authentication
```python
# Any endpoint that needs a logged-in user
@router.get("/data")
async def get_data(current_user: dict = Depends(get_current_user)):
    return {"user": current_user["username"]}
```

### Pattern 2: Tenant-Specific Data
```python
# Most common pattern for business data
@router.get("/leads")
async def get_leads(
    tenant_slug: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    # Always validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get tenant-specific database
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        return db.query(Lead).all()
```

### Pattern 3: Admin-Only Operations
```python
# For sensitive operations
@router.delete("/leads/{lead_id}")
async def delete_lead(
    lead_id: str,
    tenant_slug: str = Query(...),
    current_user: dict = Depends(require_tenant_admin)  # Admin required
):
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        # Delete logic here
        pass
```

### Pattern 4: Permission-Based Access
```python
# For granular permissions
@router.post("/payments")
async def process_payment(
    payment_data: PaymentCreate,
    tenant_slug: str = Query(...),
    current_user: dict = Depends(get_current_user)
):
    # Check specific permission
    if not check_permission(current_user, "payments.process"):
        raise HTTPException(status_code=403, detail="Payment permission required")
    
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Payment processing logic
```

## 🧪 Testing Migration

### Test Script Template
```bash
#!/bin/bash
# test_migration.sh

SERVICE_URL="http://localhost:YOUR_PORT"
SERVICE_NAME="YOUR_SERVICE"

echo "🧪 Testing $SERVICE_NAME Migration"

# Test 1: Health check
curl -s $SERVICE_URL/health || echo "❌ Service not running"

# Test 2: Create test token
TOKEN=$(docker-compose exec -T $SERVICE_NAME python3 -c "
from shared_auth import create_access_token
token = create_access_token({
    'sub': 'test_user',
    'tenant_slug': 'demo',
    'role': 'tenant_admin'
})
print(token)
")

# Test 3: Auth endpoint
echo "Testing authentication..."
curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/api/v1/auth/test

# Test 4: Protected endpoint
echo "Testing protected endpoint..."
curl -s -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/api/v1/your-endpoint/?tenant_slug=demo"

echo "✅ Migration test completed"
```

## 📊 Migration Complexity by Service

### Low Complexity (Start Here)
**System Service**: Already partially modular
- Estimated time: 2-3 hours
- Main task: Add authentication
- Modules: `users/`, `roles/`, `settings/`

### Medium Complexity
**CRM Service**: Clear business boundaries
- Estimated time: 4-6 hours  
- Main task: Separate leads/customers/sales
- Modules: `leads/`, `customers/`, `sales/`

**Financial Service**: Well-defined domains
- Estimated time: 4-6 hours
- Main task: Separate payments/invoicing/reporting
- Modules: `payments/`, `invoicing/`, `reporting/`

### High Complexity
**Booking Service**: Complex relationships
- Estimated time: 6-8 hours
- Main task: Untangle booking/itinerary/package logic
- Modules: `bookings/`, `itineraries/`, `packages/`, `operations/`

## 🔧 Migration Checklist Template

### Pre-Migration
- [ ] Service is currently working and tested
- [ ] Created backup branch
- [ ] Identified logical modules (2-4 modules max)
- [ ] Planned module responsibilities
- [ ] Reviewed communication-service pattern

### During Migration  
- [ ] Created directory structure
- [ ] Copied shared_auth.py
- [ ] Migrated models to modules (one at a time)
- [ ] Created Pydantic schemas
- [ ] Migrated endpoints with authentication
- [ ] Updated main.py to include routers
- [ ] Added test endpoints

### Post-Migration
- [ ] All endpoints return expected responses
- [ ] Authentication working (401 without token)
- [ ] Tenant access control working (403 for wrong tenant)
- [ ] Database operations successful
- [ ] Service starts without errors
- [ ] Updated service README
- [ ] Performance is acceptable

## 🚨 Common Pitfalls and Solutions

### Pitfall 1: Import Circular Dependencies
**Problem:** Module A imports from Module B which imports from Module A

**Solution:** Use common module for shared entities
```python
# ❌ Don't do this
# leads/models.py
from customers.models import Customer  

# ✅ Do this instead  
# common/enums.py
class LeadSource(Enum):
    WEBSITE = "website"
    
# leads/models.py  
from common.enums import LeadSource
```

### Pitfall 2: Database Session Issues
**Problem:** `TypeError: 'dict' object is not callable`

**Solution:** Use manual session creation pattern
```python
# ❌ Don't do this
db: Session = Depends(lambda: get_tenant_db(tenant_slug))

# ✅ Do this instead
with get_tenant_session(f"tenant_{tenant_slug}") as db:
    # Your queries
```

### Pitfall 3: Missing Authentication
**Problem:** Forgot to add auth to some endpoints

**Solution:** Use consistent pattern for all endpoints
```python
# ✅ Always include these
tenant_slug: str = Query(...)
current_user: Dict[str, Any] = Depends(get_current_user)

# ✅ Always validate
if not check_tenant_slug_access(current_user, tenant_slug):
    raise HTTPException(status_code=403, detail="Access denied")
```

### Pitfall 4: Over-Modularization
**Problem:** Too many small modules

**Solution:** Group related functionality
```python
# ❌ Too granular
# lead_creation/, lead_updating/, lead_deletion/

# ✅ Right level
# leads/ (handles all lead operations)
```

## 🎯 Migration Success Metrics

### Before Migration
- Lines of code in main.py: >500
- Models in models.py: >10  
- Endpoints without auth: >80%
- Development difficulty: High

### After Migration  
- Lines of code in main.py: <100
- Models per module: 2-5
- Endpoints with auth: 100%
- Development difficulty: Low

## 🚀 Quick Migration Commands

### For CRM Service
```bash
# 1. Backup
git checkout -b backup-crm-migration

# 2. Create structure
mkdir -p services/crm-service/{leads,customers,sales,common}

# 3. Copy auth
cp services/communication-service/shared_auth.py services/crm-service/

# 4. Create base files
touch services/crm-service/{leads,customers,sales,common}/__init__.py
touch services/crm-service/leads/{models,schemas,endpoints}.py
touch services/crm-service/customers/{models,schemas,endpoints}.py
touch services/crm-service/sales/{models,schemas,endpoints}.py
```

### For Financial Service
```bash
# Similar pattern for financial service
mkdir -p services/financial-service/{payments,invoicing,reporting,common}
cp services/communication-service/shared_auth.py services/financial-service/
```

## 📚 Additional Resources

### Reference Files
- `services/communication-service/` - Complete reference implementation
- `services/shared/auth.py` - Master authentication system
- `services/communication-service/README.md` - Documentation pattern

### Testing Tools
- Health check: `curl http://localhost:PORT/health`
- Auth test: `curl http://localhost:PORT/api/v1/auth/test`  
- Swagger docs: `http://localhost:PORT/docs`

## 🎯 Success Stories

### Communication Service
✅ **Before**: Monolithic structure
✅ **After**: 2 modules (inbox, chat), full authentication
✅ **Result**: Easier to maintain, secure, scalable

### Next Target: CRM Service
🎯 **Goal**: Apply same pattern
🎯 **Expected**: 3 modules (leads, customers, sales)
🎯 **Timeline**: 1 sprint

---

## 🚀 Ready to Migrate?

1. **Choose your service** (start with CRM for practice)
2. **Follow the checklist** step by step
3. **Use communication-service** as reference
4. **Test frequently** during migration
5. **Keep it simple** - don't over-engineer

**Remember**: The goal is maintainable, secure, scalable code. The communication-service proves this pattern works! 🎉