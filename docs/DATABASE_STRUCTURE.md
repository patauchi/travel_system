# 📊 Estructura de Base de Datos - Sistema Multi-Tenant

## 📍 Resumen Ejecutivo

### Estadísticas Actuales
- **Total de Usuarios**: 10
- **Total de Tenants**: 9
- **Relaciones Usuario-Tenant**: 9
- **Registros de Auditoría**: 21

### Arquitectura
- **Base de Datos**: PostgreSQL 14+
- **Tipo**: Multi-tenant con schemas aislados
- **Schemas Principales**: `shared` (global), `tenant_*` (por cliente)

## 🏗️ Arquitectura General

El sistema utiliza PostgreSQL con una arquitectura multi-tenant híbrida:
- **Schema Compartido (`shared`)**: Datos globales y de gestión
- **Schema por Tenant (`tenant_*`)**: Datos aislados de cada tenant
- **Schema Template (`tenant_template`)**: Plantilla para nuevos tenants

## 📁 Schemas

### 1. Schema `shared` (Global)
Contiene todas las tablas compartidas entre tenants y la gestión del sistema.

### 2. Schema `tenant_template` 
Plantilla que se clona para cada nuevo tenant.

### 3. Schemas Dinámicos `tenant_*`
Un schema por cada tenant (ej: `tenant_company1`, `tenant_company2`).

---

## 📋 Tablas del Schema `shared`

