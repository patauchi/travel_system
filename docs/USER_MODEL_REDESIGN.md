# 🔄 Rediseño del Modelo de Usuarios - Sistema Multi-Tenant

## 📋 Resumen Ejecutivo

### Problema Actual
El sistema actual mezcla usuarios del sistema con usuarios del tenant en una sola tabla (`shared.users`), con 4 roles que confunden niveles de acceso:
- `super_admin` ✅ (correcto - nivel sistema)
- `tenant_admin` ✅ (correcto - nivel sistema)
- `tenant_user` ❌ (incorrecto - debería ser nivel tenant)
- `tenant_viewer` ❌ (incorrecto - debería ser nivel tenant)

### Solución Propuesta
Separar completamente los usuarios del sistema de los usuarios del tenant:
- **Sistema**: Solo administradores de la plataforma
- **Tenant**: Usuarios específicos de cada organización con sus propios roles

## 🏗️ Nueva Arquitectura

### 1️⃣ Nivel Sistema (Schema `shared`)

```
┌─────────────────────────────────────┐
│         system_users                │  ← Solo admins de la plataforma
├─────────────────────────────────────┤
│ • id (UUID)                         │
│ • email (VARCHAR)                   │
│ • username (VARCHAR)                │
│ • password_hash (VARCHAR)           │
│ • system_role (ENUM)                │  ← super_admin | tenant_admin
│ • is_platform_user (BOOLEAN)       │
│ • managed_tenants (JSONB)          │  ← Lista de tenants que administra
└─────────────────────────────────────┘
```

**Roles del Sistema:**
- `super_admin`: Acceso total a la plataforma
- `tenant_admin`: Administrador de uno o más tenants específicos

### 2️⃣ Nivel Tenant (Schema `tenant_*`)

Cada tenant tiene sus propias tablas de usuarios:

```
┌─────────────────────────────────────┐
│      tenant_X.users                 │  ← Usuarios del tenant
├─────────────────────────────────────┤
│ • id (UUID)                         │
│ • email (VARCHAR)                   │
│ • username (VARCHAR)                │
│ • password_hash (VARCHAR)           │
│ • role_id (FK → roles)              │  ← Rol dentro del tenant
│ • department (VARCHAR)              │
│ • job_title (VARCHAR)               │
│ • employee_id (VARCHAR)             │
│ • preferences (JSONB)               │
│ • metadata (JSONB)                  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│       tenant_X.roles                │  ← Roles personalizables
├─────────────────────────────────────┤
│ • id (UUID)                         │
│ • name (VARCHAR)                    │
│ • display_name (VARCHAR)            │
│ • permissions (JSONB)               │
│ • is_system (BOOLEAN)               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│    tenant_X.permissions             │  ← Permisos granulares
├─────────────────────────────────────┤
│ • id (UUID)                         │
│ • name (VARCHAR)                    │
│ • resource (VARCHAR)                │
│ • action (VARCHAR)                  │
└─────────────────────────────────────┘
```

## 🔀 Flujos de Autenticación

### Flujo 1: Admin del Sistema
```mermaid
1. Admin accede a: localhost:3000/admin/login
2. Se autentica contra shared.system_users
3. Token incluye: { role: "super_admin", type: "system" }
4. Accede al panel de administración global
5. Puede ver y gestionar TODOS los tenants
```

### Flujo 2: Admin de Tenant
```mermaid
1. Admin accede a: localhost:3000/admin/login
2. Se autentica contra shared.system_users
3. Token incluye: { role: "tenant_admin", type: "system", tenants: ["tenant1"] }
4. Accede al panel de administración
5. Solo ve los tenants que administra
```

### Flujo 3: Usuario del Tenant
```mermaid
1. Usuario accede a: tenant1.localhost:3000/login
2. Se autentica contra tenant1.users
3. Token incluye: { role: "user", type: "tenant", tenant: "tenant1" }
4. Accede al sistema del tenant
5. Permisos según su rol en el tenant
```

## 📊 Comparación: Antes vs Después

