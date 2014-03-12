from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base


def get_class_factory():
    """
    Utility for creating new inheritable SQLAlchemy base model class
    with a common declarative base.
    """

    base = declarative_base()

    def ModelClassFactory(class_name, bases=[]):
        return type(str(class_name), tuple([base] + bases), {
            '__abstract__': True,
            'metadata': MetaData()})

    return ModelClassFactory


# This is the method to use in client modules
ModelClass = get_class_factory()

DataStoreModel = ModelClass('DataStoreModel')


from .auditing import Auditable  # NOQA
from .metadata import User, Describeable, Modifiable, Referenceable  # NOQA
from .schema import Schema, Section, Category, Attribute, Choice  # NOQA
from .storage import (  # NOQA
    nameModelMap,
    State, Context, Entity,
    HasEntities,
    ValueInteger, ValueString, ValueDecimal, ValueDatetime, ValueText,
    ValueChoice, ValueBlob)
