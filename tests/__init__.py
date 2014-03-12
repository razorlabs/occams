"""
Testing fixtures
"""

from six.moves.configparser import SafeConfigParser
from sqlalchemy import create_engine, orm

from occams.datastore.models.events import register


_user = u'bitcore@ucsd.edu'

Session = orm.scoped_session(orm.sessionmaker())
register(Session)

config = SafeConfigParser()
config.read('setup.cfg')


def setup_package():
    from occams.datastore import models
    engine = create_engine(config.get('db', 'default'))
    models.DataStoreModel.metadata.create_all(engine)
    Session.configure(bind=engine, info={'user': _user})


def teardown_package():
    """
    Destroys the database structures.
    """
    from occams.datastore import models
    models.DataStoreModel.metadata.drop_all(Session.bind)


def begin_func():
    from occams.datastore import models
    Session.add(models.User(key=_user))
    Session.flush()


def rollback_func():
    Session.rollback()
