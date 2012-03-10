""" Database Definitions
"""

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import has_inherited_table
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer
from sqlalchemy.types import String
from sqlalchemy.types import Unicode


class AutoNamed(object):
    """
    Generates the SQL table name from the class name.
    """

    @declared_attr
    def __tablename__(cls):
        if has_inherited_table(cls) and AutoNamed not in cls.__bases__:
            return None
        return cls.__name__.lower()


# Base class for declarative syntax on our models
Model = declarative_base(cls=AutoNamed)


class Referenceable(object):
    """
    Adds primary key id columns to tables.
    """

    id = Column(Integer, primary_key=True)


class Describeable(object):
    """
    Adds standard content properties to tables.
    """

    name = Column(String, nullable=False)

    title = Column(Unicode, nullable=False)

    description = Column(Unicode)
