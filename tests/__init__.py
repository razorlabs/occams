"""
Testing fixtures

To specify a pyramid configuration use:

    nosetests --tc=ini:/path/to/my/config.ini

"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest
from testconfig import config


INI = config['ini']

REDIS_URL = 'redis://localhost/9'


def setup_package():
    """
    Sets up the package-wide fixture.

    Useful for installing system-wide heavy resources such as a database.
    (Costly to do per-test or per-fixture)
    """
    from pyramid.paster import get_appsettings
    from sqlalchemy import engine_from_config
    from occams.clinical import Session, models as clinical
    from occams.datastore import models as datastore
    from occams.roster import Session as RosterSession
    from occams.roster import models as roster

    settings = get_appsettings(INI)

    Session.configure(bind=engine_from_config(settings, 'app.db.'))
    RosterSession.configure(bind=engine_from_config(settings, 'pid.db.'))

    datastore.DataStoreModel.metadata.create_all(Session.bind)
    clinical.Base.metadata.create_all(Session.bind)
    roster.Base.metadata.create_all(RosterSession.bind)


def teardown_package():
    """
    Releases system-wide fixtures
    """
    import os
    from occams.clinical import Session, models as clinical
    from occams.datastore import models as datastore
    from occams.roster import Session as RosterSession
    from occams.roster import models as roster

    roster.Base.metadata.drop_all(RosterSession.bind)
    clinical.Base.metadata.drop_all(Session.bind)
    datastore.DataStoreModel.metadata.drop_all(Session.bind)

    for session in (Session, RosterSession):
        url = session.bind.url
        if url.drivername == 'sqlite' and url.database:
            os.remove(url.database)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        from occams.clinical.models import Base
        self.config = testing.setUp()
        Base.metadata.info['settings'] = self.config.registry.settings

    def tearDown(self):
        from occams.clinical import Session
        from pyramid import testing
        import transaction
        testing.tearDown()
        transaction.abort()
        Session.remove()


class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    @classmethod
    def setUpClass(cls):
        from pyramid.paster import get_app
        cls.app = get_app(INI)

    def setUp(self):
        from webtest import TestApp
        self.app = TestApp(self.app)

    def tearDown(self):
        import transaction
        from occams.clinical import Session, models as clinical
        from occams.datastore import models as datastore
        from occams.roster import Session as RosterSession
        from occams.roster import models as roster
        with transaction.manager:
            Session.query(clinical.Site).delete('fetch')
            Session.query(clinical.Study).delete('fetch')
            Session.query(clinical.Partner).delete('fetch')
            Session.query(datastore.Schema).delete('fetch')
            Session.query(datastore.Category).delete('fetch')
            Session.query(datastore.User).delete('fetch')
            Session.query(roster.Site).delete('fetch')
            Session.query(roster.Identifier).delete('fetch')
        Session.remove()
        RosterSession.remove()

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

    def assert_can_view(self, url, environ=None, msg=None):
        response = self.app.get(url, extra_environ=environ)
        if response.status_code != 200:
            raise AssertionError(msg or 'Cannot view %s' % url)

    def assert_cannot_view(self, url, environ=None, msg=None):
        response = self.app.get(url, extra_environ=environ, status='*')
        if response.status_code not in (401, 403):
            raise AssertionError(msg or 'Can view %s' % url)
