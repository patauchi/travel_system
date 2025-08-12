# Sistema de Control de Acceso Multi-Tenant con Roles

## 📋 Resumen

Este documento describe la implementación del sistema de control de acceso basado en roles y subdominios para la plataforma multi-tenant.

## 🎯 Objetivos Implementados

1. ✅ El rol del usuario se envía en el token JWT
2. ✅ Super Admin tiene acceso completo al panel /admin con lista de todos los tenants
3. ✅ Tenant Admin accede a /admin y ve solo información de su tenant ("Hola Tenant X")
4. ✅ Usuarios de tenant solo pueden acceder a través de su subdominio específico

## 🏗️ Arquitectura del Sistema

### Roles de Usuario

```python
class UserRole(Enum):
    SUPER_ADMIN = "super_admin"      # Acceso total al sistema
    TENANT_ADMIN = "tenant_admin"    # Admin de un tenant específico
    TENANT_USER = "tenant_user"      # Usuario regular de tenant
    TENANT_VIEWER = "tenant_viewer"  # Usuario de solo lectura
```

### Estructura del Token JWT

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "username": "username",
  "role": "tenant_admin",
  "tenant_id": "tenant_uuid",
  "tenant_slug": "tenant1",
  "exp": 1234567890
}
```

## 🔐 Reglas de Acceso

### 1. Super Admin
- **Acceso**: Dominio principal (localhost:3000)
- **Permisos**: 
  - Acceso completo a /admin
  - Ve todos los tenants
  - Puede acceder a cualquier subdominio
  - Gestión completa del sistema

### 2. Tenant Admin
- **Acceso**: Subdominio del tenant (tenant1.localhost:3000)
- **Permisos**:
  - Acceso a /admin con vista limitada
  - Ve solo información de su tenant
  - Gestiona usuarios de su tenant
  - Configuración del tenant

### 3. Tenant User
- **Acceso**: Solo subdominio del tenant (tenant1.localhost:3000)
- **Permisos**:
  - Acceso al dashboard del tenant
  - Funcionalidades según permisos asignados
  - NO puede acceder a /admin

## 📁 Archivos Modificados/Creados

### Backend (Python/FastAPI)

1. **services/auth-service/main.py**
   - Modificado login para incluir rol en el token
   - Determina rol basado en usuario y tenant

2. **services/auth-service/tenant_access_middleware.py** (NUEVO)
   - Middleware para verificar acceso por subdominio
   - Valida que usuarios accedan solo a su tenant
   - Extrae tenant del subdominio/headers

### Frontend (React/TypeScript)

1. **src/components/guards/AdminRoute.tsx**
   - Verifica rol del usuario desde el token
   - Restringe acceso a super_admin y tenant_admin

2. **src/pages/admin/AdminDashboard.tsx**
   - Renderiza contenido diferente según rol
   - Super Admin: Ve todos los tenants
   - Tenant Admin: Ve "Hola [Nombre Tenant]"

3. **src/components/guards/TenantAccessGuard.tsx** (NUEVO)
   - Componente para verificar acceso por subdominio
   - Redirige usuarios al subdominio correcto
   - Valida permisos por rol

4. **src/utils/tenantAccess.ts** (NUEVO)
   - Utilidades para manejo de subdominios
   - Verificación de acceso por tenant
   - Funciones helper para URLs

5. **src/store/slices/authSlice.ts**
   - Actualizado para incluir rol en el estado
   - Decodifica rol del token JWT

## 🚀 Instrucciones de Configuración

### 1. Configurar Subdominios Locales

Editar `/etc/hosts` (Mac/Linux) o `C:\Windows\System32\drivers\etc\hosts` (Windows):

```bash
127.0.0.1   localhost
127.0.0.1   tenant1.localhost
127.0.0.1   tenant2.localhost
127.0.0.1   tenant3.localhost
```

### 2. Instalar Dependencias

**Frontend:**
```bash
cd multitenant-platform/frontend
npm install jwt-decode
```

**Backend (opcional para script de prueba):**
```bash
cd multitenant-platform
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install psycopg2-binary passlib bcrypt
```

### 3. Crear Usuarios de Prueba

```bash
cd multitenant-platform
python3 create_test_users.py
```

## 🧪 Usuarios de Prueba

### Super Admin
- **Username**: admin
- **Password**: Admin123!@#
- **Email**: admin@example.com
- **Acceso**: http://localhost:3000/auth/login

### Tenant 1 Admin
- **Username**: tenant1_admin
- **Password**: Tenant1Admin123!
- **Email**: admin@tenant1.com
- **Acceso**: http://tenant1.localhost:3000/auth/login

### Tenant 1 Users
- **Username**: tenant1_user1
- **Password**: User123!@#
- **Email**: user1@tenant1.com
- **Acceso**: http://tenant1.localhost:3000/auth/login

### Tenant 2 Admin
- **Username**: tenant2_admin
- **Password**: Tenant2Admin123!
- **Email**: admin@tenant2.com
- **Acceso**: http://tenant2.localhost:3000/auth/login

## 🧪 Casos de Prueba

### Test 1: Super Admin Access
1. Ir a http://localhost:3000/auth/login
2. Login con: admin / Admin123!@#
3. Navegar a /admin
4. **Resultado esperado**: Ver lista completa de todos los tenants

### Test 2: Tenant Admin Access
1. Ir a http://tenant1.localhost:3000/auth/login
2. Login con: tenant1_admin / Tenant1Admin123!
3. Navegar a /admin
4. **Resultado esperado**: Ver "Hola Tenant One" con información del tenant

### Test 3: Tenant User Restriction
1. Ir a http://tenant1.localhost:3000/auth/login
2. Login con: tenant1_user1 / User123!@#
3. Intentar acceder a /admin
4. **Resultado esperado**: Redirigido a /dashboard (acceso denegado)

### Test 4: Cross-Tenant Access Prevention
1. Login como tenant1_user1 en tenant1.localhost:3000
2. Intentar acceder a http://tenant2.localhost:3000
3. **Resultado esperado**: Acceso denegado

### Test 5: Wrong Domain Access
1. Login como tenant1_admin en localhost:3000 (sin subdominio)
2. **Resultado esperado**: Redirigido a tenant1.localhost:3000

## 🔧 Configuración de Producción

### 1. Variables de Entorno

```env
# Backend
JWT_SECRET_KEY=your-production-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Frontend
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_MAIN_DOMAIN=yourdomain.com
```

### 2. Configuración de Nginx

```nginx
# Main domain
server {
    server_name yourdomain.com;
    location / {
        proxy_pass http://localhost:3000;
    }
}

