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

-- Create enum types (only two roles)
CREATE TYPE user_role AS ENUM ('super_admin', 'tenant_admin');
CREATE TYPE tenant_status AS ENUM ('active', 'suspended', 'trial', 'expired', 'pending');
CREATE TYPE subscription_plan AS ENUM ('free', 'starter', 'professional', 'enterprise');

-- Table: central_tenants (in shared schema)
CREATE TABLE IF NOT EXISTS shared.central_tenants (
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

-- Table: central_users (in shared schema - global users)
CREATE TABLE IF NOT EXISTS shared.central_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    role user_role DEFAULT 'tenant_admin',
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

-- Table: central_tenant_users (user-tenant relationship)
CREATE TABLE IF NOT EXISTS shared.central_tenant_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.central_tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES shared.central_users(id) ON DELETE CASCADE,
    role user_role DEFAULT 'tenant_admin',
    is_owner BOOLEAN DEFAULT false,
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    invited_by UUID REFERENCES shared.central_users(id),
    invitation_token VARCHAR(255),
    invitation_accepted_at TIMESTAMP WITH TIME ZONE,
    last_active_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, user_id)
);

-- Table: central_api_keys (for tenant API access)
CREATE TABLE IF NOT EXISTS shared.central_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.central_tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    scopes JSONB DEFAULT '[]',
    rate_limit INTEGER DEFAULT 1000,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES shared.central_users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(tenant_id, name)
);

-- Table: central_audit_logs (system-wide audit)
CREATE TABLE IF NOT EXISTS shared.central_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES shared.central_tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES shared.central_users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: central_feature_flags
CREATE TABLE IF NOT EXISTS shared.central_feature_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_enabled BOOLEAN DEFAULT false,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    tenant_overrides JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table: central_tenant_features (feature flags per tenant)
CREATE TABLE IF NOT EXISTS shared.central_tenant_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.central_tenants(id) ON DELETE CASCADE,
    feature_id UUID NOT NULL REFERENCES shared.central_feature_flags(id) ON DELETE CASCADE,
    is_enabled BOOLEAN NOT NULL,
    configuration JSONB DEFAULT '{}',
    enabled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    enabled_by UUID REFERENCES shared.central_users(id),
    UNIQUE(tenant_id, feature_id)
);

-- Table: central_subscription_history
CREATE TABLE IF NOT EXISTS shared.central_subscription_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.central_tenants(id) ON DELETE CASCADE,
    plan_from subscription_plan,
    plan_to subscription_plan NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- upgrade, downgrade, renewal, cancellation
    price_paid DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by UUID REFERENCES shared.central_users(id),
    notes TEXT
);

-- Table: central_webhooks
CREATE TABLE IF NOT EXISTS shared.central_webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES shared.central_tenants(id) ON DELETE CASCADE,
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

-- Table: central_webhook_logs
CREATE TABLE IF NOT EXISTS shared.central_webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES shared.central_webhooks(id) ON DELETE CASCADE,
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

-- Table: central_system_settings
CREATE TABLE IF NOT EXISTS shared.central_system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES shared.central_users(id)
);

-- Indexes for performance
CREATE INDEX idx_central_tenants_slug ON shared.central_tenants(slug);
CREATE INDEX idx_central_tenants_subdomain ON shared.central_tenants(subdomain);
CREATE INDEX idx_central_tenants_status ON shared.central_tenants(status);
CREATE INDEX idx_central_users_email ON shared.central_users(email);
CREATE INDEX idx_central_users_username ON shared.central_users(username);
CREATE INDEX idx_central_users_role ON shared.central_users(role);
CREATE INDEX idx_central_tenant_users_tenant_id ON shared.central_tenant_users(tenant_id);
CREATE INDEX idx_central_tenant_users_user_id ON shared.central_tenant_users(user_id);
CREATE INDEX idx_central_api_keys_tenant_id ON shared.central_api_keys(tenant_id);
CREATE INDEX idx_central_api_keys_key_prefix ON shared.central_api_keys(key_prefix);
CREATE INDEX idx_central_audit_logs_tenant_id ON shared.central_audit_logs(tenant_id);
CREATE INDEX idx_central_audit_logs_user_id ON shared.central_audit_logs(user_id);
CREATE INDEX idx_central_audit_logs_created_at ON shared.central_audit_logs(created_at);
CREATE INDEX idx_central_webhook_logs_webhook_id ON shared.central_webhook_logs(webhook_id);
CREATE INDEX idx_central_webhook_logs_created_at ON shared.central_webhook_logs(created_at);

