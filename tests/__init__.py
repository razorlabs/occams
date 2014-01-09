import os.path
import unittest

from pyramid import testing
from pyramid.paster import get_app
from webtest import TestApp

from occams.clinical import Session, RosterSession, models
from occams.datastore import model as datastore
from occams.roster import model as roster


HERE = os.path.abspath(os.path.dirname(__file__))


class ModelFixture(unittest.TestCase):

    def setUp(self):
        Session.begin()

    def tearDown(self):
        Session.rollback()


class ViewFixture(unittest.TestCase):

    def setUp(self):
        testing.setUp()
        app = get_app(os.path.join(HERE, 'etc', 'app.ini'), 'occams.clinical')
        self.app = TestApp(app)

        datastore.DataStoreModel.metadata.create_all(Session.bind)
        models.ClinicalModel.metadata.create_all(Session.bind)
        roster.Model.metadata.create_all(RosterSession.bind)

    def tearDown(self):
        roster.Model.metadata.drop_all(RosterSession.bind)
        models.ClinicalModel.metadata.drop_all(Session.bind)
        datastore.DataStoreModel.metadata.drop_all(Session.bind)
        Session.remove()
        RosterSession.remove()
        testing.tearDown()


def make_environ(userid='testuser', properties={}, groups=(), headers=()):
    """
    Creates dummy environ variables for mock-authentication
    """
    if not userid:
        return

    return {
        'REMOTE_USER': userid,
        #'repose.who.api': MockWhoAPI(userid, headers),
        'repoze.who.identity': {
            'repoze.who.userid': userid,
            'properties': properties,
            'groups': groups}}
