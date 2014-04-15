try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os.path

from pyramid import testing
from repoze.who.interfaces import (IIdentifier,
                                   IAuthenticator,
                                   IChallenger,
                                   IMetadataProvider)
from zope.interface import implementer

from occams.datastore import model as datastore
from occams.form import Session


HERE = os.path.abspath(os.path.dirname(__file__))

config = configparser.ConfigParser()


class FormModelFixture(object):

    def setUp(self):
        Session.begin()

    def tearDown(self):
        Session.rollback()


class FormFunctionalFixture(object):

    def setUp(self):
        from webtest import TestApp
        from pyramid.paster import get_app
        app = get_app(os.path.join(HERE, 'test.ini'))
        self.app = TestApp(app)
        testing.setUp()

    def tearDown(self):
        empty_db()
        testing.tearDown()


def empty_db():
    """
    Truncate database tables.
    """
    for mapping in (
            datastore.Schema,
            datastore.User):
        Session.query(mapping).delete(False)
    Session.commit()
