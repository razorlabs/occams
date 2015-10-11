"""
Testing fixtures

To run the tests you'll then need to run the following command:

    nosetests --tc=db:postgres://user:pass@host/db

"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from nose.plugins.attrib import attr

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles


import warnings
from sqlalchemy.exc import SAWarning
warnings.simplefilter('error', category=SAWarning)


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
    from occams import celery
    from occams_datastore import models as datastore
    from occams_studies import Session, models
    from occams_roster import models as roster, Session as RosterSession

    # parse db name from command line
    # example: nosetests --tc=db:postgresql://plone:plone@/test
    db = config.get('db')
    studies_engine = create_engine(db)
    Session.configure(bind=studies_engine)
    celery.Session.configure(bind=studies_engine)

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


@attr('integration')
class IntegrationFixture(unittest.TestCase):
    """
    Fixure for testing component integration
    """

    def setUp(self):
        from pyramid import testing
        import transaction
        from occams_studies import models, Session

        self.config = testing.setUp()

        blame = models.User(key=u'tester')
        Session.add(blame)
        Session.flush()
        Session.info['blame'] = blame
        Session.info['settings'] = self.config.registry.settings

        # Add hard-coded default states
        Session.add_all([
            models.State(name=u'pending-entry', title=u'Pending Entry'),
            models.State(name=u'pending-review', title=u'Pending Review'),
            models.State(name=u'pending-correction',
                         title=u'Pending Correction'),
            models.State(name=u'complete', title=u'Complete')
        ])

        self.addCleanup(testing.tearDown)
        self.addCleanup(transaction.abort)
        self.addCleanup(Session.remove)


@attr('functional')
class FunctionalFixture(unittest.TestCase):
    """
    Fixture for testing the full application stack.
    Tests under this fixture will be very slow, so use sparingly.
    """

    @classmethod
    def setUpClass(cls):
        """
        Sets up a singleton WSGI app
        """
        import tempfile
        import six
        from occams import main
        from occams_studies import Session

        # The pyramid_who plugin requires a who file, so let's create a
        # barebones files for it...
        who_ini = tempfile.NamedTemporaryFile()
        who = six.moves.configparser.ConfigParser()
        who.add_section('general')
        who.set('general', 'request_classifier',
                'repoze.who.classifiers:default_request_classifier')
        who.set('general', 'challenge_decider',
                'repoze.who.classifiers:default_challenge_decider')
        who.set('general', 'remote_user_key', 'REMOTE_USER')
        who.write(who_ini)
        who_ini.flush()

        wsgi = main({}, **{
            'redis.url': REDIS_URL,
            'redis.sessions.secret': 'sekrit',

            'who.config_file': who_ini.name,
            'who.identifier_id': '',

            # Enable regular error messages so we can see useful traceback
            'debugtoolbar.enabled': True,
            'pyramid.debug_all': True,

            'webassets.debug': True,

            'occams.apps': 'occams_studies',

            'occams.db.url': Session.bind,
            'occams.groups': [],

            'celery.broker.url': REDIS_URL,
            'celery.backend.url': REDIS_URL,
            'celery.blame': 'celery@localhost',

            'studies.export.dir': '/tmp',
            'studies.pid.package': 'occams.roster',
            'studies.blob.dir': '/tmp',

            'roster.db.url': 'sqlite://',
        })

        who_ini.close()

        cls.wsgi = wsgi

    def setUp(self):
        import transaction
        from webtest import TestApp
        from occams_studies import Session, models

        app = TestApp(self.wsgi)

        # Add hard-coded workflow that needs to one day be replaced...
        with transaction.manager:
            blame = models.User(key=u'autostate')
            Session.add(blame)
            Session.flush()
            Session.info['blame'] = blame

            Session.add_all([
                models.State(name=u'pending-entry', title=u'Pending Entry'),
                models.State(name=u'pending-review', title=u'Pending Review'),
                models.State(name=u'pending-correction',
                             title=u'Pending Correction'),
                models.State(name=u'complete', title=u'Complete')
            ])

        self.app = app

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
            Session.execute('DELETE FROM "schema" CASCADE')
            Session.execute('DELETE FROM "export" CASCADE')
            Session.execute('DELETE FROM "state" CASCADE')
            Session.execute('DELETE FROM "user" CASCADE')
            mark_changed(Session())
        Session.remove()
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

    def get_csrf_token(self, environ):
        """Request the app so csrf cookie is available"""
        self.app.get('/', extra_environ=environ)

        return self.app.cookies['csrf_token']
