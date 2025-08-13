#!/usr/bin/env python3
"""
Fix script to ensure tenant owner users are properly synchronized between shared.users
and tenant-specific user tables after tenant creation.

This script addresses the issue where tenant owners are created in shared.users but not
in their respective tenant schemas, causing authentication failures.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)


class TenantOwnerSync:
    """Synchronizes tenant owners between shared.users and tenant schemas"""

    def __init__(self, database_url: str = DATABASE_URL):
        """Initialize the sync manager"""
        self.engine = create_engine(
            database_url,
            poolclass=NullPool,
            echo=False
        )
        self.Session = sessionmaker(bind=self.engine)
        logger.info("TenantOwnerSync initialized")

    def get_all_tenants(self):
        """Get all active tenants from the database"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        t.id,
                        t.slug,
                        t.name,
                        t.schema_name,
                        t.status
                    FROM shared.tenants t
                    WHERE t.status IN ('active', 'trial')
                    ORDER BY t.created_at
                """))

                tenants = []
                for row in result:
                    tenants.append({
                        'id': row[0],
                        'slug': row[1],
                        'name': row[2],
                        'schema_name': row[3],
                        'status': row[4]
                    })

                logger.info(f"Found {len(tenants)} active/trial tenants")
                return tenants

        except Exception as e:
            logger.error(f"Failed to get tenants: {str(e)}")
            return []

    def get_tenant_owners(self, tenant_id: str):
        """Get all owners for a specific tenant"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        u.id,
                        u.email,
                        u.username,
                        u.password_hash,
                        u.first_name,
                        u.last_name,
                        u.phone,
                        u.is_active,
                        u.is_verified,
                        u.email_verified_at,
                        tu.role,
                        tu.is_owner
                    FROM shared.users u
                    JOIN shared.tenant_users tu ON u.id = tu.user_id
                    WHERE tu.tenant_id = :tenant_id
                    AND tu.is_owner = true
                """), {'tenant_id': tenant_id})

                owners = []
                for row in result:
                    owners.append({
                        'id': row[0],
                        'email': row[1],
                        'username': row[2],
                        'password_hash': row[3],
                        'first_name': row[4],
                        'last_name': row[5],
                        'phone': row[6],
                        'is_active': row[7],
                        'is_verified': row[8],
                        'email_verified_at': row[9],
                        'role': row[10],
                        'is_owner': row[11]
                    })

                return owners

        except Exception as e:
            logger.error(f"Failed to get owners for tenant {tenant_id}: {str(e)}")
            return []

    def check_user_exists_in_tenant(self, schema_name: str, user_id: str):
        """Check if a user exists in the tenant schema"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT COUNT(*)
                    FROM {schema_name}.users
                    WHERE id = :user_id
                """), {'user_id': user_id})

                count = result.scalar()
                return count > 0

        except Exception as e:
            logger.error(f"Failed to check user in schema {schema_name}: {str(e)}")
            return False

    def ensure_roles_exist(self, schema_name: str):
        """Ensure default roles exist in the tenant schema"""
        try:
            with self.engine.connect() as conn:
                # Check if roles exist
                result = conn.execute(text(f"""
                    SELECT COUNT(*) FROM {schema_name}.roles
                """))

                role_count = result.scalar()

                if role_count == 0:
                    logger.info(f"Creating default roles for schema {schema_name}")

                    # Create default roles
                    conn.execute(text(f"""
                        INSERT INTO {schema_name}.roles (id, name, display_name, description, is_system, is_active, created_at, updated_at)
                        VALUES
                            (gen_random_uuid(), 'admin', 'Administrator', 'Full system access', true, true, NOW(), NOW()),
                            (gen_random_uuid(), 'manager', 'Manager', 'Management access', true, true, NOW(), NOW()),
                            (gen_random_uuid(), 'user', 'User', 'Standard user access', true, true, NOW(), NOW()),
                            (gen_random_uuid(), 'viewer', 'Viewer', 'Read-only access', true, true, NOW(), NOW())
                        ON CONFLICT (name) DO NOTHING
                    """))

                    conn.commit()
                    logger.info(f"Default roles created for schema {schema_name}")
                else:
                    logger.info(f"Roles already exist in schema {schema_name} (count: {role_count})")

                return True

        except Exception as e:
            logger.error(f"Failed to ensure roles for schema {schema_name}: {str(e)}")
            return False

    def sync_owner_to_tenant(self, tenant_info: dict, owner_info: dict):
        """Sync an owner user to the tenant schema"""
        schema_name = tenant_info['schema_name']

        try:
            # First ensure roles exist
            if not self.ensure_roles_exist(schema_name):
                logger.warning(f"Could not ensure roles for {schema_name}")
                return False

            with self.engine.connect() as conn:
                # Check if user already exists
                if self.check_user_exists_in_tenant(schema_name, owner_info['id']):
                    logger.info(f"User {owner_info['username']} already exists in {schema_name}")
                    return True

                # Insert user into tenant schema
                conn.execute(text(f"""
                    INSERT INTO {schema_name}.users (
                        id, email, username, password_hash,
                        first_name, last_name, phone,
                        status, is_active, is_verified,
                        email_verified_at,
                        created_at, updated_at
                    ) VALUES (
                        :id, :email, :username, :password_hash,
                        :first_name, :last_name, :phone,
                        'active', :is_active, :is_verified,
                        :email_verified_at,
                        NOW(), NOW()
                    )
                """), {
                    'id': owner_info['id'],
                    'email': owner_info['email'],
                    'username': owner_info['username'],
                    'password_hash': owner_info['password_hash'],
                    'first_name': owner_info['first_name'] or '',
                    'last_name': owner_info['last_name'] or '',
                    'phone': owner_info['phone'],
                    'is_active': owner_info['is_active'],
                    'is_verified': owner_info['is_verified'],
                    'email_verified_at': owner_info['email_verified_at']
                })

                # Determine which role to assign based on tenant_users.role
                role_name = 'admin' if owner_info['role'] == 'tenant_admin' else 'user'

                # Assign role to user
                conn.execute(text(f"""
                    INSERT INTO {schema_name}.user_roles (user_id, role_id, assigned_at, assigned_by)
                    SELECT :user_id, id, NOW(), :user_id
                    FROM {schema_name}.roles
                    WHERE name = :role_name
                    LIMIT 1
                """), {
                    'user_id': owner_info['id'],
                    'role_name': role_name
                })

                conn.commit()
                logger.info(f"Successfully synced owner {owner_info['username']} to schema {schema_name} with role {role_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to sync owner to schema {schema_name}: {str(e)}")
            return False

    def sync_all_tenant_owners(self, dry_run: bool = False):
        """Sync all tenant owners to their respective schemas"""
        logger.info(f"Starting tenant owner sync (dry_run={dry_run})")

        tenants = self.get_all_tenants()

        stats = {
            'total_tenants': len(tenants),
            'processed': 0,
            'synced': 0,
            'already_synced': 0,
            'failed': 0
        }

        for tenant in tenants:
            logger.info(f"\nProcessing tenant: {tenant['name']} ({tenant['slug']})")
            stats['processed'] += 1

            # Get owners for this tenant
            owners = self.get_tenant_owners(tenant['id'])

            if not owners:
                logger.warning(f"No owners found for tenant {tenant['slug']}")
                continue

            for owner in owners:
                logger.info(f"  Checking owner: {owner['username']} ({owner['email']})")

                # Check if owner exists in tenant schema
                exists = self.check_user_exists_in_tenant(tenant['schema_name'], owner['id'])

                if exists:
                    logger.info(f"    ✓ Already synced")
                    stats['already_synced'] += 1
                else:
                    logger.info(f"    → Need to sync")

                    if not dry_run:
                        success = self.sync_owner_to_tenant(tenant, owner)
                        if success:
                            logger.info(f"    ✓ Synced successfully")
                            stats['synced'] += 1
                        else:
                            logger.error(f"    ✗ Sync failed")
                            stats['failed'] += 1
                    else:
                        logger.info(f"    [DRY RUN] Would sync user")

        # Print summary
        logger.info("\n" + "="*50)
        logger.info("SYNC SUMMARY")
        logger.info("="*50)
        logger.info(f"Total tenants:    {stats['total_tenants']}")
        logger.info(f"Processed:        {stats['processed']}")
        logger.info(f"Already synced:   {stats['already_synced']}")
        logger.info(f"Newly synced:     {stats['synced']}")
        logger.info(f"Failed:           {stats['failed']}")

        return stats

    def fix_specific_tenant(self, tenant_slug: str):
        """Fix a specific tenant by slug"""
        logger.info(f"Fixing tenant: {tenant_slug}")

        try:
            with self.engine.connect() as conn:
                # Get tenant info
                result = conn.execute(text("""
                    SELECT id, slug, name, schema_name, status
                    FROM shared.tenants
                    WHERE slug = :slug
                    LIMIT 1
                """), {'slug': tenant_slug})

                row = result.first()
                if not row:
                    logger.error(f"Tenant not found: {tenant_slug}")
                    return False

                tenant = {
                    'id': row[0],
                    'slug': row[1],
                    'name': row[2],
                    'schema_name': row[3],
                    'status': row[4]
                }

                # Get and sync owners
                owners = self.get_tenant_owners(tenant['id'])

                if not owners:
                    logger.warning(f"No owners found for tenant {tenant_slug}")
                    return False

                success_count = 0
                for owner in owners:
                    logger.info(f"Syncing owner: {owner['username']}")
                    if self.sync_owner_to_tenant(tenant, owner):
                        success_count += 1

                logger.info(f"Successfully synced {success_count}/{len(owners)} owners for tenant {tenant_slug}")
                return success_count == len(owners)

        except Exception as e:
            logger.error(f"Failed to fix tenant {tenant_slug}: {str(e)}")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Fix tenant owner synchronization')
    parser.add_argument('--dry-run', action='store_true', help='Run without making changes')
    parser.add_argument('--tenant', type=str, help='Fix specific tenant by slug')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sync_manager = TenantOwnerSync()

    if args.tenant:
        # Fix specific tenant
        success = sync_manager.fix_specific_tenant(args.tenant)
        sys.exit(0 if success else 1)
    else:
        # Sync all tenants
        stats = sync_manager.sync_all_tenant_owners(dry_run=args.dry_run)
        sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == "__main__":
    main()
