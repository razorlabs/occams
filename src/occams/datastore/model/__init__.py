
import sqlalchemy.orm
import sqlalchemy.ext.declarative


# Base class for declarative syntax on our models
Model = sqlalchemy.ext.declarative.declarative_base()


from occams.datastore.model.metadata import User
from occams.datastore.model.metadata import setActiveUser
from occams.datastore.model.metadata import getActiveUser

from occams.datastore.model.auditing import Auditable
from occams.datastore.model.auditing import registerAuditingListener
from occams.datastore.model.auditing import unregisterAuditingListener

from occams.datastore.model.schema import Schema
from occams.datastore.model.schema import Attribute
from occams.datastore.model.schema import Choice
from occams.datastore.model.schema import registerAttributeListener
from occams.datastore.model.schema import unregisterAttributeListener

from occams.datastore.model.storage import Entity
from occams.datastore.model.storage import ValueInteger
from occams.datastore.model.storage import ValueString
from occams.datastore.model.storage import ValueObject
from occams.datastore.model.storage import ValueDecimal
from occams.datastore.model.storage import ValueDatetime
from occams.datastore.model.storage import registerEntityListener


class DataStoreSession(sqlalchemy.orm.Session):
    """
    Custom session that registers itself to the various datastore listeners.

    The intention of this class is to allow a client plugin to just be able
    to use this method as a substitute to sqlalchemy's ``Session``
    class to allow comprehensive datastore functionality.

    If the client plugin needs ``scoped_session`` support, this class
    can be used as a parameter in ``sessionmaker`` as follows::

        engine = sqlalchemy.create_engine('sqlite:///')
        factory = sqlalchemy.orm.sessionmaker(engine, class_=DataStoreSession)

    """

    def __init__(self, *args, **kwargs):
        """
        Constructor with default parameters overriden. Also registers listeners.
        """
        super(DataStoreSession, self).__init__(*args, **kwargs)
        kwargs.setdefault('autoflush', True)
        kwargs.setdefault('autocommit', False)
        registerAuditingListener(self)
        registerEntityListener(self)
        registerAttributeListener(self)


if __name__ == '__main__':
    # A convenient way for checking the model even correctly loads the tables
    Model.metadata.create_all(bind=sqlalchemy.create_engine('sqlite:///', echo=True))
