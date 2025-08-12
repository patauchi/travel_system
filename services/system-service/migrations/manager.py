"""
Migration Manager for system-service
Handles database migrations for tenant schemas
"""

import os
import logging
from typing import List, Optional
from sqlalchemy import create_engine, text
from pathlib import Path
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manages database migrations for tenant schemas
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the migration manager

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
        )

        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true"
        )

        # Get migrations directory
        self.migrations_dir = Path(__file__).parent

        logger.info(f"Migration manager initialized with migrations from: {self.migrations_dir}")

    def get_migration_files(self) -> List[Path]:
        """
        Get all SQL migration files sorted by name

        Returns:
            List of migration file paths
        """
        migration_files = []

        for file in self.migrations_dir.glob("*.sql"):
            # Skip backup files and temporary files
            if file.name.startswith(".") or file.name.endswith("~"):
                continue

            migration_files.append(file)

        # Sort by filename (should be numbered like 001_initial.sql, 002_update.sql)
        migration_files.sort(key=lambda x: x.name)

        return migration_files

    def create_migrations_table(self, schema_name: str) -> None:
        """
        Create migrations tracking table in the schema

        Args:
            schema_name: Name of the schema
        """
        with self.engine.connect() as conn:
            # Create migrations table if it doesn't exist
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(255) UNIQUE NOT NULL,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    success BOOLEAN DEFAULT true,
                    error_message TEXT
                )
            """))
            conn.commit()

            logger.info(f"Migrations table created/verified in schema {schema_name}")

    def get_applied_migrations(self, schema_name: str) -> List[str]:
        """
        Get list of already applied migrations for a schema

        Args:
            schema_name: Name of the schema

        Returns:
            List of applied migration versions
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"""
                    SELECT version
                    FROM {schema_name}.schema_migrations
                    WHERE success = true
                    ORDER BY version
                """))

                return [row[0] for row in result]
        except Exception as e:
            logger.warning(f"Could not get applied migrations for {schema_name}: {str(e)}")
            return []

    def apply_migration(self, schema_name: str, migration_file: Path) -> bool:
        """
        Apply a single migration to a schema

        Args:
            schema_name: Name of the schema
            migration_file: Path to the migration file

        Returns:
            True if successful, False otherwise
        """
        version = migration_file.stem  # Filename without extension

        logger.info(f"Applying migration {version} to schema {schema_name}")

        # Read migration SQL
        try:
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
        except Exception as e:
            logger.error(f"Failed to read migration file {migration_file}: {str(e)}")
            return False

        # Replace placeholder with actual schema name if needed
        migration_sql = migration_sql.replace("{{schema_name}}", schema_name)

        # Apply migration
        import time
        start_time = time.time()

        try:
            with self.engine.connect() as conn:
                # Set search path to the tenant schema
                conn.execute(text(f"SET search_path TO {schema_name}, public"))

                # Execute migration SQL
                # Split by semicolons but be careful with functions/procedures
                statements = self._split_sql_statements(migration_sql)

                for statement in statements:
                    if statement.strip():
                        conn.execute(text(statement))

                # Record successful migration
                elapsed_ms = int((time.time() - start_time) * 1000)

                conn.execute(text(f"""
                    INSERT INTO {schema_name}.schema_migrations
                    (version, execution_time_ms, success)
                    VALUES (:version, :elapsed_ms, true)
                """), {"version": version, "elapsed_ms": elapsed_ms})

                conn.commit()

                logger.info(f"Successfully applied migration {version} to {schema_name} in {elapsed_ms}ms")
                return True

        except Exception as e:
            logger.error(f"Failed to apply migration {version} to {schema_name}: {str(e)}")

            # Record failed migration
            try:
                with self.engine.connect() as conn:
                    conn.execute(text(f"""
                        INSERT INTO {schema_name}.schema_migrations
                        (version, success, error_message)
                        VALUES (:version, false, :error)
                        ON CONFLICT (version) DO UPDATE
                        SET success = false,
                            error_message = :error,
                            executed_at = CURRENT_TIMESTAMP
                    """), {"version": version, "error": str(e)})
                    conn.commit()
            except:
                pass  # Ignore errors recording the failure

            return False

    def _split_sql_statements(self, sql: str) -> List[str]:
        """
        Split SQL into individual statements, handling functions/procedures

        Args:
            sql: SQL string to split

        Returns:
            List of SQL statements
        """
        # Simple split for now - can be enhanced to handle complex cases
        statements = []
        current_statement = []
        in_function = False

        for line in sql.split('\n'):
            # Check for function/procedure start
            if re.match(r'^\s*CREATE\s+(OR\s+REPLACE\s+)?(FUNCTION|PROCEDURE)', line, re.IGNORECASE):
                in_function = True

            current_statement.append(line)

            # Check for end of statement
            if not in_function and line.rstrip().endswith(';'):
                statements.append('\n'.join(current_statement))
                current_statement = []
            elif in_function and re.match(r'^\$\$\s*LANGUAGE', line, re.IGNORECASE):
                # End of function
                statements.append('\n'.join(current_statement))
                current_statement = []
                in_function = False

        # Add any remaining statement
        if current_statement:
            statements.append('\n'.join(current_statement))

        return statements

    def create_tenant_schema(self, schema_name: str) -> bool:
        """
        Create a new schema for a tenant

        Args:
            schema_name: Name of the schema to create

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Create schema
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()

                logger.info(f"Created schema: {schema_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            return False

    def drop_tenant_schema(self, schema_name: str) -> bool:
        """
        Drop a tenant schema (use with caution!)

        Args:
            schema_name: Name of the schema to drop

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Drop schema cascade
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()

                logger.info(f"Dropped schema: {schema_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to drop schema {schema_name}: {str(e)}")
            return False

    def run_tenant_migrations(self, schema_name: str, force: bool = False) -> bool:
        """
        Run all pending migrations for a tenant schema

        Args:
            schema_name: Name of the tenant schema
            force: If True, run all migrations even if already applied

        Returns:
            True if all migrations successful, False otherwise
        """
        logger.info(f"Running migrations for schema {schema_name}")

        # Ensure schema exists
        if not self.schema_exists(schema_name):
            logger.error(f"Schema {schema_name} does not exist")
            return False

        # Create migrations table
        self.create_migrations_table(schema_name)

        # Get applied migrations
        applied_migrations = [] if force else self.get_applied_migrations(schema_name)

        # Get migration files
        migration_files = self.get_migration_files()

        if not migration_files:
            logger.warning("No migration files found")
            return True

        # Apply pending migrations
        success = True
        applied_count = 0

        for migration_file in migration_files:
            version = migration_file.stem

            if version in applied_migrations:
                logger.debug(f"Skipping already applied migration: {version}")
                continue

            if self.apply_migration(schema_name, migration_file):
                applied_count += 1
            else:
                success = False
                if not force:
                    break  # Stop on first failure unless forcing

        logger.info(f"Applied {applied_count} migrations to {schema_name}")

        return success

    def schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema exists

        Args:
            schema_name: Name of the schema

        Returns:
            True if schema exists, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = :schema_name
                """), {"schema_name": schema_name})

                return result.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking schema existence: {str(e)}")
            return False

    def get_schema_status(self, schema_name: str) -> dict:
        """
        Get migration status for a schema

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary with migration status information
        """
        if not self.schema_exists(schema_name):
            return {
                "exists": False,
                "error": "Schema does not exist"
            }

        applied_migrations = self.get_applied_migrations(schema_name)
        all_migrations = [f.stem for f in self.get_migration_files()]
        pending_migrations = [m for m in all_migrations if m not in applied_migrations]

        return {
            "exists": True,
            "applied_migrations": applied_migrations,
            "pending_migrations": pending_migrations,
            "total_migrations": len(all_migrations),
            "applied_count": len(applied_migrations),
            "pending_count": len(pending_migrations),
            "up_to_date": len(pending_migrations) == 0
        }

    def migrate_all_tenants(self, force: bool = False) -> dict:
        """
        Run migrations for all tenant schemas

        Args:
            force: If True, run all migrations even if already applied

        Returns:
            Dictionary with migration results for each tenant
        """
        results = {}

        # Get all tenant schemas
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name LIKE 'tenant_%'
                    ORDER BY schema_name
                """))

                tenant_schemas = [row[0] for row in result]

        except Exception as e:
            logger.error(f"Failed to get tenant schemas: {str(e)}")
            return {"error": str(e)}

        # Run migrations for each tenant
        for schema_name in tenant_schemas:
            logger.info(f"Migrating {schema_name}")
            success = self.run_tenant_migrations(schema_name, force)
            results[schema_name] = {
                "success": success,
                "status": self.get_schema_status(schema_name)
            }

        return results