### 👥 **users**
Tabla principal de usuarios del sistema.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `email` | VARCHAR(255) | Email del usuario | UNIQUE, NOT NULL |
| `username` | VARCHAR(100) | Nombre de usuario | UNIQUE, NOT NULL |
| `password_hash` | VARCHAR(255) | Hash de contraseña | NOT NULL |
| `first_name` | VARCHAR(100) | Nombre | |
| `last_name` | VARCHAR(100) | Apellido | |
| `phone` | VARCHAR(50) | Teléfono | |
| `is_active` | BOOLEAN | Usuario activo | DEFAULT true |
| `is_verified` | BOOLEAN | Email verificado | DEFAULT false |
| `email_verified_at` | TIMESTAMP | Fecha de verificación | |
| `last_login_at` | TIMESTAMP | Último login | |
| `failed_login_attempts` | INTEGER | Intentos fallidos | DEFAULT 0 |
| `locked_until` | TIMESTAMP | Bloqueado hasta | |
| `two_factor_enabled` | BOOLEAN | 2FA habilitado | DEFAULT false |
| `two_factor_secret` | VARCHAR(255) | Secreto 2FA | |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_users_email` ON (email)
- `idx_users_username` ON (username)

---

### 🏢 **tenants**
Tabla de organizaciones/empresas del sistema.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `slug` | VARCHAR(100) | Slug único | UNIQUE, NOT NULL |
| `name` | VARCHAR(255) | Nombre del tenant | NOT NULL |
| `domain` | VARCHAR(255) | Dominio personalizado | |
| `subdomain` | VARCHAR(100) | Subdominio | UNIQUE |
| `schema_name` | VARCHAR(63) | Nombre del schema | UNIQUE, NOT NULL |
| `status` | ENUM | Estado del tenant | DEFAULT 'pending' |
| `subscription_plan` | ENUM | Plan de suscripción | DEFAULT 'free' |
| `max_users` | INTEGER | Límite de usuarios | DEFAULT 5 |
| `max_storage_gb` | INTEGER | Límite de almacenamiento | DEFAULT 10 |
| `settings` | JSONB | Configuraciones | DEFAULT '{}' |
| `metadata` | JSONB | Metadatos | DEFAULT '{}' |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |
| `suspended_at` | TIMESTAMP | Fecha de suspensión | |
| `trial_ends_at` | TIMESTAMP | Fin del trial | |
| `subscription_ends_at` | TIMESTAMP | Fin de suscripción | |

**Valores ENUM:**
- `status`: 'active', 'suspended', 'trial', 'expired', 'pending'
- `subscription_plan`: 'free', 'starter', 'professional', 'enterprise'

**Índices:**
- `idx_tenants_slug` ON (slug)
- `idx_tenants_subdomain` ON (subdomain)
- `idx_tenants_status` ON (status)

---

### 🔗 **tenant_users**
Relación entre usuarios y tenants con roles.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id), NOT NULL |
| `user_id` | UUID | ID del usuario | FK → users(id), NOT NULL |
| `role` | ENUM | Rol del usuario | DEFAULT 'tenant_user' |
| `is_owner` | BOOLEAN | Es propietario | DEFAULT false |
| `permissions` | JSONB | Permisos específicos | DEFAULT '{}' |
| `joined_at` | TIMESTAMP | Fecha de unión | DEFAULT CURRENT_TIMESTAMP |
| `invited_by` | UUID | Invitado por | FK → users(id) |
| `invitation_token` | VARCHAR(255) | Token de invitación | |
| `invitation_accepted_at` | TIMESTAMP | Invitación aceptada | |
| `last_active_at` | TIMESTAMP | Última actividad | |

**Valores ENUM `role`:**
- `super_admin`: Administrador del sistema
- `tenant_admin`: Administrador del tenant
- `tenant_user`: Usuario regular
- `tenant_viewer`: Usuario de solo lectura

**Constraints:**
- UNIQUE(tenant_id, user_id)

**Índices:**
- `idx_tenant_users_tenant_id` ON (tenant_id)
- `idx_tenant_users_user_id` ON (user_id)

---

### 🔑 **api_keys**
Claves API para acceso programático.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id), NOT NULL |
| `name` | VARCHAR(255) | Nombre de la clave | NOT NULL |
| `key_hash` | VARCHAR(255) | Hash de la clave | NOT NULL |
| `key_prefix` | VARCHAR(10) | Prefijo visible | NOT NULL |
| `scopes` | JSONB | Alcances permitidos | DEFAULT '[]' |
| `rate_limit` | INTEGER | Límite de peticiones | DEFAULT 1000 |
| `expires_at` | TIMESTAMP | Fecha de expiración | |
| `last_used_at` | TIMESTAMP | Último uso | |
| `created_by` | UUID | Creado por | FK → users(id) |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `revoked_at` | TIMESTAMP | Fecha de revocación | |

**Constraints:**
- UNIQUE(tenant_id, name)

**Índices:**
- `idx_api_keys_tenant_id` ON (tenant_id)
- `idx_api_keys_key_prefix` ON (key_prefix)

---

### 📝 **audit_logs**
Registro de auditoría del sistema.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id) ON DELETE SET NULL |
| `user_id` | UUID | ID del usuario | FK → users(id) ON DELETE SET NULL |
| `action` | VARCHAR(100) | Acción realizada | NOT NULL |
| `resource_type` | VARCHAR(100) | Tipo de recurso | |
| `resource_id` | VARCHAR(255) | ID del recurso | |
| `details` | JSONB | Detalles adicionales | DEFAULT '{}' |
| `ip_address` | INET | Dirección IP | |
| `user_agent` | TEXT | User Agent | |
| `created_at` | TIMESTAMP | Fecha del evento | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_audit_logs_tenant_id` ON (tenant_id)
- `idx_audit_logs_user_id` ON (user_id)
- `idx_audit_logs_created_at` ON (created_at)

---

### 🚀 **feature_flags**
Banderas de características del sistema.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `name` | VARCHAR(100) | Nombre de la característica | UNIQUE, NOT NULL |
| `description` | TEXT | Descripción | |
| `is_enabled` | BOOLEAN | Habilitado globalmente | DEFAULT false |
| `rollout_percentage` | INTEGER | % de despliegue | DEFAULT 0, CHECK (0-100) |
| `tenant_overrides` | JSONB | Excepciones por tenant | DEFAULT '{}' |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

---

