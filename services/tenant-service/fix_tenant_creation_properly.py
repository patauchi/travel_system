import re

# Read the file
with open('main.py', 'r') as f:
    content = f.read()

# Find the create_tenant function and fix it
pattern = r'(# Create tenant-user relationship.*?)(try:.*?# Schedule background tasks)'
replacement = r'''try:
        # Create database schema
        if not db_manager.create_tenant_schema(schema_name):
            raise Exception("Failed to create tenant schema")

        # Save tenant first
        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)
        
        # Save user
        db.add(owner_user)
        db.commit()
        db.refresh(owner_user)
        
        # Create tenant-user relationship
        tenant_user = TenantUser(
            id=str(uuid.uuid4()),
            tenant_id=new_tenant.id,
            user_id=owner_user.id,
            role="tenant_admin",
            is_owner=True,
            joined_at=datetime.utcnow()
        )
        db.add(tenant_user)
        
        # Create subscription history
        subscription_history = SubscriptionHistory(
            id=str(uuid.uuid4()),
            tenant_id=new_tenant.id,
            plan_to=tenant_data.subscription_plan.lower(),
            change_type="initial",
            changed_at=datetime.utcnow(),
            changed_by=owner_user.id
        )
        db.add(subscription_history)
        db.commit()

        # Schedule background tasks'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open('main.py', 'w') as f:
    f.write(new_content)

print("Fixed successfully")
