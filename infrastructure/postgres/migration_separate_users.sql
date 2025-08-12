-- Migration: Separate System Users from Tenant Users
-- This migration restructures the user system to properly separate platform-level users from tenant-level users
-- Date: December 2024

-- ============================================
-- STEP 1: MODIFY SYSTEM-LEVEL STRUCTURES
-- ============================================

-- Drop the old user_role enum if exists
ALTER TYPE IF EXISTS user_role RENAME TO user_role_old;

-- Create new system role enum (only for platform management)
CREATE TYPE system_role AS ENUM ('super_admin', 'tenant_admin');

-- Rename the existing users table to system_users
ALTER TABLE IF EXISTS shared.users RENAME TO system_users;

-- Update system_users table structure
ALTER TABLE shared.system_users
    ADD COLUMN IF NOT EXISTS system_role system_role DEFAULT 'tenant_admin',
    ADD COLUMN IF NOT EXISTS is_platform_user BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS managed_tenants JSONB DEFAULT '[]';

-- Update tenant_users to reference system_users
ALTER TABLE shared.tenant_users
    DROP CONSTRAINT IF EXISTS tenant_users_user_id_fkey;

ALTER TABLE shared.tenant_users
    ADD CONSTRAINT tenant_users_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES shared.system_users(id) ON DELETE CASCADE;

-- Remove tenant_user and tenant_viewer from tenant_users as they shouldn't be here
DELETE FROM shared.tenant_users
WHERE role IN ('tenant_user', 'tenant_viewer');

-- Update tenant_users to only have tenant_admin role
ALTER TABLE shared.tenant_users
    DROP COLUMN IF EXISTS role CASCADE;

ALTER TABLE shared.tenant_users
    ADD COLUMN is_primary_admin BOOLEAN DEFAULT false;

-- ============================================
-- STEP 2: CREATE TENANT-LEVEL USER STRUCTURE
-- ============================================

-- Add to tenant_template schema for each tenant
SET search_path TO tenant_template, public;

-- Create roles table for each tenant
CREATE TABLE IF NOT EXISTS tenant_template.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    permissions JSONB DEFAULT '{}',
    is_system BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create tenant users table
CREATE TABLE IF NOT EXISTS tenant_template.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    avatar_url TEXT,
    department VARCHAR(100),
    job_title VARCHAR(100),
    employee_id VARCHAR(50),
    role_id UUID REFERENCES tenant_template.roles(id),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create permissions table
CREATE TABLE IF NOT EXISTS tenant_template.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create role_permissions junction table
CREATE TABLE IF NOT EXISTS tenant_template.role_permissions (
    role_id UUID REFERENCES tenant_template.roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES tenant_template.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID,
    PRIMARY KEY (role_id, permission_id)
);

-- Create user_permissions for override permissions
CREATE TABLE IF NOT EXISTS tenant_template.user_permissions (
    user_id UUID REFERENCES tenant_template.users(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES tenant_template.permissions(id) ON DELETE CASCADE,
    is_granted BOOLEAN DEFAULT true, -- Can be used to explicitly deny
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID,
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, permission_id)
);

