# pgAdmin Configuration

pgAdmin is a web-based PostgreSQL database management tool included in the Docker Compose stack for easy database administration.

## 🚀 Access Information

- **URL**: http://localhost:5050
- **Email**: admin@admin.com
- **Password**: admin123

## 📊 Pre-configured Connection

The PostgreSQL server is automatically configured with the following settings:
- **Server Name**: MultiTenant PostgreSQL
- **Host**: postgres (internal Docker network)
- **Port**: 5432
- **Database**: multitenant_db
- **Username**: postgres
- **Password**: postgres123

## 🔧 Features Available

### Database Management
- View all schemas (tenants)
- Browse tables, views, and indexes
- Execute SQL queries
- View and edit data
- Import/Export data
- Backup and restore databases

### Schema Navigation
Each tenant has its own schema:
- `public` - Default PostgreSQL schema
- `tenant_*` - Individual tenant schemas (e.g., `tenant_abc123`)

### Useful Queries

#### View All Tenant Schemas
```sql
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE 'tenant_%'
ORDER BY schema_name;
```

#### Count Tables per Tenant
```sql
SELECT 
    schemaname as tenant_schema,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname LIKE 'tenant_%'
GROUP BY schemaname
ORDER BY schemaname;
```

#### View Inbox Conversations for a Tenant
```sql
-- Replace 'tenant_abc123' with actual tenant schema
SELECT 
    id,
    channel,
    contact_name,
    contact_identifier,
    status,
    created_at
FROM tenant_abc123.inbox_conversations
ORDER BY created_at DESC
LIMIT 10;
```

#### View Chat Channels for a Tenant
```sql
-- Replace 'tenant_abc123' with actual tenant schema
SELECT 
    id,
    name,
    type,
    created_at
FROM tenant_abc123.channels
ORDER BY created_at DESC;
```

#### Check Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname LIKE 'tenant_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 🛠️ Common Tasks

### 1. Creating a New Tenant Schema Manually
```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS tenant_new_tenant;

-- Grant permissions
GRANT ALL ON SCHEMA tenant_new_tenant TO postgres;
```

### 2. Backing Up a Tenant's Data
1. Right-click on the tenant schema
2. Select "Backup..."
3. Choose format and location
4. Click "Backup"

### 3. Viewing Real-time Queries
1. Go to Dashboard
2. Select the database
3. View "Server Activity"

### 4. Query Tool
1. Right-click on any database/schema
2. Select "Query Tool"
3. Write and execute SQL queries
4. Export results as CSV/JSON

## 🔒 Security Notes

- **Development Only**: The current configuration is for development. In production:
  - Use strong passwords
  - Enable SSL
  - Restrict network access
  - Use separate read-only accounts for viewing

- **Password Storage**: pgAdmin stores server passwords. In production, consider:
  - Using connection service files
  - Implementing OAuth/LDAP
  - Using environment-specific configurations

## 🐳 Docker Commands

### Start pgAdmin
```bash
docker-compose up -d pgadmin
```

### Stop pgAdmin
```bash
docker-compose stop pgadmin
```

### View pgAdmin Logs
```bash
docker-compose logs -f pgadmin
```

### Reset pgAdmin Configuration
```bash
docker-compose down
docker volume rm travel_system_pgadmin_data
docker-compose up -d pgadmin
```

## 📝 Troubleshooting

### Cannot Connect to Server
- Ensure PostgreSQL container is running: `docker-compose ps postgres`
- Check network connectivity: `docker network ls`
- Verify credentials in servers.json

### Forgot pgAdmin Password
1. Stop the container: `docker-compose stop pgadmin`
2. Remove the volume: `docker volume rm travel_system_pgadmin_data`
3. Start again: `docker-compose up -d pgadmin`

### Permission Denied Errors
- Ensure proper permissions on mounted volumes
- Check Docker user permissions
- Verify PostgreSQL user privileges

## 📚 Additional Resources

- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker pgAdmin Image](https://hub.docker.com/r/dpage/pgadmin4/)

## 🎯 Quick Start

1. Start the services:
```bash
docker-compose up -d postgres pgadmin
```

2. Open browser and navigate to: http://localhost:5050

3. Login with:
   - Email: `admin@admin.com`
   - Password: `admin123`

4. The PostgreSQL server is already configured and ready to use!

## 📊 Monitoring Queries

### Active Connections
```sql
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    backend_start,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY backend_start DESC;
```

### Database Size
```sql
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
ORDER BY pg_database_size(pg_database.datname) DESC;
```

### Table Statistics
```sql
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname LIKE 'tenant_%'
ORDER BY n_live_tup DESC;
```
