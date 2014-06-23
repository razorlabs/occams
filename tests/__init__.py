"""
Testing fixutres
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
    from occams.form import Session, models

    HERE = os.path.abspath(os.path.dirname(__file__))
    cfg = SafeConfigParser()
    cfg.read(os.path.join(HERE, '..', 'setup.cfg'))
    db = config.get('db') or 'default'
    engine = create_engine(cfg.get('db', db))

    Session.configure(bind=engine)

    models.DataStoreModel.metadata.create_all(Session.bind)


def teardown_package():
    """
    Releases system-wide fixtures
    """
    import os
    from occams.form import Session, models

    models.DataStoreModel.metadata.drop_all(Session.bind)

    def delete_db(session):
        url = session.bind.url
        if (url.drivername == 'sqlite'
                and url.database
                and 'memory' not in url.database):
            os.remove(url.database)

    delete_db(Session)


def track_user(login, is_current=True):
    from occams.form import Session, models
    Session.add(models.User(key=login))
    Session.flush()
    Session.info['user'] = login


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        from occams.form import models
        self.config = testing.setUp()
        models.DataStoreModel.metadata.info['settings'] = \
            self.config.registry.settings

    def tearDown(self):
        from occams.form import Session
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
        from occams.form import main, Session
        HERE = os.path.abspath(os.path.dirname(__file__))
        cls.app = main({}, **{
            'app.org.name': 'myorg',
            'app.org.title': 'MY ORGANIZATION',
            'app.db.url': Session.bind,
            'redis.url': REDIS_URL,
            'redis.sessions.secret': 'sekrit',
            'webassets.base_dir': (AssetResolver()
                                   .resolve('occams.form:static')
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
        from occams.form import Session, models
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