| Aspecto | Antes ❌ | Después ✅ |
|---------|----------|-----------|
| **Tabla de usuarios** | Una global (`shared.users`) | Separadas (sistema vs tenant) |
| **Roles del sistema** | 4 roles mezclados | 2 roles (super_admin, tenant_admin) |
| **Roles del tenant** | Fijos y globales | Personalizables por tenant |
| **Aislamiento** | Parcial | Total |
| **Escalabilidad** | Limitada | Ilimitada |
| **Personalización** | No posible | Total por tenant |

## 🎯 Ventajas del Nuevo Modelo

### 1. **Aislamiento Total**
- Los datos de usuarios de cada tenant están completamente separados
- No hay riesgo de filtración de datos entre tenants
- Cada tenant puede tener usuarios con el mismo email/username

### 2. **Roles Personalizables**
- Cada tenant puede definir sus propios roles
- Permisos granulares por recurso y acción
- Flexibilidad total para cada organización

### 3. **Escalabilidad**
- No hay límite en el número de usuarios por tenant
- Performance optimizado por schema separado
- Backup y restore independiente por tenant

### 4. **Seguridad Mejorada**
- Autenticación en dos niveles claramente separados
- Tokens con contexto específico (sistema vs tenant)
- Auditoría separada por nivel

## 🔧 Implementación

### Paso 1: Migración de Base de Datos
```sql
-- Ejecutar el script de migración
\i migration_separate_users.sql
```

### Paso 2: Actualizar Backend

#### Auth Service - Dos endpoints separados:
```python
# Para admins del sistema
@app.post("/api/v1/auth/admin/login")
async def admin_login(credentials):
    # Autenticar contra shared.system_users
    # Generar token con type="system"
    
# Para usuarios del tenant
@app.post("/api/v1/auth/tenant/login")
async def tenant_login(credentials, tenant_slug: str):
    # Autenticar contra tenant_X.users
    # Generar token con type="tenant"
```

### Paso 3: Actualizar Frontend

#### Rutas de Login Separadas:
```typescript
// Admin login (sistema)
/admin/login → shared.system_users

// Tenant login (usuarios del tenant)
/login → tenant_X.users (basado en subdominio)
```

## 📋 Roles Predefinidos por Tenant

Cuando se crea un nuevo tenant, se crean automáticamente estos roles:

| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **admin** | Administrador del tenant | Todos los permisos |
| **manager** | Gerente/Supervisor | Gestión de usuarios y recursos |
| **user** | Usuario estándar | CRUD en recursos propios |
| **viewer** | Solo lectura | Solo visualización |
| **guest** | Invitado temporal | Acceso limitado |

## 🔐 Estructura de Tokens JWT

### Token de Sistema (Admins)
```json
{
  "sub": "user_id",
  "type": "system",
  "role": "super_admin",
  "email": "admin@platform.com",
  "managed_tenants": ["tenant1", "tenant2"],
  "exp": 1234567890
}
```

### Token de Tenant (Usuarios)
```json
{
  "sub": "user_id",
  "type": "tenant",
  "tenant_id": "tenant1_id",
  "tenant_slug": "tenant1",
  "role": "manager",
  "permissions": ["users.read", "projects.write"],
  "email": "user@company.com",
  "exp": 1234567890
}
```

## 🚀 Casos de Uso

### 1. Super Admin
- Accede a: `localhost:3000/admin`
- Ve dashboard con TODOS los tenants
- Puede crear/editar/eliminar tenants
- Gestiona tenant_admins

### 2. Tenant Admin
- Accede a: `localhost:3000/admin`
- Ve solo sus tenants asignados
- Puede gestionar la configuración del tenant
- NO puede crear nuevos tenants

### 3. Usuario del Tenant (Admin)
- Accede a: `tenant1.localhost:3000`
- Gestiona usuarios dentro del tenant
- Configura roles y permisos
- Administra recursos del tenant

### 4. Usuario del Tenant (Regular)
- Accede a: `tenant1.localhost:3000`
- Usa el sistema según sus permisos
- No ve opciones de administración
- Trabaja con recursos asignados

