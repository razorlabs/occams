
from occams.datastore.model._meta import Model

from occams.datastore.model.tracking import User
from occams.datastore.model.tracking import Log
from occams.datastore.model.tracking import setActiveUser
from occams.datastore.model.tracking import getActiveUser

from occams.datastore.model.schema import Schema
from occams.datastore.model.schema import Attribute
from occams.datastore.model.schema import Choice

from occams.datastore.model.storage import Entity
from occams.datastore.model.storage import ValueInteger
from occams.datastore.model.storage import ValueString
from occams.datastore.model.storage import ValueObject
from occams.datastore.model.storage import ValueDecimal
from occams.datastore.model.storage import ValueDatetime
from occams.datastore.model.storage import Assignment


if __name__ == '__main__':
    # A convenient way for checking the model even loads
    from sqlalchemy.engine import create_engine
    from sqlalchemy.orm import scoped_session
    Model.metadata.create_all(bind=create_engine('sqlite:///', echo=True))