-- Create teams/groups table
CREATE TABLE IF NOT EXISTS tenant_template.teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_team_id UUID REFERENCES tenant_template.teams(id),
    manager_id UUID REFERENCES tenant_template.users(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create team_members junction table
CREATE TABLE IF NOT EXISTS tenant_template.team_members (
    team_id UUID REFERENCES tenant_template.teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES tenant_template.users(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, user_id)
);

-- Create sessions table for tenant users
CREATE TABLE IF NOT EXISTS tenant_template.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES tenant_template.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create password reset tokens table
CREATE TABLE IF NOT EXISTS tenant_template.password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES tenant_template.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_tenant_users_email ON tenant_template.users(email);
CREATE INDEX idx_tenant_users_username ON tenant_template.users(username);
CREATE INDEX idx_tenant_users_role_id ON tenant_template.users(role_id);
CREATE INDEX idx_tenant_users_is_active ON tenant_template.users(is_active);
CREATE INDEX idx_role_permissions_role_id ON tenant_template.role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission_id ON tenant_template.role_permissions(permission_id);
CREATE INDEX idx_user_permissions_user_id ON tenant_template.user_permissions(user_id);
CREATE INDEX idx_team_members_team_id ON tenant_template.team_members(team_id);
CREATE INDEX idx_team_members_user_id ON tenant_template.team_members(user_id);
CREATE INDEX idx_user_sessions_user_id ON tenant_template.user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON tenant_template.user_sessions(expires_at);

-- ============================================
-- STEP 3: INSERT DEFAULT TENANT ROLES
-- ============================================

-- Function to initialize default roles for a tenant
CREATE OR REPLACE FUNCTION initialize_tenant_roles(tenant_schema VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- Create default roles
    EXECUTE format('
        INSERT INTO %I.roles (name, display_name, description, is_system) VALUES
        (''admin'', ''Administrator'', ''Full access to all tenant resources'', true),
        (''manager'', ''Manager'', ''Can manage users and most resources'', true),
        (''user'', ''User'', ''Standard user with normal access'', true),
        (''viewer'', ''Viewer'', ''Read-only access to resources'', true),
        (''guest'', ''Guest'', ''Limited temporary access'', true)
    ', tenant_schema);

    -- Create default permissions
    EXECUTE format('
        INSERT INTO %I.permissions (name, resource, action, description) VALUES
        -- User management
        (''users.create'', ''users'', ''create'', ''Create new users''),
        (''users.read'', ''users'', ''read'', ''View user information''),
        (''users.update'', ''users'', ''update'', ''Update user information''),
        (''users.delete'', ''users'', ''delete'', ''Delete users''),

        -- Project management
        (''projects.create'', ''projects'', ''create'', ''Create new projects''),
        (''projects.read'', ''projects'', ''read'', ''View projects''),
        (''projects.update'', ''projects'', ''update'', ''Update projects''),
        (''projects.delete'', ''projects'', ''delete'', ''Delete projects''),

        -- Document management
        (''documents.create'', ''documents'', ''create'', ''Create documents''),
        (''documents.read'', ''documents'', ''read'', ''View documents''),
        (''documents.update'', ''documents'', ''update'', ''Update documents''),
        (''documents.delete'', ''documents'', ''delete'', ''Delete documents''),

        -- Settings management
        (''settings.read'', ''settings'', ''read'', ''View settings''),
        (''settings.update'', ''settings'', ''update'', ''Modify settings''),

        -- Reports
        (''reports.view'', ''reports'', ''read'', ''View reports''),
        (''reports.export'', ''reports'', ''export'', ''Export reports'')
    ', tenant_schema);

    -- Assign permissions to roles
    EXECUTE format('
        -- Admin role gets all permissions
        INSERT INTO %I.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM %I.roles r
        CROSS JOIN %I.permissions p
        WHERE r.name = ''admin'';

        -- Manager role gets most permissions except user deletion
        INSERT INTO %I.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM %I.roles r
        CROSS JOIN %I.permissions p
        WHERE r.name = ''manager''
        AND p.name NOT IN (''users.delete'', ''settings.update'');

        -- User role gets standard permissions
        INSERT INTO %I.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM %I.roles r
        CROSS JOIN %I.permissions p
        WHERE r.name = ''user''
        AND p.action IN (''read'', ''create'', ''update'')
        AND p.resource NOT IN (''users'', ''settings'');

        -- Viewer role gets only read permissions
        INSERT INTO %I.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM %I.roles r
        CROSS JOIN %I.permissions p
        WHERE r.name = ''viewer''
        AND p.action = ''read'';

        -- Guest role gets minimal permissions
        INSERT INTO %I.role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM %I.roles r
        CROSS JOIN %I.permissions p
        WHERE r.name = ''guest''
        AND p.name IN (''projects.read'', ''documents.read'');
    ', tenant_schema, tenant_schema, tenant_schema,
       tenant_schema, tenant_schema, tenant_schema,
       tenant_schema, tenant_schema, tenant_schema,
       tenant_schema, tenant_schema, tenant_schema,
       tenant_schema, tenant_schema, tenant_schema);
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 4: UPDATE EXISTING TENANT SCHEMAS
-- ============================================

-- Function to migrate existing tenant schemas
CREATE OR REPLACE FUNCTION migrate_existing_tenant_schemas()
RETURNS VOID AS $$
DECLARE
    tenant_schema_name TEXT;
BEGIN
    -- Loop through all existing tenant schemas
    FOR tenant_schema_name IN
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name LIKE 'tenant_%'
        AND schema_name != 'tenant_template'
    LOOP
        -- Copy new table structures from template
        PERFORM create_tables_from_template(tenant_schema_name);

        -- Initialize default roles and permissions
        PERFORM initialize_tenant_roles(tenant_schema_name);

        RAISE NOTICE 'Migrated schema: %', tenant_schema_name;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to create tables from template
CREATE OR REPLACE FUNCTION create_tables_from_template(target_schema VARCHAR)
RETURNS VOID AS $$
DECLARE
    sql_statement TEXT;
BEGIN
    -- Create tables that don't exist in the target schema
    FOR sql_statement IN
        SELECT format('CREATE TABLE IF NOT EXISTS %I.%I (LIKE tenant_template.%I INCLUDING ALL)',
                     target_schema, table_name, table_name)
        FROM information_schema.tables
        WHERE table_schema = 'tenant_template'
        AND table_type = 'BASE TABLE'
        AND table_name IN ('users', 'roles', 'permissions', 'role_permissions',
                           'user_permissions', 'teams', 'team_members',
                           'user_sessions', 'password_reset_tokens')
    LOOP
        EXECUTE sql_statement;
    END LOOP;

    -- Create indexes
    FOR sql_statement IN
        SELECT replace(replace(indexdef, 'tenant_template.', target_schema || '.'),
                      'ON tenant_template.', 'ON ' || target_schema || '.')
        FROM pg_indexes
        WHERE schemaname = 'tenant_template'
        AND tablename IN ('users', 'roles', 'permissions', 'role_permissions',
                         'user_permissions', 'teams', 'team_members',
                         'user_sessions', 'password_reset_tokens')
        AND indexname NOT LIKE '%_pkey'
    LOOP
        BEGIN
            EXECUTE sql_statement;
        EXCEPTION WHEN duplicate_table THEN
            NULL; -- Index already exists
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 5: UPDATE AUDIT TABLES
-- ============================================

-- Add column to distinguish between system and tenant actions
ALTER TABLE shared.audit_logs
    ADD COLUMN IF NOT EXISTS context VARCHAR(20) DEFAULT 'system',
    ADD COLUMN IF NOT EXISTS tenant_user_id UUID;

-- Update existing audit logs
UPDATE shared.audit_logs
SET context = 'system'
WHERE tenant_id IS NULL;

UPDATE shared.audit_logs
SET context = 'tenant'
WHERE tenant_id IS NOT NULL;

-- ============================================
-- STEP 6: CREATE HELPER FUNCTIONS
-- ============================================

-- Function to check if a user has a specific permission in a tenant
CREATE OR REPLACE FUNCTION check_tenant_user_permission(
    p_tenant_schema VARCHAR,
    p_user_id UUID,
    p_permission_name VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    has_permission BOOLEAN;
BEGIN
    EXECUTE format('
        SELECT EXISTS (
            SELECT 1
            FROM %I.users u
            LEFT JOIN %I.role_permissions rp ON u.role_id = rp.role_id
            LEFT JOIN %I.permissions p ON rp.permission_id = p.id
            LEFT JOIN %I.user_permissions up ON u.id = up.user_id AND up.permission_id = p.id
            WHERE u.id = $1
            AND (
                p.name = $2
                OR (up.permission_id IS NOT NULL AND up.is_granted = true AND p.name = $2)
            )
            AND u.is_active = true
        )', p_tenant_schema, p_tenant_schema, p_tenant_schema, p_tenant_schema)
    INTO has_permission
    USING p_user_id, p_permission_name;

    RETURN COALESCE(has_permission, false);
END;
$$ LANGUAGE plpgsql;

-- Function to create a tenant user
CREATE OR REPLACE FUNCTION create_tenant_user(
    p_tenant_schema VARCHAR,
    p_email VARCHAR,
    p_username VARCHAR,
    p_password_hash VARCHAR,
    p_first_name VARCHAR,
    p_last_name VARCHAR,
    p_role_name VARCHAR DEFAULT 'user'
) RETURNS UUID AS $$
DECLARE
    new_user_id UUID;
    role_id UUID;
BEGIN
    -- Get role ID
    EXECUTE format('SELECT id FROM %I.roles WHERE name = $1', p_tenant_schema)
    INTO role_id
    USING p_role_name;

    -- Insert new user
    EXECUTE format('
        INSERT INTO %I.users (email, username, password_hash, first_name, last_name, role_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
    ', p_tenant_schema)
    INTO new_user_id
    USING p_email, p_username, p_password_hash, p_first_name, p_last_name, role_id;

    RETURN new_user_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- STEP 7: RUN MIGRATION
-- ============================================

-- Execute migration for existing tenants
SELECT migrate_existing_tenant_schemas();

-- Update existing system users
UPDATE shared.system_users
SET system_role = 'super_admin'
WHERE username = 'superadmin' OR email LIKE '%admin@%';

UPDATE shared.system_users
SET system_role = 'tenant_admin'
WHERE username != 'superadmin' AND email NOT LIKE '%admin@%';

-- Clean up old enum type
DROP TYPE IF EXISTS user_role_old CASCADE;

-- ============================================
-- STEP 8: CREATE VIEWS FOR EASIER ACCESS
-- ============================================

-- Create view for system admins to see all tenant users
CREATE OR REPLACE VIEW shared.all_tenant_users AS
SELECT
    t.id as tenant_id,
    t.name as tenant_name,
    t.slug as tenant_slug,
    'tenant_user' as user_type,
    null as system_user_id,
    tu.id as tenant_user_id,
    tu.email,
    tu.username,
    tu.first_name,
    tu.last_name,
    r.name as role_name,
    tu.is_active,
    tu.last_login_at,
    tu.created_at
FROM shared.tenants t
CROSS JOIN LATERAL (
    SELECT * FROM dblink(
        'dbname=' || current_database(),
        format('SELECT id, email, username, first_name, last_name, role_id, is_active, last_login_at, created_at FROM %I.users', t.schema_name)
    ) AS users(
        id UUID,
        email VARCHAR,
        username VARCHAR,
        first_name VARCHAR,
        last_name VARCHAR,
        role_id UUID,
        is_active BOOLEAN,
        last_login_at TIMESTAMP,
        created_at TIMESTAMP
    )
) tu
LEFT JOIN LATERAL (
    SELECT * FROM dblink(
        'dbname=' || current_database(),
        format('SELECT id, name FROM %I.roles WHERE id = ''%s''', t.schema_name, tu.role_id)
    ) AS roles(id UUID, name VARCHAR)
) r ON true;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA shared TO postgres;
GRANT SELECT ON shared.all_tenant_users TO postgres;

-- ============================================
-- MIGRATION COMPLETE
-- ============================================

-- Display migration summary
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Changes made:';
    RAISE NOTICE '1. Renamed shared.users to shared.system_users';
    RAISE NOTICE '2. Added system_role to system_users (super_admin, tenant_admin only)';
    RAISE NOTICE '3. Created tenant-specific user tables in tenant_template';
    RAISE NOTICE '4. Added roles and permissions system for each tenant';
    RAISE NOTICE '5. Migrated existing tenant schemas';
    RAISE NOTICE '========================================';
END;
$$;
