#!/usr/bin/env python3
"""
Generate bcrypt hash for password
"""

from passlib.context import CryptContext

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password to hash
password = "SuperAdmin123!"

# Generate hash
password_hash = pwd_context.hash(password)

print(f"Password: {password}")
print(f"Hash: {password_hash}")
print("")
print("SQL Command to update:")
print(f"UPDATE shared.central_users SET password_hash = '{password_hash}' WHERE username = 'admin';")
