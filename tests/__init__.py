"""
Testing fixtures
"""

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import re
from sqlalchemy import orm


_user = u'bitcore@ucsd.edu'

Session = orm.scoped_session(orm.sessionmaker())


def setup_package():
    import os
    from six.moves.configparser import SafeConfigParser
    from sqlalchemy import create_engine
    from testconfig import config
    from occams.datastore import models
    from occams.datastore.models.events import register
    register(Session)
    HERE = os.path.abspath(os.path.dirname(__file__))
    cfg = SafeConfigParser()
    cfg.read(os.path.join(HERE, '..', 'setup.cfg'))
    db = config.get('db') or 'default'
    engine = create_engine(cfg.get('db', db))
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

#
# Expose assert* from unittest.TestCase
# - give them pep8 style names
# (Copied from nose source base to allow it to work with unittest2)
#
caps = re.compile('([A-Z])')


def pep8(name):
    return caps.sub(lambda m: '_' + m.groups()[0].lower(), name)


class Dummy(unittest.TestCase):
    def nop():
        pass
_t = Dummy('nop')


for at in [at for at in dir(_t) if at.startswith('assert') and not '_' in at]:
    pepd = pep8(at)
    vars()[pepd] = getattr(_t, at)

del Dummy
del _t
del pep8
