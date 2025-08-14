"""
Schema Manager for System Service
Uses SQLAlchemy models to create and manage tenant schemas
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

# Import all models
from models import Base as BaseModel
from models_extended import (
    Note, LogCall, Task, Attachment, Event,
    CarbonFootprint, ChannelConfig, Review
)

# Configure logging
logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Manages tenant schemas using SQLAlchemy models
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the schema manager

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
        )

        # Create engine without pooling for schema operations
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,
            echo=False
        )

        logger.info("Schema Manager initialized")

    def create_tenant_schema(self, schema_name: str) -> bool:
        """
        Create a new tenant schema

        Args:
            schema_name: Name of the schema to create

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Create schema if it doesn't exist
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()

                logger.info(f"Schema {schema_name} created successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            return False

    def create_tables_for_tenant(self, schema_name: str) -> bool:
        """
        Create all tables for a tenant using SQLAlchemy models

        Args:
            schema_name: Name of the tenant schema

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create engine with schema-specific search path
            engine = create_engine(
                self.database_url,
                connect_args={
                    "options": f"-csearch_path={schema_name}"
                },
                poolclass=NullPool,
                echo=False
            )

            # Create all tables from models
            BaseModel.metadata.create_all(bind=engine)

            logger.info(f"Tables created successfully for schema {schema_name}")

            # Dispose of the engine
            engine.dispose()

            return True

        except Exception as e:
            logger.error(f"Failed to create tables for schema {schema_name}: {str(e)}")
            return False

    def initialize_tenant_schema(self, tenant_id: str, schema_name: str) -> Dict[str, Any]:
        """
        Initialize a complete tenant schema with all tables

        Args:
            tenant_id: Tenant ID
            schema_name: Schema name

        Returns:
            Dictionary with status and details
        """
        result = {
            "tenant_id": tenant_id,
            "schema_name": schema_name,
            "status": "failed",
            "tables_created": [],
            "errors": []
        }

        try:
            # Step 1: Create schema
            if not self.create_tenant_schema(schema_name):
                result["errors"].append("Failed to create schema")
                return result

            # Step 2: Create tables from models
            if not self.create_tables_for_tenant(schema_name):
                result["errors"].append("Failed to create tables")
                return result

            # Step 3: List created tables
            tables = self.list_tables_in_schema(schema_name)
            result["tables_created"] = tables

            # Step 4: Run any post-creation tasks
            self.run_post_creation_tasks(schema_name)

            result["status"] = "success"
            logger.info(f"Successfully initialized schema {schema_name} for tenant {tenant_id}")

            return result

        except Exception as e:
            logger.error(f"Failed to initialize schema {schema_name}: {str(e)}")
            result["errors"].append(str(e))
            return result

    def list_tables_in_schema(self, schema_name: str) -> List[str]:
        """
        List all tables in a schema

        Args:
            schema_name: Name of the schema

        Returns:
            List of table names
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """), {"schema": schema_name})

                tables = [row[0] for row in result]
                return tables

        except Exception as e:
            logger.error(f"Failed to list tables in schema {schema_name}: {str(e)}")
            return []

    def run_post_creation_tasks(self, schema_name: str) -> None:
        """
        Run any post-creation tasks for the schema

        Args:
            schema_name: Name of the schema
        """
        try:
            with self.engine.connect() as conn:
                # Set search path
                conn.execute(text(f"SET search_path TO {schema_name}"))

                # Insert default data if needed
                # For example, default roles, permissions, settings

                # Create default roles
                conn.execute(text("""
                    INSERT INTO roles (name, display_name, description, is_system)
                    VALUES
                        ('admin', 'Administrator', 'Full system access', true),
                        ('manager', 'Manager', 'Management access', true),
                        ('user', 'User', 'Standard user access', true),
                        ('viewer', 'Viewer', 'Read-only access', true)
                    ON CONFLICT (name) DO NOTHING
                """))

                # Create default permissions
                conn.execute(text("""
                    INSERT INTO permissions (name, resource, action, description)
                    VALUES
                        ('users.view', 'user', 'read', 'View users'),
                        ('users.create', 'user', 'create', 'Create users'),
                        ('users.edit', 'user', 'update', 'Edit users'),
                        ('users.delete', 'user', 'delete', 'Delete users')
                    ON CONFLICT (name) DO NOTHING
                """))

                # Create default settings
                conn.execute(text("""
                    INSERT INTO settings (category, key, value, value_type, display_name)
                    VALUES
                        ('general', 'timezone', '"UTC"', 'string', 'System Timezone'),
                        ('general', 'date_format', '"YYYY-MM-DD"', 'string', 'Date Format'),
                        ('general', 'language', '"en"', 'string', 'Default Language')
                    ON CONFLICT (category, key) DO NOTHING
                """))

                conn.commit()

                logger.info(f"Post-creation tasks completed for schema {schema_name}")

        except Exception as e:
            logger.warning(f"Post-creation tasks failed for schema {schema_name}: {str(e)}")

    def drop_tenant_schema(self, schema_name: str) -> bool:
        """
        Drop a tenant schema and all its contents

        Args:
            schema_name: Name of the schema to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()

                logger.info(f"Schema {schema_name} dropped successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to drop schema {schema_name}: {str(e)}")
            return False

    def schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema exists

        Args:
            schema_name: Name of the schema

        Returns:
            True if exists, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.schemata
                        WHERE schema_name = :schema
                    )
                """), {"schema": schema_name})

                return result.scalar()

        except Exception as e:
            logger.error(f"Failed to check if schema {schema_name} exists: {str(e)}")
            return False

    def get_schema_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a schema

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary with schema information
        """
        info = {
            "schema_name": schema_name,
            "exists": False,
            "tables": [],
            "table_count": 0,
            "size": "0 bytes"
        }

        try:
            if not self.schema_exists(schema_name):
                return info

            info["exists"] = True

            with self.engine.connect() as conn:
                # Get tables
                info["tables"] = self.list_tables_in_schema(schema_name)
                info["table_count"] = len(info["tables"])

                # Get schema size
                result = conn.execute(text("""
                    SELECT pg_size_pretty(
                        SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint
                    ) as size
                    FROM pg_tables
                    WHERE schemaname = :schema
                """), {"schema": schema_name})

                row = result.first()
                if row and row[0]:
                    info["size"] = row[0]

                return info

        except Exception as e:
            logger.error(f"Failed to get info for schema {schema_name}: {str(e)}")
            return info

    def migrate_all_tenants(self) -> Dict[str, bool]:
        """
        Create/update tables for all active tenants

        Returns:
            Dictionary with migration results per tenant
        """
        results = {}

        try:
            with self.engine.connect() as conn:
                # Get all active tenant schemas
                result = conn.execute(text("""
                    SELECT id, schema_name
                    FROM shared.tenants
                    WHERE status = 'active'
                """))

                for tenant_id, schema_name in result:
                    logger.info(f"Processing tenant {tenant_id} with schema {schema_name}")

                    # Create tables for each tenant
                    success = self.create_tables_for_tenant(schema_name)
                    results[schema_name] = success

                    if success:
                        # Run post-creation tasks
                        self.run_post_creation_tasks(schema_name)

            return results

        except Exception as e:
            logger.error(f"Failed to migrate all tenants: {str(e)}")
            return results


