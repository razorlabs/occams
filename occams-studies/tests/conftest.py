"""
Testing fixtures

To run the tests you'll then need to run the following command:

    py.test --db=postgres://user:pass@host/db

Also, you can reuse a database:

    py.test --db=postgres://user:pass@host/db --reuse

This is particularly handing while developing as it saves about a minute
each time the tests are run.

"""

import pytest

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles


REDIS_URL = 'redis://localhost/9'

USERID = 'test_user'


def pytest_addoption(parser):
    """
    Registers a command line argument for a database URL connection string

    :param parser: The pytest command-line parser
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

    :param request: The pytest context

    :returns: configured database session
    """
    import os
    from sqlalchemy import create_engine
    from occams_datastore import models as datastore
    from occams_studies import models

    db_url = request.config.getoption('--db')
    reuse = request.config.getoption('--reuse')

    engine = create_engine(db_url)
    url = engine.url

    if not reuse:
        with engine.connect() as connection:
            connection.info['blame'] = 'test_installer'
            # This is very similar to the init_db script: create tables
            # and pre-populate with expected data
            datastore.DataStoreModel.metadata.create_all(connection)
            models.StudiesModel.metadata.create_all(connection)
            # Don't include state data since we'll be constantly truncating
            connection.execute('DELETE FROM state')

    def drop_tables():
        if url.drivername == 'sqlite':
            if url.database not in ('', ':memory:'):
                os.unlink(url.database)
        elif not reuse:
            models.StudiesModel.metadata.drop_all(engine)
            datastore.DataStoreModel.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


@pytest.yield_fixture
def config(request):
    """
    (Integration Testing) Instantiates a Pyramid testing configuration

    :param request: The pytest context
    """

    from pyramid import testing
    import transaction

    db_url = request.config.getoption('--db')

    test_config = testing.setUp(settings={
        'occams.db.url': db_url
    })

    # Load mimimum set of plugins
    test_config.include('occams.models')
    test_config.include('occams_studies.routes')

    yield test_config

    testing.tearDown()
    transaction.abort()


@pytest.fixture
def db_session(config):
    """
    (Integartion Testing) Instantiates a database session.

    :param config: The pyramid testing configuartion

    :returns: An instantiated sqalchemy database session
    """
    from occams_datastore import models as datastore
    import occams_datastore.models.events
    import zope.sqlalchemy

    db_session = config.registry['dbsession_factory']()

    occams_datastore.models.events.register(db_session)
    zope.sqlalchemy.register(db_session)

    # Pre-configure with a blame user
    blame = datastore.User(key=USERID)
    db_session.add(blame)
    db_session.flush()
    db_session.info['blame'] = blame

    # Other expected settings
    db_session.info['settings'] = config.registry.settings

    # Hardcoded workflow
    db_session.add_all([
        datastore.State(name=u'pending-entry', title=u'Pending Entry'),
        datastore.State(name=u'pending-review', title=u'Pending Review'),
        datastore.State(name=u'pending-correction',
                        title=u'Pending Correction'),
        datastore.State(name=u'complete', title=u'Complete')
    ])

    return db_session


@pytest.fixture
def req(db_session):
    """
    (Integration Testing) Creates a dummy request

    The request is setup with configuration CSRF values and the expected
    ``db_session`` property, the goal being to be be as close to a real
    database session as possible.

    Note that we must called it "req" as "request" is reserved by pytest.

    :param db_session: The testing database session

    :returns: a configured request object
    """
    import uuid
    import mock
    from pyramid.testing import DummyRequest

    dummy_request = DummyRequest()

    # Configurable csrf token
    csrf_token = str(uuid.uuid4())
    get_csrf_token = mock.Mock(return_value=csrf_token)
    dummy_request.session.get_csrf_token = get_csrf_token
    dummy_request.headers['X-CSRF-Token'] = csrf_token

    # Attach database session for expected behavior
    dummy_request.db_session = db_session
    db_session.info['request'] = dummy_request

    return dummy_request


@pytest.fixture
def factories(db_session):
    """
    Configures the data factories

    :param db_session: testing session fixture
    :returns: the configured factories module
    """

    import inspect
    from . import factories

    classes = inspect.getmembers(factories, inspect.isclass)

    for class_name, class_ in classes:
        if hasattr(class_, '_meta') and hasattr(class_._meta, 'model'):
            class_._meta.sqlalchemy_session = db_session

    return factories