## 📊 Ejemplo de Datos

### Sistema (shared.system_users)
```sql
-- Super Admin
('admin@platform.com', 'superadmin', 'super_admin')

-- Tenant Admins
('john@platform.com', 'johnadmin', 'tenant_admin', '["tenant1", "tenant2"]')
('jane@platform.com', 'janeadmin', 'tenant_admin', '["tenant3"]')
```

### Tenant 1 (tenant1.users)
```sql
-- Usuarios específicos de Tenant 1
('ceo@company1.com', 'ceo', 'admin')
('manager@company1.com', 'manager1', 'manager')
('employee1@company1.com', 'emp1', 'user')
('employee2@company1.com', 'emp2', 'user')
('intern@company1.com', 'intern1', 'viewer')
```

### Tenant 2 (tenant2.users)
```sql
-- Usuarios específicos de Tenant 2
('owner@company2.com', 'owner', 'admin')
('supervisor@company2.com', 'super1', 'manager')
('worker1@company2.com', 'work1', 'user')
('worker2@company2.com', 'work2', 'user')
```

## ⚠️ Consideraciones Importantes

### 1. Migración de Datos Existentes
- Los usuarios actuales en `shared.users` deben clasificarse
- Los que son admins permanecen en `system_users`
- Los usuarios regulares se mueven a sus respectivos tenant schemas

### 2. Compatibilidad Hacia Atrás
- Mantener endpoints legacy por un período de transición
- Migración gradual de tokens
- Logs de auditoría para tracking

### 3. Performance
- Cada tenant tiene sus propios índices
- Consultas optimizadas por schema
- Cache separado por tenant

### 4. Backup y Recovery
- Backup independiente por tenant
- Recovery selectivo posible
- Exportación de datos por tenant

## 📈 Roadmap de Implementación

### Fase 1: Preparación (Semana 1)
- [x] Diseñar nueva estructura
- [ ] Crear scripts de migración
- [ ] Preparar ambiente de pruebas

### Fase 2: Backend (Semana 2)
- [ ] Implementar nuevos modelos
- [ ] Crear endpoints separados
- [ ] Actualizar middleware de autenticación
- [ ] Implementar sistema de permisos

### Fase 3: Frontend (Semana 3)
- [ ] Crear páginas de login separadas
- [ ] Actualizar guards de rutas
- [ ] Implementar contexto de tenant
- [ ] Actualizar dashboards

### Fase 4: Migración (Semana 4)
- [ ] Migrar datos de producción
- [ ] Pruebas de integración
- [ ] Documentación final
- [ ] Despliegue

## 🔍 Queries Útiles

### Ver todos los usuarios del sistema
```sql
SELECT * FROM shared.system_users;
```

### Ver usuarios de un tenant específico
```sql
SELECT * FROM tenant1.users;
```

### Ver permisos de un rol
```sql
SELECT r.name, p.name as permission
FROM tenant1.roles r
JOIN tenant1.role_permissions rp ON r.id = rp.role_id
JOIN tenant1.permissions p ON rp.permission_id = p.id
WHERE r.name = 'manager';
```

### Verificar permisos de un usuario
```sql
SELECT check_tenant_user_permission('tenant1', 'user_uuid', 'projects.create');
```

## 📝 Conclusión

Esta separación clara entre usuarios del sistema y usuarios del tenant proporciona:
- ✅ **Mejor seguridad**: Aislamiento total de datos
- ✅ **Mayor flexibilidad**: Roles personalizables por tenant
- ✅ **Escalabilidad**: Sin límites por tenant
- ✅ **Simplicidad**: Modelo mental más claro
- ✅ **Compliance**: Facilita cumplimiento de regulaciones

El nuevo modelo está listo para soportar el crecimiento de la plataforma manteniendo la seguridad y flexibilidad necesarias para un sistema multi-tenant profesional.

---
**Última actualización**: Diciembre 2024
**Versión**: 2.0.0
**Estado**: Propuesta para implementación