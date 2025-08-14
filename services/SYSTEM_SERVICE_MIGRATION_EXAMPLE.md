# System Service Migration Example

Real-world example of migrating the `system-service` from monolithic to modular architecture with authentication.

## 🎯 Current State Analysis

### Existing Models (27 total in 2 files)

**Core Models (models.py):**
- `User` - Tenant users with profiles, roles, sessions
- `Role` - User roles with hierarchical permissions  
- `Permission` - Granular permissions for resources/actions
- `Team` - Departments and team organization
- `Setting` - Tenant configuration settings
- `AuditLog` - System action audit trail

**Extended Models (models_extended.py):**
- `Note` - Documentation and notes system
- `Task` - Task management and assignment
- `LogCall` - Call logging and tracking
- `Event` - Calendar and event management
- `Attachment` - File attachment system
- `ChannelConfig` - Integration configurations

### Current Issues
- 🚨 **27 models in 2 large files** - Hard to navigate
- 🚨 **No authentication** on endpoints - Security risk
- 🚨 **Mixed responsibilities** - Users + Tools + Settings all together
- 🚨 **Monolithic structure** - Difficult team collaboration

## 🏗️ Target Modular Structure

```
system-service/
├── users/                    # 👥 User Management (User, Role, Permission, Team)
│   ├── models.py            # User, Role, Permission, Team
│   ├── schemas.py           # UserCreate, RoleCreate, TeamCreate
│   └── endpoints.py         # User/Role/Team CRUD + Authentication
├── settings/                 # ⚙️ Configuration (Settings, Audit)
│   ├── models.py            # Setting, AuditLog
│   ├── schemas.py           # SettingUpdate, AuditLogResponse
│   └── endpoints.py         # Settings management + Audit viewing
├── tools/                    # 📝 Productivity (Notes, Tasks, Calendar)
│   ├── models.py            # Note, Task, LogCall, Event, Attachment
│   ├── schemas.py           # NoteCreate, TaskCreate, EventCreate
│   └── endpoints.py         # Notes, Tasks, Calendar management
├── common/
│   └── enums.py             # All enums consolidated
├── main.py                   # Clean entry point (< 100 lines)
├── database.py               # Multi-tenant session management
└── shared_auth.py            # JWT authentication system
```

## 🔄 Migration Steps

### Step 1: Setup Structure

```bash
# Create directories
mkdir -p services/system-service/{users,settings,tools,common}
touch services/system-service/{users,settings,tools,common}/__init__.py

# Copy authentication system
cp services/communication-service/shared_auth.py services/system-service/
```

### Step 2: Common Enums (common/enums.py)

```python
"""Consolidated enums for all system service modules"""
import enum

# User Management
class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"

class PermissionAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"

class ResourceType(str, enum.Enum):
    USER = "user"
    ROLE = "role"
    TEAM = "team"
    SETTING = "setting"
    TASK = "task"
    NOTE = "note"

# Tools
class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class NotePriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CallType(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class CallStatus(str, enum.Enum):
    ANSWERED = "answered"
    MISSED = "missed"
    BUSY = "busy"
```

### Step 3: Users Module

#### users/models.py
```python
"""User Management Models"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Table, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from common.enums import UserStatus, PermissionAction, ResourceType

Base = declarative_base()

# Association tables
user_roles = Table('user_roles', Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE')),
    UniqueConstraint('user_id', 'role_id')
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    title = Column(String(100))
    department = Column(String(100))
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
```

#### users/endpoints.py
```python
"""User Management Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any
from shared_auth import get_current_user, require_tenant_admin, check_tenant_slug_access
from database import get_tenant_session
from .models import User, Role

# Create routers
users_router = APIRouter(prefix="/api/v1/users", tags=["Users"])
roles_router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])

@users_router.get("/", response_model=List[dict])
async def list_users(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List users with authentication"""
    # Validate tenant access
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    # Get database session after validation
    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        users = db.query(User).all()
        return [user.to_dict() for user in users]

@roles_router.get("/", response_model=List[dict])
async def list_roles(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(require_tenant_admin)
):
    """List roles (admin only)"""
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        roles = db.query(Role).all()
        return [{"id": str(role.id), "name": role.name, "display_name": role.display_name} for role in roles]
```

### Step 4: Settings Module

#### settings/models.py
```python
"""Settings and Audit Models"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(JSONB, nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('category', 'key'),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

#### settings/endpoints.py
```python
"""Settings Management Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from shared_auth import get_current_user, require_tenant_admin, check_tenant_slug_access
from database import get_tenant_session
from .models import Setting, AuditLog

settings_router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])
audit_router = APIRouter(prefix="/api/v1/audit", tags=["Audit"])

@settings_router.get("/")
async def list_settings(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List tenant settings"""
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        settings = db.query(Setting).all()
        return [{"category": s.category, "key": s.key, "value": s.value} for s in settings]

@audit_router.get("/")
async def list_audit_logs(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(require_tenant_admin)
):
    """List audit logs (admin only)"""
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
        return [{"action": log.action, "resource_type": log.resource_type, "created_at": log.created_at} for log in logs]
