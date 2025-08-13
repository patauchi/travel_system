#!/usr/bin/env python3
"""
Test script to verify tenant database context and schema configuration
Tests the proper setup of tenant schemas in database queries
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import asyncio
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    get_tenant_engine,
    get_tenant_session_factory,
    get_tenant_db,
    tenant_db_context,
    get_schema_name_from_slug,
    verify_tenant_schema_exists
)
from dependencies import get_tenant_db_session
from models import User, Role, Permission, Setting

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_TENANT_SLUG = "tenant100"
TEST_SCHEMA_NAME = "tenant_tenant100"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@localhost:5432/multitenant_db"
)


def test_schema_verification():
    """Test if tenant schema exists"""
    logger.info("=" * 60)
    logger.info("Testing schema verification...")

    schema_name = get_schema_name_from_slug(TEST_TENANT_SLUG)
    logger.info(f"Schema name from slug '{TEST_TENANT_SLUG}': {schema_name}")

    exists = verify_tenant_schema_exists(schema_name)
    logger.info(f"Schema '{schema_name}' exists: {exists}")

    if not exists:
        logger.error(f"Schema '{schema_name}' does not exist! Please create it first.")
        return False

    return True


def test_tenant_engine():
    """Test tenant engine creation and search_path configuration"""
    logger.info("=" * 60)
    logger.info("Testing tenant engine creation...")

    try:
        # Get tenant engine
        engine = get_tenant_engine(TEST_SCHEMA_NAME)
        logger.info(f"Created engine for schema: {TEST_SCHEMA_NAME}")

        # Test connection and search_path
        with engine.connect() as conn:
            # Check current search_path
            result = conn.execute(text("SHOW search_path"))
            search_path = result.scalar()
            logger.info(f"Engine search_path: {search_path}")

            # Verify it includes our schema
            if TEST_SCHEMA_NAME not in search_path:
                logger.error(f"Schema {TEST_SCHEMA_NAME} not in search_path!")
                return False

            # Test query execution
            result = conn.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            logger.info(f"Current schema: {current_schema}")

        return True

    except Exception as e:
        logger.error(f"Error testing tenant engine: {str(e)}")
        return False


def test_tenant_session():
    """Test tenant session creation and queries"""
    logger.info("=" * 60)
    logger.info("Testing tenant session...")

    try:
        # Get session using get_tenant_db
        session = get_tenant_db(TEST_TENANT_SLUG)

        try:
            # Check search_path in session
            result = session.execute(text("SHOW search_path"))
            search_path = result.scalar()
            logger.info(f"Session search_path: {search_path}")

            # Query users table
            logger.info("Attempting to query users table...")
            user_count = session.query(User).count()
            logger.info(f"Users in tenant schema: {user_count}")

            # Query with explicit schema (should work)
            result = session.execute(
                text(f"SELECT COUNT(*) FROM {TEST_SCHEMA_NAME}.users")
            )
            explicit_count = result.scalar()
            logger.info(f"Users with explicit schema: {explicit_count}")

            # Query without schema (should also work if search_path is correct)
            result = session.execute(text("SELECT COUNT(*) FROM users"))
            implicit_count = result.scalar()
            logger.info(f"Users without explicit schema: {implicit_count}")

            if explicit_count != implicit_count:
                logger.warning("Count mismatch between explicit and implicit schema queries!")

            return True

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error testing tenant session: {str(e)}")
        logger.exception("Full traceback:")
        return False


def test_tenant_context_manager():
    """Test tenant database context manager"""
    logger.info("=" * 60)
    logger.info("Testing tenant context manager...")

    try:
        with tenant_db_context(TEST_TENANT_SLUG) as db:
            # Check search_path
            result = db.execute(text("SHOW search_path"))
            search_path = result.scalar()
            logger.info(f"Context manager search_path: {search_path}")

            # Try a query
            users = db.query(User).limit(5).all()
            logger.info(f"Found {len(users)} users using context manager")

            for user in users:
                logger.debug(f"  - User: {user.username} ({user.email})")

        logger.info("Context manager closed successfully")
        return True

    except Exception as e:
        logger.error(f"Error testing context manager: {str(e)}")
        return False


def test_dependency_function():
    """Test the FastAPI dependency function"""
    logger.info("=" * 60)
    logger.info("Testing FastAPI dependency function...")

    try:
        # Simulate FastAPI dependency injection
        gen = get_tenant_db_session(TEST_TENANT_SLUG)
        session = next(gen)

        try:
            # Check search_path
            result = session.execute(text("SHOW search_path"))
            search_path = result.scalar()
            logger.info(f"Dependency search_path: {search_path}")

            # Verify schema is set correctly
            if TEST_SCHEMA_NAME not in search_path:
                logger.error(f"Schema {TEST_SCHEMA_NAME} not in search_path!")
                return False

            # Try querying
            result = session.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            logger.info(f"Current schema in dependency: {current_schema}")

            # Query users
            users = session.query(User).limit(3).all()
            logger.info(f"Found {len(users)} users via dependency")

            return True

        finally:
            # Cleanup (simulate FastAPI cleanup)
            try:
                next(gen)
            except StopIteration:
                pass

    except Exception as e:
        logger.error(f"Error testing dependency function: {str(e)}")
        logger.exception("Full traceback:")
        return False


def test_direct_sql_queries():
    """Test direct SQL queries to verify schema setup"""
    logger.info("=" * 60)
    logger.info("Testing direct SQL queries...")

    try:
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # List all schemas
            result = conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'")
            )
            schemas = [row[0] for row in result]
            logger.info(f"Available tenant schemas: {schemas}")

            # Check if our test schema exists
            if TEST_SCHEMA_NAME not in schemas:
                logger.error(f"Test schema {TEST_SCHEMA_NAME} not found!")
                return False

            # List tables in the tenant schema
            result = conn.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = :schema
                    ORDER BY table_name
                """),
                {"schema": TEST_SCHEMA_NAME}
            )
            tables = [row[0] for row in result]
            logger.info(f"Tables in {TEST_SCHEMA_NAME}: {tables}")

            # Check for expected tables
            expected_tables = ['users', 'roles', 'permissions', 'settings', 'teams']
            missing_tables = [t for t in expected_tables if t not in tables]

            if missing_tables:
                logger.error(f"Missing tables in schema: {missing_tables}")
                return False

            logger.info("All expected tables found in tenant schema")
            return True

    except Exception as e:
        logger.error(f"Error in direct SQL queries: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("TENANT DATABASE CONFIGURATION TEST")
    logger.info(f"Testing with tenant: {TEST_TENANT_SLUG}")
    logger.info(f"Expected schema: {TEST_SCHEMA_NAME}")
    logger.info("=" * 60)

    tests = [
        ("Schema Verification", test_schema_verification),
        ("Direct SQL Queries", test_direct_sql_queries),
        ("Tenant Engine", test_tenant_engine),
        ("Tenant Session", test_tenant_session),
        ("Context Manager", test_tenant_context_manager),
        ("FastAPI Dependency", test_dependency_function),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            logger.info(f"\nRunning: {test_name}")
            result = test_func()
            results[test_name] = result

            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")

        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! Tenant database configuration is working correctly.")
        return 0
    else:
        logger.error("⚠️ Some tests failed. Please check the configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