-- Function to create a new tenant schema
CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_schema_name VARCHAR)
RETURNS VOID AS $$
BEGIN
    -- Create the new schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', tenant_schema_name);

    -- Set search path to the new schema
    EXECUTE format('SET search_path TO %I', tenant_schema_name);

    -- Create basic audit_log table for the tenant
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I.audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(50),
        resource_id UUID,
        changes JSONB DEFAULT %L,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )', tenant_schema_name, '{}');

    -- Create index for audit_log
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_audit_log_user_id ON %I.audit_log(user_id)',
                   replace(tenant_schema_name, '-', '_'), tenant_schema_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_audit_log_created_at ON %I.audit_log(created_at)',
                   replace(tenant_schema_name, '-', '_'), tenant_schema_name);

    -- Reset search path
    SET search_path TO public;
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
        AND table_schema = 'shared'
        AND table_name LIKE 'central_%'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS update_%I_updated_at ON %I.%I',
                       t.table_name, t.table_schema, t.table_name);
        EXECUTE format('CREATE TRIGGER update_%I_updated_at BEFORE UPDATE ON %I.%I
                       FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()',
                       t.table_name, t.table_schema, t.table_name);
    END LOOP;
END;
$$;

-- Insert default system settings
INSERT INTO shared.central_system_settings (key, value, description, is_public) VALUES
    ('default_tenant_plan', '"free"', 'Default subscription plan for new tenants', false),
    ('trial_days', '14', 'Number of days for trial period', false),
    ('max_login_attempts', '5', 'Maximum failed login attempts before account lock', false),
    ('lock_duration_minutes', '30', 'Account lock duration in minutes', false),
    ('password_min_length', '8', 'Minimum password length', true),
    ('session_timeout_minutes', '60', 'Session timeout in minutes', false),
    ('enable_two_factor', 'false', 'Enable two-factor authentication', true),
    ('maintenance_mode', 'false', 'System maintenance mode', true)
ON CONFLICT (key) DO NOTHING;

-- Insert default feature flags
INSERT INTO shared.central_feature_flags (name, description, is_enabled, rollout_percentage) VALUES
    ('dark_mode', 'Enable dark mode UI', true, 100),
    ('advanced_analytics', 'Advanced analytics dashboard', false, 0),
    ('api_v2', 'New API version 2', false, 10),
    ('bulk_operations', 'Enable bulk operations', true, 100),
    ('export_data', 'Allow data export', true, 100),
    ('webhooks', 'Enable webhook integrations', false, 50),
    ('custom_branding', 'Allow custom branding', false, 0),
    ('sso_integration', 'Single Sign-On integration', false, 0)
ON CONFLICT (name) DO NOTHING;

-- Create initial super admin user (password: SuperAdmin123!)
-- This will be replaced by environment variables in production
INSERT INTO shared.central_users (
    id,
    email,
    username,
    password_hash,
    first_name,
    last_name,
    role,
    is_active,
    is_verified,
    email_verified_at
)
VALUES (
    uuid_generate_v4(),
    'admin@system.local',
    'superadmin',
    '$2b$12$K8Z.3V.KNWsJZH0GDTJmNeFKpWVGBXiXHGJK6YqLqY8hSYxKxGJNy', -- bcrypt hash of 'SuperAdmin123!'
    'System',
    'Administrator',
    'super_admin',
    true,
    true,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA shared TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA shared TO postgres;
