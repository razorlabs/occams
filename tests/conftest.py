"""
Testing fixtures

To run the tests you'll then need to run the following command:

    py.test --db=postgres://user:pass@host/db

"""

import pytest

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles


REDIS_URL = 'redis://localhost/9'

USERID = 'test_user'


def pytest_addoption(parser):
    """
    Registers a command line argument for a database URL connection string
    """
    parser.addoption('--db', action='store', help='db string for testing')
    parser.addoption('--reuse', action='store_true',
                     help='Reuses existing database')


@compiles(CreateTable, 'postgresql')
def compile_unlogged(create, compiler, **kwargs):
    """
    Updates the CREATE TABLE construct for PostgreSQL to UNLOGGED

    The benefit of this is faster writes for testing, at the cost of
    slightly slower table creation.

    See: http://www.postgresql.org/docs/9.1/static/sql-createtable.html

    :param create:      the sqlalchemy CREATE construct
    :param compiler:    the current dialect compiler

    :return: the compiled SQL string

    """
    if 'UNLOGGED' not in create.element._prefixes:
        create.element._prefixes.append('UNLOGGED')
        return compiler.visit_create_table(create)


@pytest.fixture(scope='session', autouse=True)
def create_tables(request):
    """
    Creates the database tables for the entire testing session

    :param request: the testing context

    :returns: configured database session
    """
    import os
    from sqlalchemy import create_engine
    from occams_datastore import models as datastore
    from occams_studies import models
    from occams_roster import models as roster, Session as RosterSession

    db_url = request.config.getoption('--db')
    reuse = request.config.getoption('--reuse')

    engine = create_engine(db_url)
    url = engine.url

    RosterSession.configure(bind=create_engine('sqlite://'))
    roster.Base.metadata.create_all(RosterSession.bind)

    if not reuse:
        # This is very similar to the init_db script: create tables
        # and pre-populate with expected data
        datastore.DataStoreModel.metadata.create_all(engine)
        models.Base.metadata.create_all(engine)

    def drop_tables():
        if url.drivername == 'sqlite':
            if url.database not in ('', ':memory:'):
                os.unlink(url.database)
        elif not reuse:
            models.Base.metadata.drop_all(engine)
            datastore.DataStoreModel.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


@pytest.yield_fixture
def config(request):
    """
    Configuration for integration testing
    """

    from sqlalchemy import create_engine
    from pyramid import testing
    import transaction
    from occams_studies import models, Session as db_session

    db_url = request.config.getoption('--db')

    engine = create_engine(db_url)
    db_session.configure(bind=engine)
    test_config = testing.setUp()

    blame = models.User(key=u'tester')
    db_session.add(blame)
    db_session.flush()
    db_session.info['blame'] = blame
    db_session.info['settings'] = test_config.registry.settings

    _install_workflow(db_session)

    test_config.include('occams_studies.routes')

    yield test_config

    testing.tearDown()
    transaction.abort()
    db_session.remove()


@pytest.fixture
@pytest.mark.usefixtures('create_tables')
def celery(request):
    import shutil
    import tempfile
    import mock
    from redis import StrictRedis
    from sqlalchemy import create_engine
    from occams.celery import Session
    from occams_studies import tasks, models

    settings = {
        'studies.export.dir': tempfile.mkdtemp(),
        'celery.blame': 'dummy',
    }

    tasks.app.userid = settings['celery.blame']
    tasks.app.redis = StrictRedis.from_url(REDIS_URL)
    tasks.app.settings = settings

    db_url = request.config.getoption('--db')
    engine = create_engine(db_url)
    Session.configure(bind=engine, info={'settings': settings})
    Session.add(models.User(key=settings['celery.blame']))
    Session.flush()

    commitmock = mock.patch('occams_studies.tasks.Session.commit')
    commitmock.start()

    def cleanup():
        commitmock.stop()
        shutil.rmtree(settings['studies.export.dir'])
        Session.remove()

    request.addfinalizer(cleanup)


@pytest.fixture
def req(config):
    """
    Returns a dummy request for testings.
    Note that we must called it "req" as "request" is reserved by pytest.
    """
    import uuid
    import mock
    from pyramid.testing import DummyRequest

    csrf_token = str(uuid.uuid4())
    get_csrf_token = mock.Mock(return_value=csrf_token)

    dummy_request = DummyRequest()
    dummy_request.session.get_csrf_token = get_csrf_token
    dummy_request.headers['X-CSRF-Token'] = csrf_token

    return dummy_request


@pytest.fixture
def db_session(config):
    from occams_studies import Session
    return Session


@pytest.fixture(scope='session')
def wsgi(request):
    """
    Sets up a singleton WSGI app
    """
    import tempfile
    import shutil
    import six
    from occams import main

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

    db_url = request.config.getoption('--db')

    tmp_dir = tempfile.mkdtemp()

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

        'occams.db.url': db_url,
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

    def cleanup():
        shutil.rmtree(tmp_dir)

    request.addfinalizer(cleanup)

    return wsgi


@pytest.yield_fixture
def app(request, wsgi, db_session):
    """
    Initiates a user request against a WSGI stack for functional testing
    """
    import transaction
    from webtest import TestApp
    from zope.sqlalchemy import mark_changed

    app = TestApp(wsgi)

    with transaction.manager:
        _install_workflow(db_session)

    yield app

    with transaction.manager:
        # DELETE is dramatically faster than TRUNCATE
        # http://stackoverflow.com/a/11423886/148781
        # We also have to do this as a raw query becuase SA does
        # not have a way to invoke server-side cascade
        db_session.execute('DELETE FROM "study" CASCADE')
        db_session.execute('DELETE FROM "patient" CASCADE')
        db_session.execute('DELETE FROM "site" CASCADE')
        db_session.execute('DELETE FROM "schema" CASCADE')
        db_session.execute('DELETE FROM "export" CASCADE')
        db_session.execute('DELETE FROM "state" CASCADE')
        db_session.execute('DELETE FROM "user" CASCADE')
        mark_changed(db_session())
    db_session.remove()


def _install_workflow(db_session):
    from occams_studies import models

    blame = models.User(key=u'installer')
    db_session.add(blame)
    db_session.flush()
    db_session.info['blame'] = blame

    # Add hard-coded default states
    db_session.add_all([
        models.State(name=u'pending-entry', title=u'Pending Entry'),
        models.State(name=u'pending-review', title=u'Pending Review'),
        models.State(name=u'pending-correction',
                     title=u'Pending Correction'),
        models.State(name=u'complete', title=u'Complete')
    ])
