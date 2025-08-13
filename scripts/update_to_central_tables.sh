#!/bin/bash

# Script to update all references from old table names to new central_ prefix tables
# This script updates all Python files to use the new table naming convention

echo "Starting migration to central_ table names..."

# Define the replacements
declare -A replacements=(
    ["shared.users"]="shared.central_users"
    ["shared.tenants"]="shared.central_tenants"
    ["shared.tenant_users"]="shared.central_tenant_users"
    ["shared.subscription_history"]="shared.central_subscription_history"
    ["shared.audit_logs"]="shared.central_audit_logs"
    ["shared.api_keys"]="shared.central_api_keys"
    ["shared.feature_flags"]="shared.central_feature_flags"
    ["shared.tenant_features"]="shared.central_tenant_features"
    ["shared.webhooks"]="shared.central_webhooks"
    ["shared.webhook_logs"]="shared.central_webhook_logs"
    ["shared.system_settings"]="shared.central_system_settings"
    ["'users'"]="'central_users'"
    ['"users"']='"central_users"'
    ["'tenants'"]="'central_tenants'"
    ['"tenants"']='"central_tenants"'
    ["'tenant_users'"]="'central_tenant_users'"
    ['"tenant_users"']='"central_tenant_users"'
    ["'subscription_history'"]="'central_subscription_history'"
    ['"subscription_history"']='"central_subscription_history"'
    ["'audit_logs'"]="'central_audit_logs'"
    ['"audit_logs"']='"central_audit_logs"'
    ["'api_keys'"]="'central_api_keys'"
    ['"api_keys"']='"central_api_keys"'
    ["'feature_flags'"]="'central_feature_flags'"
    ['"feature_flags"']='"central_feature_flags"'
    ["'tenant_features'"]="'central_tenant_features'"
    ['"tenant_features"']='"central_tenant_features"'
    ["'webhooks'"]="'central_webhooks'"
    ['"webhooks"']='"central_webhooks"'
    ["'webhook_logs'"]="'central_webhook_logs'"
    ['"webhook_logs"']='"central_webhook_logs"'
    ["'system_settings'"]="'central_system_settings'"
    ['"system_settings"']='"central_system_settings"'
)

# Find all Python files in the services directory
find ./services -name "*.py" -type f | while read -r file; do
    echo "Processing: $file"

    # Create a temporary file
    temp_file="${file}.tmp"
    cp "$file" "$temp_file"

    # Apply all replacements
    for old in "${!replacements[@]}"; do
        new="${replacements[$old]}"
        sed -i "s/${old}/${new}/g" "$temp_file" 2>/dev/null || sed -i '' "s/${old}/${new}/g" "$temp_file"
    done

    # Check if file changed
    if ! cmp -s "$file" "$temp_file"; then
        mv "$temp_file" "$file"
        echo "  ✓ Updated $file"
    else
        rm "$temp_file"
        echo "  - No changes needed in $file"
    fi
done

# Update script files
find ./scripts -name "*.py" -type f | while read -r file; do
    echo "Processing: $file"

    # Create a temporary file
    temp_file="${file}.tmp"
    cp "$file" "$temp_file"

    # Apply all replacements
    for old in "${!replacements[@]}"; do
        new="${replacements[$old]}"
        sed -i "s/${old}/${new}/g" "$temp_file" 2>/dev/null || sed -i '' "s/${old}/${new}/g" "$temp_file"
    done

    # Check if file changed
    if ! cmp -s "$file" "$temp_file"; then
        mv "$temp_file" "$file"
        echo "  ✓ Updated $file"
    else
        rm "$temp_file"
        echo "  - No changes needed in $file"
    fi
done

echo ""
echo "Migration complete!"
echo ""
echo "Next steps:"
echo "1. Restart all services to apply changes"
echo "2. The database will use the new table names on next initialization"
echo "3. Existing databases need to be recreated or migrated manually"
echo ""
echo "To recreate the database:"
echo "  docker-compose down"
echo "  docker volume rm travel_system_postgres_data"
echo "  docker-compose up -d"
