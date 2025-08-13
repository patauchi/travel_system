"""
Financial Service Base Models
Base configuration for all Financial Service models
"""

from sqlalchemy.ext.declarative import declarative_base

# Create Base class for all models
Base = declarative_base()

# This Base will be used by all other model files in the financial service
