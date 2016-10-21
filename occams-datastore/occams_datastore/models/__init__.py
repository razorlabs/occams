import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base


# Use this to create an app-specific table model-base
# DO NOT directly subclass this in your app's table models....
Base = declarative_base()


class DataStoreModel(Base):
    __abstract__ = True
    # TODO: Use dedicated 'datastore' schema
    metadata = sa.MetaData()


from .auditing import Auditable  # NOQA
from .metadata import User, Describeable, Modifiable, Referenceable  # NOQA
from .schema import Schema, Category, Attribute, Choice  # NOQA
from .storage import (  # NOQA
    nameModelMap,
    State, Context, Entity,
    HasEntities,
    ValueString, ValueNumber, ValueDatetime, ValueText,
    ValueChoice, ValueBlob, BlobInfo)
