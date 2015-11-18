"""
Testing fixtures

Execute:
    py.test --db=postgresql://USER:PASS@/DATABASE
"""

import pytest

_user = u'bitcore@ucsd.edu'


def pytest_addoption(parser):
    """
    Registers a command line argument for a database URL connection string
    """
    parser.addoption('--db', action='store', help='db string for testing')
    parser.addoption('--reuse', action='store_true',
                     help='Reuses existing database')


@pytest.yield_fixture(scope='session')
def engine(request):
    from sqlalchemy import create_engine
    from occams_datastore import models
    db_url = request.config.getoption('--db')
    reuse = request.config.getoption('--reuse')
    engine = create_engine(db_url)
    if not reuse:
        with engine.begin() as connection:
            connection.info['blame'] = 'test_installer'
            models.DataStoreModel.metadata.create_all(connection)
            # Clear states since we'll be truncating on tear down
            connection.execute('DELETE FROM state')

    yield engine
    if not reuse:
        models.DataStoreModel.metadata.drop_all(bind=engine)


@pytest.fixture(scope='session')
def sessionmaker(engine):
    from sqlalchemy import orm
    from occams_datastore.models.events import register
    Session = orm.sessionmaker(bind=engine)
    register(Session)
    return Session


@pytest.yield_fixture
def db_session(sessionmaker):
    from occams_datastore import models
    session = sessionmaker()
    blame = models.User(key=u'tester')
    session.add(blame)
    session.flush()
    session.info['blame'] = blame
    yield session
    session.rollback()