# CLI interface for running migrations
if __name__ == "__main__":
    import sys

    manager = MigrationManager()

    if len(sys.argv) < 2:
        print("Usage: python manager.py <command> [args]")
        print("Commands:")
        print("  create <schema_name>  - Create a new tenant schema")
        print("  migrate <schema_name> - Run migrations for a tenant")
        print("  migrate-all           - Run migrations for all tenants")
        print("  status <schema_name>  - Get migration status for a tenant")
        print("  drop <schema_name>    - Drop a tenant schema (DANGEROUS!)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: python manager.py create <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        if manager.create_tenant_schema(schema_name):
            print(f"Created schema: {schema_name}")
        else:
            print(f"Failed to create schema: {schema_name}")
            sys.exit(1)

    elif command == "migrate":
        if len(sys.argv) < 3:
            print("Usage: python manager.py migrate <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        if manager.run_tenant_migrations(schema_name):
            print(f"Successfully migrated: {schema_name}")
        else:
            print(f"Migration failed for: {schema_name}")
            sys.exit(1)

    elif command == "migrate-all":
        results = manager.migrate_all_tenants()
        for schema, result in results.items():
            status = "✓" if result.get("success") else "✗"
            print(f"{status} {schema}")

    elif command == "status":
        if len(sys.argv) < 3:
            print("Usage: python manager.py status <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]
        status = manager.get_schema_status(schema_name)

        if not status.get("exists"):
            print(f"Schema {schema_name} does not exist")
        else:
            print(f"Schema: {schema_name}")
            print(f"Applied migrations: {status['applied_count']}/{status['total_migrations']}")
            print(f"Pending migrations: {status['pending_count']}")
            if status['pending_migrations']:
                print("Pending:")
                for m in status['pending_migrations']:
                    print(f"  - {m}")

    elif command == "drop":
        if len(sys.argv) < 3:
            print("Usage: python manager.py drop <schema_name>")
            sys.exit(1)
        schema_name = sys.argv[2]

        # Confirm dangerous operation
        confirm = input(f"Are you sure you want to DROP schema {schema_name}? This cannot be undone! (yes/no): ")
        if confirm.lower() == "yes":
            if manager.drop_tenant_schema(schema_name):
                print(f"Dropped schema: {schema_name}")
            else:
                print(f"Failed to drop schema: {schema_name}")
                sys.exit(1)
        else:
            print("Operation cancelled")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