### 🎯 **tenant_features**
Características habilitadas por tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id), NOT NULL |
| `feature_id` | UUID | ID de la característica | FK → feature_flags(id), NOT NULL |
| `is_enabled` | BOOLEAN | Habilitado | NOT NULL |
| `configuration` | JSONB | Configuración específica | DEFAULT '{}' |
| `enabled_at` | TIMESTAMP | Fecha de habilitación | DEFAULT CURRENT_TIMESTAMP |
| `enabled_by` | UUID | Habilitado por | FK → users(id) |

**Constraints:**
- UNIQUE(tenant_id, feature_id)

---

### 💳 **subscription_history**
Historial de cambios de suscripción.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id), NOT NULL |
| `plan_from` | ENUM | Plan anterior | |
| `plan_to` | ENUM | Plan nuevo | NOT NULL |
| `change_type` | VARCHAR(50) | Tipo de cambio | NOT NULL |
| `price_paid` | DECIMAL(10,2) | Precio pagado | |
| `currency` | VARCHAR(3) | Moneda | DEFAULT 'USD' |
| `payment_method` | VARCHAR(50) | Método de pago | |
| `transaction_id` | VARCHAR(255) | ID de transacción | |
| `changed_at` | TIMESTAMP | Fecha del cambio | DEFAULT CURRENT_TIMESTAMP |
| `changed_by` | UUID | Cambiado por | FK → users(id) |
| `notes` | TEXT | Notas adicionales | |

**Valores `change_type`:**
- 'upgrade', 'downgrade', 'renewal', 'cancellation'

---

### 🔔 **webhooks**
Configuración de webhooks por tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `tenant_id` | UUID | ID del tenant | FK → tenants(id), NOT NULL |
| `name` | VARCHAR(255) | Nombre del webhook | NOT NULL |
| `url` | TEXT | URL destino | NOT NULL |
| `events` | JSONB | Eventos suscritos | NOT NULL, DEFAULT '[]' |
| `headers` | JSONB | Headers personalizados | DEFAULT '{}' |
| `secret` | VARCHAR(255) | Secreto para firma | |
| `is_active` | BOOLEAN | Activo | DEFAULT true |
| `retry_count` | INTEGER | Intentos de reintento | DEFAULT 3 |
| `timeout_seconds` | INTEGER | Timeout en segundos | DEFAULT 30 |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |
| `last_triggered_at` | TIMESTAMP | Último disparo | |

**Constraints:**
- UNIQUE(tenant_id, name)

---

### 📊 **webhook_logs**
Registro de ejecuciones de webhooks.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `webhook_id` | UUID | ID del webhook | FK → webhooks(id), NOT NULL |
| `event_type` | VARCHAR(100) | Tipo de evento | NOT NULL |
| `payload` | JSONB | Payload enviado | NOT NULL |
| `response_status` | INTEGER | Código HTTP respuesta | |
| `response_body` | TEXT | Cuerpo de respuesta | |
| `attempts` | INTEGER | Número de intentos | DEFAULT 1 |
| `success` | BOOLEAN | Fue exitoso | DEFAULT false |
| `error_message` | TEXT | Mensaje de error | |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `completed_at` | TIMESTAMP | Fecha de completado | |

**Índices:**
- `idx_webhook_logs_webhook_id` ON (webhook_id)
- `idx_webhook_logs_created_at` ON (created_at)

---

### ⚙️ **system_settings**
Configuraciones globales del sistema.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `key` | VARCHAR(100) | Clave de configuración | PRIMARY KEY |
| `value` | JSONB | Valor | NOT NULL |
| `description` | TEXT | Descripción | |
| `is_public` | BOOLEAN | Es público | DEFAULT false |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |
| `updated_by` | UUID | Actualizado por | FK → users(id) |

---

## 📋 Tablas del Schema `tenant_template`

Estas tablas se replican para cada tenant en su schema específico.