# Wildcard subdomain for tenants
server {
    server_name *.yourdomain.com;
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Tenant-Slug $subdomain;
    }
}
```

### 3. DNS Configuration

Configurar wildcard DNS record:
```
*.yourdomain.com -> Your server IP
```

## 🔍 Debugging

### Verificar Token en Browser Console

```javascript
// En la consola del navegador
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('User Role:', payload.role);
console.log('Tenant:', payload.tenant_slug);
```

### Logs del Middleware

El middleware registra intentos de acceso no autorizado:
```
Access denied. User role 'tenant_user' from tenant 'tenant1' attempted to access tenant 'tenant2'
```

## 📊 Diagrama de Flujo de Autenticación

```
1. Usuario ingresa a tenant1.localhost:3000/auth/login
2. Login con credenciales
3. Backend verifica credenciales
4. Backend determina rol del usuario:
   - Si username = "admin" → role = "super_admin"
   - Si está en tenant_users → role según tabla
5. Backend genera JWT con rol incluido
6. Frontend decodifica token
7. TenantAccessGuard verifica:
   - Rol del usuario
   - Subdominio actual
   - Permisos de acceso
8. Si acceso válido → Renderiza contenido
   Si acceso inválido → Redirige o muestra error
```

## 🐛 Solución de Problemas Comunes

### Problema: "Access Denied" al acceder a /admin
**Solución**: Verificar que el rol en el token sea "super_admin" o "tenant_admin"

### Problema: Loop de redirección
**Solución**: Verificar configuración de subdominios en /etc/hosts

### Problema: Token no incluye rol
**Solución**: Verificar que el backend esté usando la versión actualizada de main.py

### Problema: No se puede acceder a subdominios
**Solución**: 
1. Verificar /etc/hosts
2. Reiniciar navegador
3. Limpiar caché y cookies

## 📚 Referencias

- [JWT.io](https://jwt.io/) - Para decodificar y verificar tokens
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [React Router Guards](https://reactrouter.com/en/main/route/route#loader)

## 🤝 Contribuciones

Para agregar nuevos roles o modificar permisos:

1. Actualizar enum `UserRole` en `models.py`
2. Modificar lógica en `tenant_access_middleware.py`
3. Actualizar `TenantAccessGuard.tsx` con nuevas reglas
4. Agregar casos de prueba

## 📝 Notas Importantes

1. **Seguridad**: Nunca confiar solo en validación frontend, siempre validar en backend
2. **Tokens**: Implementar refresh tokens para sesiones largas
3. **Auditoría**: Registrar todos los intentos de acceso no autorizado
4. **Performance**: Considerar caché para verificaciones frecuentes de permisos

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0.0