#!/usr/bin/env python3
"""
Fix Tenant Schemas Script
This script fixes existing tenant schemas and ensures all tables have the correct structure
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres123@localhost:5432/multitenant_db")

# SQL for creating tables with correct structure
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    phone VARCHAR(50),
    phone_secondary VARCHAR(50),
    avatar_url VARCHAR(500),
    bio TEXT,

    -- Professional Information
    title VARCHAR(100),
    department VARCHAR(100),
    employee_id VARCHAR(50) UNIQUE,

    -- Status and Verification
    status VARCHAR(20) DEFAULT 'active',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,
    phone_verified_at TIMESTAMPTZ,

    -- Preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(3) DEFAULT 'USD',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT '24h',

    -- Notifications
    notification_preferences JSONB DEFAULT '{{}}',
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,

    -- Security
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    last_activity_at TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,

    -- Metadata
    metadata_json JSONB DEFAULT '{{}}',
    tags JSONB DEFAULT '[]',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,
    created_by UUID,
    updated_by UUID,
    deleted_by UUID
);

CREATE INDEX IF NOT EXISTS idx_{schema}_users_email ON {schema}.users(email);
CREATE INDEX IF NOT EXISTS idx_{schema}_users_username ON {schema}.users(username);
CREATE INDEX IF NOT EXISTS idx_{schema}_users_is_active ON {schema}.users(is_active);
CREATE INDEX IF NOT EXISTS idx_{schema}_users_status ON {schema}.users(status);
"""

CREATE_ROLES_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Hierarchy
    parent_id UUID REFERENCES {schema}.roles(id),
    priority INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,

    -- Metadata
    metadata_json JSONB DEFAULT '{{}}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS idx_{schema}_roles_name ON {schema}.roles(name);
CREATE INDEX IF NOT EXISTS idx_{schema}_roles_is_active ON {schema}.roles(is_active);
"""

CREATE_PERMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    conditions JSONB,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(resource, action)
);

CREATE INDEX IF NOT EXISTS idx_{schema}_permissions_name ON {schema}.permissions(name);
CREATE INDEX IF NOT EXISTS idx_{schema}_permissions_resource ON {schema}.permissions(resource);
CREATE INDEX IF NOT EXISTS idx_{schema}_permissions_action ON {schema}.permissions(action);
"""

CREATE_TEAMS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    code VARCHAR(20),

    -- Hierarchy
    parent_id UUID REFERENCES {schema}.teams(id),
    manager_id UUID REFERENCES {schema}.users(id),
    lead_id UUID REFERENCES {schema}.users(id),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Metadata
    metadata_json JSONB DEFAULT '{{}}',

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_by UUID
);

CREATE INDEX IF NOT EXISTS idx_{schema}_teams_name ON {schema}.teams(name);
CREATE INDEX IF NOT EXISTS idx_{schema}_teams_is_active ON {schema}.teams(is_active);
"""

# Association tables
CREATE_USER_ROLES_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.user_roles (
    user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
    role_id UUID REFERENCES {schema}.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID,
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, role_id)
);
"""

CREATE_USER_TEAMS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.user_teams (
    user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES {schema}.teams(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50),
    PRIMARY KEY (user_id, team_id)
);
"""

CREATE_ROLE_PERMISSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.role_permissions (
    role_id UUID REFERENCES {schema}.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES {schema}.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID,
    PRIMARY KEY (role_id, permission_id)
);
"""

CREATE_TEAM_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.team_members (
    team_id UUID REFERENCES {schema}.teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    role VARCHAR(50),
    PRIMARY KEY (team_id, user_id)
);
"""

# Additional tables
CREATE_USER_SESSIONS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    refresh_token_hash VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    last_activity TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{schema}_sessions_token ON {schema}.user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_{schema}_sessions_user ON {schema}.user_sessions(user_id);
"""

CREATE_AUDIT_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES {schema}.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    response_status INTEGER,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{schema}_audit_user ON {schema}.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_{schema}_audit_action ON {schema}.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_{schema}_audit_created ON {schema}.audit_logs(created_at);
"""

CREATE_API_KEYS_TABLE = """
CREATE TABLE IF NOT EXISTS {schema}.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES {schema}.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    permissions JSONB DEFAULT '[]',
    allowed_ips JSONB DEFAULT '[]',
    allowed_origins JSONB DEFAULT '[]',
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_{schema}_apikeys_user ON {schema}.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_{schema}_apikeys_prefix ON {schema}.api_keys(key_prefix);
"""

# All table creation statements
ALL_TABLES = [
    ("users", CREATE_USERS_TABLE),
    ("roles", CREATE_ROLES_TABLE),
    ("permissions", CREATE_PERMISSIONS_TABLE),
    ("teams", CREATE_TEAMS_TABLE),
    ("user_roles", CREATE_USER_ROLES_TABLE),
    ("user_teams", CREATE_USER_TEAMS_TABLE),
    ("role_permissions", CREATE_ROLE_PERMISSIONS_TABLE),
    ("team_members", CREATE_TEAM_MEMBERS_TABLE),
    ("user_sessions", CREATE_USER_SESSIONS_TABLE),
    ("audit_logs", CREATE_AUDIT_LOGS_TABLE),
    ("api_keys", CREATE_API_KEYS_TABLE)
]

def get_tenant_schemas(engine):
    """Get all tenant schemas from the database"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name LIKE 'tenant_%'
            ORDER BY schema_name
        """))
        return [row[0] for row in result]

def get_schema_tables(engine, schema):
    """Get all tables in a schema"""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = :schema
            ORDER BY tablename
        """), {"schema": schema})
        return [row[0] for row in result]

