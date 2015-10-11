"""
Testing fixutres

To specify a pyramid configuration use:

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
    from occams_forms import Session

    db = config.get('db')
    studies_engine = create_engine(db)
    Session.configure(bind=studies_engine)

    datastore.DataStoreModel.metadata.create_all(studies_engine)


def teardown_package():
    import os
    from occams_datastore import models as datastore
    from occams_forms import Session

    url = Session.bind.url

    if Session.bind.url.drivername == 'sqlite':
        if Session.bind.url.database not in ('', ':memory:'):
            os.unlink(url.database)
    else:
        datastore.DataStoreModel.metadata.drop_all(Session.bind)


class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        import transaction
        from occams_forms import models, Session

        self.config = testing.setUp()

        blame = models.User(key=u'tester')
        Session.add(blame)
        Session.flush()
        Session.info['blame'] = blame

        # HACK: add hardcoded workflow until we can implement it
        Session.add_all([
            models.State(name=u'pending-entry', title=u'Pending Entry'),
            models.State(name=u'pending-review', title=u'Pending Review'),
            models.State(name=u'pending-correction',
                         title=u'Pending Correction'),
            models.State(name=u'complete', title=u'Complete'),
        ])
        Session.flush()

        models.DataStoreModel.metadata.info['settings'] = \
            self.config.registry.settings

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

        from occams import main, Session

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
            'pyramid.debug_all': True,

            'webassets.debug': True,

            'occams.apps': 'occams_forms',

            'occams.db.url': Session.bind,
            'occams.groups': [],

            'celery.broker.url': REDIS_URL,
            'celery.backend.url': REDIS_URL,
            'celery.blame': 'celery@localhost',

            'roster.db.url': 'sqlite://',
        })

        self.app = TestApp(app)

    def tearDown(self):
        import transaction
        from zope.sqlalchemy import mark_changed
        from occams_forms import Session
        with transaction.manager:
            # DELETE is significantly faster than TRUNCATE
            # http://stackoverflow.com/a/11423886/148781
            # We also have to do this as a raw query becuase SA does
            # not have a way to invoke server-side cascade
            Session.execute('DELETE FROM "entity" CASCADE')
            Session.execute('DELETE FROM "state" CASCADE')
            Session.execute('DELETE FROM "schema" CASCADE')
            Session.execute('DELETE FROM "user" CASCADE')
            mark_changed(Session())
        Session.remove()
        self.who_ini.close()
        del self.app

    def make_environ(self, userid=USERID, properties={}, groups=()):
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

    def get_csrf_token(self, environ):
        """Request the app so csrf cookie is available"""
        self.app.get('/', extra_environ=environ)

        return self.app.cookies['csrf_token']