### 👤 **profiles**
Perfiles de usuario específicos del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `user_id` | UUID | ID del usuario | NOT NULL |
| `avatar_url` | TEXT | URL del avatar | |
| `bio` | TEXT | Biografía | |
| `preferences` | JSONB | Preferencias | DEFAULT '{}' |
| `timezone` | VARCHAR(50) | Zona horaria | DEFAULT 'UTC' |
| `language` | VARCHAR(10) | Idioma | DEFAULT 'en' |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_profiles_user_id` ON (user_id)

---

### 📁 **projects**
Proyectos del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `name` | VARCHAR(255) | Nombre del proyecto | NOT NULL |
| `description` | TEXT | Descripción | |
| `status` | VARCHAR(50) | Estado | DEFAULT 'active' |
| `owner_id` | UUID | ID del propietario | NOT NULL |
| `settings` | JSONB | Configuraciones | DEFAULT '{}' |
| `metadata` | JSONB | Metadatos | DEFAULT '{}' |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |
| `archived_at` | TIMESTAMP | Fecha de archivo | |

**Índices:**
- `idx_projects_owner_id` ON (owner_id)

---

### 📄 **documents**
Documentos del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `project_id` | UUID | ID del proyecto | FK → projects(id) |
| `title` | VARCHAR(255) | Título | NOT NULL |
| `content` | TEXT | Contenido | |
| `content_type` | VARCHAR(100) | Tipo de contenido | |
| `file_path` | TEXT | Ruta del archivo | |
| `file_size` | BIGINT | Tamaño del archivo | |
| `version` | INTEGER | Versión | DEFAULT 1 |
| `created_by` | UUID | Creado por | NOT NULL |
| `updated_by` | UUID | Actualizado por | |
| `tags` | JSONB | Etiquetas | DEFAULT '[]' |
| `metadata` | JSONB | Metadatos | DEFAULT '{}' |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_documents_project_id` ON (project_id)

---

### ✅ **tasks**
Tareas del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `project_id` | UUID | ID del proyecto | FK → projects(id) |
| `title` | VARCHAR(255) | Título | NOT NULL |
| `description` | TEXT | Descripción | |
| `status` | VARCHAR(50) | Estado | DEFAULT 'pending' |
| `priority` | VARCHAR(20) | Prioridad | DEFAULT 'medium' |
| `assignee_id` | UUID | Asignado a | |
| `due_date` | DATE | Fecha de vencimiento | |
| `completed_at` | TIMESTAMP | Fecha de completado | |
| `tags` | JSONB | Etiquetas | DEFAULT '[]' |
| `metadata` | JSONB | Metadatos | DEFAULT '{}' |
| `created_by` | UUID | Creado por | NOT NULL |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_tasks_project_id` ON (project_id)
- `idx_tasks_assignee_id` ON (assignee_id)

---

### 💬 **comments**
Comentarios del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `resource_type` | VARCHAR(50) | Tipo de recurso | NOT NULL |
| `resource_id` | UUID | ID del recurso | NOT NULL |
| `parent_id` | UUID | Comentario padre | FK → comments(id) |
| `content` | TEXT | Contenido | NOT NULL |
| `author_id` | UUID | ID del autor | NOT NULL |
| `edited_at` | TIMESTAMP | Fecha de edición | |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |
| `updated_at` | TIMESTAMP | Última actualización | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_comments_resource` ON (resource_type, resource_id)

---

