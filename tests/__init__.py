"""
Testing fixutres

If using a database other than sqlite, you must preinstall
the database by first runnning:

    initdb path/to/ini



To specify a pyramid configuration use:

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
    from occams.datastore import models as datastore
    from occams.forms import Session

    Session.configure(bind=create_engine(config.get('db')))
    datastore.DataStoreModel.metadata.create_all(Session.bind)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        import transaction
        from occams.forms import models, Session

        self.config = testing.setUp()

        self.addCleanup(testing.tearDown)
        self.addCleanup(transaction.abort)
        self.addCleanup(Session.remove)

        blame = models.User(key=u'tester')
        Session.add(blame)
        Session.flush()
        Session.info['blame'] = blame

        models.DataStoreModel.metadata.info['settings'] = \
            self.config.registry.settings


class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    @classmethod
    def setUpClass(cls):
        import os
        from pyramid.path import AssetResolver
        from occams.forms import main, Session
        HERE = os.path.abspath(os.path.dirname(__file__))
        cls.app = main({}, **{
            'app.org.name': 'myorg',
            'app.org.title': 'MY ORGANIZATION',
            'app.db.url': Session.bind,
            'redis.url': REDIS_URL,
            'redis.sessions.secret': 'sekrit',
            'webassets.base_dir': (AssetResolver()
                                   .resolve('occams.forms:static')
                                   .abspath()),
            'webassets.base_url': '/static',
            'webassets.debug': 'false',
            'who.config_file': os.path.join(HERE, 'who.ini'),
            'who.identifier_id': '',
        })

    def setUp(self):
        from webtest import TestApp
        self.app = TestApp(self.app)

    def tearDown(self):
        import transaction
        from occams.forms import Session, models
        with transaction.manager:
            Session.query(models.User).delete()
        Session.remove()

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
