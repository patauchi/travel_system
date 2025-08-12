# Simplify models to use String IDs instead of UUID
import re

# Read models.py
with open('models.py', 'r') as f:
    content = f.read()

# Replace UUID columns with String columns
content = re.sub(r'Column\(UUID\(as_uuid=True\)', 'Column(String(36)', content)
content = re.sub(r', default=uuid\.uuid4', '', content)
content = re.sub(r'from sqlalchemy\.dialects\.postgresql import UUID,', 'from sqlalchemy.dialects.postgresql import', content)
content = re.sub(r'import uuid\n', '', content)

# Write back
with open('models.py', 'w') as f:
    f.write(content)

print("Models simplified to use String IDs")

# Now fix main.py to always use str(uuid.uuid4())
with open('main.py', 'r') as f:
    content = f.read()

# Ensure all id assignments use str(uuid.uuid4())
content = re.sub(r'id=uuid\.uuid4\(\)', 'id=str(uuid.uuid4())', content)
content = re.sub(r'id=str\(str\(uuid\.uuid4\(\)\)\)', 'id=str(uuid.uuid4())', content)

# Fix TenantResponse to not need str() conversion
content = re.sub(r'id=str\(new_tenant\.id\)', 'id=new_tenant.id', content)
content = re.sub(r'id=str\(tenant\.id\)', 'id=tenant.id', content)

with open('main.py', 'w') as f:
    f.write(content)

print("Main.py updated to use string IDs")