### 🔔 **notifications**
Notificaciones del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `user_id` | UUID | ID del usuario | NOT NULL |
| `type` | VARCHAR(50) | Tipo de notificación | NOT NULL |
| `title` | VARCHAR(255) | Título | NOT NULL |
| `message` | TEXT | Mensaje | |
| `data` | JSONB | Datos adicionales | DEFAULT '{}' |
| `is_read` | BOOLEAN | Leída | DEFAULT false |
| `read_at` | TIMESTAMP | Fecha de lectura | |
| `created_at` | TIMESTAMP | Fecha de creación | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_notifications_user_id` ON (user_id)
- `idx_notifications_is_read` ON (is_read)

---

### 📊 **activity_log**
Registro de actividad del tenant.

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `id` | UUID | Identificador único | PRIMARY KEY |
| `user_id` | UUID | ID del usuario | NOT NULL |
| `action` | VARCHAR(100) | Acción realizada | NOT NULL |
| `resource_type` | VARCHAR(50) | Tipo de recurso | |
| `resource_id` | UUID | ID del recurso | |
| `changes` | JSONB | Cambios realizados | DEFAULT '{}' |
| `ip_address` | INET | Dirección IP | |
| `user_agent` | TEXT | User Agent | |
| `created_at` | TIMESTAMP | Fecha del evento | DEFAULT CURRENT_TIMESTAMP |

**Índices:**
- `idx_activity_log_user_id` ON (user_id)
- `idx_activity_log_created_at` ON (created_at)

---

## 🔧 Funciones del Sistema

### create_tenant_schema(tenant_schema_name VARCHAR)
Crea un nuevo schema para un tenant copiando la estructura de `tenant_template`.

```sql
-- Ejemplo de uso:
SELECT create_tenant_schema('tenant_company1');
```

### drop_tenant_schema(tenant_schema_name VARCHAR)
Elimina completamente un schema de tenant.

```sql
-- Ejemplo de uso:
SELECT drop_tenant_schema('tenant_company1');
```

### update_updated_at_column()
Trigger function que actualiza automáticamente el campo `updated_at`.

---

## 🔄 Triggers

### update_{table}_updated_at
Trigger aplicado a todas las tablas con columna `updated_at` que actualiza automáticamente la fecha de modificación.

---

## 🎨 Diagrama de Relaciones Principales

### Diagrama ERD Simplificado

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│    users     │◄────────┤ tenant_users ├────────►│   tenants    │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                         │
       │                        │                         │
       ▼                        ▼                         ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  audit_logs  │         │   api_keys   │         │   webhooks   │
└──────────────┘         └──────────────┘         └──────────────┘
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │ webhook_logs │
                                                   └──────────────┘

┌──────────────┐         ┌──────────────┐
│feature_flags │◄────────┤tenant_features│
└──────────────┘         └──────────────┘

┌──────────────────┐
│subscription_history│
└──────────────────┘
```

### Diagrama ERD Detallado

```
╔═══════════════════════════════════════════════════════════════════════╗
║                            SCHEMA: shared                              ║
╚═══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────┐
│            users                    │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│    │ email (VARCHAR) [UNIQUE]       │
│    │ username (VARCHAR) [UNIQUE]    │
│    │ password_hash (VARCHAR)        │
│    │ first_name (VARCHAR)           │
│    │ last_name (VARCHAR)            │
│    │ is_active (BOOLEAN)            │
│    │ is_verified (BOOLEAN)          │
│    │ created_at (TIMESTAMP)         │
└─────────────────────────────────────┘
         │                    ▲
         │                    │
         │              ┌─────┴─────┐
         ▼              │           │
┌─────────────────────────────────────┐
│         tenant_users                │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│ FK │ tenant_id ──────────┐         │
│ FK │ user_id             │         │
│    │ role (ENUM)         │         │
│    │ is_owner (BOOLEAN)  │         │
│    │ permissions (JSONB) │         │
│    │ joined_at (TIMESTAMP)         │
└─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────┐
│            tenants                  │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│    │ slug (VARCHAR) [UNIQUE]        │
│    │ name (VARCHAR)                 │
│    │ subdomain (VARCHAR) [UNIQUE]   │
│    │ schema_name (VARCHAR) [UNIQUE] │
│    │ status (ENUM)                  │
│    │ subscription_plan (ENUM)       │
│    │ max_users (INTEGER)            │
│    │ created_at (TIMESTAMP)         │
└─────────────────────────────────────┘
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  api_keys    │ │   webhooks   │ │tenant_features│ │subscription_ │
│              │ │              │ │              │ │   history    │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

╔═══════════════════════════════════════════════════════════════════════╗
║                        SCHEMA: tenant_template                         ║
║                    (Clonado para cada nuevo tenant)                    ║
╚═══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────┐
│           projects                  │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│    │ name (VARCHAR)                 │
│    │ owner_id (UUID)                │
│    │ status (VARCHAR)               │
└─────────────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  documents   │ │    tasks     │ │  comments    │
└──────────────┘ └──────────────┘ └──────────────┘

┌─────────────────────────────────────┐
│         notifications               │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│    │ user_id (UUID)                 │
│    │ type (VARCHAR)                 │
│    │ is_read (BOOLEAN)              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│         activity_log                │
├─────────────────────────────────────┤
│ PK │ id (UUID)                      │
│    │ user_id (UUID)                 │
│    │ action (VARCHAR)               │
│    │ created_at (TIMESTAMP)         │
└─────────────────────────────────────┘
```

