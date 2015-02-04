"""
Testing fixtures

The test suite is quite expensive to setup on a database such
as postgres. So you'll need to run the `os_initdb` on the
target testing database:

    os_initdb --db postgres://user:pass@host/db

To run the tests you'll then need to run the following command:

    nosetests --tc=db:postgres://user:pass@host/db

"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

# Raise unicode warnings as errors so we can fix them
import warnings
from sqlalchemy.exc import SAWarning
warnings.filterwarnings('error', category=SAWarning)


REDIS_URL = 'redis://localhost/9'


def setup_package():
    """
    Sets up the package-wide fixture.

    Useful for installing system-wide heavy resources such as a database.
    (Costly to do per-test or per-fixture)
    """
    from sqlalchemy import create_engine
    from testconfig import config
    from occams.studies import Session, models as studies
    from occams.datastore import models as datastore
    from occams.roster import Session as RosterSession
    from occams.roster import models as roster

    db = config.get('db') or 'sqlite:///'
    studies_engine = create_engine(db)
    roster_engine = create_engine('sqlite:///')

    Session.configure(bind=studies_engine)
    RosterSession.configure(bind=roster_engine)

    if (studies_engine.url.drivername == 'sqlite'
            and studies_engine.url.database is None):
        datastore.DataStoreModel.metadata.create_all(Session.bind)
        studies.Base.metadata.create_all(Session.bind)
        roster.Base.metadata.create_all(RosterSession.bind)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        import transaction
        from occams.studies import models, Session
        from occams.studies.models import Base

        self.config = testing.setUp()

        self.addCleanup(testing.tearDown)
        self.addCleanup(transaction.abort)
        self.addCleanup(Session.remove)

        Session.add(models.User(key=u'tester'))
        Session.flush()
        Session.info['user'] = u'tester'

        Base.metadata.info['settings'] = self.config.registry.settings


class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    @classmethod
    def setUpClass(cls):
        import os
        from pyramid.path import AssetResolver
        from occams.studies import main, Session
        HERE = os.path.abspath(os.path.dirname(__file__))
        cls.app = main({}, **{
            'app.org.name': 'myorg',
            'app.org.title': 'MY ORGANIZATION',
            'app.export.dir': '/tmp',
            'app.export.user': 'celery@localhost',
            'app.db.url': Session.bind,
            'pid.package': 'occams.roster',
            'pid.db.url': 'sqlite:///',
            'redis.url': REDIS_URL,
            'redis.sessions.secret': 'sekrit',
            'webassets.base_dir': (AssetResolver()
                                   .resolve('occams.studies:static')
                                   .abspath()),
            'webassets.base_url': '/static',
            'webassets.debug': 'false',
            'celery.broker.url': REDIS_URL,
            'celery.backend.url': REDIS_URL,
            'who.config_file': os.path.join(HERE, 'who.ini'),
            'who.identifier_id': '',
            })

    def setUp(self):
        from webtest import TestApp
        self.app = TestApp(self.app)

    def tearDown(self):
        import transaction
        from occams.studies import Session, models as studies
        from occams.roster import Session as RosterSession
        from occams.roster import models as roster
        with transaction.manager:
            Session.query(studies.User).delete()
            Session.query(roster.Site).delete()
        Session.remove()
        RosterSession.remove()

    def make_environ(self, userid='testuser', properties={}, groups=()):
        """
        Creates dummy environ variables for mock-authentication
        """
        if userid:
            return {
                'REMOTE_USER': userid,
                'repoze.who.identity': {
                    'repoze.who.userid': userid,
                    'properties': properties,
                    'groups': groups}}
