"""
Testing fixtures

To specify a pyramid configuration use:

    nosetests --tc=ini:/path/to/my/config.ini

"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest


REDIS_URL = 'redis://localhost/9'


def setup_package():
    """
    Sets up the package-wide fixture.

    Useful for installing system-wide heavy resources such as a database.
    (Costly to do per-test or per-fixture)
    """
    import os
    from six.moves.configparser import SafeConfigParser
    from sqlalchemy import create_engine
    from testconfig import config
    from occams.studies import Session, models as studies
    from occams.datastore import models as datastore
    from occams.roster import Session as RosterSession
    from occams.roster import models as roster

    HERE = os.path.abspath(os.path.dirname(__file__))
    cfg = SafeConfigParser()
    cfg.read(os.path.join(HERE, '..', 'setup.cfg'))
    db = config.get('db') or 'default'
    studies_engine = create_engine(cfg.get('db', db))
    roster_engine = create_engine('sqlite:///')

    Session.configure(bind=studies_engine)
    RosterSession.configure(bind=roster_engine)

    datastore.DataStoreModel.metadata.create_all(Session.bind)
    studies.Base.metadata.create_all(Session.bind)
    roster.Base.metadata.create_all(RosterSession.bind)


def teardown_package():
    """
    Releases system-wide fixtures
    """
    import os
    from occams.studies import Session, models as studies
    from occams.datastore import models as datastore
    from occams.roster import Session as RosterSession
    from occams.roster import models as roster

    roster.Base.metadata.drop_all(RosterSession.bind)
    studies.Base.metadata.drop_all(Session.bind)
    datastore.DataStoreModel.metadata.drop_all(Session.bind)

    for session in (Session, RosterSession):
        url = session.bind.url
        if (url.drivername == 'sqlite'
                and url.database
                and 'memory' not in url.database):
            os.remove(url.database)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        from occams.studies.models import Base
        self.config = testing.setUp()
        Base.metadata.info['settings'] = self.config.registry.settings

    def tearDown(self):
        from occams.studies import Session
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
