import os.path
import threading
import unittest

from pyramid import testing
from pyramid.security import has_permission
from pyramid.paster import get_appsettings, get_app
from webtest import TestApp
from sqlalchemy import engine_from_config
import transaction

from occams.clinical import Session, RosterSession, models
from occams.datastore import model as datastore
from occams.roster import model as roster


HERE = os.path.abspath(os.path.dirname(__file__))
TEST_INI = os.path.join(HERE, 'app.ini')

REDIS_URL = 'redis://localhost:6379/9'
CLINICAL_URL = 'sqlite://'
ROSTER_URL = 'sqlite://'


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    @classmethod
    def setUpClass(cls):
        cls.settings = settings = get_appsettings(TEST_INI)
        Session.configure(bind=engine_from_config(settings, 'clinicaldb.'))
        RosterSession.configure(bind=engine_from_config(settings, 'rosterdb.'))
        create_db()

    @classmethod
    def tearDownClass(cls):
        drop_db()
        disconnect_db()

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_request_method(
            lambda r, n: has_permission(n, r.context, r),
            'has_permission')

    def tearDown(self):
        testing.tearDown()
        transaction.abort()

    def add_user(self, userid):
        Session.add(datastore.User(key=userid))
        Session.flush()
        Session.info['user'] = userid


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
        Session.add(datastore.User(key=userid))
        Session.flush()
        Session.info['user'] = userid

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


class PubSubListener(threading.Thread):
    """
    Helper class to listen for redis channel broadcasts in separate thread.
    To close the thread, any channel must publish a "KILL" data value
    """

    def __init__(self, r, *channels):
        """
        Parameters:
        r -- the redis instance
        channels -- the channel(s) to subscribe
        """
        super(PubSubListener, self).__init__()
        assert len(channels)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        self.messages = []

    def run(self):
        for item in self.pubsub.listen():
            if item['data'] == 'KILL':
                break
            if item['type'] == 'message':
                self.messages.append(item['data'])


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
