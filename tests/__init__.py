import os.path
import unittest

from pyramid import testing
from pyramid.paster import get_appsettings, get_app
from webtest import TestApp
from sqlalchemy import engine_from_config

from occams.clinical import Session, RosterSession, models
from occams.datastore import model as datastore
from occams.roster import model as roster


HERE = os.path.abspath(os.path.dirname(__file__))
TEST_INI = os.path.join(HERE, 'etc', 'app.ini')


class ModelFixture(unittest.TestCase):
    """
    Fixture for testing the database models only.
    """

    @classmethod
    def setUpClass(cls):
        settings = get_appsettings(TEST_INI)
        Session.configure(bind=engine_from_config(settings, 'clinical.'))

    def setUp(self):
        Session.begin()

    def tearDown(self):
        Session.rollback()


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    @classmethod
    def setUpClass(cls):
        cls.settings = get_appsettings(TEST_INI)

    def setUp(self):
        settings = self.settings
        self.config = testing.setUp()
        Session.configure(bind=engine_from_config(settings, 'clinicaldb.'))
        RosterSession.configure(bind=engine_from_config(settings, 'rosterdb.'))
        create_db()

    def tearDown(self):
        testing.tearDown()
        drop_db()
        disconnect_db()

    def add_user(self, userid):
        session = Session()
        session.add(datastore.User(key=userid))
        session.flush()
        session.info['user'] = userid


class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = get_app(TEST_INI)

    def setUp(self):
        self.app = TestApp(self.app)
        create_db()

    def tearDown(self):
        drop_db()
        disconnect_db()

    def add_user(self, userid):
        session = Session()
        session.add(datastore.User(key=userid))
        session.flush()
        session.info['user'] = userid

    def make_environ(self, userid='testuser', properties={}, groups=()):
        """
        Creates dummy environ variables for mock-authentication
        """
        if not userid:
            return

        return {
            'REMOTE_USER': userid,
            'repoze.who.identity': {
                'repoze.who.userid': userid,
                'properties': properties,
                'groups': groups}}

    def assertCanView(self, url, environ=None, msg=None):
        response = self.app.get(url, extra_environ=environ)
        if response.status_code != 200:
            raise AssertionError(msg or 'Cannot view %s' % url)

    def assertCannotView(self, url, environ=None, msg=None):
        response = self.app.get(url, extra_environ=environ, status='*')
        if response.status_code not in (401, 403):
            raise AssertionError(msg or 'Can view %s' % url)


def create_db():
    datastore.DataStoreModel.metadata.create_all(Session.bind)
    models.ClinicalModel.metadata.create_all(Session.bind)
    roster.Model.metadata.create_all(RosterSession.bind)


def drop_db():
    roster.Model.metadata.drop_all(RosterSession.bind)
    models.ClinicalModel.metadata.drop_all(Session.bind)
    datastore.DataStoreModel.metadata.drop_all(Session.bind)


def disconnect_db():
    Session.remove()
    RosterSession.remove()
