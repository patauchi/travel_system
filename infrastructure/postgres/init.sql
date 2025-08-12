-- Multi-tenant PostgreSQL Initialization Script
-- This script sets up the initial database structure for multi-tenant architecture

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA public;

-- Create public schema if not exists
CREATE SCHEMA IF NOT EXISTS public;

-- Create shared schema for global data
CREATE SCHEMA IF NOT EXISTS shared;

-- Set search path
SET search_path TO public, shared;

-- Create enum types
CREATE TYPE user_role AS ENUM ('super_admin', 'tenant_admin', 'tenant_user', 'tenant_viewer');
CREATE TYPE tenant_status AS ENUM ('active', 'suspended', 'trial', 'expired', 'pending');
CREATE TYPE subscription_plan AS ENUM ('free', 'starter', 'professional', 'enterprise');

-- Table: tenants (in shared schema)
CREATE TABLE IF NOT EXISTS shared.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    subdomain VARCHAR(100) UNIQUE,
    schema_name VARCHAR(63) UNIQUE NOT NULL,
    status tenant_status DEFAULT 'pending',
    subscription_plan subscription_plan DEFAULT 'free',
    max_users INTEGER DEFAULT 5,
    max_storage_gb INTEGER DEFAULT 10,
    settings JSONB DEFAULT '{}',
    tenant_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    suspended_at TIMESTAMP WITH TIME ZONE,
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    subscription_ends_at TIMESTAMP WITH TIME ZONE
);

-- Table: users (in shared schema - global users)
CREATE TABLE IF NOT EXISTS shared.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: tenant_users (user-tenant relationship)
CREATE TABLE IF NOT EXISTS shared.tenant_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES shared.users(id) ON DELETE CASCADE,
    role user_role DEFAULT 'tenant_user',
    is_owner BOOLEAN DEFAULT false,
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    invited_by UUID REFERENCES shared.users(id),
    invitation_token VARCHAR(255),
    invitation_accepted_at TIMESTAMP WITH TIME ZONE,
    last_active_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, user_id)
);

-- Table: api_keys (for tenant API access)
CREATE TABLE IF NOT EXISTS shared.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    scopes JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 1000,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES shared.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, name)
);

-- Table: audit_logs (system-wide audit)
CREATE TABLE IF NOT EXISTS shared.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES shared.tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES shared.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: feature_flags
CREATE TABLE IF NOT EXISTS shared.feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    tenant_overrides JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: tenant_features (feature flags per tenant)
CREATE TABLE IF NOT EXISTS shared.tenant_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    feature_id UUID NOT NULL REFERENCES shared.feature_flags(id) ON DELETE CASCADE,
    is_enabled BOOLEAN NOT NULL,
    configuration JSONB DEFAULT '{}',
    enabled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    enabled_by UUID REFERENCES shared.users(id),
    UNIQUE(tenant_id, feature_id)
);

-- Table: subscription_history
CREATE TABLE IF NOT EXISTS shared.subscription_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    plan_from subscription_plan,
    plan_to subscription_plan NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- upgrade, downgrade, renewal, cancellation
    price_paid DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID REFERENCES shared.users(id),
    notes TEXT
);

-- Table: webhooks
CREATE TABLE IF NOT EXISTS shared.webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    events JSONB NOT NULL DEFAULT '[]',
    headers JSONB DEFAULT '{}',
    secret VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, name)
);

-- Table: webhook_logs
CREATE TABLE IF NOT EXISTS shared.webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES shared.webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    response_status INTEGER,
    response_body TEXT,
    attempts INTEGER DEFAULT 1,
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table: system_settings
CREATE TABLE IF NOT EXISTS shared.system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES shared.users(id)
);

-- Indexes for performance
CREATE INDEX idx_tenants_slug ON shared.tenants(slug);
CREATE INDEX idx_tenants_subdomain ON shared.tenants(subdomain);
CREATE INDEX idx_tenants_status ON shared.tenants(status);
CREATE INDEX idx_users_email ON shared.users(email);
CREATE INDEX idx_users_username ON shared.users(username);
CREATE INDEX idx_tenant_users_tenant_id ON shared.tenant_users(tenant_id);
CREATE INDEX idx_tenant_users_user_id ON shared.tenant_users(user_id);
CREATE INDEX idx_api_keys_tenant_id ON shared.api_keys(tenant_id);
CREATE INDEX idx_api_keys_key_prefix ON shared.api_keys(key_prefix);
CREATE INDEX idx_audit_logs_tenant_id ON shared.audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user_id ON shared.audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON shared.audit_logs(created_at);
CREATE INDEX idx_webhook_logs_webhook_id ON shared.webhook_logs(webhook_id);
CREATE INDEX idx_webhook_logs_created_at ON shared.webhook_logs(created_at);

-- Create template schema for tenants
CREATE SCHEMA IF NOT EXISTS tenant_template;

-- Switch to template schema
SET search_path TO tenant_template, public;