### Leyenda de Relaciones
- `──────►` : Relación uno a muchos (1:N)
- `◄──────►` : Relación muchos a muchos (N:M)
- `PK` : Primary Key
- `FK` : Foreign Key
- `[UNIQUE]` : Constraint único

---

## 🚀 Flujo de Creación de Tenant

1. **Registro de Tenant**: Se inserta en `tenants`
2. **Creación de Schema**: Se ejecuta `create_tenant_schema('tenant_xyz')`
3. **Asignación de Usuario**: Se inserta en `tenant_users` con rol `tenant_admin`
4. **Configuración Inicial**: Se establecen feature flags en `tenant_features`
5. **Registro de Suscripción**: Se inserta en `subscription_history`

---

## 🔐 Consideraciones de Seguridad

1. **Aislamiento de Datos**: Cada tenant tiene su propio schema
2. **Row Level Security**: Implementado a nivel de aplicación mediante tenant_id
3. **Auditoría Completa**: Todos los cambios se registran en `audit_logs`
4. **API Keys**: Hash seguro de claves con prefijo visible
5. **Roles Granulares**: Sistema de roles con permisos específicos

---

## 📈 Optimización y Performance

### Índices Críticos
- Búsquedas por email/username
- Filtrado por tenant_id
- Consultas por fechas (created_at)
- Búsquedas por slug/subdomain

### Particionamiento Sugerido
Para grandes volúmenes:
- `audit_logs`: Particionar por mes
- `webhook_logs`: Particionar por mes
- `activity_log`: Particionar por tenant y mes

---

## 🔄 Mantenimiento

### Tareas Periódicas Recomendadas
1. **VACUUM ANALYZE** semanal en tablas grandes
2. **Limpieza de logs** antiguos (>90 días)
3. **Archivado de audit_logs** (>1 año)
4. **Revisión de índices** no utilizados
5. **Monitoreo de tamaño** de schemas por tenant

---

## 📊 Consultas SQL Útiles

### Verificar Tamaño de Schemas
```sql
SELECT 
    schemaname,
    pg_size_pretty(sum(pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename)))::bigint) as size
FROM pg_tables 
WHERE schemaname LIKE 'tenant_%' 
GROUP BY schemaname
ORDER BY sum(pg_total_relation_size(quote_ident(schemaname)||'.'||quote_ident(tablename)))::bigint DESC;
```

### Usuarios por Tenant
```sql
SELECT 
    t.name as tenant_name,
    t.slug,
    COUNT(tu.user_id) as user_count,
    t.max_users as max_allowed
FROM shared.tenants t
LEFT JOIN shared.tenant_users tu ON t.id = tu.tenant_id
GROUP BY t.id, t.name, t.slug, t.max_users
ORDER BY user_count DESC;
```

### Actividad Reciente
```sql
SELECT 
    al.action,
    u.username,
    t.name as tenant_name,
    al.created_at
FROM shared.audit_logs al
LEFT JOIN shared.users u ON al.user_id = u.id
LEFT JOIN shared.tenants t ON al.tenant_id = t.id
ORDER BY al.created_at DESC
LIMIT 20;
```

### Estado de Suscripciones
```sql
SELECT 
    subscription_plan,
    status,
    COUNT(*) as count
FROM shared.tenants
GROUP BY subscription_plan, status
ORDER BY subscription_plan, status;
```

---

**Última actualización**: Diciembre 2024
**Versión de PostgreSQL**: 14+
**Total de Tablas en Schema Shared**: 11
**Total de Tablas en Template**: 8