# 📚 Guía de Implementación de Nuevos Servicios

Esta guía explica cómo crear nuevos servicios basándose en la arquitectura exitosa del `system-service`.

## 🏗️ Arquitectura Base

Cada servicio nuevo debe seguir la estructura del `system-service` que usa:
- **SQLAlchemy** para definir modelos (NO archivos SQL)
- **FastAPI** para los endpoints
- **Pydantic** para validación
- **Schema Manager** para gestión de tablas

## 📁 Estructura de Archivos Requerida

```
services/
└── nombre-service/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                 # FastAPI app principal
    ├── models.py               # Modelos SQLAlchemy
    ├── schemas.py              # Schemas Pydantic
    ├── database.py             # Conexión a BD
    ├── schema_manager.py       # Gestión de schemas
    ├── endpoints.py            # Endpoints del servicio
    └── utils.py                # Funciones auxiliares
```

## 🔧 Paso a Paso para Crear un Nuevo Servicio

### 1️⃣ **Crear la Estructura Base**

```bash
# Crear directorio del servicio
mkdir -p services/booking-service
cd services/booking-service
```

### 2️⃣ **Crear requirements.txt**

```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic[email]
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
httpx==0.25.1
python-dotenv==1.0.0
```

### 3️⃣ **Crear models.py (Basado en Migraciones Laravel)**

```python
"""
Models for Booking Service
Define todas las tablas usando SQLAlchemy
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, DECIMAL, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# IMPORTANTE: Convertir las migraciones de Laravel a modelos SQLAlchemy
# Ejemplo de conversión:

class Booking(Base):
    __tablename__ = "bookings"
    
    # Laravel: $table->id();
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Laravel: $table->string('reference_number', 100)->unique();
    reference_number = Column(String(100), unique=True, nullable=False)
    
    # Laravel: $table->decimal('total_amount', 10, 2);
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    
    # Laravel: $table->foreignId('customer_id')->constrained('customers');
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'))
    
    # Laravel: $table->json('metadata')->nullable();
    metadata = Column(JSONB, nullable=True, default={})
    
    # Laravel: $table->timestamps();
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Laravel: $table->softDeletes();
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

### 4️⃣ **Crear database.py**

```python
"""
Database configuration for the service
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_tenant_db(schema_name: str):
    """Get a database session for a specific tenant schema"""
    engine = create_engine(
        DATABASE_URL,
        connect_args={"options": f"-csearch_path={schema_name}"},
        poolclass=NullPool
    )
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
```

### 5️⃣ **Crear schema_manager.py**

```python
"""
Schema Manager - Gestiona la creación de tablas desde modelos
"""

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from models import Base
import logging
import os

logger = logging.getLogger(__name__)

class SchemaManager:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
        )
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,
            echo=False
        )

    def create_tables_for_tenant(self, schema_name: str) -> bool:
        """Crear todas las tablas para un tenant usando los modelos"""
        try:
            # Crear engine con schema específico
            engine = create_engine(
                self.database_url,
                connect_args={"options": f"-csearch_path={schema_name}"},
                poolclass=NullPool
            )
            
            # Crear todas las tablas desde los modelos
            Base.metadata.create_all(bind=engine)
            
            logger.info(f"Tablas creadas para schema {schema_name}")
            engine.dispose()
            return True
            
        except Exception as e:
            logger.error(f"Error creando tablas: {str(e)}")
            return False

    def initialize_tenant(self, tenant_id: str, schema_name: str):
        """Inicializar schema con todas las tablas del servicio"""
        return self.create_tables_for_tenant(schema_name)
```

### 6️⃣ **Crear schemas.py (Pydantic)**

```python
"""
Pydantic schemas for API validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Request/Response models
class BookingBase(BaseModel):
    reference_number: str = Field(..., max_length=100)
    total_amount: float
    customer_id: UUID
    metadata: Optional[Dict[str, Any]] = {}

class BookingCreate(BookingBase):
    pass

