"""
Shared database models and base classes for system-service
This module provides the shared Base class and common database utilities
to ensure all models across modules use the same metadata and can reference each other.
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData

# Create a shared metadata instance
metadata = MetaData()

# Create the shared Base class that all models will inherit from
Base = declarative_base(metadata=metadata)

# Export the Base class for use in all modules
__all__ = ["Base", "metadata"]
