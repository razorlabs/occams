"""
Base delcarative metadata class
Everything that will plug into DataStore should be using this as its base class.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base class for declarative syntax on our models
Model = declarative_base()