-- Template tables for each tenant schema
CREATE TABLE IF NOT EXISTS tenant_template.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    preferences JSONB DEFAULT '{}',
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_template.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    owner_id UUID NOT NULL,
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS tenant_template.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES tenant_template.projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    content_type VARCHAR(100),
    file_path TEXT,
    file_size BIGINT,
    version INTEGER DEFAULT 1,
    created_by UUID NOT NULL,
    updated_by UUID,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_template.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES tenant_template.projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    assignee_id UUID,
    due_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_template.comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID NOT NULL,
    parent_id UUID REFERENCES tenant_template.comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author_id UUID NOT NULL,
    edited_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_template.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    data JSONB DEFAULT '{}',
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_template.activity_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    changes JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for template schema
CREATE INDEX idx_profiles_user_id ON tenant_template.profiles(user_id);
CREATE INDEX idx_projects_owner_id ON tenant_template.projects(owner_id);
CREATE INDEX idx_documents_project_id ON tenant_template.documents(project_id);
CREATE INDEX idx_tasks_project_id ON tenant_template.tasks(project_id);
CREATE INDEX idx_tasks_assignee_id ON tenant_template.tasks(assignee_id);
CREATE INDEX idx_comments_resource ON tenant_template.comments(resource_type, resource_id);
CREATE INDEX idx_notifications_user_id ON tenant_template.notifications(user_id);
CREATE INDEX idx_notifications_is_read ON tenant_template.notifications(is_read);
CREATE INDEX idx_activity_log_user_id ON tenant_template.activity_log(user_id);
CREATE INDEX idx_activity_log_created_at ON tenant_template.activity_log(created_at);

-- Reset search path
SET search_path TO public;

-- Function to create a new tenant schema
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_schema_name VARCHAR)
RETURNS VOID AS $$
DECLARE
    sql_statement TEXT;
BEGIN
    -- Create the new schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_schema_name);

    -- Copy all tables from tenant_template to the new schema
    FOR sql_statement IN
        SELECT format('CREATE TABLE %I.%I (LIKE tenant_template.%I INCLUDING ALL)',
                     tenant_schema_name, table_name, table_name)
        FROM information_schema.tables
        WHERE table_schema = 'tenant_template'
        AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE sql_statement;
    END LOOP;

    -- Copy all indexes
    FOR sql_statement IN
        SELECT replace(replace(indexdef, 'tenant_template.', tenant_schema_name || '.'),
                      'ON tenant_template.', 'ON ' || tenant_schema_name || '.')
        FROM pg_indexes
        WHERE schemaname = 'tenant_template'
        AND indexname NOT LIKE '%_pkey'  -- Skip primary key indexes as they're created with INCLUDING ALL
    LOOP
        BEGIN
            EXECUTE sql_statement;
        EXCEPTION WHEN duplicate_table THEN
            -- Index already exists, skip
            NULL;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to drop a tenant schema
CREATE OR REPLACE FUNCTION drop_tenant_schema(tenant_schema_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('DROP SCHEMA IF EXISTS %I CASCADE', tenant_schema_name);
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at column
DO $$
DECLARE
    t record;
BEGIN
    FOR t IN
        SELECT table_schema, table_name
        FROM information_schema.columns
        WHERE column_name = 'updated_at'
        AND table_schema IN ('shared', 'tenant_template')
    LOOP
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I.%I
                       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
                       t.table_name, t.table_schema, t.table_name);
    END LOOP;
END;
$$;

-- Insert default system settings
INSERT INTO shared.system_settings (key, value, description, is_public) VALUES
    ('default_tenant_plan', '"free"', 'Default subscription plan for new tenants', false),
    ('trial_days', '14', 'Number of days for trial period', false),
    ('max_login_attempts', '5', 'Maximum failed login attempts before account lock', false),
    ('lock_duration_minutes', '30', 'Account lock duration in minutes', false),
    ('password_min_length', '8', 'Minimum password length', true),
    ('session_timeout_minutes', '60', 'Session timeout in minutes', false),
    ('enable_two_factor', 'false', 'Enable two-factor authentication', true),
    ('maintenance_mode', 'false', 'System maintenance mode', true);

-- Insert default feature flags
INSERT INTO shared.feature_flags (name, description, is_enabled, rollout_percentage) VALUES
    ('dark_mode', 'Enable dark mode UI', true, 100),
    ('advanced_analytics', 'Advanced analytics dashboard', false, 0),
    ('api_v2', 'New API version 2', false, 10),
    ('bulk_operations', 'Enable bulk operations', true, 100),
    ('export_data', 'Allow data export', true, 100),
    ('webhooks', 'Enable webhook integrations', false, 50),
    ('custom_branding', 'Allow custom branding', false, 0),
    ('sso_integration', 'Single Sign-On integration', false, 0);

-- Create initial super admin user (password: Admin123!)
INSERT INTO shared.users (email, username, password_hash, first_name, last_name, is_active, is_verified, email_verified_at)
VALUES (
    'admin@multitenant.com',
    'superadmin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5L2oLYFsT4JQe', -- bcrypt hash of 'Admin123!'
    'Super',
    'Admin',
    true,
    true,
    CURRENT_TIMESTAMP
);

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON SCHEMA tenant_template TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant_template TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA tenant_template TO postgres;