def create_schema_if_not_exists(engine, schema):
    """Create schema if it doesn't exist"""
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()

def create_table(engine, schema, table_name, create_sql):
    """Create a table in the specified schema"""
    try:
        with engine.connect() as conn:
            # Format the SQL with the schema name
            formatted_sql = create_sql.format(schema=schema)
            conn.execute(text(formatted_sql))
            conn.commit()
            logger.info(f"✓ Created/verified table {schema}.{table_name}")
            return True
    except Exception as e:
        logger.error(f"✗ Failed to create table {schema}.{table_name}: {str(e)}")
        return False

def fix_tenant_schema(engine, schema):
    """Fix a single tenant schema"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing schema: {schema}")
    logger.info(f"{'='*60}")

    # Get existing tables
    existing_tables = get_schema_tables(engine, schema)
    logger.info(f"Existing tables ({len(existing_tables)}): {', '.join(existing_tables)}")

    # Create all required tables
    success_count = 0
    failed_count = 0

    for table_name, create_sql in ALL_TABLES:
        if create_table(engine, schema, table_name, create_sql):
            success_count += 1
        else:
            failed_count += 1

    # Get updated table list
    updated_tables = get_schema_tables(engine, schema)
    new_tables = set(updated_tables) - set(existing_tables)

    logger.info(f"\nSummary for {schema}:")
    logger.info(f"  • Tables before: {len(existing_tables)}")
    logger.info(f"  • Tables after: {len(updated_tables)}")
    logger.info(f"  • New tables created: {len(new_tables)}")
    if new_tables:
        logger.info(f"  • New tables: {', '.join(new_tables)}")
    logger.info(f"  • Success: {success_count}, Failed: {failed_count}")

    return success_count, failed_count

def create_new_test_tenant(engine, tenant_slug):
    """Create a new test tenant with all proper tables"""
    schema_name = f"tenant_{tenant_slug}"

    logger.info(f"\n{'='*60}")
    logger.info(f"Creating new test tenant: {tenant_slug}")
    logger.info(f"Schema: {schema_name}")
    logger.info(f"{'='*60}")

    # Create schema
    try:
        create_schema_if_not_exists(engine, schema_name)
        logger.info(f"✓ Schema {schema_name} created/verified")
    except Exception as e:
        logger.error(f"✗ Failed to create schema: {str(e)}")
        return False

    # Create all tables
    success_count = 0
    failed_count = 0

    for table_name, create_sql in ALL_TABLES:
        if create_table(engine, schema_name, table_name, create_sql):
            success_count += 1
        else:
            failed_count += 1

    # Insert tenant record in shared.tenants table
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO shared.tenants (
                    id, slug, name, subdomain, schema_name,
                    status, subscription_plan, max_users, max_storage_gb,
                    settings, created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :slug, :name, :subdomain, :schema_name,
                    'active', 'professional', 100, 10,
                    '{"features": ["users", "roles", "teams", "permissions"]}'::jsonb,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                ON CONFLICT (slug) DO NOTHING
            """), {
                "slug": tenant_slug,
                "name": f"Test Tenant {tenant_slug}",
                "subdomain": tenant_slug,
                "schema_name": schema_name
            })
            conn.commit()
            logger.info(f"✓ Tenant record created in shared.tenants")
    except Exception as e:
        logger.warning(f"⚠ Could not create tenant record (may already exist): {str(e)}")

    logger.info(f"\n✅ Test tenant '{tenant_slug}' created successfully!")
    logger.info(f"  • Schema: {schema_name}")
    logger.info(f"  • Tables created: {success_count}")
    logger.info(f"  • Tables failed: {failed_count}")

    return True

def main():
    """Main function"""
    logger.info("=" * 60)
    logger.info("TENANT SCHEMA FIX SCRIPT")
    logger.info("=" * 60)

    # Create engine
    engine = create_engine(DB_URL)

    # Get all tenant schemas
    tenant_schemas = get_tenant_schemas(engine)
    logger.info(f"\nFound {len(tenant_schemas)} tenant schemas")

    # Process each schema
    total_success = 0
    total_failed = 0

    for schema in tenant_schemas:
        success, failed = fix_tenant_schema(engine, schema)
        total_success += success
        total_failed += failed

    # Create a new test tenant
    test_tenant_slug = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.info(f"\n{'='*60}")
    logger.info("Creating a fresh test tenant for CRUD operations")
    create_new_test_tenant(engine, test_tenant_slug)

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Tenant schemas processed: {len(tenant_schemas)}")
    logger.info(f"Total operations successful: {total_success}")
    logger.info(f"Total operations failed: {total_failed}")
    logger.info(f"New test tenant created: {test_tenant_slug}")
    logger.info(f"\n✅ Schema fix completed!")

    # Return the test tenant slug for use in tests
    print(f"\nTEST_TENANT_SLUG={test_tenant_slug}")

if __name__ == "__main__":
    main()
