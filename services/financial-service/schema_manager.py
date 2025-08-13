"""
Schema Manager for Financial Service
Manages database schema and table creation for tenant isolation
"""

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.pool import NullPool
import os

from models import Base

# Configure logging
logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Manages tenant schemas and table creation for Financial service
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the schema manager

        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@postgres:5432/multitenant_db"
        )

        # Create engine without pooling for schema operations
        self.engine = create_engine(
            self.database_url,
            poolclass=NullPool,
            echo=False
        )

        logger.info("Financial Service Schema Manager initialized")

    def create_tenant_schema(self, schema_name: str) -> bool:
        """
        Create a new tenant schema if it doesn't exist

        Args:
            schema_name: Name of the schema to create

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Create schema if it doesn't exist
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()

                logger.info(f"Schema {schema_name} created or verified successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            return False

    def create_tables_for_tenant(self, schema_name: str) -> bool:
        """
        Create all Financial tables for a tenant

        Args:
            schema_name: Name of the tenant schema

        Returns:
            bool: True if successful, False otherwise
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
            Base.metadata.create_all(bind=engine, checkfirst=True)

            logger.info(f"Financial tables created successfully for schema {schema_name}")

            # Dispose of the engine
            engine.dispose()

            # Add foreign key constraints after tables are created
            if not self.add_foreign_key_constraints(schema_name):
                logger.warning(f"Failed to add some foreign key constraints for schema {schema_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to create tables for schema {schema_name}: {str(e)}")
            return False

    def add_foreign_key_constraints(self, schema_name: str) -> bool:
        """
        Add foreign key constraints to Financial tables after they're created

        Args:
            schema_name: Name of the tenant schema

        Returns:
            bool: True if all constraints added successfully, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Set search path to the schema
                conn.execute(text(f"SET search_path TO {schema_name}"))

                # Define foreign key constraints to add
                fk_constraints = [
                    # Orders table
                    """ALTER TABLE orders
                       ADD CONSTRAINT fk_orders_cancelled_by
                       FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Invoices table
                    """ALTER TABLE invoices
                       ADD CONSTRAINT fk_invoices_created_by
                       FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Payments table
                    """ALTER TABLE payments
                       ADD CONSTRAINT fk_payments_processed_by
                       FOREIGN KEY (processed_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE payments
                       ADD CONSTRAINT fk_payments_verified_by
                       FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Expenses table
                    """ALTER TABLE expenses
                       ADD CONSTRAINT fk_expenses_employee_id
                       FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE expenses
                       ADD CONSTRAINT fk_expenses_approved_by
                       FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE expenses
                       ADD CONSTRAINT fk_expenses_paid_by
                       FOREIGN KEY (paid_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Petty Cash table
                    """ALTER TABLE petty_cashes
                       ADD CONSTRAINT fk_petty_cashes_custodian_id
                       FOREIGN KEY (custodian_id) REFERENCES users(id) ON DELETE CASCADE""",

                    """ALTER TABLE petty_cashes
                       ADD CONSTRAINT fk_petty_cashes_last_reconciled_by
                       FOREIGN KEY (last_reconciled_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE petty_cashes
                       ADD CONSTRAINT fk_petty_cashes_last_audited_by
                       FOREIGN KEY (last_audited_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Petty Cash Transactions table
                    """ALTER TABLE petty_cash_transactions
                       ADD CONSTRAINT fk_petty_cash_trans_performed_by
                       FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE CASCADE""",

                    """ALTER TABLE petty_cash_transactions
                       ADD CONSTRAINT fk_petty_cash_trans_approved_by
                       FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE petty_cash_transactions
                       ADD CONSTRAINT fk_petty_cash_trans_reconciled_by
                       FOREIGN KEY (reconciled_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Vouchers table
                    """ALTER TABLE vouchers
                       ADD CONSTRAINT fk_vouchers_created_by
                       FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE""",

                    """ALTER TABLE vouchers
                       ADD CONSTRAINT fk_vouchers_approved_by
                       FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE vouchers
                       ADD CONSTRAINT fk_vouchers_paid_by
                       FOREIGN KEY (paid_by) REFERENCES users(id) ON DELETE SET NULL""",

                    """ALTER TABLE vouchers
                       ADD CONSTRAINT fk_vouchers_cancelled_by
                       FOREIGN KEY (cancelled_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Passenger Documents table
                    """ALTER TABLE passenger_documents
                       ADD CONSTRAINT fk_passenger_docs_verified_by
                       FOREIGN KEY (verified_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Accounts Payable table
                    """ALTER TABLE accounts_payables
                       ADD CONSTRAINT fk_accounts_payables_approved_by
                       FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL""",

                    # Accounts Receivable table
                    """ALTER TABLE accounts_receivables
                       ADD CONSTRAINT fk_accounts_receivables_written_off_by
                       FOREIGN KEY (written_off_by) REFERENCES users(id) ON DELETE SET NULL""",
                ]

                # Try to add each constraint
                successful = 0
                failed = 0

                for constraint_sql in fk_constraints:
                    try:
                        # Check if constraint already exists before adding
                        constraint_name = constraint_sql.split("ADD CONSTRAINT")[1].strip().split()[0]
                        check_sql = text("""
                            SELECT 1 FROM information_schema.table_constraints
                            WHERE constraint_schema = :schema
                            AND constraint_name = :name
                        """)
                        result = conn.execute(check_sql, {"schema": schema_name, "name": constraint_name})

                        if not result.fetchone():
                            conn.execute(text(constraint_sql))
                            successful += 1
                            logger.debug(f"Added constraint: {constraint_name}")
                        else:
                            logger.debug(f"Constraint already exists: {constraint_name}")
                            successful += 1

                    except Exception as e:
                        failed += 1
                        logger.warning(f"Failed to add constraint: {str(e)}")

                conn.commit()

                logger.info(f"Foreign key constraints added for schema {schema_name}: {successful} successful, {failed} failed")
                return failed == 0

        except Exception as e:
            logger.error(f"Failed to add foreign key constraints for schema {schema_name}: {str(e)}")
            return False

    def initialize_tenant_schema(self, tenant_id: str, schema_name: str) -> Dict[str, Any]:
        """
        Initialize a complete tenant schema with all Financial tables

        Args:
            tenant_id: Tenant ID
            schema_name: Schema name

        Returns:
            Dictionary with status and details
        """
        result = {
            "tenant_id": tenant_id,
            "schema_name": schema_name,
            "service": "financial-service",
            "status": "failed",
            "tables_created": [],
            "errors": []
        }

        try:
            # Step 1: Ensure schema exists
            if not self.create_tenant_schema(schema_name):
                result["errors"].append("Failed to create or verify schema")
                return result

            # Step 2: Create tables from models
            if not self.create_tables_for_tenant(schema_name):
                result["errors"].append("Failed to create tables")
                return result

            # Step 3: List created tables
            tables = self.list_tables_in_schema(schema_name)
            result["tables_created"] = tables

            # Step 4: Add foreign key constraints
            if self.add_foreign_key_constraints(schema_name):
                logger.info(f"Foreign key constraints added successfully for schema {schema_name}")
            else:
                logger.warning(f"Some foreign key constraints could not be added for schema {schema_name}")

            # Step 5: Run any post-creation tasks
            self.run_post_creation_tasks(schema_name)

            result["status"] = "success"
            logger.info(f"Successfully initialized Financial schema {schema_name} for tenant {tenant_id}")

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

                # Insert default expense categories
                conn.execute(text("""
                    INSERT INTO expense_categories (name, code, description, is_active)
                    VALUES
                        ('Travel', 'TRAVEL', 'Travel and transportation expenses', true),
                        ('Accommodation', 'ACCOMMODATION', 'Hotel and lodging expenses', true),
                        ('Meals & Entertainment', 'MEALS', 'Meals and entertainment expenses', true),
                        ('Office Supplies', 'OFFICE', 'Office supplies and equipment', true),
                        ('Marketing', 'MARKETING', 'Marketing and advertising expenses', true),
                        ('Professional Services', 'PROFESSIONAL', 'Legal, accounting, consulting fees', true),
                        ('Utilities', 'UTILITIES', 'Electricity, water, internet, phone', true),
                        ('Insurance', 'INSURANCE', 'Business insurance premiums', true),
                        ('Taxes & Licenses', 'TAXES', 'Business taxes and licenses', true),
                        ('Commissions', 'COMMISSIONS', 'Sales commissions and fees', true),
                        ('Maintenance', 'MAINTENANCE', 'Repairs and maintenance', true),
                        ('Other', 'OTHER', 'Other business expenses', true)
                    ON CONFLICT DO NOTHING
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
            bool: True if successful, False otherwise
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
            bool: True if exists, False otherwise
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

                # Get table row counts
                table_counts = {}
                for table in info["tables"]:
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{table}"))
                    table_counts[table] = count_result.scalar()

                info["table_counts"] = table_counts

                return info

        except Exception as e:
            logger.error(f"Failed to get info for schema {schema_name}: {str(e)}")
            return info


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
            if key != "table_counts":
                print(f"  {key}: {value}")
        if "table_counts" in info:
            print("  Table row counts:")
            for table, count in info["table_counts"].items():
                print(f"    - {table}: {count} rows")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
