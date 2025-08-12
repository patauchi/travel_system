# Fix TenantResponse to handle UUID
with open('main.py', 'r') as f:
    content = f.read()

# Find the return statement with TenantResponse and fix it
import re

# Replace the return statement
pattern = r'return TenantResponse\((.*?)\)'
def replace_func(match):
    args = match.group(1)
    # Add str() around new_tenant.id
    args = re.sub(r'id=new_tenant\.id', r'id=str(new_tenant.id)', args)
    return f'return TenantResponse({args})'

content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

with open('main.py', 'w') as f:
    f.write(content)

print("Fixed TenantResponse")
