from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
import logging
from contextlib import contextmanager
from typing import Generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres123@postgres:5432/multitenant_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Use NullPool for better connection management in multi-tenant
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    connect_args={
        "options": "-csearch_path=shared,public",
        "connect_timeout": 10,
        "application_name": "tenant-service"
    }
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create base class for models
Base = declarative_base()

# Metadata for shared schema
metadata = MetaData(schema="shared")

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    This ensures that the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Useful for scripts and background tasks.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

class DatabaseManager:
    """
    Database manager for handling multi-tenant operations
    """

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def create_tenant_schema(self, schema_name: str) -> bool:
        """
        Create a new schema for a tenant
        """
        try:
            with self.engine.connect() as conn:
                # Create schema
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

                # Copy structure from template schema
                conn.execute(text(f"SELECT create_tenant_schema('{schema_name}')"))

                conn.commit()
                logger.info(f"Created schema for tenant: {schema_name}")
                return True
        except Exception as e:
            logger.error(f"Error creating tenant schema: {str(e)}")
            return False

    def drop_tenant_schema(self, schema_name: str) -> bool:
        """
        Drop a tenant's schema
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()
                logger.info(f"Dropped schema for tenant: {schema_name}")
                return True
        except Exception as e:
            logger.error(f"Error dropping tenant schema: {str(e)}")
            return False

    def get_tenant_session(self, schema_name: str) -> Session:
        """
        Get a database session for a specific tenant schema
        """
        # Create a new engine with the tenant's schema in search_path
        tenant_engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,
            echo=False,
            connect_args={
                "options": f"-csearch_path={schema_name},shared,public"
            }
        )

        # Create session for tenant
        TenantSession = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=tenant_engine
        )

        return TenantSession()

    def check_schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema exists
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"),
                    {"schema_name": schema_name}
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking schema existence: {str(e)}")
            return False

# Create global database manager instance
db_manager = DatabaseManager()
