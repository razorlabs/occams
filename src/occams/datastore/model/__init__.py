import sqlalchemy.ext.declarative


# Base class for declarative syntax on our models
Model = sqlalchemy.ext.declarative.declarative_base()


from occams.datastore.model.metadata import User
from occams.datastore.model.metadata import NOW
from occams.datastore.model.auditing import Auditable

from occams.datastore.model.schema import Schema
from occams.datastore.model.schema import Category
from occams.datastore.model.schema import Attribute
from occams.datastore.model.schema import Choice

from occams.datastore.model.storage import Context
from occams.datastore.model.storage import Entity
from occams.datastore.model.storage import HasEntities
from occams.datastore.model.storage import ValueInteger
from occams.datastore.model.storage import ValueString
from occams.datastore.model.storage import ValueObject
from occams.datastore.model.storage import ValueDecimal
from occams.datastore.model.storage import ValueDatetime

from occams.datastore.model.session import DataStoreSession


__all__ = (
    'Model',
    'User',
    'Auditable',
    'Schema',
    'Category',
    'Attribute',
    'Choice',
    'Entity',
    'HasEntities',
    'ValueInteger',
    'ValueString',
    'ValueObject',
    'ValueDecimal',
    'ValueDatetime',
    'Context',
    )


if __name__ == '__main__': # pragma: no cover
    # A convenient way for checking the model even correctly loads the tables
    Model.metadata.create_all(bind=sqlalchemy.create_engine('sqlite://', echo=True))