# CLI interface for testing
if __name__ == "__main__":
    import sys

    manager = SchemaManager()

    if len(sys.argv) < 2:
        print("Usage: python schema_manager.py <command> [args]")
        print("Commands:")
        print("  create <schema_name> - Create a new schema with tables")
        print("  drop <schema_name> - Drop a schema")
        print("  list <schema_name> - List tables in a schema")
        print("  info <schema_name> - Get schema information")
        print("  migrate-all - Migrate all active tenants")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: python schema_manager.py create <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        result = manager.initialize_tenant_schema("manual", schema_name)
        print(f"Result: {result}")

    elif command == "drop":
        if len(sys.argv) < 3:
            print("Usage: python schema_manager.py drop <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        success = manager.drop_tenant_schema(schema_name)
        print(f"Schema dropped: {success}")

    elif command == "list":
        if len(sys.argv) < 3:
            print("Usage: python schema_manager.py list <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        tables = manager.list_tables_in_schema(schema_name)
        print(f"Tables in {schema_name}:")
        for table in tables:
            print(f"  - {table}")

    elif command == "info":
        if len(sys.argv) < 3:
            print("Usage: python schema_manager.py info <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        info = manager.get_schema_info(schema_name)
        print(f"Schema info:")
        for key, value in info.items():
            print(f"  {key}: {value}")

    elif command == "migrate-all":
        results = manager.migrate_all_tenants()
        print("Migration results:")
        for schema, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {schema}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