```

### Step 5: Tools Module

#### tools/models.py
```python
"""Productivity Tools Models"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Date, ForeignKey, BigInteger, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from common.enums import TaskStatus, TaskPriority, NotePriority, CallType, CallStatus

Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(191))
    content = Column(Text, nullable=False)
    notable_id = Column(BigInteger, nullable=False)
    notable_type = Column(String(50), nullable=False)
    priority = Column(SQLEnum(NotePriority), default=NotePriority.MEDIUM)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.LOW)
    due_date = Column(Date)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class LogCall(Base):
    __tablename__ = "logacalls"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone_number = Column(String(255), nullable=False)
    call_type = Column(SQLEnum(CallType), nullable=False)
    status = Column(SQLEnum(CallStatus), nullable=False)
    notes = Column(Text)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
```

#### tools/endpoints.py
```python
"""Productivity Tools Endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Dict, Any
from shared_auth import get_current_user, check_tenant_slug_access
from database import get_tenant_session
from .models import Note, Task, LogCall

notes_router = APIRouter(prefix="/api/v1/notes", tags=["Notes"])
tasks_router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])
calls_router = APIRouter(prefix="/api/v1/calls", tags=["Calls"])

@notes_router.get("/")
async def list_notes(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List notes"""
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        notes = db.query(Note).all()
        return [{"id": note.id, "title": note.title, "content": note.content[:100]} for note in notes]

@tasks_router.get("/")
async def list_tasks(
    tenant_slug: str = Query(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List tasks"""
    if not check_tenant_slug_access(current_user, tenant_slug):
        raise HTTPException(status_code=403, detail="Access denied")

    with get_tenant_session(f"tenant_{tenant_slug}") as db:
        tasks = db.query(Task).filter(Task.assigned_to == current_user["id"]).all()
        return [{"id": task.id, "title": task.title, "status": task.status} for task in tasks]
```

### Step 6: Updated Main Application

#### main.py
```python
"""
System Service - Modular Architecture v2.0
User management, settings, and productivity tools with authentication
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime

# Import shared authentication
from shared_auth import get_current_user, require_super_admin

# Import database management
from database import verify_connection

# Import module routers
from users.endpoints import users_router, roles_router
from settings.endpoints import settings_router, audit_router
from tools.endpoints import notes_router, tasks_router, calls_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting System Service v2.0...")
    if not verify_connection():
        raise Exception("Database connection failed")
    logger.info("System Service started successfully")
    yield
    logger.info("Shutting down System Service...")

# Create FastAPI application
app = FastAPI(
    title="System Service",
    description="Modular user management, settings, and productivity tools",
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
app.include_router(users_router)
app.include_router(roles_router)
app.include_router(settings_router)
app.include_router(audit_router)
app.include_router(notes_router)
app.include_router(tasks_router)
app.include_router(calls_router)

# Root endpoints
@app.get("/")
async def root():
    return {
        "service": "System Service",
        "version": "2.0.0",
        "architecture": "modular",
        "modules": {
            "users": "User and role management",
            "settings": "Configuration and audit",
            "tools": "Productivity tools"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "System Service",
        "modules": {
            "users": "active",
            "settings": "active", 
            "tools": "active"
        }
    }

# Authentication test endpoints
@app.get("/api/v1/auth/test")
async def auth_test(current_user: dict = Depends(get_current_user)):
    return {
        "message": "System Service authentication working!",
        "user": {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
            "tenant_slug": current_user.get("tenant_slug")
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)
```

## 🧪 Testing the Migration

### Test Authentication
```bash
# Create test token
TOKEN=$(docker-compose exec -T system-service python3 -c "
from shared_auth import create_access_token
token = create_access_token({
    'sub': 'test_user',
    'tenant_slug': 'demo',
    'role': 'tenant_admin'
})
print(token)
")

# Test without auth (should fail)
curl http://localhost:8008/api/v1/auth/test

# Test with auth (should work)
curl -H "Authorization: Bearer $TOKEN" http://localhost:8008/api/v1/auth/test
```

### Test Module Endpoints
```bash
# Test users module
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8008/api/v1/users/?tenant_slug=demo"

# Test settings module  
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8008/api/v1/settings/?tenant_slug=demo"

# Test tools module
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:8008/api/v1/tasks/?tenant_slug=demo"
```

## 📊 Migration Benefits

### Before Migration
- **Lines in main.py**: 800+ lines
- **Models per file**: 27 models in 2 files
- **Authentication**: None
- **Team collaboration**: Difficult (conflicts)
- **Maintainability**: Low

### After Migration
- **Lines in main.py**: < 100 lines
- **Models per module**: 2-6 models each
- **Authentication**: 100% coverage
- **Team collaboration**: Easy (module separation)
- **Maintainability**: High

## 🎯 Migration Checklist

### Pre-Migration
- [ ] Backup current system-service code
- [ ] Understand current endpoints and models
- [ ] Plan module boundaries
- [ ] Test current functionality

### During Migration
- [ ] Create modular directory structure
- [ ] Copy shared authentication system
- [ ] Migrate models to appropriate modules
- [ ] Create endpoints with authentication
- [ ] Update main.py to include routers
- [ ] Test each module independently

### Post-Migration
- [ ] All endpoints return expected responses
- [ ] Authentication working (401 without token)
- [ ] Tenant access control working (403 for wrong tenant)
- [ ] Module separation is clean
- [ ] Service starts without errors
- [ ] Documentation updated

## 💡 Key Takeaways

1. **Modular Structure**: Separate concerns into logical modules
2. **Authentication**: Use shared system for consistency
3. **Tenant Validation**: Always check tenant access
4. **Database Sessions**: Manual session creation after validation
5. **Testing**: Test auth before testing business logic

## 🚀 Next Steps

1. **Apply this pattern** to system-service first (easiest)
2. **Use as template** for other services (crm, financial, booking)
3. **Maintain consistency** across all microservices
4. **Document lessons learned** for future migrations

---

**Result**: Transform monolithic services into maintainable, secure, scalable microservices following the proven communication-service pattern.