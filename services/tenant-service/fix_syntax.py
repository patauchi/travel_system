# Fix syntax errors in main.py
with open('main.py', 'r') as f:
    content = f.read()

# Remove extra closing parentheses
content = content.replace('    )\n\n    )\n\n    # Create subscription history\n    )', '')

# Fix any double blank lines
import re
content = re.sub(r'\n\n\n+', '\n\n', content)

with open('main.py', 'w') as f:
    f.write(content)

print("Syntax fixed")
