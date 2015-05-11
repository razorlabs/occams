"""
Testing fixtures

To run the tests you'll then need to run the following command:

    nosetests --tc=db:postgres://user:pass@host/db

"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles


REDIS_URL = 'redis://localhost/9'

USERID = 'test_user'


@compiles(CreateTable, 'postgresql')
def compile_unlogged(create, compiler, **kwargs):
    """
    Enables unlogged-tables for testing purposes.
    This will make table creates slower, but data writes faster.
    """
    if 'UNLOGGED' not in create.element._prefixes:
        create.element._prefixes.append('UNLOGGED')
        return compiler.visit_create_table(create)


def setup_package():
    """
    Sets up the package-wide fixture.

    Useful for installing system-wide heavy resources such as a database.
    (Costly to do per-test or per-fixture)
    """
    from sqlalchemy import create_engine
    from testconfig import config
    from occams_datastore import models as datastore
    from occams_studies import Session, models
    from occams_roster import models as roster, Session as RosterSession

    db = config.get('db')
    studies_engine = create_engine(db)
    Session.configure(bind=studies_engine)

    datastore.DataStoreModel.metadata.create_all(studies_engine)
    models.Base.metadata.create_all(studies_engine)

    roster_engine = create_engine('sqlite://')
    RosterSession.configure(bind=roster_engine)
    roster.Base.metadata.create_all(RosterSession.bind)


def teardown_package():
    import os
    from occams_datastore import models as datastore
    from occams_studies import Session, models

    url = Session.bind.url

    if Session.bind.url.drivername == 'sqlite':
        if Session.bind.url.database not in ('', ':memory:'):
            os.unlink(url.database)
    else:
        models.Base.metadata.drop_all(Session.bind)
        datastore.DataStoreModel.metadata.drop_all(Session.bind)


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

        blame = models.User(key=u'tester')
        Session.add(blame)
        Session.flush()
        Session.info['blame'] = blame

        Base.metadata.info['settings'] = self.config.registry.settings

        self.addCleanup(testing.tearDown)
        self.addCleanup(transaction.abort)
        self.addCleanup(Session.remove)


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
                'repoze.who.classifiers:default_challenge_decider')
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

            'webassets.debug': True,
            'webassets.auto_build': False,

            'occams.apps': 'occams_studies',

            'occams.db.url': Session.bind,
            'occams.groups': [],

            'studies.export.dir': '/tmp',
            'studies.export.user': 'celery@localhost',
            'studies.celery.broker.url': REDIS_URL,
            'studies.celery.backend.url': REDIS_URL,
            'studies.pid.package': 'occams.roster',

            'roster.db.url': 'sqlite://',
        })

        self.app = TestApp(app)

    def tearDown(self):
        import transaction
        from zope.sqlalchemy import mark_changed
        from occams_studies import Session
        with transaction.manager:
            # DELETE is significantly faster than TRUNCATE
            # http://stackoverflow.com/a/11423886/148781
            # We also have to do this as a raw query becuase SA does
            # not have a way to invoke server-side cascade
            Session.execute('DELETE FROM "study" CASCADE')
            Session.execute('DELETE FROM "patient" CASCADE')
            Session.execute('DELETE FROM "site" CASCADE')
            Session.execute('DELETE FROM "export" CASCADE')
            Session.execute('DELETE FROM "user" CASCADE')
            mark_changed(Session())
        Session.remove()
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
