# Restore UUID types in models
with open('models.py', 'r') as f:
    content = f.read()

# Add UUID import if not present
if 'from sqlalchemy.dialects.postgresql import' not in content:
    content = content.replace('from sqlalchemy.dialects.postgresql import INET, JSONB', 
                             'from sqlalchemy.dialects.postgresql import UUID, INET, JSONB')
else:
    content = content.replace('from sqlalchemy.dialects.postgresql import', 
                             'from sqlalchemy.dialects.postgresql import UUID,')

# Add uuid import if not present
if 'import uuid' not in content:
    content = 'import uuid\n' + content

# Replace String(36) back to UUID
import re
content = re.sub(r'Column\(String\(36\)\)', 'Column(UUID(as_uuid=True)', content)
# Add default uuid generation
content = re.sub(r'Column\(UUID\(as_uuid=True\), primary_key=True\)', 
                'Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)', content)

with open('models.py', 'w') as f:
    f.write(content)

print("UUID types restored")
