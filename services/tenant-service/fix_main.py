# Read the original file
with open('main.py', 'r') as f:
    lines = f.readlines()

# Find and replace the problematic section
new_lines = []
in_try_block = False
skip_until_background = False

for i, line in enumerate(lines):
    if 'try:' in line and '# Create database schema' in ''.join(lines[i:i+2]):
        in_try_block = True
        # Write the corrected version
        new_lines.append('    try:\n')
        new_lines.append('        # Create database schema\n')
        new_lines.append('        if not db_manager.create_tenant_schema(schema_name):\n')
        new_lines.append('            raise Exception("Failed to create tenant schema")\n')
        new_lines.append('\n')
        new_lines.append('        # First save the tenant\n')
        new_lines.append('        db.add(new_tenant)\n')
        new_lines.append('        db.commit()\n')
        new_lines.append('        db.refresh(new_tenant)\n')
        new_lines.append('\n')
        new_lines.append('        # Then save the user\n')
        new_lines.append('        db.add(owner_user)\n')
        new_lines.append('        db.commit()\n')
        new_lines.append('        db.refresh(owner_user)\n')
        new_lines.append('\n')
        new_lines.append('        # Then create the tenant-user relationship\n')
        new_lines.append('        tenant_user = TenantUser(\n')
        new_lines.append('            id=str(uuid.uuid4()),\n')
        new_lines.append('            tenant_id=new_tenant.id,\n')
        new_lines.append('            user_id=owner_user.id,\n')
        new_lines.append('            role="tenant_admin",\n')
        new_lines.append('            is_owner=True,\n')
        new_lines.append('            joined_at=datetime.utcnow()\n')
        new_lines.append('        )\n')
        new_lines.append('        db.add(tenant_user)\n')
        new_lines.append('        db.commit()\n')
        new_lines.append('\n')
        new_lines.append('        # Create subscription history\n')
        new_lines.append('        subscription_history = SubscriptionHistory(\n')
        new_lines.append('            id=str(uuid.uuid4()),\n')
        new_lines.append('            tenant_id=new_tenant.id,\n')
        new_lines.append('            plan_to=tenant_data.subscription_plan.lower(),\n')
        new_lines.append('            change_type="initial",\n')
        new_lines.append('            changed_at=datetime.utcnow(),\n')
        new_lines.append('            changed_by=owner_user.id\n')
        new_lines.append('        )\n')
        new_lines.append('        db.add(subscription_history)\n')
        new_lines.append('        db.commit()\n')
        new_lines.append('\n')
        skip_until_background = True
    elif skip_until_background and '# Schedule background tasks' in line:
        skip_until_background = False
        new_lines.append(line)
    elif not skip_until_background:
        new_lines.append(line)

# Write the fixed file
with open('main.py', 'w') as f:
    f.writelines(new_lines)
    
print("main.py has been fixed")
