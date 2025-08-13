"""
Schema Manager for Booking Operations Service
Handles tenant schema creation and management
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session
from datetime import datetime

from models import Base
from database import DATABASE_URL

logger = logging.getLogger(__name__)


class SchemaManager:
    """
    Manages database schemas for multi-tenant architecture
    """

    def __init__(self):
        """Initialize schema manager with database connection"""
        self.engine = create_engine(
            DATABASE_URL,
            isolation_level="AUTOCOMMIT",
            pool_pre_ping=True
        )
        logger.info("SchemaManager initialized")

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
                # Create schema if it doesn't exist
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                logger.info(f"Created schema: {schema_name}")
                return True
        except Exception as e:
            logger.error(f"Error creating schema {schema_name}: {str(e)}")
            return False

    def create_tables_for_tenant(self, schema_name: str) -> bool:
        """
        Create all tables in a tenant schema

        Args:
            schema_name: Name of the tenant schema

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create engine with schema-specific search path
            tenant_engine = create_engine(
                DATABASE_URL,
                connect_args={
                    "options": f"-csearch_path={schema_name}"
                }
            )

            # Create all tables
            Base.metadata.create_all(bind=tenant_engine)

            logger.info(f"Created tables for schema: {schema_name}")

            # Dispose of the engine
            tenant_engine.dispose()

            return True

        except Exception as e:
            logger.error(f"Error creating tables for schema {schema_name}: {str(e)}")
            return False

    def add_foreign_key_constraints(self, schema_name: str) -> bool:
        """
        Add foreign key constraints that reference other services' tables

        Args:
            schema_name: Name of the tenant schema

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Set search path
                conn.execute(text(f"SET search_path TO {schema_name}"))

                # Add foreign key constraints to other services
                constraints = [
                    # Bookings -> Orders (Financial Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_bookings_order_id'
                        ) THEN
                            ALTER TABLE bookings
                            ADD CONSTRAINT fk_bookings_order_id
                            FOREIGN KEY (order_id)
                            REFERENCES orders(id) ON DELETE CASCADE;
                        END IF;
                    END $$;
                    """,

                    # BookingLines -> OrderLines (Financial Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_booking_lines_order_line_id'
                        ) THEN
                            ALTER TABLE booking_lines
                            ADD CONSTRAINT fk_booking_lines_order_line_id
                            FOREIGN KEY (order_line_id)
                            REFERENCES order_lines(id) ON DELETE CASCADE;
                        END IF;
                    END $$;
                    """,

                    # Passengers -> Contacts (CRM Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_passengers_contact_id'
                        ) THEN
                            ALTER TABLE passengers
                            ADD CONSTRAINT fk_passengers_contact_id
                            FOREIGN KEY (contact_id)
                            REFERENCES contacts(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                    """,

                    # BookingLines -> Users (Auth Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_booking_lines_handled_by'
                        ) THEN
                            ALTER TABLE booking_lines
                            ADD CONSTRAINT fk_booking_lines_handled_by
                            FOREIGN KEY (handled_by)
                            REFERENCES users(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                    """,

                    # ServiceOperations -> Users (Auth Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_service_operations_assigned_to'
                        ) THEN
                            ALTER TABLE service_operations
                            ADD CONSTRAINT fk_service_operations_assigned_to
                            FOREIGN KEY (assigned_to)
                            REFERENCES users(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                    """,

                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_service_operations_supervised_by'
                        ) THEN
                            ALTER TABLE service_operations
                            ADD CONSTRAINT fk_service_operations_supervised_by
                            FOREIGN KEY (supervised_by)
                            REFERENCES users(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                    """,

                    # ServiceParticipants -> Users (Auth Service)
                    """
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_constraint
                            WHERE conname = 'fk_service_participants_checked_in_by'
                        ) THEN
                            ALTER TABLE service_participants
                            ADD CONSTRAINT fk_service_participants_checked_in_by
                            FOREIGN KEY (checked_in_by)
                            REFERENCES users(id) ON DELETE SET NULL;
                        END IF;
                    END $$;
                    """
                ]

                # Execute each constraint
                for constraint_sql in constraints:
                    try:
                        conn.execute(text(constraint_sql))
                    except Exception as e:
                        logger.warning(f"Could not add constraint: {str(e)}")
                        # Continue with other constraints

                logger.info(f"Added foreign key constraints for schema: {schema_name}")
                return True

        except Exception as e:
            logger.error(f"Error adding foreign key constraints: {str(e)}")
            return False

    def initialize_tenant_schema(self, tenant_id: str, schema_name: str) -> Dict[str, Any]:
        """
        Initialize a complete tenant schema with all tables and constraints

        Args:
            tenant_id: UUID of the tenant
            schema_name: Name of the schema to create

        Returns:
            Dictionary with status and details
        """
        result = {
            "tenant_id": tenant_id,
            "schema_name": schema_name,
            "status": "success",
            "tables_created": [],
            "errors": []
        }

        try:
            # Step 1: Create schema
            if not self.create_tenant_schema(schema_name):
                result["status"] = "error"
                result["errors"].append("Failed to create schema")
                return result

            # Step 2: Create tables
            if not self.create_tables_for_tenant(schema_name):
                result["status"] = "error"
                result["errors"].append("Failed to create tables")
                return result

            # Step 3: List created tables
            tables = self.list_tables_in_schema(schema_name)
            result["tables_created"] = tables

            # Step 4: Add foreign key constraints (optional, may fail if other services not initialized)
            self.add_foreign_key_constraints(schema_name)

            # Step 5: Run post-creation tasks
            self.run_post_creation_tasks(schema_name)

            logger.info(f"Successfully initialized schema for tenant {tenant_id}")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            logger.error(f"Error initializing tenant schema: {str(e)}")

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
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = :schema_name
                    ORDER BY tablename
                """), {"schema_name": schema_name})

                return [row[0] for row in result]
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            return []

    def run_post_creation_tasks(self, schema_name: str) -> bool:
        """
        Run post-creation tasks like inserting default data

        Args:
            schema_name: Name of the schema

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                # Set search path
                conn.execute(text(f"SET search_path TO {schema_name}"))

                # Insert default cancellation policies
                conn.execute(text("""
                    INSERT INTO cancellation_policies (name, code, policy_type, cancellation_rules, is_active, is_default, created_at, updated_at)
                    VALUES
                    ('Flexible Policy', 'FLEX', 'flexible',
                     '[{"hours_before": 24, "refund_percentage": 100, "fee_amount": 0}]'::jsonb,
                     true, true, NOW(), NOW()),
                    ('Moderate Policy', 'MOD', 'moderate',
                     '[{"hours_before": 72, "refund_percentage": 100, "fee_amount": 0},
                       {"hours_before": 48, "refund_percentage": 50, "fee_amount": 25}]'::jsonb,
                     true, false, NOW(), NOW()),
                    ('Strict Policy', 'STRICT', 'strict',
                     '[{"hours_before": 168, "refund_percentage": 100, "fee_amount": 0},
                       {"hours_before": 72, "refund_percentage": 50, "fee_amount": 50},
                       {"hours_before": 24, "refund_percentage": 0, "fee_amount": 100}]'::jsonb,
                     true, false, NOW(), NOW())
                    ON CONFLICT (code) DO NOTHING
                """))

                # Insert sample countries (if needed)
                conn.execute(text("""
                    INSERT INTO countries (code, code3, name, continent, is_active, created_at, updated_at)
                    VALUES
                    ('PE', 'PER', 'Peru', 'South America', true, NOW(), NOW()),
                    ('US', 'USA', 'United States', 'North America', true, NOW(), NOW()),
                    ('ES', 'ESP', 'Spain', 'Europe', true, NOW(), NOW()),
                    ('FR', 'FRA', 'France', 'Europe', true, NOW(), NOW()),
                    ('JP', 'JPN', 'Japan', 'Asia', true, NOW(), NOW())
                    ON CONFLICT (code) DO NOTHING
                """))

                logger.info(f"Completed post-creation tasks for schema: {schema_name}")
                return True

        except Exception as e:
            logger.error(f"Error running post-creation tasks: {str(e)}")
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
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
                logger.info(f"Dropped schema: {schema_name}")
                return True
        except Exception as e:
            logger.error(f"Error dropping schema {schema_name}: {str(e)}")
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
                    SELECT 1 FROM information_schema.schemata
                    WHERE schema_name = :schema_name
                """), {"schema_name": schema_name})

                return result.first() is not None
        except Exception as e:
            logger.error(f"Error checking schema existence: {str(e)}")
            return False

    def get_schema_info(self, schema_name: str) -> Dict[str, Any]:
        """
        Get information about a schema

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary with schema information
        """
        info = {
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
                tables = self.list_tables_in_schema(schema_name)
                info["tables"] = tables
                info["table_count"] = len(tables)

                # Get schema size
                result = conn.execute(text("""
                    SELECT pg_size_pretty(
                        SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint
                    ) as size
                    FROM pg_tables
                    WHERE schemaname = :schema_name
                """), {"schema_name": schema_name})

                row = result.first()
                if row and row[0]:
                    info["size"] = row[0]

        except Exception as e:
            logger.error(f"Error getting schema info: {str(e)}")

        return info