@pytest.fixture(scope='session')
def wsgi(request):
    """
    (Functional Testing) Sets up a full-stacked singleton WSGI app

    :param request: The pytest context

    :returns: a WSGI application
    """
    import os
    import tempfile
    import shutil
    import sqlalchemy as sa
    import six
    from occams import main
    from occams_roster import models as roster

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

    roster_path = os.path.join(tmp_dir, 'roster.db')
    roster_url = 'sqlite:///{}'.format(roster_path)

    roster_engine = sa.create_engine(roster_url)
    roster.Base.metadata.create_all(roster_engine)

    wsgi = main({}, **{
        'redis.url': REDIS_URL,
        'redis.sessions.secret': 'sekrit',

        'who.config_file': who_ini.name,
        'who.identifier_id': '',

        # Enable regular error messages so we can see useful traceback
        'debugtoolbar.enabled': True,
        'pyramid.debug_all': True,

        'webassets.debug': True,

        'occams.apps': ['occams_studies', 'occams_roster'],

        'occams.db.url': db_url,
        'occams.groups': [],

        'celery.broker.url': REDIS_URL,
        'celery.backend.url': REDIS_URL,
        'celery.blame': 'celery@localhost',

        'studies.export.dir': '/tmp',
        'studies.export.plans': [
            'occams_studies.exports.pid.PidPlan',
            'occams_studies.exports.enrollment.EnrollmentPlan',
            'occams_studies.exports.visit.VisitPlan',
            'occams_studies.exports.schema.SchemaPlan.list_all',
        ],
        'studies.pid.package': 'occams_roster',
        'studies.blob.dir': '/tmp',

        'roster.db.url': roster_url,
    })

    who_ini.close()

    def cleanup():
        os.unlink(roster_path)
        shutil.rmtree(tmp_dir)

    request.addfinalizer(cleanup)

    return wsgi


@pytest.yield_fixture
def app(request, wsgi, db_session):
    """
    (Functional Testing) Initiates a user request against a WSGI stack

    :param request: The pytest context
    :param wsgi: An initialized WSGI stack
    :param db_session: A database session for seting up pre-existing data

    :returns: a test app request against the WSGI instance
    """
    import transaction
    from webtest import TestApp
    from zope.sqlalchemy import mark_changed
    from occams_datastore import models as datastore

    # Save all changes up tho this point (db_session does some configuration)
    with transaction.manager:
        blame = datastore.User(key='workflow@localhost')
        db_session.add(blame)
        db_session.flush()
        db_session.info['blame'] = blame

        db_session.add_all([
            datastore.State(name=u'pending-entry', title=u'Pending Entry'),
            datastore.State(name=u'pending-review', title=u'Pending Review'),
            datastore.State(name=u'pending-correction',
                            title=u'Pending Correction'),
            datastore.State(name=u'complete', title=u'Complete')
        ])

    app = TestApp(wsgi)

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
        mark_changed(db_session)


@pytest.fixture
@pytest.mark.usefixtures('create_tables')
def celery(request):
    """
    (Function Testing) Sets up a celery application for testing

    :param request: The pytest context
    """
    import shutil
    import tempfile
    import mock
    from redis import StrictRedis
    from sqlalchemy import create_engine
    from occams.celery import Session
    from occams_datastore import models as datastore
    from occams_studies import tasks

    settings = {
        'studies.export.dir': tempfile.mkdtemp(),
        'celery.blame': USERID
    }

    tasks.app.userid = settings['celery.blame']
    tasks.app.redis = StrictRedis.from_url(REDIS_URL)
    tasks.app.settings = settings

    db_url = request.config.getoption('--db')
    engine = create_engine(db_url)
    Session.configure(bind=engine, info={'settings': settings})
    Session.add(datastore.User(key=settings['celery.blame']))
    Session.flush()

    commitmock = mock.patch('occams_studies.tasks.Session.commit')
    commitmock.start()

    def cleanup():
        commitmock.stop()
        shutil.rmtree(settings['studies.export.dir'])
        Session.remove()

    request.addfinalizer(cleanup)
