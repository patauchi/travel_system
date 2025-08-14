"""
Simplified shared authentication utilities for system-service
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import base64
import json
import hashlib

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Security scheme
security = HTTPBearer(auto_error=False)

def create_simple_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a simple base64-encoded token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = {
        **data,
        "exp": expire.timestamp(),
        "type": "access"
    }

    # Simple encoding (not secure for production)
    token_string = json.dumps(token_data)
    token_bytes = token_string.encode('utf-8')
    encoded_token = base64.b64encode(token_bytes).decode('utf-8')

    return encoded_token

def verify_simple_token(token: str) -> Dict[str, Any]:
    """Verify and decode a simple token"""
    try:
        # Decode base64
        token_bytes = base64.b64decode(token.encode('utf-8'))
        token_string = token_bytes.decode('utf-8')
        payload = json.loads(token_string)

        # Check expiration
        if 'exp' in payload:
            exp_time = datetime.fromtimestamp(payload['exp'])
            if datetime.utcnow() > exp_time:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Extract current user from token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_simple_token(credentials.credentials)

# Mock user class for compatibility
class MockUser:
    def __init__(self, user_data: dict):
        self.id = user_data.get('sub', 'mock-user-id')
        self.username = user_data.get('username', 'mock-user')
        self.email = user_data.get('email', 'mock@example.com')
        self.is_active = True

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active
        }

async def get_current_user(
    token_data: Dict[str, Any] = Depends(get_current_user_from_token)
) -> MockUser:
    """Get current user from token data"""
    return MockUser(token_data)

async def get_current_tenant() -> str:
    """Get current tenant ID - simplified implementation"""
    return "default_tenant"

def require_permission(permission: str):
    """Decorator for permission checking - simplified implementation"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # For now, just pass through - implement actual permission checking later
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def verify_token(token: str) -> Dict[str, Any]:
    """Verify token - alias for compatibility"""
    return verify_simple_token(token)

# Password utilities
def hash_password(password: str) -> str:
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return hash_password(plain_password) == hashed_password
