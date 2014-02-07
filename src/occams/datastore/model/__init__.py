from sqlalchemy import MetaData
from sqlalchemy.ext import declarative


def get_class_factory():
    """
    Utility for creating new inheritable SQLAlchemy base model class
    with a common declarative base.
    """

    declarative_base = declarative.declarative_base()
    def ModelClassFactory(class_name, bases=[]):
        return type(str(class_name),
            tuple([declarative_base] + bases), {
            '__abstract__': True,
            'metadata': MetaData()
            })
    return ModelClassFactory


# This is the method to use in client modules
ModelClass = get_class_factory()

# Useful example
DataStoreModel = ModelClass(u'DataStoreModel')

from .auditing import Auditable
from .metadata import User, NOW, AutoNamed, Describeable, Modifiable, Referenceable
from .schema import Schema, Section, Category, Attribute, Choice
from .storage import (
    nameModelMap,
    State, Context, Entity,
    HasEntities,
    ValueInteger, ValueString, ValueDecimal, ValueDatetime, ValueText, ValueBlob)
from .session import DataStoreSession