class BookingUpdate(BaseModel):
    total_amount: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BookingResponse(BookingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

### 7️⃣ **Crear endpoints.py**

```python
"""
API Endpoints for the service
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_tenant_db
from models import Booking
from schemas import BookingCreate, BookingUpdate, BookingResponse

router = APIRouter(prefix="/api/v1/tenants/{tenant_slug}/bookings", tags=["Bookings"])

@router.post("/", response_model=BookingResponse)
async def create_booking(
    tenant_slug: str,
    booking_data: BookingCreate,
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Crear nueva reserva"""
    booking = Booking(**booking_data.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

@router.get("/", response_model=List[BookingResponse])
async def list_bookings(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Listar reservas"""
    bookings = db.query(Booking).filter(
        Booking.deleted_at.is_(None)
    ).offset(skip).limit(limit).all()
    return bookings

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    tenant_slug: str,
    booking_id: int,
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Obtener reserva específica"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.deleted_at.is_(None)
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return booking

@router.put("/{booking_id}", response_model=BookingResponse)
async def update_booking(
    tenant_slug: str,
    booking_id: int,
    update_data: BookingUpdate,
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Actualizar reserva"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.deleted_at.is_(None)
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(booking, field, value)
    
    booking.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)
    return booking

@router.delete("/{booking_id}")
async def delete_booking(
    tenant_slug: str,
    booking_id: int,
    db: Session = Depends(lambda: get_tenant_db(f"tenant_{tenant_slug}"))
):
    """Soft delete de reserva"""
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.deleted_at.is_(None)
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "Booking deleted successfully"}
```

### 8️⃣ **Crear main.py**

```python
"""
Main FastAPI application
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import httpx
import os

from schema_manager import SchemaManager
from endpoints import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

schema_manager = SchemaManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Booking Service...")
    yield
    logger.info("Shutting down Booking Service...")

app = FastAPI(
    title="Booking Service",
    description="Gestión de reservas multi-tenant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "booking-service"}

@app.post("/api/v1/tenants/{tenant_id}/initialize")
async def initialize_tenant(tenant_id: str, request: Request):
    """Inicializar schema del tenant con tablas del servicio"""
    data = await request.json()
    schema_name = data.get("schema_name", f"tenant_{tenant_id}")
    
    success = schema_manager.initialize_tenant(tenant_id, schema_name)
    
    if success:
        # Notificar a otros servicios si es necesario
        try:
            async with httpx.AsyncClient() as client:
                # Ejemplo: notificar a otro servicio
                pass
        except:
            pass
    
    return {
        "status": "success" if success else "failed",
        "tenant_id": tenant_id,
        "schema_name": schema_name
    }
```

### 9️⃣ **Crear Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]
```

### 🔟 **Agregar al docker-compose.yml**

```yaml
  booking-service:
    build:
      context: ./services/booking-service
      dockerfile: Dockerfile
    container_name: multitenant-booking-service
    ports:
      - "8005:8005"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/multitenant_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    networks:
      - multitenant-network
    volumes:
      - ./services/booking-service:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8005 --reload
```

## 🔄 Conversión de Migraciones Laravel a SQLAlchemy

### Tabla de Conversión

| Laravel Migration | SQLAlchemy Model |
|-------------------|------------------|
| `$table->id()` | `Column(Integer, primary_key=True, autoincrement=True)` |
| `$table->bigIncrements('id')` | `Column(BigInteger, primary_key=True, autoincrement=True)` |
| `$table->uuid('id')` | `Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)` |
| `$table->string('name', 100)` | `Column(String(100))` |
| `$table->text('description')` | `Column(Text)` |
| `$table->integer('quantity')` | `Column(Integer)` |
| `$table->decimal('price', 10, 2)` | `Column(DECIMAL(10, 2))` |
| `$table->boolean('is_active')` | `Column(Boolean)` |
| `$table->date('birth_date')` | `Column(Date)` |
| `$table->datetime('start_at')` | `Column(DateTime(timezone=True))` |
| `$table->json('metadata')` | `Column(JSONB)` |
| `$table->enum('status', [...])` | `Column(SQLEnum(...))` |
| `$table->foreignId('user_id')` | `Column(UUID(as_uuid=True), ForeignKey('users.id'))` |
| `$table->unique('email')` | `unique=True` en Column |
| `$table->index('created_at')` | Usar `__table_args__` con Index |
| `$table->nullable()` | `nullable=True` |
| `$table->default('value')` | `default='value'` |
| `$table->timestamps()` | `created_at` y `updated_at` columns |
| `$table->softDeletes()` | `deleted_at = Column(DateTime, nullable=True)` |

### Ejemplo de Conversión Completa

**Laravel:**
```php
Schema::create('products', function (Blueprint $table) {
    $table->id();
    $table->string('name', 255);
    $table->text('description')->nullable();
    $table->decimal('price', 10, 2);
    $table->integer('stock')->default(0);
    $table->boolean('is_active')->default(true);
    $table->enum('status', ['draft', 'published', 'archived']);
    $table->foreignId('category_id')->constrained('categories');
    $table->json('attributes')->nullable();
    $table->timestamps();
    $table->softDeletes();
    
    $table->index('name');
    $table->unique('sku');
});
```

**SQLAlchemy:**
```python
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

class ProductStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    status = Column(SQLEnum(ProductStatus), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    attributes = Column(JSONB, nullable=True, default={})
    sku = Column(String(100), unique=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
```

## 🚀 Integración con el Sistema

### 1. **Modificar tenant-service**

En `tenant-service/create_tenant_v2.py`, agregar llamada al nuevo servicio:

```python
def initialize_booking_service(tenant_id: str, schema_name: str) -> bool:
    """Initialize booking service for tenant"""
    try:
        with httpx.Client() as client:
            response = client.post(
                f"http://booking-service:8005/api/v1/tenants/{tenant_id}/initialize",
                json={"schema_name": schema_name},
                timeout=30
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error initializing booking service: {str(e)}")
        return False

# En la función create_tenant_v2, después de system-service:
if not initialize_booking_service(tenant_id, schema_name):
    logger.warning(f"Failed to initialize booking service for tenant {tenant_id}")
```

### 2. **Orden de Inicialización**

1. `system-service` - Tablas base del sistema
2. `booking-service` - Tablas de reservas
3. `financial-service` - Tablas financieras
4. `crm-service` - Tablas de CRM
5. `communication-service` - Tablas de comunicación

## 📋 Checklist para Nuevo Servicio

- [ ] Crear estructura de directorios
- [ ] Crear `requirements.txt`
- [ ] Convertir migraciones Laravel a `models.py`
- [ ] Crear `database.py` con conexión multi-tenant
- [ ] Crear `schema_manager.py` para gestión de tablas
- [ ] Crear `schemas.py` con modelos Pydantic
- [ ] Crear `endpoints.py` con rutas API
- [ ] Crear `main.py` con FastAPI app
- [ ] Crear `Dockerfile`
- [ ] Agregar servicio a `docker-compose.yml`
- [ ] Integrar con `tenant-service`
- [ ] Probar creación de tenant
- [ ] Verificar tablas en PostgreSQL
- [ ] Verificar Swagger UI

## 🎯 Servicios a Implementar

Basándose en `/services-references/`:

1. **booking-operations-service**
   - Reservas
   - Itinerarios
   - Pasajeros
   - Documentos de viaje

2. **financial-service**
   - Pagos
   - Facturas
   - Comisiones
   - Reportes financieros

3. **crm-services**
   - Clientes
   - Contactos
   - Leads
   - Oportunidades

4. **communication-services**
   - Emails
   - SMS
   - Notificaciones
   - Templates

## 🔍 Validación

Para verificar que un servicio está correctamente implementado:

```bash
# 1. Crear un nuevo tenant
curl -X POST http://localhost:8002/api/v1/tenants ...

# 2. Verificar tablas creadas
docker exec multitenant-postgres psql -U postgres -d multitenant_db \
  -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'tenant_XXX';"

# 3. Verificar Swagger
curl http://localhost:8005/docs

# 4. Probar endpoints
curl http://localhost:8005/api/v1/tenants/XXX/bookings
```

## 💡 Tips Importantes

1. **NO usar archivos SQL** - Todo debe ser modelos SQLAlchemy
2. **Siempre usar soft deletes** - Campo `deleted_at`
3. **Timestamps automáticos** - `created_at`, `updated_at`
4. **Relaciones polimórficas** - Para flexibilidad (como Laravel)
5. **JSONB para metadata** - Datos flexibles sin esquema
6. **Índices en foreign keys** - Para performance
7. **Enums como clases Python** - Type safety
8. **Paginación en listados** - skip/limit parameters
9. **Swagger automático** - FastAPI lo genera
10. **Multi-tenant desde el inicio** - Cada endpoint con tenant_slug

## 🚨 Errores Comunes y Soluciones

| Error | Solución |
|-------|----------|
| "Table already exists" | El schema ya tiene las tablas, verificar con psql |
| "Column metadata reserved" | Usar otro nombre como `meta_data` o `data` |
| "Cannot import module" | Verificar que todos los archivos existen |
| "Connection refused" | Verificar que el servicio está en docker-compose |
| "Tenant not found" | Crear el tenant primero con tenant-service |

## 📚 Recursos

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Laravel to SQLAlchemy Migration Guide](https://github.com/sqlalchemy/sqlalchemy/wiki)