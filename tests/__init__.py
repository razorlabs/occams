try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import os.path
import unittest

from pyramid import testing
from pyramid.paster import get_app
from webtest import TestApp

from occams.clinical import Session, RosterSession, models, auth
from occams.datastore import model as datastore
from occams.roster import model as roster


HERE = os.path.abspath(os.path.dirname(__file__))

config = configparser.ConfigParser()

REMOTE_USER = 'testuser'

class ModelFixture(unittest.TestCase):

    def setUp(self):
        Session.begin()

    def tearDown(self):
        Session.rollback()


class ViewFixture(unittest.TestCase):

    def setUp(self):
        app = get_app(os.path.join(HERE, 'etc', 'app.ini'), 'occams.clinical')
        self.app = TestApp(app)
        testing.setUp()

        datastore.DataStoreModel.metadata.create_all(Session.bind)
        models.ClinicalModel.metadata.create_all(Session.bind)
        roster.Model.metadata.create_all(RosterSession.bind)

    def tearDown(self):
        roster.Model.metadata.drop_all(RosterSession.bind)
        models.ClinicalModel.metadata.drop_all(Session.bind)
        datastore.DataStoreModel.metadata.drop_all(Session.bind)
        testing.tearDown()


def make_environ(userid=REMOTE_USER, properties={}, groups=(), headers=()):
    return {
        'REMOTE_USER': userid,
        'repose.who.api': MockWhoAPI(userid, headers),
        'repoze.who.identity': {
            'repoze.who.userid': userid,
            'properties': properties,
            'groups': groups}}


class MockWhoAPI(object):
    """
    Unapolagetically copied from pyramid_who test fixtures
    """

    def __init__(self, authenticated=None, headers=()):
        self._authenticated = authenticated
        self._headers = headers
        self.name_registry = {}

        # Need this for repoze.who middleware
        self.challenge_decider = auth.challenge_decider

    def authenticate(self):
        if self._authenticated is not None:
            return {'repoze.who.userid': self._authenticated}

    def remember(self, identity=None):
        self._remembered = identity
        return self._headers

    def forget(self, identity=None):
        self._forgtten = identity
        return self._headersl
