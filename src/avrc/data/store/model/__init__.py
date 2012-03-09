
from avrc.data.store.model._meta import Model

from avrc.data.store.model.tracking import User
from avrc.data.store.model.tracking import Log
from avrc.data.store.model.tracking import setActiveUser
from avrc.data.store.model.tracking import getActiveUser

from avrc.data.store.model.schema import Schema
from avrc.data.store.model.schema import Attribute
from avrc.data.store.model.schema import Choice

from avrc.data.store.model.storage import Entity
from avrc.data.store.model.storage import ValueInteger
from avrc.data.store.model.storage import ValueString
from avrc.data.store.model.storage import ValueObject
from avrc.data.store.model.storage import ValueDecimal
from avrc.data.store.model.storage import ValueDatetime
from avrc.data.store.model.storage import Assignment


if __name__ == '__main__':
    # A convenient way for checking the model even loads
    from sqlalchemy.engine import create_engine
    from sqlalchemy.orm import scoped_session
    Model.metadata.create_all(bind=create_engine('sqlite:///', echo=True))
