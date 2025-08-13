#!/usr/bin/env python3
"""
Script to initialize the database with a super admin user and initial data
"""

import os
import sys
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from database import Base, engine, SessionLocal
from models import User

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def init_database():
    """Initialize database with tables and default data"""
    print("🔧 Initializing database...")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")

    # Get database session
    db = SessionLocal()

    try:
        # Check if super admin already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()

        if existing_admin:
            print("ℹ️  Super admin user already exists")
            return

        # Create super admin user
        admin_user = User(
            id=uuid4(),
            email="admin@system.local",
            username="admin",
            password_hash=hash_password("Admin123!"),
            first_name="System",
            last_name="Administrator",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(admin_user)
        db.commit()

        print("✅ Super admin user created:")
        print(f"   Username: admin")
        print(f"   Password: Admin123!")
        print(f"   Email: admin@system.local")

        # Create demo tenant if needed
        with engine.connect() as conn:
            # Check if demo tenant exists
            result = conn.execute(
                text("SELECT COUNT(*) FROM shared.tenants WHERE slug = 'demo'")
            )
            count = result.scalar()

            if count == 0:
                # Create demo tenant
                demo_tenant_id = uuid4()
                demo_schema = "tenant_demo"

                conn.execute(
                    text("""
                        INSERT INTO shared.tenants
                        (id, slug, name, schema_name, status, subscription_plan, max_users, created_at, updated_at)
                        VALUES
                        (:id, :slug, :name, :schema_name, 'active', 'starter', 10, NOW(), NOW())
                    """),
                    {
                        "id": demo_tenant_id,
                        "slug": "demo",
                        "name": "Demo Company",
                        "schema_name": demo_schema
                    }
                )

                # Create schema for demo tenant
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {demo_schema}"))

                # Create users table in tenant schema
                conn.execute(
                    text(f"""
                        CREATE TABLE IF NOT EXISTS {demo_schema}.users (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            email VARCHAR(255) UNIQUE NOT NULL,
                            username VARCHAR(100) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            first_name VARCHAR(100),
                            last_name VARCHAR(100),
                            phone VARCHAR(20),
                            avatar_url TEXT,
                            is_active BOOLEAN DEFAULT true,
                            is_verified BOOLEAN DEFAULT false,
                            failed_login_attempts INTEGER DEFAULT 0,
                            locked_until TIMESTAMP WITH TIME ZONE,
                            last_login_at TIMESTAMP WITH TIME ZONE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                )

                # Create roles table in tenant schema
                conn.execute(
                    text(f"""
                        CREATE TABLE IF NOT EXISTS {demo_schema}.roles (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            name VARCHAR(50) UNIQUE NOT NULL,
                            display_name VARCHAR(100) NOT NULL,
                            description TEXT,
                            permissions JSONB DEFAULT '[]',
                            priority INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                )

                # Create user_roles table
                conn.execute(
                    text(f"""
                        CREATE TABLE IF NOT EXISTS {demo_schema}.user_roles (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES {demo_schema}.users(id) ON DELETE CASCADE,
                            role_id UUID NOT NULL REFERENCES {demo_schema}.roles(id) ON DELETE CASCADE,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(user_id, role_id)
                        )
                    """)
                )

                # Insert default roles
                admin_role_id = uuid4()
                user_role_id = uuid4()

                conn.execute(
                    text(f"""
                        INSERT INTO {demo_schema}.roles (id, name, display_name, description, priority)
                        VALUES
                        (:admin_id, 'admin', 'Administrator', 'Full access to tenant resources', 100),
                        (:user_id, 'user', 'User', 'Standard user access', 10)
                    """),
                    {"admin_id": admin_role_id, "user_id": user_role_id}
                )

                # Create demo admin user in tenant
                demo_admin_id = uuid4()
                conn.execute(
                    text(f"""
                        INSERT INTO {demo_schema}.users
                        (id, email, username, password_hash, first_name, last_name, is_active, is_verified)
                        VALUES
                        (:id, :email, :username, :password_hash, :first_name, :last_name, true, true)
                    """),
                    {
                        "id": demo_admin_id,
                        "email": "admin@demo.com",
                        "username": "demo_admin",
                        "password_hash": hash_password("Demo123!"),
                        "first_name": "Demo",
                        "last_name": "Admin"
                    }
                )

                # Assign admin role to demo admin
                conn.execute(
                    text(f"""
                        INSERT INTO {demo_schema}.user_roles (user_id, role_id)
                        VALUES (:user_id, :role_id)
                    """),
                    {"user_id": demo_admin_id, "role_id": admin_role_id}
                )

                # Create demo regular user
                demo_user_id = uuid4()
                conn.execute(
                    text(f"""
                        INSERT INTO {demo_schema}.users
                        (id, email, username, password_hash, first_name, last_name, is_active, is_verified)
                        VALUES
                        (:id, :email, :username, :password_hash, :first_name, :last_name, true, true)
                    """),
                    {
                        "id": demo_user_id,
                        "email": "user@demo.com",
                        "username": "demo_user",
                        "password_hash": hash_password("User123!"),
                        "first_name": "Demo",
                        "last_name": "User"
                    }
                )

                # Assign user role to demo user
                conn.execute(
                    text(f"""
                        INSERT INTO {demo_schema}.user_roles (user_id, role_id)
                        VALUES (:user_id, :role_id)
                    """),
                    {"user_id": demo_user_id, "role_id": user_role_id}
                )

                conn.commit()

                print("\n✅ Demo tenant created:")
                print(f"   Tenant: Demo Company (slug: demo)")
                print(f"   Admin - Username: demo_admin, Password: Demo123!")
                print(f"   User - Username: demo_user, Password: User123!")

        print("\n🎉 Database initialization completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
