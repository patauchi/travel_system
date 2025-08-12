# Remove enum usage from models
with open('models.py', 'r') as f:
    content = f.read()

# Replace SQLEnum with String
import re
content = re.sub(r'SQLEnum\([^)]+\)', 'String(50)', content)

with open('models.py', 'w') as f:
    f.write(content)

print("Enums replaced with String")
