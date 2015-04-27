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

USERID = 'test_user'


def setup_package():
    """
    Sets up the package-wide fixture.

    Useful for installing system-wide heavy resources such as a database.
    (Costly to do per-test or per-fixture)
    """
    from sqlalchemy import create_engine
    from testconfig import config
    from occams_studies import Session
    from occams_roster import Session as RosterSession
    from occams_roster import models as roster

    db = config.get('db')
    studies_engine = create_engine(db)
    Session.configure(bind=studies_engine)

    roster_engine = create_engine('sqlite:///')
    RosterSession.configure(bind=roster_engine)
    roster.Base.metadata.create_all(RosterSession.bind)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        import transaction
        from occams_studies import models, Session
        from occams_studies.models import Base

        self.config = testing.setUp()

        self.addCleanup(testing.tearDown)
        self.addCleanup(transaction.abort)
        self.addCleanup(Session.remove)

        blame = models.User(key=u'tester')
        Session.add(blame)
        Session.flush()
        Session.info['blame'] = blame

        Base.metadata.info['settings'] = self.config.registry.settings


class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    def setUp(self):
        import tempfile
        import six
        from webtest import TestApp
        from occams import main
        from occams_studies import Session

        # The pyramid_who plugin requires a who file, so let's create a
        # barebones files for it...
        self.who_ini = tempfile.NamedTemporaryFile()
        who = six.moves.configparser.ConfigParser()
        who.add_section('general')
        who.set('general', 'request_classifier',
                'repoze.who.classifiers:default_request_classifier')
        who.set('general', 'challenge_decider',
                'pyramid_who.classifiers:forbidden_challenger')
        who.set('general', 'remote_user_key', 'REMOTE_USER')
        who.write(self.who_ini)
        self.who_ini.flush()

        app = main({}, **{
            'redis.url': REDIS_URL,
            'redis.sessions.secret': 'sekrit',

            'who.config_file': self.who_ini.name,
            'who.identifier_id': '',

            # Enable regular error messages so we can see useful traceback
            'debugtoolbar.enabled': True,

            'occams.apps': 'occams_studies',

            'occams.db.url': Session.bind,
            'occams.org.name': 'myorg',
            'occams.org.title': 'MY ORGANIZATION',
            'occams.groups': [],

            'studies.export.dir': '/tmp',
            'studies.export.user': 'celery@localhost',
            'studies.celery.broker.url': REDIS_URL,
            'studies.celery.backend.url': REDIS_URL,
            'studies.pid.package': 'occams.roster',

            'roster.db.url': 'sqlite:///',
            })

        self.app = TestApp(app)

    def tearDown(self):
        from zope.sqlalchemy import mark_changed
        import transaction
        from occams_studies import Session, models as studies
        from occams_roster import Session as RosterSession, models as roster
        with transaction.manager:
            Session.execute('TRUNCATE "user" CASCADE')
            mark_changed(Session())
            # Session.query(studies.User).delete()
            RosterSession.query(roster.Site).delete()
        Session.remove()
        RosterSession.remove()
        self.who_ini.close()
        del self.app

    def make_environ(self, userid=USERID, properties={}, groups=()):
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
