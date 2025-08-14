#!/usr/bin/env python3
"""
JWT Token Generator for Financial Service Testing
Creates valid JWT tokens for testing authentication endpoints
"""

import os
import sys
from datetime import datetime, timedelta
from jose import jwt
import json
import argparse

# JWT Configuration (should match shared_auth.py)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_test_token(
    user_id: str = "test-user-123",
    tenant_id: str = "test-tenant-456",
    tenant_slug: str = "test-company",
    role: str = "financial_admin",
    email: str = "test@example.com",
    username: str = "testuser",
    permissions: list = None,
    expires_hours: int = 24
):
    """Create a test JWT token with financial service permissions"""

    if permissions is None:
        permissions = [
            # Orders permissions
            "orders:read", "orders:create", "orders:update", "orders:delete",

            # Expenses permissions
            "expenses:read", "expenses:create", "expenses:update", "expenses:delete",
            "expenses:approve", "expenses:reimburse", "expenses:admin",

            # Petty Cash permissions
            "pettycash:read", "pettycash:create", "pettycash:update", "pettycash:delete",
            "pettycash:transaction", "pettycash:reconcile", "pettycash:replenish", "pettycash:admin",

            # Voucher permissions
            "vouchers:read", "vouchers:create", "vouchers:update", "vouchers:delete",
            "vouchers:approve", "vouchers:pay", "vouchers:cancel", "vouchers:post", "vouchers:admin",

            # Invoice permissions
            "invoices:read", "invoices:create", "invoices:update", "invoices:delete",
            "invoices:send", "invoices:payment", "invoices:write_off", "invoices:credit_hold",

            # Payment permissions
            "payments:read", "payments:create", "payments:update", "payments:delete",
            "payments:process", "payments:refund", "payments:dispute", "payments:admin",

            # General financial permissions
            "financial:read", "financial:admin"
        ]

    # Create token payload
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "tenant_slug": tenant_slug,
        "role": role,
        "email": email,
        "username": username,
        "permissions": permissions,
        "type": "access",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expires_hours)
    }

    # Generate token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, payload

def create_service_token(service_name: str = "test-service", expires_hours: int = 24):
    """Create a service-to-service token"""
    payload = {
        "sub": f"service:{service_name}",
        "type": "service",
        "service": service_name,
        "role": "super_admin",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=expires_hours)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, payload

def verify_token(token: str):
    """Verify and decode a token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired"
    except jwt.JWTError as e:
        return None, f"Token error: {str(e)}"

def print_token_info(token: str, payload: dict):
    """Print formatted token information"""
    print("=" * 80)
    print("🔐 JWT TOKEN GENERATED")
    print("=" * 80)
    print(f"Token: {token}")
    print()
    print("📋 Token Details:")
    print(f"  User ID: {payload.get('sub')}")
    print(f"  Tenant ID: {payload.get('tenant_id')}")
    print(f"  Role: {payload.get('role')}")
    print(f"  Email: {payload.get('email')}")
    print(f"  Type: {payload.get('type')}")
    print(f"  Issued At: {datetime.fromtimestamp(payload.get('iat', 0))}")
    print(f"  Expires At: {datetime.fromtimestamp(payload.get('exp', 0))}")
    print()
    print("🎯 Permissions:")
    permissions = payload.get('permissions', [])
    if permissions:
        for perm in sorted(permissions):
            print(f"  - {perm}")
    else:
        print("  - No specific permissions (service token or super admin)")
    print()

def print_curl_examples(token: str):
    """Print example curl commands"""
    print("🌐 Example API Calls:")
    print()

    base_url = "http://localhost:8007"

    examples = [
        ("Health Check", f'{base_url}/health'),
        ("Financial Health", f'{base_url}/api/v1/financial/health'),
        ("Orders Health", f'{base_url}/api/v1/financial/orders/health'),
        ("List Orders", f'{base_url}/api/v1/financial/orders'),
        ("List Expenses", f'{base_url}/api/v1/financial/expenses'),
        ("List Invoices", f'{base_url}/api/v1/financial/invoices'),
        ("List Payments", f'{base_url}/api/v1/financial/payments'),
        ("Modules Info", f'{base_url}/api/v1/financial/modules'),
    ]

    for name, url in examples:
        print(f"# {name}")
        print(f'curl -H "Authorization: Bearer {token}" \\')
        print(f'     -H "Content-Type: application/json" \\')
        print(f'     -H "X-Tenant-ID: test-tenant-456" \\')
        print(f'     "{url}"')
        print()

def main():
    parser = argparse.ArgumentParser(description="Generate JWT tokens for Financial Service testing")
    parser.add_argument("--user-id", default="test-user-123", help="User ID")
    parser.add_argument("--tenant-id", default="test-tenant-456", help="Tenant ID")
    parser.add_argument("--role", default="financial_admin", help="User role")
    parser.add_argument("--email", default="test@example.com", help="User email")
    parser.add_argument("--expires", type=int, default=24, help="Token expiration in hours")
    parser.add_argument("--service", help="Create service token with this name")
    parser.add_argument("--verify", help="Verify an existing token")
    parser.add_argument("--quiet", action="store_true", help="Only output the token")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.verify:
        # Verify existing token
        payload, error = verify_token(args.verify)
        if error:
            print(f"❌ Token verification failed: {error}", file=sys.stderr)
            return 1
        else:
            print("✅ Token is valid!")
            print(json.dumps(payload, indent=2, default=str))
            return 0

    # Generate new token
    if args.service:
        token, payload = create_service_token(args.service, args.expires)
    else:
        token, payload = create_test_token(
            user_id=args.user_id,
            tenant_id=args.tenant_id,
            role=args.role,
            email=args.email,
            expires_hours=args.expires
        )

    if args.quiet:
        print(token)
    elif args.json:
        result = {
            "token": token,
            "payload": payload
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        print_token_info(token, payload)
        print_curl_examples(token)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
