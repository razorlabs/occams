"""
Testing fixtures

To run the tests yo'll then need to run the following command:

    py.test --db=postgres://user:pass@host/db

Also, you can reuse a database:

    py.test --db=postgres://user:pass@host/db --reuse

This is particularly handing while developing as it saves about a minute
each time the tests are run.

"""

import pytest

from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles

USERID = 'test_user'

def pytest_addoption(parser):
    """
    Registers a command line argument for a database URL connection string

    :param parser: The pytest command-line parser
    """
    parser.addoption('--db', action='store', help='db string for testing')
    parser.addoption('--redis', action='store', help='redis uri for testing')
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
    from sqlalchemy import create_engine
    from occams.models import set_pg_locals
    from occams.models.meta import Base

    db_url = request.config.getoption('--db')
    reuse = request.config.getoption('--reuse')

    engine = create_engine(db_url)

    if not reuse:
        with engine.connect() as connection:
            set_pg_locals(connection, 'pytest', USERID)
            # This is very similar to the init_db script: create tables
            # and pre-populate with expected data
            Base.metadata.create_all(connection)
            # Don't include state data since we'll be constantly truncating
            connection.execute('DELETE FROM state')

    def drop_tables():
        if not reuse:
            Base.metadata.drop_all(engine)

    request.addfinalizer(drop_tables)


@pytest.fixture
def config(request):
    """
    (Integration Testing) Instantiates a Pyramid testing configuration

    :param request: The pytest context
    """

    from pyramid import testing
    import transaction

    db_url = request.config.getoption('--db')

    test_config = testing.setUp(settings={
        'sqlalchemy.url': db_url
    })

    # Load mimimum set of plugins
    test_config.include('occams.models')
    test_config.include('occams.routes')

    yield test_config

    testing.tearDown()
    transaction.abort()


@pytest.fixture
def dbsession(config):
    """
    (Integartion Testing) Instantiates a database session.

    :param config: The pyramid testing configuartion

    :returns: An instantiated sqalchemy database session
    """
    from occams import models
    from occams.models import set_pg_locals, get_tm_session
    import transaction

    session_factory = config.registry['dbsession_factory']
    dbsession = get_tm_session(session_factory, transaction.manager)

    set_pg_locals(dbsession.bind, 'pytest', USERID)

    # Other expected settings
    dbsession.info['settings'] = config.registry.settings

    # Hardcoded workflow
    dbsession.add_all([
        models.State(name='pending-entry', title='Pending Entry'),
        models.State(name='pending-review', title='Pending Review'),
        models.State(name='pending-correction', title='Pending Correction'),
        models.State(name='complete', title='Complete')
    ])

    return dbsession


@pytest.fixture
def req(dbsession):
    """
    (Integration Testing) Creates a dummy request

    The request is setup with configuration CSRF values and the expected
    ``dbsession`` property, the goal being to be be as close to a real
    database session as possible.

    Note that we must called it "req" as "request" is reserved by pytest.

    :param dbsession: The testing database session

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
    dummy_request.dbsession = dbsession
    dbsession.info['request'] = dummy_request

    return dummy_request


@pytest.fixture
def factories(dbsession):
    """
    Configures the data factories

    :param dbsession: testing session fixture
    :returns: the configured factories module
    """

    import inspect
    from . import factories

    classes = inspect.getmembers(factories, inspect.isclass)

    for class_name, class_ in classes:
        if hasattr(class_, '_meta') and hasattr(class_._meta, 'model'):
            class_._meta.sqlalchemy_session = dbsession

    return factories

